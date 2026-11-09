import datetime
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
from uuid import UUID

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from pushikoo_interface import (
    Detail,
    Getter,
    Processer,
    Pusher,
    Struct,
    StructImage,
    StructText,
    TerminateFlowException,
)
from sqlalchemy import delete, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import func, select

from pushikoo.db import AdapterInstance as AdapterInstanceDB
from pushikoo.db import Flow as FlowDB
from pushikoo.db import FlowCron as FlowCronDB
from pushikoo.db import FlowInstance as FlowInstanceDB
from pushikoo.db import FlowItem as FlowItemDB
from pushikoo.db import FlowMessage as FlowMessageDB
from pushikoo.db import FlowNodeExecution as FlowNodeExecutionDB
from pushikoo.db import Message as MessageDB
from pushikoo.db import get_session
from pushikoo.model.config import SystemConfig
from pushikoo.model.cron import Cron, CronCreate, CronListFilter, CronUpdate
from pushikoo.model.flow import (
    Flow,
    FlowCreate,
    FlowInstanceKind,
    FlowInstanceListFilter,
    FlowInstanceOrder,
    FlowInstanceStatus,
    FlowItem,
    FlowItemActionRequest,
    FlowItemCounts,
    FlowItemDismissResponse,
    FlowItemListFilter,
    FlowItemRetryResponse,
    FlowItemStatus,
    FlowListFilter,
    FlowUpdate,
)
from pushikoo.model.flow import (
    FlowInstance as FlowInstanceModel,
)
from pushikoo.model.pagination import Page, apply_page_limit
from pushikoo.service.adapter import AdapterInstanceService
from pushikoo.service.config import ConfigService
from pushikoo.service.image import ImageService
from pushikoo.service.message import MessageService
from pushikoo.service.warning import WarningService
from pushikoo.service.base import (
    ConflictException,
    InvalidInputException,
    NotFoundException,
)
from pushikoo.util.setting import CRON_SCHEDULER_MAX_WORKERS

getter_get_timeline_continuous_failed_times: dict[tuple[str, str], int] = {}


class FlowService:
    @staticmethod
    def _to_model(session, flow_db: FlowDB) -> Flow:
        return Flow(
            id=flow_db.id,
            name=flow_db.name,
            nodes=list(flow_db.nodes or []),
        )

    @staticmethod
    def create(flow_create: FlowCreate) -> Flow:
        with get_session() as session:
            if not flow_create.nodes:
                raise InvalidInputException("Flow must have at least one node")

            # Validate all nodes exist
            for adapter_instance_id in flow_create.nodes:
                adapter_db = session.exec(
                    select(AdapterInstanceDB).where(
                        AdapterInstanceDB.id == adapter_instance_id
                    )
                ).first()
                if not adapter_db:
                    raise InvalidInputException(
                        f"Flow node adapter instance not found: {adapter_instance_id}"
                    )

            flow_db = FlowDB(name=flow_create.name, nodes=list(flow_create.nodes))
            session.add(flow_db)
            session.flush()

            session.commit()
            logger.info(f"Created flow {flow_db.id}")
            return FlowService._to_model(session, flow_db)

    @staticmethod
    def list_(filter: FlowListFilter) -> Page[Flow]:
        with get_session() as session:
            # When filtering by getter_instance_id we must filter in Python,
            # because getter is encoded as the first node in the JSON list.
            if filter and filter.getter_instance_id is not None:
                all_rows = session.exec(select(FlowDB).order_by(FlowDB.id)).all()
                filtered_rows = [
                    f
                    for f in all_rows
                    if f.nodes and f.nodes[0] == filter.getter_instance_id
                ]
                total = len(filtered_rows)
                if filter.offset is not None:
                    filtered_rows = filtered_rows[filter.offset :]
                if filter.limit is not None:
                    filtered_rows = filtered_rows[: filter.limit]
                rows = filtered_rows
            else:
                # Get total count
                count_q = select(func.count()).select_from(FlowDB)
                total = session.exec(count_q).one()

                q = select(FlowDB).order_by(FlowDB.id)
                if filter and filter.offset is not None:
                    q = q.offset(filter.offset)
                if filter and filter.limit is not None:
                    q = q.limit(apply_page_limit(filter.limit))
                rows = session.exec(q).all()

            items = [FlowService._to_model(session, f) for f in rows]
            return Page(
                items=items,
                total=total,
                limit=filter.limit if filter else None,
                offset=filter.offset if filter else None,
            )

    @staticmethod
    def get(flow_id: UUID) -> Flow:
        with get_session() as session:
            flow_db = session.exec(select(FlowDB).where(FlowDB.id == flow_id)).first()

            if not flow_db:
                raise NotFoundException("Flow not found")

            return FlowService._to_model(session, flow_db)

    @staticmethod
    def update(flow_id: UUID, flow_update: FlowUpdate) -> Flow:
        with get_session() as session:
            flow_db = session.exec(select(FlowDB).where(FlowDB.id == flow_id)).first()
            if not flow_db:
                raise NotFoundException("Flow not found")

            if flow_update.name is not None:
                flow_db.name = flow_update.name

            if flow_update.nodes is not None:
                if not flow_update.nodes:
                    raise InvalidInputException("Flow must have at least one node")

                # Validate all nodes exist
                for adapter_instance_id in flow_update.nodes:
                    adapter_db = session.exec(
                        select(AdapterInstanceDB).where(
                            AdapterInstanceDB.id == adapter_instance_id
                        )
                    ).first()
                    if not adapter_db:
                        raise InvalidInputException(
                            f"Flow node adapter instance not found: {adapter_instance_id}"
                        )

                flow_db.nodes = list(flow_update.nodes)

            session.commit()
            logger.info(f"Updated flow {flow_id}")
            return FlowService._to_model(session, flow_db)

    @staticmethod
    def delete(flow_id: UUID) -> None:
        with get_session() as session:
            flow_db = session.exec(select(FlowDB).where(FlowDB.id == flow_id)).first()
            if not flow_db:
                raise NotFoundException("Flow not found")

            # remove related crons for this flow
            flow_crons = session.exec(
                select(FlowCronDB).where(FlowCronDB.flow_id == flow_id)
            ).all()
            for cron in flow_crons:
                session.delete(cron)

            session.execute(
                delete(FlowMessageDB).where(FlowMessageDB.flow_id == flow_id)
            )
            session.delete(flow_db)
            session.commit()

        # reload scheduler to drop any jobs bound to this flow
        CronService._reload()

        logger.info(f"Deleted flow {flow_id}")


