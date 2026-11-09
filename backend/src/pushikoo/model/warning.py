from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pushikoo_interface import Struct
from pydantic import BaseModel


class WarningRecipientCreate(BaseModel):
    adapter_instance_id: UUID


class WarningDeliveryStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class WarningDelivery(BaseModel):
    id: UUID
    adapter_instance_id: UUID
    recipient_name: str
    status: WarningDeliveryStatus
    attempts: int
    last_error: str | None
    sent_at: datetime | None


class Warning(BaseModel):
    id: UUID
    content: Struct
    created_at: datetime
    deliveries: list[WarningDelivery]
