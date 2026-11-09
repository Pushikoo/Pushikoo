import datetime
import threading
from uuid import UUID

from loguru import logger
from pushikoo_interface import Pusher, Struct
from sqlalchemy import delete, update
from sqlmodel import func, select

from pushikoo.db import AdapterInstance as AdapterInstanceDB
from pushikoo.db import Warning as WarningDB
from pushikoo.db import WarningDelivery as WarningDeliveryDB
from pushikoo.db import WarningRecipient as WarningRecipientDB
from pushikoo.db import get_session
from pushikoo.model.adapter import AdapterInstance
from pushikoo.model.config import SystemConfig
from pushikoo.model.pagination import Page, apply_page_limit
from pushikoo.model.warning import (
    Warning,
    WarningDelivery,
    WarningDeliveryStatus,
)
from pushikoo.service.adapter import AdapterInstanceService, AdapterService
from pushikoo.service.base import (
    ConflictException,
    InvalidInputException,
    NotFoundException,
)
from pushikoo.service.config import ConfigService


class WarningService:
    LEASE_MINUTES = 5
    LOCK_TIMEOUT_SECONDS = 60
    RETRY_MINUTES = (1, 5, 15, 30, 60)
    _cleanup_lock = threading.Lock()
    _last_cleanup_date: datetime.date | None = None

    @staticmethod
    def _now() -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def add_recipient(adapter_instance_id: UUID) -> AdapterInstance:
        with get_session() as session:
            adapter_instance = session.get(AdapterInstanceDB, adapter_instance_id)
            if not adapter_instance:
                raise NotFoundException(
                    f"Adapter instance {adapter_instance_id} not found"
                )

            adapter_class = AdapterService.get_clsobj_by_name(
                adapter_instance.adapter_name
            )
            if not issubclass(adapter_class, Pusher):
                raise InvalidInputException(
                    f"Adapter {adapter_instance.adapter_name} is not a Pusher. "
                    "Only Pusher adapters can be warning recipients."
                )

            existing = session.exec(
                select(WarningRecipientDB).where(
                    WarningRecipientDB.adapter_instance_id == adapter_instance_id
                )
            ).first()
            if existing:
                raise ConflictException(
                    f"Adapter instance {adapter_instance_id} already exists as warning recipient"
                )

            session.add(WarningRecipientDB(adapter_instance_id=adapter_instance_id))
            session.commit()
            result = AdapterInstance(
                id=adapter_instance.id,
                adapter_name=adapter_instance.adapter_name,
                identifier=adapter_instance.identifier,
            )
        logger.info(
            f"Added warning recipient for adapter instance {adapter_instance_id}"
        )
        return result

    @staticmethod
    def _fail_pending_for_recipient(
        session, adapter_instance_id: UUID, reason: str
    ) -> None:
        now = WarningService._now()
        session.execute(
            update(WarningDeliveryDB)
            .where(
                WarningDeliveryDB.adapter_instance_id == adapter_instance_id,
                WarningDeliveryDB.status == WarningDeliveryStatus.PENDING.value,
            )
            .values(
                status=WarningDeliveryStatus.FAILED.value,
                last_error=reason,
                updated_at=now,
            )
        )

    @staticmethod
    def remove_recipient(adapter_instance_id: UUID) -> None:
        with get_session() as session:
            adapter_instance = session.get(AdapterInstanceDB, adapter_instance_id)
            if not adapter_instance:
                raise NotFoundException(
                    f"Adapter instance {adapter_instance_id} not found"
                )
            recipient = session.exec(
                select(WarningRecipientDB).where(
                    WarningRecipientDB.adapter_instance_id == adapter_instance_id
                )
            ).first()
            if not recipient:
                raise NotFoundException(
                    f"Warning recipient for adapter instance {adapter_instance_id} not found"
                )
            WarningService._fail_pending_for_recipient(
                session,
                adapter_instance_id,
                "Warning recipient was removed",
            )
            session.delete(recipient)
            session.commit()
        logger.info(
            f"Removed warning recipient for adapter instance {adapter_instance_id}"
        )

    @staticmethod
    def list_recipients(
        limit: int | None = None,
        offset: int | None = None,
    ) -> Page[AdapterInstance]:
        with get_session() as session:
            q = (
                select(WarningRecipientDB)
                .join(AdapterInstanceDB)
                .order_by(WarningRecipientDB.created_at.desc())
            )
            total = session.exec(select(func.count()).select_from(q.subquery())).one()
            if offset is not None:
                q = q.offset(offset)
            if limit is not None:
                q = q.limit(apply_page_limit(limit))
            recipients = session.exec(q).all()
            items = [
                AdapterInstance(
                    id=r.adapter_instance.id,
                    adapter_name=r.adapter_instance.adapter_name,
                    identifier=r.adapter_instance.identifier,
                )
                for r in recipients
            ]
        return Page(items=items, total=total, limit=limit, offset=offset)

    @staticmethod
    def issue(message: Struct) -> None:
        """Persist and immediately fan out a warning. Never raise to the caller."""
        delivery_ids: list[UUID] = []
        try:
            now = WarningService._now()
            with get_session() as session:
                warning = WarningDB(content=message.model_dump(), created_at=now)
                session.add(warning)
                session.flush()
                recipients = session.exec(select(WarningRecipientDB)).all()
                for recipient in recipients:
                    delivery = WarningDeliveryDB(
                        warning_id=warning.id,
                        adapter_instance_id=recipient.adapter_instance_id,
                        status=WarningDeliveryStatus.PENDING.value,
                        attempts=0,
                        next_attempt_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(delivery)
                    session.flush()
                    delivery_ids.append(delivery.id)
                session.commit()
            if not delivery_ids:
                logger.warning("Warning persisted with no configured recipients")
            for delivery_id in delivery_ids:
                WarningService.deliver(delivery_id)
        except Exception:
            logger.exception("Failed to persist or dispatch warning")

    @staticmethod
    def _claim(delivery_id: UUID) -> bool:
        now = WarningService._now()
        lease_until = now + datetime.timedelta(minutes=WarningService.LEASE_MINUTES)
        with get_session() as session:
            result = session.execute(
                update(WarningDeliveryDB)
                .where(
                    WarningDeliveryDB.id == delivery_id,
                    WarningDeliveryDB.status == WarningDeliveryStatus.PENDING.value,
                    WarningDeliveryDB.next_attempt_at <= now,
                )
                .values(next_attempt_at=lease_until, updated_at=now)
            )
            session.commit()
            return bool(result.rowcount)

    @staticmethod
    def deliver(delivery_id: UUID) -> bool:
        if not WarningService._claim(delivery_id):
            return False

        with get_session() as session:
            delivery = session.get(WarningDeliveryDB, delivery_id)
            warning = session.get(WarningDB, delivery.warning_id) if delivery else None
            if not delivery or not warning:
                return False
            adapter_instance_id = delivery.adapter_instance_id
            warning_content = Struct.model_validate(warning.content)
            created_at = delivery.created_at
            attempts = delivery.attempts

        try:
            # A pusher stuck in a flow must not block warnings (or the retry job)
            # indefinitely; a busy recipient is retried later like any failure.
            with AdapterInstanceService.call_lock(
                adapter_instance_id, timeout=WarningService.LOCK_TIMEOUT_SECONDS
            ) as instance:
                if not isinstance(instance, Pusher):
                    raise InvalidInputException(
                        f"Adapter instance {adapter_instance_id} is not a Pusher"
                    )
                instance.push(warning_content.model_copy(deep=True))
        except Exception as exc:
            now = WarningService._now()
            new_attempts = attempts + 1
            try:
                max_hours = (
                    ConfigService("system", SystemConfig)
                    .get()
                    .policy.warning_retry_max_hours
                )
            except Exception:
                logger.exception("Failed to read warning retry policy; using 24 hours")
                max_hours = 24
            expired = now - created_at >= datetime.timedelta(hours=max_hours)
            delay = WarningService.RETRY_MINUTES[
                min(new_attempts - 1, len(WarningService.RETRY_MINUTES) - 1)
            ]
            with get_session() as session:
                current = session.get(WarningDeliveryDB, delivery_id)
                if current and current.status == WarningDeliveryStatus.PENDING.value:
                    current.attempts = new_attempts
                    current.last_error = str(exc)
                    current.updated_at = now
                    if expired:
                        current.status = WarningDeliveryStatus.FAILED.value
                    else:
                        current.next_attempt_at = now + datetime.timedelta(
                            minutes=delay
                        )
                    session.add(current)
                    session.commit()
            logger.error(
                f"Failed warning delivery {delivery_id} to {adapter_instance_id}: {exc}"
            )
            return False

        now = WarningService._now()
        with get_session() as session:
            current = session.get(WarningDeliveryDB, delivery_id)
            if current and current.status == WarningDeliveryStatus.PENDING.value:
                current.status = WarningDeliveryStatus.SENT.value
                current.sent_at = now
                current.last_error = None
                current.updated_at = now
                session.add(current)
                session.commit()
        logger.debug(f"Warning delivery {delivery_id} sent to {adapter_instance_id}")
        return True

    @staticmethod
    def retry_due(limit: int = 100) -> int:
        now = WarningService._now()
        with get_session() as session:
            delivery_ids = list(
                session.exec(
                    select(WarningDeliveryDB.id)
                    .where(
                        WarningDeliveryDB.status == WarningDeliveryStatus.PENDING.value,
                        WarningDeliveryDB.next_attempt_at <= now,
                    )
                    .order_by(WarningDeliveryDB.next_attempt_at)
                    .limit(limit)
                ).all()
            )
        delivered = sum(
            int(WarningService.deliver(delivery_id)) for delivery_id in delivery_ids
        )
        WarningService.cleanup_once_daily()
        return delivered

    @staticmethod
    def cleanup_once_daily() -> int:
        today = WarningService._now().date()
        with WarningService._cleanup_lock:
            if WarningService._last_cleanup_date == today:
                return 0
            WarningService._last_cleanup_date = today

        cutoff = WarningService._now() - datetime.timedelta(days=30)
        with get_session() as session:
            incomplete_warning_ids = select(WarningDeliveryDB.warning_id).where(
                WarningDeliveryDB.status == WarningDeliveryStatus.PENDING.value
            )
            warning_ids = list(
                session.exec(
                    select(WarningDB.id).where(
                        WarningDB.created_at < cutoff,
                        WarningDB.id.not_in(incomplete_warning_ids),
                    )
                ).all()
            )
            if not warning_ids:
                return 0
            session.execute(
                delete(WarningDeliveryDB).where(
                    WarningDeliveryDB.warning_id.in_(warning_ids)
                )
            )
            result = session.execute(
                delete(WarningDB).where(WarningDB.id.in_(warning_ids))
            )
            session.commit()
            return result.rowcount  # type: ignore[return-value]

    @staticmethod
    def list_(limit: int | None = None, offset: int | None = None) -> Page[Warning]:
        with get_session() as session:
            base = select(WarningDB)
            total = session.exec(
                select(func.count()).select_from(base.subquery())
            ).one()
            q = base.order_by(WarningDB.created_at.desc(), WarningDB.id.desc())
            if offset is not None:
                q = q.offset(offset)
            if limit is not None:
                q = q.limit(apply_page_limit(limit))
            warnings = list(session.exec(q).all())
            warning_ids = [warning.id for warning in warnings]
            rows = (
                list(
                    session.exec(
                        select(WarningDeliveryDB, AdapterInstanceDB)
                        .join(
                            AdapterInstanceDB,
                            AdapterInstanceDB.id
                            == WarningDeliveryDB.adapter_instance_id,
                        )
                        .where(WarningDeliveryDB.warning_id.in_(warning_ids))
                        .order_by(WarningDeliveryDB.created_at)
                    ).all()
                )
                if warning_ids
                else []
            )
            deliveries: dict[UUID, list[WarningDelivery]] = {}
            for delivery, instance in rows:
                deliveries.setdefault(delivery.warning_id, []).append(
                    WarningDelivery(
                        id=delivery.id,
                        adapter_instance_id=delivery.adapter_instance_id,
                        recipient_name=f"{instance.adapter_name}.{instance.identifier}",
                        status=WarningDeliveryStatus(delivery.status),
                        attempts=delivery.attempts,
                        last_error=delivery.last_error,
                        sent_at=delivery.sent_at,
                    )
                )
            items = [
                Warning(
                    id=warning.id,
                    content=Struct.model_validate(warning.content),
                    created_at=warning.created_at,
                    deliveries=deliveries.get(warning.id, []),
                )
                for warning in warnings
            ]
        return Page(items=items, total=total, limit=limit, offset=offset)

    @staticmethod
    def retry_delivery(delivery_id: UUID) -> None:
        now = WarningService._now()
        with get_session() as session:
            delivery = session.get(WarningDeliveryDB, delivery_id)
            if not delivery:
                raise NotFoundException(f"Warning delivery {delivery_id} not found")
            if delivery.status == WarningDeliveryStatus.SENT.value:
                raise InvalidInputException("Sent warning deliveries cannot be retried")
            delivery.status = WarningDeliveryStatus.PENDING.value
            delivery.next_attempt_at = now
            delivery.updated_at = now
            session.add(delivery)
            session.commit()
        WarningService.deliver(delivery_id)