class FlowInstanceService:
    @staticmethod
    def _empty_counts() -> dict[str, int]:
        return {status.value: 0 for status in FlowItemStatus}

    @staticmethod
    def _to_model(
        instance_db: FlowInstanceDB, counts: dict[str, int] | None = None
    ) -> FlowInstanceModel:
        return FlowInstanceModel(
            id=instance_db.id,
            flow_id=instance_db.flow_id,
            status=FlowInstanceStatus(instance_db.status),
            kind=FlowInstanceKind(instance_db.kind),
            parent_instance_id=instance_db.parent_instance_id,
            nodes=list(instance_db.nodes or []),
            cursor=instance_db.cursor,
            created_at=instance_db.created_at,
            item_counts=FlowItemCounts(
                **(counts or FlowInstanceService._empty_counts())
            ),
        )

    @staticmethod
    def _counts_for(session, instance_ids: list[UUID]) -> dict[UUID, dict[str, int]]:
        counts = {
            instance_id: FlowInstanceService._empty_counts()
            for instance_id in instance_ids
        }
        if not instance_ids:
            return counts
        rows = session.exec(
            select(
                FlowItemDB.flow_instance_id,
                FlowItemDB.status,
                func.count(FlowItemDB.id),
            )
            .where(FlowItemDB.flow_instance_id.in_(instance_ids))
            .group_by(FlowItemDB.flow_instance_id, FlowItemDB.status)
        ).all()
        for instance_id, status, count in rows:
            if status in counts[instance_id]:
                counts[instance_id][status] = count
        return counts

    @staticmethod
    def create(
        flow_id: UUID,
        nodes: list[str] | None = None,
        status: FlowInstanceStatus = FlowInstanceStatus.WAITING,
    ) -> FlowInstanceModel:
        with get_session() as session:
            if nodes is None:
                flow_db = session.get(FlowDB, flow_id)
                if not flow_db:
                    raise NotFoundException(f"Flow not found: {flow_id}")
                nodes = list(flow_db.nodes or [])
            instance_db = FlowInstanceDB(
                flow_id=flow_id, status=status.value, nodes=nodes, cursor=0
            )
            session.add(instance_db)
            session.commit()
            session.refresh(instance_db)
            logger.info(f"Created flow instance {instance_db.id} for flow {flow_id}")
            return FlowInstanceService._to_model(instance_db)

    @staticmethod
    def update_status(
        instance_id: UUID, status: FlowInstanceStatus
    ) -> FlowInstanceModel:
        with get_session() as session:
            instance_db = session.exec(
                select(FlowInstanceDB).where(FlowInstanceDB.id == instance_id)
            ).first()

            if not instance_db:
                raise NotFoundException("Flow instance not found")

            instance_db.status = status.value
            session.add(instance_db)
            session.commit()
            session.refresh(instance_db)
            logger.info(f"Updated flow instance {instance_id} status to {status.value}")
            return FlowInstanceService._to_model(instance_db)

    @staticmethod
    def get(instance_id: UUID) -> FlowInstanceModel:
        with get_session() as session:
            instance_db = session.exec(
                select(FlowInstanceDB).where(FlowInstanceDB.id == instance_id)
            ).first()

            if not instance_db:
                raise NotFoundException("Flow instance not found")

            counts = FlowInstanceService._counts_for(session, [instance_db.id])
            return FlowInstanceService._to_model(instance_db, counts[instance_db.id])

    @staticmethod
    def list_(filter: FlowInstanceListFilter) -> Page[FlowInstanceModel]:
        with get_session() as session:
            q = select(FlowInstanceDB)
            if filter:
                if filter.flow_id is not None:
                    q = q.where(FlowInstanceDB.flow_id == filter.flow_id)
                if filter.status is not None:
                    q = q.where(FlowInstanceDB.status == filter.status.value)

            # Get total count before pagination
            count_q = select(func.count()).select_from(q.subquery())
            total = session.exec(count_q).one()

            # Apply ordering
            if filter and filter.order == FlowInstanceOrder.CREATED_AT_ASC:
                q = q.order_by(FlowInstanceDB.created_at.asc())
            else:
                q = q.order_by(FlowInstanceDB.created_at.desc())

            # Apply pagination
            if filter:
                if filter.offset is not None:
                    q = q.offset(filter.offset)
                if filter.limit is not None:
                    q = q.limit(apply_page_limit(filter.limit))
            rows = session.exec(q).all()
            counts = FlowInstanceService._counts_for(session, [row.id for row in rows])
            items = [FlowInstanceService._to_model(row, counts[row.id]) for row in rows]

            return Page(
                items=items,
                total=total,
                limit=filter.limit if filter else None,
                offset=filter.offset if filter else None,
            )

    @staticmethod
    def prune(seconds: int) -> int:
        """Delete old instances unless they still contain a failed item."""
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=seconds
        )
        with get_session() as session:
            failed_instance_ids = select(FlowItemDB.flow_instance_id).where(
                FlowItemDB.status == FlowItemStatus.FAILED.value
            )
            old_ids = list(
                session.exec(
                    select(FlowInstanceDB.id).where(
                        FlowInstanceDB.created_at < cutoff,
                        FlowInstanceDB.id.not_in(failed_instance_ids),
                    )
                ).all()
            )
            if not old_ids:
                return 0
            session.execute(
                update(FlowInstanceDB)
                .where(FlowInstanceDB.parent_instance_id.in_(old_ids))
                .values(parent_instance_id=None)
            )
            old_item_ids = select(FlowItemDB.id).where(
                FlowItemDB.flow_instance_id.in_(old_ids)
            )
            session.execute(
                update(FlowItemDB)
                .where(FlowItemDB.retried_by.in_(old_item_ids))
                .values(retried_by=None)
            )
            session.execute(
                delete(FlowItemDB).where(FlowItemDB.flow_instance_id.in_(old_ids))
            )
            session.execute(
                delete(FlowNodeExecutionDB).where(
                    FlowNodeExecutionDB.flow_instance_id.in_(old_ids)
                )
            )
            result = session.execute(
                delete(FlowInstanceDB).where(FlowInstanceDB.id.in_(old_ids))
            )
            session.commit()
            return result.rowcount  # type: ignore[return-value]

    @staticmethod
    def recover() -> int:
        """Resume instances interrupted while waiting or running."""
        now = datetime.datetime.now(datetime.timezone.utc)
        with get_session() as session:
            rows = session.exec(
                select(FlowInstanceDB).where(
                    FlowInstanceDB.status.in_(  # type: ignore[union-attr]
                        [
                            FlowInstanceStatus.RUNNING.value,
                            FlowInstanceStatus.WAITING.value,
                        ]
                    )
                )
            ).all()
            instance_ids = [row.id for row in rows]
            if instance_ids:
                session.execute(
                    update(FlowNodeExecutionDB)
                    .where(
                        FlowNodeExecutionDB.flow_instance_id.in_(instance_ids),
                        FlowNodeExecutionDB.status == "running",
                    )
                    .values(
                        status="failed",
                        error_message="interrupted",
                        finished_at=now,
                    )
                )
                session.commit()

        for instance_id in instance_ids:
            try:
                FlowInstanceRunner.resume(instance_id).do()
            except Exception:
                logger.exception(f"Failed to resume flow instance {instance_id}")
        return len(instance_ids)


