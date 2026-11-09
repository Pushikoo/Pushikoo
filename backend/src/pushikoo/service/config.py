from typing import Generic, TypeVar

import threading

from loguru import logger
from pydantic import BaseModel, ValidationError

from pushikoo.db import Config as ConfigDB, get_session

TCONFIG = TypeVar("TCONFIG", bound=BaseModel)


class ConfigService(Generic[TCONFIG]):
    _locks: dict[str, threading.Lock] = {}
    _warned_invalid_keys: set[str] = set()

    def __init__(self, id_: str, model_type: type[TCONFIG] = None):
        self.id = id_
        self.model: type[BaseModel] = model_type

    @classmethod
    def _get_lock(cls, key: str) -> threading.Lock:
        return cls._locks.setdefault(key, threading.Lock())

    def get(self) -> TCONFIG:
        def struct_config():
            try:
                return self.model()
            except Exception:
                return None

        should_warn = False
        invalid_fields: set[str] = set()
        lock = self._get_lock(self.id)
        with lock:
            with get_session() as session:
                row = session.get(ConfigDB, self.id)
                if not row or row.value is None:
                    return struct_config()

                try:
                    return self.model.model_validate(row.value)
                except ValidationError as error:
                    invalid_fields = {
                        str(item["loc"][0])
                        for item in error.errors()
                        if item.get("loc")
                    }
                    if not invalid_fields:
                        invalid_fields.add("<root>")
                    logger.error(
                        "Invalid config for key '{}'; invalid fields: {}",
                        self.id,
                        ", ".join(sorted(invalid_fields)),
                    )

                    if self.id not in self._warned_invalid_keys:
                        self._warned_invalid_keys.add(self.id)
                        should_warn = True

                    defaults = struct_config()
                    recovered_data = (
                        defaults.model_dump() if defaults is not None else {}
                    )
                    if isinstance(row.value, dict):
                        recovered_data.update(
                            {
                                key: value
                                for key, value in row.value.items()
                                if key not in invalid_fields
                            }
                        )

                    try:
                        result = self.model.model_validate(recovered_data)
                    except ValidationError:
                        result = defaults

        if should_warn:
            self._issue_invalid_config_warning(invalid_fields)
        return result

    def _issue_invalid_config_warning(self, invalid_fields: set[str]) -> None:
        try:
            from pushikoo_interface import Struct, StructText

            from pushikoo.service.warning import WarningService

            field_names = ", ".join(sorted(invalid_fields))
            WarningService.issue(
                Struct(
                    content=[
                        StructText(
                            text=(
                                f"Configuration '{self.id}' is invalid in fields "
                                f"{field_names}. Please open the UI and save it again."
                            )
                        )
                    ]
                )
            )
        except Exception as error:
            logger.error(
                "Failed to issue invalid-config warning for key '{}': {}",
                self.id,
                error,
            )

    def set(self, config: TCONFIG):
        data = config.model_dump()
        lock = self._get_lock(self.id)
        with lock:
            with get_session() as session:
                row = session.get(ConfigDB, self.id)
                if row is None:
                    row = ConfigDB(key=self.id, value=data)
                else:
                    row.value = data
                session.add(row)
                session.commit()
            self._warned_invalid_keys.discard(self.id)
        logger.info(f"Updated config: {self.id}")

    def delete(self) -> bool:
        lock = self._get_lock(self.id)
        with lock:
            with get_session() as session:
                row = session.get(ConfigDB, self.id)
                if row is not None:
                    session.delete(row)
                    session.commit()
                    logger.info(f"Deleted config: {self.id}")
                    return True
                return False
