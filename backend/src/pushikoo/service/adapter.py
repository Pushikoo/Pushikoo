import importlib
import sys
import threading
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import FastAPI
from loguru import logger
from pushikoo_interface import (
    Adapter,
    Getter,
    Processer,
    Pusher,
    get_adapter_config_types,
)
from pushikoo_interface import Adapter as InterfaceAdapter
from pushikoo_interface import (
    AdapterFrameworkContext as AdapterFrameworkContextInterface,
)
from pushikoo_interface import (
    AdapterMeta as InterfaceAdapterMeta,
)
from pydantic import ValidationError
from sqlmodel import func, select

from pushikoo.db import AdapterInstance as AdapterInstanceDB
from pushikoo.db import get_session
from pushikoo.model.adapter import (
    AdapterInstance,
    AdapterInstanceCreate,
    AdapterInstanceListFilter,
    AdapterMeta,
    AdapterType,
)
from pushikoo.model.config import SystemConfig
from pushikoo.model.pagination import Page, apply_page_limit
from pushikoo.service.base import (
    ConflictException,
    InvalidInputException,
    NotFoundException,
)
from pushikoo.service.config import ConfigService
from pushikoo.util.setting import DATA_DIR, settings

ADAPTER_ENTRY_GROUP = "pushikoo.adapter"
adapter_container_app = FastAPI()


def _remove_routes_by_prefix(prefix: str) -> None:
    """Remove all routes from adapter_container_app whose path starts with prefix."""
    adapter_container_app.router.routes = [
        r
        for r in adapter_container_app.router.routes
        if not getattr(r, "path", "").startswith(prefix)
    ]


def _set_adapter_router(adapter_name: str, adapter_class: type[Adapter]) -> None:
    prefix = f"/adapters/{adapter_name}"
    _remove_routes_by_prefix(prefix)
    try:
        router = adapter_class.get_adapter_router()
    except NotImplementedError:
        return
    except Exception as e:
        logger.exception(f"Failed to build adapter router for {adapter_name}: {e}")
        return
    adapter_container_app.include_router(router, prefix=prefix)


def _remove_adapter_router(adapter_name: str) -> None:
    _remove_routes_by_prefix(f"/adapters/{adapter_name}")


def _set_instance_router(instance: InterfaceAdapter) -> None:
    prefix = f"/adapter_instances/{instance.adapter_name}.{instance.identifier}"
    _remove_routes_by_prefix(prefix)
    try:
        router = instance.get_instance_router()
    except NotImplementedError:
        return
    except Exception as e:
        logger.exception(f"Failed to build instance router for {instance}: {e}")
        return
    adapter_container_app.include_router(router, prefix=prefix)


def _remove_instance_router(adapter_name: str, identifier: str) -> None:
    _remove_routes_by_prefix(f"/adapter_instances/{adapter_name}.{identifier}")


class AdapterFrameworkContext(AdapterFrameworkContextInterface):
    storage_base_path: Path = DATA_DIR / "adapters" / "storage"
    adapter_base_url: str = ""
    instance_base_url: str = ""

    def get_proxies(self) -> dict[str, str]:
        return ConfigService("system", SystemConfig).get().network.proxies