class FlowItemService:
    @staticmethod
    def _validate_action(payload: FlowItemActionRequest) -> None:
        if (
            not payload.item_ids
            and payload.instance_id is None
            and payload.flow_id is None
        ):
            raise InvalidInputException("At least one item selector is required")

    @staticmethod
    def _query(filter: FlowItemListFilter | FlowItemActionRequest):
        q = select(FlowItemDB).join(
            FlowInstanceDB, FlowInstanceDB.id == FlowItemDB.flow_instance_id
        )
        if getattr(filter, "item_ids", None):
            q = q.where(FlowItemDB.id.in_(filter.item_ids))
        if filter.instance_id is not None:
            q = q.where(FlowItemDB.flow_instance_id == filter.instance_id)
        if filter.flow_id is not None:
            q = q.where(FlowInstanceDB.flow_id == filter.flow_id)
        status = getattr(filter, "status", None)
        if status is not None:
            q = q.where(FlowItemDB.status == status.value)
        return q

    @staticmethod
    def _to_model(
        item: FlowItemDB,
        instance: FlowInstanceDB,
        retried_instances: dict[UUID, UUID],
    ) -> FlowItem:
        nodes = list(instance.nodes or [])
        adapter_instance_id = (
            UUID(nodes[item.cursor]) if 0 <= item.cursor < len(nodes) else None
        )
        return FlowItem(
            id=item.id,
            instance_id=item.flow_instance_id,
            message_id=item.message_id,
            content=item.content,
            cursor=item.cursor,
            status=FlowItemStatus(item.status),
            last_error=item.last_error,
            retried_by=item.retried_by,
            retried_by_instance_id=retried_instances.get(item.retried_by),
            adapter_instance_id=adapter_instance_id,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    @staticmethod
    def list_(filter: FlowItemListFilter) -> Page[FlowItem]:
        with get_session() as session:
            base = FlowItemService._query(filter)
            total = session.exec(
                select(func.count()).select_from(base.subquery())
            ).one()
            q = base.order_by(FlowItemDB.created_at.desc(), FlowItemDB.id.desc())
            if filter.offset is not None:
                q = q.offset(filter.offset)
            if filter.limit is not None:
                q = q.limit(apply_page_limit(filter.limit))
            rows = list(session.exec(q).all())
            instances = (
                {
                    row.id: row
                    for row in session.exec(
                        select(FlowInstanceDB).where(
                            FlowInstanceDB.id.in_(
                                {item.flow_instance_id for item in rows}
                            )
                        )
                    ).all()
                }
                if rows
                else {}
            )
            retried_ids = {item.retried_by for item in rows if item.retried_by}
            retried_instances = (
                {
                    item_id: instance_id
                    for item_id, instance_id in session.exec(
                        select(FlowItemDB.id, FlowItemDB.flow_instance_id).where(
                            FlowItemDB.id.in_(retried_ids)
                        )
                    ).all()
                }
                if retried_ids
                else {}
            )
            return Page(
                items=[
                    FlowItemService._to_model(
                        item, instances[item.flow_instance_id], retried_instances
                    )
                    for item in rows
                ],
                total=total,
                limit=filter.limit,
                offset=filter.offset,
            )

    @staticmethod
    def list_by_instance(instance_id: UUID) -> list[FlowItem]:
        return FlowItemService.list_(FlowItemListFilter(instance_id=instance_id)).items

    @staticmethod
    def retry(payload: FlowItemActionRequest) -> FlowItemRetryResponse:
        FlowItemService._validate_action(payload)
        new_instance_ids: list[UUID] = []
        retried = 0
        with get_session() as session:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            selected = list(session.exec(FlowItemService._query(payload)).all())
            instance_ids = {item.flow_instance_id for item in selected}
            instances = (
                {
                    row.id: row
                    for row in session.exec(
                        select(FlowInstanceDB).where(
                            FlowInstanceDB.id.in_(instance_ids)
                        )
                    ).all()
                }
                if instance_ids
                else {}
            )
            ended = {
                FlowInstanceStatus.COMPLETED.value,
                FlowInstanceStatus.FAILED.value,
            }
            grouped: dict[UUID, list[FlowItemDB]] = {}
            for item in selected:
                instance = instances[item.flow_instance_id]
                if (
                    item.status == FlowItemStatus.FAILED.value
                    and instance.status in ended
                ):
                    grouped.setdefault(instance.id, []).append(item)

            now = datetime.datetime.now(datetime.timezone.utc)
            for parent_id, items in grouped.items():
                parent = instances[parent_id]
                retry_instance = FlowInstanceDB(
                    flow_id=parent.flow_id,
                    status=FlowInstanceStatus.WAITING.value,
                    kind=FlowInstanceKind.RETRY.value,
                    parent_instance_id=parent.id,
                    nodes=list(parent.nodes or []),
                    cursor=min(item.cursor for item in items),
                    created_at=now,
                )
                session.add(retry_instance)
                session.flush()
                copied = 0
                for item in items:
                    copied_item = FlowItemDB(
                        flow_instance_id=retry_instance.id,
                        message_id=item.message_id,
                        content=item.content,
                        cursor=item.cursor,
                        status=FlowItemStatus.PENDING.value,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(copied_item)
                    session.flush()
                    result = session.execute(
                        update(FlowItemDB)
                        .where(
                            FlowItemDB.id == item.id,
                            FlowItemDB.status == FlowItemStatus.FAILED.value,
                        )
                        .values(
                            status=FlowItemStatus.RETRIED.value,
                            retried_by=copied_item.id,
                            updated_at=now,
                        )
                    )
                    if result.rowcount:
                        copied += 1
                    else:
                        session.delete(copied_item)
                if copied:
                    retried += copied
                    new_instance_ids.append(retry_instance.id)
                else:
                    session.delete(retry_instance)
            session.commit()

        for instance_id in new_instance_ids:
            FlowInstanceRunner.resume(instance_id).do()
        return FlowItemRetryResponse(
            retried=retried,
            skipped=len(selected) - retried,
            instance_ids=new_instance_ids,
        )

    @staticmethod
    def dismiss(payload: FlowItemActionRequest) -> FlowItemDismissResponse:
        FlowItemService._validate_action(payload)
        with get_session() as session:
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            selected = list(session.exec(FlowItemService._query(payload)).all())
            instance_ids = {item.flow_instance_id for item in selected}
            ended_ids = (
                set(
                    session.exec(
                        select(FlowInstanceDB.id).where(
                            FlowInstanceDB.id.in_(instance_ids),
                            FlowInstanceDB.status.in_(
                                [
                                    FlowInstanceStatus.COMPLETED.value,
                                    FlowInstanceStatus.FAILED.value,
                                ]
                            ),
                        )
                    ).all()
                )
                if instance_ids
                else set()
            )
            eligible_ids = [
                item.id
                for item in selected
                if item.status == FlowItemStatus.FAILED.value
                and item.flow_instance_id in ended_ids
            ]
            now = datetime.datetime.now(datetime.timezone.utc)
            result = (
                session.execute(
                    update(FlowItemDB)
                    .where(
                        FlowItemDB.id.in_(eligible_ids),
                        FlowItemDB.status == FlowItemStatus.FAILED.value,
                    )
                    .values(status=FlowItemStatus.DROPPED.value, updated_at=now)
                )
                if eligible_ids
                else None
            )
            dismissed = result.rowcount if result is not None else 0
            session.commit()
            return FlowItemDismissResponse(
                dismissed=dismissed,
                skipped=len(selected) - dismissed,
            )


class FlowNodeExecutionService:
    """Service for managing FlowNodeExecution records."""

    @staticmethod
    def prune(seconds: int) -> int:
        """Delete old node executions unless their instance has a failed item."""
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=seconds
        )
        with get_session() as session:
            failed_instance_ids = select(FlowItemDB.flow_instance_id).where(
                FlowItemDB.status == FlowItemStatus.FAILED.value
            )
            old_ids = select(FlowInstanceDB.id).where(
                FlowInstanceDB.created_at < cutoff,
                FlowInstanceDB.id.not_in(failed_instance_ids),
            )
            result = session.execute(
                delete(FlowNodeExecutionDB).where(
                    FlowNodeExecutionDB.flow_instance_id.in_(old_ids)
                )
            )
            session.commit()
            return result.rowcount  # type: ignore[return-value]

    @staticmethod
    def create(
        flow_instance_id: UUID,
        adapter_instance_id: UUID,
        node_index: int,
    ) -> UUID:
        """Create a node execution record when a node starts. Returns the record ID."""
        from pushikoo.db import FlowNodeExecution as FlowNodeExecutionDB
        from pushikoo.model.flow import FlowNodeExecutionStatus

        with get_session() as session:
            record = FlowNodeExecutionDB(
                flow_instance_id=flow_instance_id,
                adapter_instance_id=adapter_instance_id,
                node_index=node_index,
                status=FlowNodeExecutionStatus.RUNNING.value,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id

    @staticmethod
    def update(
        record_id: UUID,
        status: str,
        message: str | None = None,
        error_message: str | None = None,
        items_in: int = 0,
        items_out: int = 0,
    ) -> None:
        """Update node execution record with final status and details."""
        import datetime
        from pushikoo.db import FlowNodeExecution as FlowNodeExecutionDB

        with get_session() as session:
            record = session.get(FlowNodeExecutionDB, record_id)
            if record:
                record.status = status
                record.finished_at = datetime.datetime.now(datetime.timezone.utc)
                record.message = message
                record.error_message = error_message
                record.items_in = items_in
                record.items_out = items_out
                session.add(record)
                session.commit()

    @staticmethod
    def list_by_instance(flow_instance_id: UUID) -> list:
        """Get all node executions for a flow instance, ordered by node_index."""
        from pushikoo.db import FlowNodeExecution as FlowNodeExecutionDB
        from pushikoo.model.flow import FlowNodeExecution, FlowNodeExecutionStatus

        with get_session() as session:
            records = session.exec(
                select(FlowNodeExecutionDB)
                .where(FlowNodeExecutionDB.flow_instance_id == flow_instance_id)
                .order_by(FlowNodeExecutionDB.node_index)
            ).all()

            return [
                FlowNodeExecution(
                    id=r.id,
                    flow_instance_id=r.flow_instance_id,
                    adapter_instance_id=r.adapter_instance_id,
                    node_index=r.node_index,
                    status=FlowNodeExecutionStatus(r.status)
                    if r.status in ("success", "failed", "running")
                    else FlowNodeExecutionStatus.FAILED,
                    started_at=r.started_at,
                    finished_at=r.finished_at,
                    message=r.message,
                    error_message=r.error_message,
                    items_in=r.items_in,
                    items_out=r.items_out,
                )
                for r in records
            ]


class FlowInstanceRunner:
    """Persistent, resumable pipeline runner."""

    ATTEMPT_COUNT = 3

    def __init__(
        self,
        flow_id: UUID | None = None,
        include_nodes: list[UUID] | None = None,
        *,
        instance_id: UUID | None = None,
    ):
        if (flow_id is None) == (instance_id is None):
            raise InvalidInputException("Provide exactly one of flow_id or instance_id")

        self.flow_instance_id = instance_id
        self.current_processing_adapter_inst: str | None = None
        self._thread: threading.Thread | None = None

        if instance_id is not None:
            with get_session() as session:
                instance = session.get(FlowInstanceDB, instance_id)
                if not instance:
                    raise NotFoundException(f"Flow instance not found: {instance_id}")
                self.flow_id = instance.flow_id
                self.flow_nodes = list(instance.nodes or [])
            return

        self.flow_id = flow_id
        included = (
            {str(node_id) for node_id in include_nodes}
            if include_nodes is not None
            else None
        )
        with get_session() as session:
            flow = session.get(FlowDB, flow_id)
            if not flow:
                raise NotFoundException(f"Flow not found: {flow_id}")
            all_nodes = [str(node) for node in (flow.nodes or [])]
        self.flow_nodes = (
            [node for node in all_nodes if node in included]
            if included is not None
            else all_nodes
        )
        if not self.flow_nodes:
            raise InvalidInputException(f"Flow has no selected nodes: {flow_id}")

    @classmethod
    def resume(cls, instance_id: UUID) -> "FlowInstanceRunner":
        return cls(instance_id=instance_id)

    def _issue_warning(self, warning_text: str) -> None:
        try:
            WarningService.issue(Struct(content=[StructText(text=warning_text)]))
        except Exception:
            logger.exception("Failed to issue flow warning")

    def _process_struct_images(self, struct: Struct) -> None:
        if not struct or not struct.content:
            return
        for item in struct.content:
            if isinstance(item, StructImage) and item.source:
                item.source = ImageService.create(item.source)

    def _track_getter_timeline_failure(self, getter: Getter, ex: Exception) -> None:
        key = (getter.adapter_name, getter.identifier)
        attempt_count = getter_get_timeline_continuous_failed_times.get(key, 0) + 1
        getter_get_timeline_continuous_failed_times[key] = attempt_count
        warning_counts = (
            ConfigService("system", SystemConfig).get().policy.attempt.getter_timeline
        )
        if attempt_count in warning_counts:
            self._issue_warning(
                f"Getter '{getter.adapter_name}.{getter.identifier}' failed to fetch "
                f"timeline as its consecutive failures exceeded {attempt_count} times. "
                f"Latest exception: {ex}"
            )

    def _pending_items(self, node_index: int) -> list[FlowItemDB]:
        with get_session() as session:
            return list(
                session.exec(
                    select(FlowItemDB)
                    .where(
                        FlowItemDB.flow_instance_id == self.flow_instance_id,
                        FlowItemDB.cursor == node_index,
                        FlowItemDB.status == FlowItemStatus.PENDING.value,
                    )
                    .order_by(FlowItemDB.created_at, FlowItemDB.id)
                ).all()
            )

    def _advance_items(self, node_index: int) -> int:
        now = datetime.datetime.now(datetime.timezone.utc)
        with get_session() as session:
            result = session.execute(
                update(FlowItemDB)
                .where(
                    FlowItemDB.flow_instance_id == self.flow_instance_id,
                    FlowItemDB.cursor == node_index,
                    FlowItemDB.status == FlowItemStatus.PENDING.value,
                )
                .values(cursor=node_index + 1, updated_at=now)
            )
            session.commit()
            return result.rowcount  # type: ignore[return-value]

    def _set_items_failed(self, node_index: int, error: str) -> int:
        now = datetime.datetime.now(datetime.timezone.utc)
        with get_session() as session:
            result = session.execute(
                update(FlowItemDB)
                .where(
                    FlowItemDB.flow_instance_id == self.flow_instance_id,
                    FlowItemDB.cursor == node_index,
                    FlowItemDB.status == FlowItemStatus.PENDING.value,
                )
                .values(
                    status=FlowItemStatus.FAILED.value,
                    last_error=error,
                    updated_at=now,
                )
            )
            session.commit()
            return result.rowcount  # type: ignore[return-value]

    def _unclaimed_identifiers(
        self, getter_name: str, identifiers: list[str]
    ) -> list[str]:
        identifiers = list(dict.fromkeys(identifiers))
        if not identifiers:
            return []
        with get_session() as session:
            claimed = set(
                session.exec(
                    select(MessageDB.message_identifier)
                    .join(FlowMessageDB, FlowMessageDB.message_id == MessageDB.id)
                    .where(
                        FlowMessageDB.flow_id == self.flow_id,
                        MessageDB.getter_name == getter_name,
                        MessageDB.message_identifier.in_(identifiers),
                    )
                ).all()
            )
        return [identifier for identifier in identifiers if identifier not in claimed]

    def _cached_message(self, getter_name: str, identifier: str) -> MessageDB | None:
        with get_session() as session:
            return session.exec(
                select(MessageDB).where(
                    MessageDB.getter_name == getter_name,
                    MessageDB.message_identifier == identifier,
                )
            ).first()

    def _cache_and_claim(
        self,
        getter_name: str,
        identifier: str,
        node_index: int,
        *,
        detail: Detail | None = None,
    ) -> bool:
        now = datetime.datetime.now(datetime.timezone.utc)
        with get_session() as session:
            message = session.exec(
                select(MessageDB).where(
                    MessageDB.getter_name == getter_name,
                    MessageDB.message_identifier == identifier,
                )
            ).first()
            if message is None:
                if detail is None:
                    raise RuntimeError("detail is required for an uncached message")
                content = MessageService.Template.v1(detail)
                self._process_struct_images(content)
                session.execute(
                    sqlite_insert(MessageDB)
                    .values(
                        id=uuid.uuid4(),
                        message_identifier=identifier,
                        getter_name=getter_name,
                        ts=detail.ts,
                        content=content.model_dump(),
                    )
                    .on_conflict_do_nothing(
                        index_elements=["message_identifier", "getter_name"]
                    )
                )
                message = session.exec(
                    select(MessageDB).where(
                        MessageDB.getter_name == getter_name,
                        MessageDB.message_identifier == identifier,
                    )
                ).one()

            claim_id = session.execute(
                sqlite_insert(FlowMessageDB)
                .values(
                    id=uuid.uuid4(),
                    flow_id=self.flow_id,
                    message_id=message.id,
                    created_at=now,
                )
                .on_conflict_do_nothing(index_elements=["flow_id", "message_id"])
                .returning(FlowMessageDB.id)
            ).scalar_one_or_none()
            if claim_id is None:
                session.rollback()
                return False

            session.add(
                FlowItemDB(
                    flow_instance_id=self.flow_instance_id,
                    message_id=message.id,
                    content=message.content,
                    cursor=node_index + 1,
                    status=FlowItemStatus.PENDING.value,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()
            return True

    def _cache_and_claim_merged(
        self,
        getter_name: str,
        identifiers: list[str],
        detail: Detail,
        node_index: int,
    ) -> bool:
        content = MessageService.Template.v1(detail)
        self._process_struct_images(content)
        content_data = content.model_dump()
        now = datetime.datetime.now(datetime.timezone.utc)
        claimed_message_ids: list[UUID] = []

        with get_session() as session:
            for identifier in identifiers:
                session.execute(
                    sqlite_insert(MessageDB)
                    .values(
                        id=uuid.uuid4(),
                        message_identifier=identifier,
                        getter_name=getter_name,
                        ts=detail.ts,
                        content=content_data,
                    )
                    .on_conflict_do_nothing(
                        index_elements=["message_identifier", "getter_name"]
                    )
                )
                message = session.exec(
                    select(MessageDB).where(
                        MessageDB.getter_name == getter_name,
                        MessageDB.message_identifier == identifier,
                    )
                ).one()
                claim_id = session.execute(
                    sqlite_insert(FlowMessageDB)
                    .values(
                        id=uuid.uuid4(),
                        flow_id=self.flow_id,
                        message_id=message.id,
                        created_at=now,
                    )
                    .on_conflict_do_nothing(index_elements=["flow_id", "message_id"])
                    .returning(FlowMessageDB.id)
                ).scalar_one_or_none()
                if claim_id is not None:
                    claimed_message_ids.append(message.id)

            if not claimed_message_ids:
                session.rollback()
                return False
            session.add(
                FlowItemDB(
                    flow_instance_id=self.flow_instance_id,
                    message_id=claimed_message_ids[0],
                    content=content_data,
                    cursor=node_index + 1,
                    status=FlowItemStatus.PENDING.value,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()
        return True

    def _execute_getter(self, getter: Getter, node_index: int) -> int:
        getter_name = getter.adapter_name
        getter_full_name = f"{getter.adapter_name}.{getter.identifier}"
        try:
            identifiers = self._unclaimed_identifiers(getter_name, getter.timeline())
        except Exception as ex:
            self._track_getter_timeline_failure(getter, ex)
            raise

        getter_get_timeline_continuous_failed_times[
            (getter.adapter_name, getter.identifier)
        ] = 0
        if not identifiers:
            return 0

        cached = [
            identifier
            for identifier in identifiers
            if self._cached_message(getter_name, identifier) is not None
        ]
        claimed = sum(
            int(self._cache_and_claim(getter_name, identifier, node_index))
            for identifier in cached
        )
        uncached = [
            identifier for identifier in identifiers if identifier not in cached
        ]

        if (
            uncached
            and ConfigService("system", SystemConfig).get().policy.perf_merged_details
        ):
            try:
                detail = getter.details(uncached)
                claimed += int(
                    self._cache_and_claim_merged(
                        getter_name, uncached, detail, node_index
                    )
                )
                return claimed
            except NotImplementedError:
                pass
            except Exception as ex:
                logger.exception(
                    f"Getter {getter_full_name} details() failed, falling back to detail(): {ex}"
                )

        identifiers = uncached

        def fetch_and_claim(identifier: str) -> bool:
            cached = self._cached_message(getter_name, identifier)
            if cached is not None:
                return self._cache_and_claim(getter_name, identifier, node_index)
            for attempt in range(1, self.ATTEMPT_COUNT + 1):
                try:
                    return self._cache_and_claim(
                        getter_name,
                        identifier,
                        node_index,
                        detail=getter.detail(identifier),
                    )
                except Exception as ex:
                    if attempt == self.ATTEMPT_COUNT:
                        self._issue_warning(
                            f"Getter '{getter_full_name}' failed to fetch details for "
                            f"identifier {identifier} after {self.ATTEMPT_COUNT} attempts."
                        )
                        logger.exception(f"Failed to get detail for {identifier}: {ex}")
                    else:
                        logger.warning(
                            f"Getter detail() attempt {attempt} failed: {ex}"
                        )
            return False

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_and_claim, value) for value in identifiers]
            for future in as_completed(futures):
                claimed += int(future.result())
        return claimed

    def _execute_processer(
        self, processer: Processer, node_index: int
    ) -> tuple[int, int, int]:
        items = self._pending_items(node_index)
        succeeded = 0
        failed = 0
        for item in items:
            last_error = ""
            for attempt in range(1, self.ATTEMPT_COUNT + 1):
                try:
                    processed = processer.process(
                        Struct.model_validate(item.content).model_copy(deep=True)
                    )
                    now = datetime.datetime.now(datetime.timezone.utc)
                    with get_session() as session:
                        current = session.get(FlowItemDB, item.id)
                        if current and current.status == FlowItemStatus.PENDING.value:
                            current.content = processed.model_dump()
                            current.cursor = node_index + 1
                            current.last_error = None
                            current.updated_at = now
                            session.add(current)
                            session.commit()
                    succeeded += 1
                    break
                except TerminateFlowException:
                    with get_session() as session:
                        current = session.get(FlowItemDB, item.id)
                        if current:
                            current.status = FlowItemStatus.DROPPED.value
                            current.updated_at = datetime.datetime.now(
                                datetime.timezone.utc
                            )
                            session.add(current)
                            session.commit()
                    break
                except Exception as ex:
                    last_error = str(ex)
                    if attempt < self.ATTEMPT_COUNT:
                        logger.warning(f"Processer attempt {attempt} failed: {ex}")
            else:
                with get_session() as session:
                    current = session.get(FlowItemDB, item.id)
                    if current:
                        current.status = FlowItemStatus.FAILED.value
                        current.last_error = last_error
                        current.updated_at = datetime.datetime.now(
                            datetime.timezone.utc
                        )
                        session.add(current)
                        session.commit()
                failed += 1
                self._issue_warning(
                    f"Processer '{processer.adapter_name}.{processer.identifier}' failed "
                    f"after {self.ATTEMPT_COUNT} attempts. Error: {last_error}"
                )
        return len(items), succeeded, failed

    def _execute_pusher(self, pusher: Pusher, node_index: int) -> tuple[int, int, int]:
        items = self._pending_items(node_index)
        succeeded = 0
        failed = 0
        for item in items:
            last_error = ""
            for attempt in range(1, self.ATTEMPT_COUNT + 1):
                try:
                    pusher.push(
                        Struct.model_validate(item.content).model_copy(deep=True)
                    )
                    with get_session() as session:
                        current = session.get(FlowItemDB, item.id)
                        if current and current.status == FlowItemStatus.PENDING.value:
                            current.status = FlowItemStatus.DONE.value
                            current.last_error = None
                            current.updated_at = datetime.datetime.now(
                                datetime.timezone.utc
                            )
                            session.add(current)
                            session.commit()
                    succeeded += 1
                    break
                except Exception as ex:
                    last_error = str(ex)
                    if attempt < self.ATTEMPT_COUNT:
                        logger.warning(f"Pusher attempt {attempt} failed: {ex}")
            else:
                with get_session() as session:
                    current = session.get(FlowItemDB, item.id)
                    if current:
                        current.status = FlowItemStatus.FAILED.value
                        current.last_error = last_error
                        current.updated_at = datetime.datetime.now(
                            datetime.timezone.utc
                        )
                        session.add(current)
                        session.commit()
                failed += 1
                self._issue_warning(
                    f"Pusher '{pusher.adapter_name}.{pusher.identifier}' failed after "
                    f"{self.ATTEMPT_COUNT} attempts. Error: {last_error}"
                )
        return len(items), succeeded, failed

    def _advance_instance(self, cursor: int) -> None:
        with get_session() as session:
            instance = session.get(FlowInstanceDB, self.flow_instance_id)
            if not instance:
                raise NotFoundException(
                    f"Flow instance not found: {self.flow_instance_id}"
                )
            instance.cursor = cursor
            session.add(instance)
            session.commit()

    def _finish(self) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        with get_session() as session:
            session.execute(
                update(FlowItemDB)
                .where(
                    FlowItemDB.flow_instance_id == self.flow_instance_id,
                    FlowItemDB.status == FlowItemStatus.PENDING.value,
                )
                .values(status=FlowItemStatus.DONE.value, updated_at=now)
            )
            failed = session.exec(
                select(FlowItemDB.id).where(
                    FlowItemDB.flow_instance_id == self.flow_instance_id,
                    FlowItemDB.status == FlowItemStatus.FAILED.value,
                )
            ).first()
            instance = session.get(FlowInstanceDB, self.flow_instance_id)
            if instance:
                instance.cursor = len(instance.nodes or [])
                instance.status = (
                    FlowInstanceStatus.FAILED.value
                    if failed is not None
                    else FlowInstanceStatus.COMPLETED.value
                )
                session.add(instance)
            session.commit()

    def _refresh_worker(self) -> None:
        try:
            if self.flow_instance_id is None:
                instance = FlowInstanceService.create(
                    self.flow_id, nodes=self.flow_nodes
                )
                self.flow_instance_id = instance.id

            FlowInstanceService.update_status(
                self.flow_instance_id, FlowInstanceStatus.RUNNING
            )
            instance = FlowInstanceService.get(self.flow_instance_id)

            for node_index in range(instance.cursor, len(self.flow_nodes)):
                adapter_instance_id = UUID(self.flow_nodes[node_index])
                node_exec_id = FlowNodeExecutionService.create(
                    self.flow_instance_id, adapter_instance_id, node_index
                )
                items_in = len(self._pending_items(node_index))
                items_out = 0
                node_message = None
                try:
                    node_obj = AdapterInstanceService.get_object_by_id(
                        adapter_instance_id
                    )
                except Exception as ex:
                    items_out = self._set_items_failed(node_index, str(ex))
                    FlowNodeExecutionService.update(
                        node_exec_id,
                        "failed",
                        error_message=str(ex),
                        items_in=items_in,
                        items_out=items_out,
                    )
                    self._issue_warning(
                        f"Flow {self.flow_id} could not load node "
                        f"{adapter_instance_id}: {ex}"
                    )
                    self._advance_instance(node_index + 1)
                    continue

                self.current_processing_adapter_inst = (
                    f"{node_obj.adapter_name}.{node_obj.identifier}"
                )
                node_failed = False
                error_message = None
                if isinstance(node_obj, Getter):
                    existing = self._advance_items(node_index)
                    created = 0
                    if instance.kind == FlowInstanceKind.NORMAL:
                        try:
                            created = self._execute_getter(node_obj, node_index)
                        except Exception as ex:
                            node_failed = True
                            error_message = str(ex)
                            logger.warning(
                                f"Getter {adapter_instance_id} failed; continuing: {ex}"
                            )
                    items_out = existing + created
                    node_message = (
                        f"Released {existing} retry items"
                        if instance.kind == FlowInstanceKind.RETRY
                        else f"Retrieved {created} items"
                    )
                elif isinstance(node_obj, Processer):
                    items_in, items_out, failed = self._execute_processer(
                        node_obj, node_index
                    )
                    if failed:
                        node_failed = True
                        error_message = f"{failed} item(s) failed"
                elif isinstance(node_obj, Pusher):
                    items_in, items_out, failed = self._execute_pusher(
                        node_obj, node_index
                    )
                    if failed:
                        node_failed = True
                        error_message = f"{failed} item(s) failed"
                else:
                    items_out = self._advance_items(node_index)
                    logger.warning(
                        f"Unknown node type for {adapter_instance_id}: {type(node_obj)}"
                    )

                FlowNodeExecutionService.update(
                    node_exec_id,
                    "failed" if node_failed else "success",
                    message=node_message,
                    error_message=error_message,
                    items_in=items_in,
                    items_out=items_out,
                )
                self._advance_instance(node_index + 1)

            self._finish()
            logger.debug(f"Completed refresh for flow: {self.flow_id}")
        except Exception as ex:
            logger.exception(f"Unexpected failure in flow {self.flow_id}")
            if self.flow_instance_id is not None:
                try:
                    self._abort(str(ex))
                except Exception:
                    logger.exception("Failed to mark flow instance failed")

    def _abort(self, error: str) -> None:
        """Fail all pending items so they are not left stranded, then fail the instance."""
        now = datetime.datetime.now(datetime.timezone.utc)
        with get_session() as session:
            session.execute(
                update(FlowItemDB)
                .where(
                    FlowItemDB.flow_instance_id == self.flow_instance_id,
                    FlowItemDB.status == FlowItemStatus.PENDING.value,
                )
                .values(
                    status=FlowItemStatus.FAILED.value,
                    last_error=f"aborted: {error}",
                    updated_at=now,
                )
            )
            instance = session.get(FlowInstanceDB, self.flow_instance_id)
            if instance:
                instance.status = FlowInstanceStatus.FAILED.value
                session.add(instance)
            session.commit()

    def do(self) -> None:
        self._thread = threading.Thread(target=self._refresh_worker, daemon=True)
        self._thread.start()


class CronService:
    _scheduler = BackgroundScheduler(
        executors={
            "default": {"type": "threadpool", "max_workers": CRON_SCHEDULER_MAX_WORKERS}
        }
    )
    _lock = threading.Lock()

    @staticmethod
    def _parse_cron_to_trigger(expr: str) -> CronTrigger:
        expr = expr.strip()
        parts = expr.split()

        try:
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
                return CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                )

            elif len(parts) == 6:
                second, minute, hour, day, month, day_of_week = parts
                return CronTrigger(
                    second=second,
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                )

            elif len(parts) == 7:
                second, minute, hour, day, month, day_of_week, year = parts
                return CronTrigger(
                    second=second,
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    year=year,
                )

            else:
                raise InvalidInputException(f"Invalid cron expression: '{expr}'")
        except ValueError as e:
            raise InvalidInputException(f"Invalid cron expression: '{expr}' - {e}")

    @staticmethod
    def _job_id(flow_id: UUID, cron_expr: str) -> str:
        return str(flow_id) + cron_expr

    @staticmethod
    def _load_all_from_db() -> List[Tuple[UUID, UUID, str, bool]]:
        with get_session() as session:
            rows = session.exec(select(FlowCronDB)).all()
            result: List[Tuple[UUID, UUID, str, bool]] = []
            for c in rows:
                result.append((c.id, c.flow_id, c.cron, c.enabled))
            return result

    @classmethod
    def _reload(cls):
        with cls._lock:
            logger.info("CronService reloading scheduler...")

            db_crons = cls._load_all_from_db()
            # Only schedule enabled crons
            enabled_crons = [
                (cron_id, flow_id, cron_expr)
                for cron_id, flow_id, cron_expr, enabled in db_crons
                if enabled
            ]
            db_ids = {
                cls._job_id(flow_id, cron_expr)
                for cron_id, flow_id, cron_expr in enabled_crons
            }

            job_ids = {job.id for job in cls._scheduler.get_jobs()}

            to_add = db_ids - job_ids
            to_remove = job_ids - db_ids

            cron_map = {
                cls._job_id(flow_id, cron_expr): (cron_id, flow_id, cron_expr)
                for cron_id, flow_id, cron_expr in enabled_crons
            }

            for job_id in to_add:
                cron_id, flow_id, cron = cron_map[job_id]
                cls._scheduler.add_job(
                    func=lambda flow_id=flow_id: FlowInstanceRunner(flow_id).do(),
                    trigger=CronService._parse_cron_to_trigger(cron),
                    id=job_id,
                    replace_existing=True,
                )
                logger.info(f"Added {job_id}")

            for job_id in to_remove:
                try:
                    cls._scheduler.remove_job(job_id)
                    logger.info(f"Removed {job_id}")
                except Exception:
                    logger.warning(f"Job {job_id} does not exist")

    @classmethod
    def init(cls):
        cls._reload()
        if not cls._scheduler.running:
            cls._scheduler.start()

    @classmethod
    def create(cls, cron_create: CronCreate) -> Cron:
        cls._parse_cron_to_trigger(cron_create.cron)

        with get_session() as session:
            flow_db = session.exec(
                select(FlowDB).where(FlowDB.id == cron_create.flow_id)
            ).first()
            if not flow_db:
                raise NotFoundException("Flow not found")

            flow_id = flow_db.id

            # Check for duplicate (flow_id, cron)
            existing = session.exec(
                select(FlowCronDB).where(
                    FlowCronDB.flow_id == flow_id,
                    FlowCronDB.cron == cron_create.cron,
                )
            ).first()
            if existing:
                raise ConflictException(
                    f"Cron with schedule '{cron_create.cron}' already exists for this flow"
                )

            cron_db = FlowCronDB(
                flow_id=flow_id,
                cron=cron_create.cron,
                enabled=cron_create.enabled,
            )
            session.add(cron_db)
            session.commit()
            session.refresh(cron_db)

        cls._reload()
        logger.info(
            f"Created cron: {cron_db.id} for flow {flow_id} with schedule '{cron_create.cron}' enabled={cron_db.enabled}"
        )

        return Cron(
            id=cron_db.id,
            flow_id=flow_id,
            cron=cron_db.cron,
            enabled=cron_db.enabled,
        )

    @classmethod
    def update(cls, cron_id: UUID, cron_update: CronUpdate) -> Cron:
        with get_session() as session:
            cron_record = session.exec(
                select(FlowCronDB).where(FlowCronDB.id == cron_id)
            ).first()

            if not cron_record:
                raise NotFoundException("Cron not found")

            if cron_update.cron is not None:
                cls._parse_cron_to_trigger(cron_update.cron)
                # Check for duplicate (flow_id, cron) excluding current record
                existing = session.exec(
                    select(FlowCronDB).where(
                        FlowCronDB.flow_id == cron_record.flow_id,
                        FlowCronDB.cron == cron_update.cron,
                        FlowCronDB.id != cron_id,
                    )
                ).first()
                if existing:
                    raise ConflictException(
                        f"Cron with schedule '{cron_update.cron}' already exists for this flow"
                    )
                cron_record.cron = cron_update.cron
            if cron_update.enabled is not None:
                cron_record.enabled = cron_update.enabled

            session.add(cron_record)
            session.commit()
            session.refresh(cron_record)

        cls._reload()
        logger.info(
            f"Updated cron: {cron_id} cron='{cron_record.cron}' enabled={cron_record.enabled}"
        )

        return Cron(
            id=cron_record.id,
            flow_id=cron_record.flow_id,
            cron=cron_record.cron,
            enabled=cron_record.enabled,
        )

    @staticmethod
    def list(filter: CronListFilter) -> Page[Cron]:
        with get_session() as session:
            q = select(FlowCronDB)
            if filter:
                if filter.flow_id is not None:
                    q = q.where(FlowCronDB.flow_id == filter.flow_id)
                if filter.cron is not None:
                    q = q.where(FlowCronDB.cron == filter.cron)
                if filter.enabled is not None:
                    q = q.where(FlowCronDB.enabled == filter.enabled)

            # Get total count before pagination
            count_q = select(func.count()).select_from(q.subquery())
            total = session.exec(count_q).one()

            q = q.order_by(FlowCronDB.id)
            if filter and filter.offset is not None:
                q = q.offset(filter.offset)
            if filter and filter.limit is not None:
                q = q.limit(apply_page_limit(filter.limit))
            rows = session.exec(q).all()
            items: list[Cron] = []
            for c in rows:
                items.append(
                    Cron(
                        id=c.id,
                        flow_id=c.flow_id,
                        cron=c.cron,
                        enabled=c.enabled,
                    )
                )

            return Page(
                items=items,
                total=total,
                limit=filter.limit if filter else None,
                offset=filter.offset if filter else None,
            )

    @classmethod
    def delete(cls, cron_id: UUID) -> None:
        with get_session() as session:
            cron_record = session.exec(
                select(FlowCronDB).where(FlowCronDB.id == cron_id)
            ).first()

            if not cron_record:
                raise NotFoundException("Cron not found")

            session.delete(cron_record)
            session.commit()

        cls._reload()
        logger.info(
            f"Deleted cron: {cron_id} for flow {cron_record.flow_id} with schedule '{cron_record.cron}'"
        )

    @classmethod
    def close(cls):
        with cls._lock:
            if cls._scheduler.running:
                cls._scheduler.shutdown(wait=False)
                logger.info("CronService scheduler shutdown complete")