class AdapterService:
    """Service for managing adapter discovery and instantiation."""

    adapters: dict[str, type] = {}
    adapter_versions: dict[str, str] = {}
    adapter_metas: dict[str, InterfaceAdapterMeta] = {}

    ensure_load_adapter_lock = threading.Lock()

    @staticmethod
    def _discover() -> list[EntryPoint]:
        """Discover all adapter entry points."""
        return list(entry_points().select(group=ADAPTER_ENTRY_GROUP))

    @staticmethod
    def _remove_module_recursively(module_name: str):
        for sys_module_name in list(sys.modules):
            if sys_module_name.startswith(module_name):
                sys.modules.pop(sys_module_name)

    @staticmethod
    def _inject_class_context(cls: type[Adapter], adapter_name: str) -> None:
        """Inject a class-level context into the adapter class"""
        ctx = AdapterFrameworkContext()
        ctx.adapter_base_url = (
            f"{settings.BACKEND_BASE_HOST}/ext/adapters/{adapter_name}"
        )
        ctx.get_proxies = lambda: (
            ConfigService("system", SystemConfig).get().network.proxies
        )

        adapter_config_type, _ = get_adapter_config_types(cls)
        ctx.get_config = lambda: ConfigService(adapter_name, adapter_config_type).get()

        cls.ctx = ctx
        cls.adapter_name = adapter_name
        cls.adapter_storage_path = ctx.storage_base_path / adapter_name
        cls.adapter_storage_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _force_load_adapter(entry_point: EntryPoint) -> type:
        """Force reload an adapter module and return its class.

        If loading fails, removes the adapter from cache to prevent inconsistent state.
        """
        module_name = entry_point.value.split(":")[0].split(".")[0]
        dist_name = entry_point.dist.name
        AdapterService._remove_module_recursively(module_name)

        try:
            importlib.import_module(module_name)
            return entry_point.load()
        except Exception as e:
            logger.exception(f"Failed to load adapter {dist_name}: {e}")
            # Clean up to prevent inconsistent state
            AdapterService.adapters.pop(dist_name, None)
            AdapterService.adapter_versions.pop(dist_name, None)
            AdapterService.adapter_metas.pop(dist_name, None)
            raise

    @staticmethod
    def ensure_load_adapter():
        with AdapterService.ensure_load_adapter_lock:
            discovered_eps = AdapterService._discover()
            discovered_names = {ep.dist.name for ep in discovered_eps}

            # Remove uninstalled adapters
            for name in list(AdapterService.adapters.keys()):
                if name not in discovered_names:
                    logger.info(f"Adapter {name} was uninstalled, removing from cache")
                    AdapterService.adapters.pop(name, None)
                    AdapterService.adapter_versions.pop(name, None)
                    AdapterService.adapter_metas.pop(name, None)
                    _remove_adapter_router(name)

            # Load or reload adapters
            for ep in discovered_eps:
                name = ep.dist.name
                if (
                    name not in AdapterService.adapter_versions
                    or ep.dist.version != AdapterService.adapter_versions[name]
                ):
                    logger.debug(f"Loading or reloading adapter {name}...")
                    try:
                        cls = AdapterService._force_load_adapter(ep)
                        AdapterService._inject_class_context(cls, name)
                        AdapterService.adapters[name] = cls
                        AdapterService.adapter_versions[name] = ep.dist.version
                        AdapterService.adapter_metas[name] = getattr(cls, "meta", None)
                        _set_adapter_router(name, cls)
                    except Exception:
                        _remove_adapter_router(name)
                        # Error already logged in _force_load_adapter, continue with other adapters
                        continue

    @staticmethod
    def list_all_adapter_with_type() -> list[tuple[type, AdapterMeta]]:
        """List all available adapter classes with metadata including adapter type."""
        result: list[tuple[type, AdapterMeta]] = []
        AdapterService.ensure_load_adapter()

        for adapter_name, cls in AdapterService.adapters.items():
            meta = AdapterService.adapter_metas[adapter_name]
            if issubclass(cls, Getter):
                adapter_type = AdapterType.GETTER
            elif issubclass(cls, Pusher):
                adapter_type = AdapterType.PUSHER
            elif issubclass(cls, Processer):
                adapter_type = AdapterType.PROCESSER
            else:
                raise InvalidInputException(
                    f"Adapter {cls.__name__} must be subclass of Getter, Pusher or Processer"
                )

            enriched_meta = AdapterMeta(
                **meta.model_dump(),
                type=adapter_type,
            )
            result.append((cls, enriched_meta))

        return result

    @staticmethod
    def get_clsobj_by_name(adapter_name) -> type[Adapter]:
        """Get adapter class by name."""
        AdapterService.ensure_load_adapter()
        adapter_matched = [
            (stored_adapter_name, stored_adapter_class)
            for stored_adapter_name, stored_adapter_class in AdapterService.adapters.items()
            if stored_adapter_name == adapter_name
        ]
        if not adapter_matched:
            raise NotFoundException(f"Adapter class {adapter_name} not found")

        _adapter_name, AdapterClass = adapter_matched[0]
        return AdapterClass

    @staticmethod
    def create_instance(name: str, identifier: str):
        """Create an adapter instance."""
        obj = AdapterService.get_clsobj_by_name(name)
        adapter_config_type, adapter_config_inst_type = get_adapter_config_types(obj)
        ctx = AdapterFrameworkContext()
        ctx.get_config = lambda: ConfigService(name, adapter_config_type).get()
        ctx.get_instance_config = lambda: ConfigService(
            f"{name}.{identifier}", adapter_config_inst_type
        ).get()
        ctx.adapter_base_url = f"{settings.BACKEND_BASE_HOST}/ext/adapters/{name}"
        ctx.instance_base_url = (
            f"{settings.BACKEND_BASE_HOST}/ext/adapter_instances/{name}.{identifier}"
        )
        instance = obj.create(identifier=identifier, ctx=ctx)
        logger.debug(f"Created adapter instance: {name}.{identifier}")
        return instance

    @staticmethod
    def get_config(name: str) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        adapter_config_type, _ = get_adapter_config_types(obj)

        return ConfigService(name, adapter_config_type).get().model_dump()

    @staticmethod
    def set_config(name: str, config_data: dict[str, Any]) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        adapter_config_type, _ = get_adapter_config_types(obj)
        try:
            config_model = adapter_config_type.model_validate(config_data)
        except ValidationError as e:
            logger.warning(
                f"Failed to validate adapter config for {name} when setting: {e}"
            )
            raise

        ConfigService(name, adapter_config_type).set(config_model)
        return config_model.model_dump()

    @staticmethod
    def get_config_jsonschema(name: str) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        adapter_config_type, _ = get_adapter_config_types(obj)
        return adapter_config_type.model_json_schema()

    @staticmethod
    def get_instance_config_jsonschema(name: str) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        _, adapter_config_inst_type = get_adapter_config_types(obj)
        return adapter_config_inst_type.model_json_schema()


class AdapterInstanceService:
    instance_objects: dict[UUID, InterfaceAdapter] = {}
    instance_versions: dict[UUID, str] = {}
    instance_lock = threading.Lock()

    @staticmethod
    def get_object(adapter_name: str, identifier: str) -> InterfaceAdapter:
        result = next(
            (
                i
                for i in AdapterInstanceService.instance_objects.values()
                if i.adapter_name == adapter_name and i.identifier == identifier
            ),
            None,
        )
        if result is None:
            raise NotFoundException(
                f"Adapter instance object {adapter_name}.{identifier} not found in cache"
            )
        return result

    @staticmethod
    def ensure_load_instance(instance_id: UUID) -> None:
        with get_session() as session:
            row = session.get(AdapterInstanceDB, instance_id)

        if not row:
            raise NotFoundException(f"Adapter instance {instance_id} not found")

        adapter_class = AdapterService.get_clsobj_by_name(row.adapter_name)
        current_version = adapter_class.meta.version

        with AdapterInstanceService.instance_lock:
            cached_version = AdapterInstanceService.instance_versions.get(instance_id)
            if cached_version == current_version:
                return

            if cached_version is not None:
                logger.info(
                    f"Adapter version changed for {row.adapter_name}.{row.identifier}: "
                    f"{cached_version} -> {current_version}, re-instantiating"
                )

            instance = AdapterService.create_instance(row.adapter_name, row.identifier)
            AdapterInstanceService.instance_objects[instance_id] = instance
            AdapterInstanceService.instance_versions[instance_id] = current_version
            _set_instance_router(instance)

    @staticmethod
    def ensure_load_all_instances() -> None:
        with get_session() as session:
            rows = session.exec(select(AdapterInstanceDB)).all()
        for row in rows:
            try:
                AdapterInstanceService.ensure_load_instance(row.id)
            except Exception:
                logger.exception(
                    f"Failed to load instance {row.adapter_name}.{row.identifier}"
                )

    @staticmethod
    def get_object_by_id(instance_id: UUID) -> InterfaceAdapter:
        AdapterInstanceService.ensure_load_instance(instance_id)
        return AdapterInstanceService.instance_objects[instance_id]

    @staticmethod
    def get(instance_id: UUID) -> AdapterInstance:
        """Get an adapter instance by ID, returning the Pydantic model."""
        with get_session() as session:
            row = session.get(AdapterInstanceDB, instance_id)

        if not row:
            raise NotFoundException(f"Adapter instance {instance_id} not found")

        return AdapterInstance(
            id=row.id,
            adapter_name=row.adapter_name,
            identifier=row.identifier,
        )

    @staticmethod
    def create(instance_create: AdapterInstanceCreate) -> AdapterInstance:
        with get_session() as session:
            # Check for duplicate (adapter_name, identifier)
            existing = session.exec(
                select(AdapterInstanceDB).where(
                    AdapterInstanceDB.adapter_name == instance_create.adapter_name,
                    AdapterInstanceDB.identifier == instance_create.identifier,
                )
            ).first()
            if existing:
                raise ConflictException(
                    f"Adapter instance {instance_create.adapter_name}.{instance_create.identifier} already exists"
                )

            db_obj = AdapterInstanceDB(
                adapter_name=instance_create.adapter_name,
                identifier=instance_create.identifier,
            )
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)

        logger.info(
            f"Created adapter instance: {instance_create.adapter_name}.{instance_create.identifier}"
        )
        result = AdapterInstance(
            id=db_obj.id,
            adapter_name=db_obj.adapter_name,
            identifier=db_obj.identifier,
        )
        # Eagerly instantiate so the instance router is registered immediately
        AdapterInstanceService.get_object_by_id(db_obj.id)
        return result

    @staticmethod
    def list(filter: AdapterInstanceListFilter) -> Page[AdapterInstance]:
        with get_session() as session:
            q = select(AdapterInstanceDB)
            if filter:
                if filter.adapter_name is not None:
                    q = q.where(AdapterInstanceDB.adapter_name == filter.adapter_name)
                if filter.identifier is not None:
                    q = q.where(AdapterInstanceDB.identifier == filter.identifier)

            # Get total count before pagination
            count_q = select(func.count()).select_from(q.subquery())
            total = session.exec(count_q).one()

            q = q.order_by(AdapterInstanceDB.adapter_name, AdapterInstanceDB.identifier)
            if filter and filter.offset is not None:
                q = q.offset(filter.offset)
            if filter and filter.limit is not None:
                q = q.limit(apply_page_limit(filter.limit))
            rows = session.exec(q).all()
            items = [
                AdapterInstance(
                    id=i.id, adapter_name=i.adapter_name, identifier=i.identifier
                )
                for i in rows
            ]

            return Page(
                items=items,
                total=total,
                limit=filter.limit if filter else None,
                offset=filter.offset if filter else None,
            )

    @staticmethod
    def delete(adapter_name: str, identifier: str) -> None:
        with get_session() as session:
            instance_record = session.exec(
                select(AdapterInstanceDB).where(
                    (AdapterInstanceDB.adapter_name == adapter_name)
                    & (AdapterInstanceDB.identifier == identifier)
                )
            ).first()

            if not instance_record:
                raise NotFoundException("Adapter instance not found")

            instance_id = instance_record.id
            session.delete(instance_record)
            session.commit()

        AdapterInstanceService.instance_objects.pop(instance_id, None)
        AdapterInstanceService.instance_versions.pop(instance_id, None)
        _remove_instance_router(adapter_name, identifier)

        logger.info(f"Deleted adapter instance: {adapter_name}.{identifier}")

    @staticmethod
    def get_config(name, identifier):
        obj = AdapterService.get_clsobj_by_name(name)
        _, adapter_inst_config_type = get_adapter_config_types(obj)
        return ConfigService(f"{name}.{identifier}", adapter_inst_config_type).get()

    @staticmethod
    def set_config(name: str, identifier: str, config_data: dict[str, Any]) -> dict:
        obj = AdapterService.get_clsobj_by_name(name)
        _, adapter_inst_config_type = get_adapter_config_types(obj)
        try:
            config_model = adapter_inst_config_type.model_validate(config_data)
        except ValidationError as e:
            logger.warning(
                f"Failed to validate adapter instance config for {name}.{identifier} when setting: {e}"
            )
            raise

        ConfigService(f"{name}.{identifier}", adapter_inst_config_type).set(
            config_model
        )
        return config_model.model_dump()
