from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class FlowCreate(BaseModel):
    name: str = ""
    nodes: list[UUID]


class FlowUpdate(BaseModel):
    name: str | None = None
    nodes: list[UUID] | None = None


class FlowListFilter(BaseModel):
    getter_instance_id: UUID | None = None  # filter by first node (= getter)
    limit: int | None = None
    offset: int | None = None


class Flow(BaseModel):
    id: UUID
    name: str
    nodes: list[UUID]


class FlowInstanceStatus(StrEnum):
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FlowInstanceKind(StrEnum):
    NORMAL = "normal"
    RETRY = "retry"


class FlowInstanceOrder(StrEnum):
    CREATED_AT_DESC = "created_at_desc"
    CREATED_AT_ASC = "created_at_asc"


class FlowInstanceListFilter(BaseModel):
    flow_id: UUID | None = None
    status: FlowInstanceStatus | None = None
    limit: int | None = None
    offset: int | None = None
    order: FlowInstanceOrder = FlowInstanceOrder.CREATED_AT_DESC


class FlowItemCounts(BaseModel):
    pending: int = 0
    done: int = 0
    dropped: int = 0
    failed: int = 0
    retried: int = 0


class FlowInstance(BaseModel):
    id: UUID
    flow_id: UUID
    status: FlowInstanceStatus
    kind: FlowInstanceKind
    parent_instance_id: UUID | None
    nodes: list[UUID]
    cursor: int
    created_at: datetime
    item_counts: FlowItemCounts


class FlowItemStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    DROPPED = "dropped"
    FAILED = "failed"
    RETRIED = "retried"


class FlowItem(BaseModel):
    id: UUID
    instance_id: UUID
    message_id: UUID | None
    content: dict
    cursor: int
    status: FlowItemStatus
    last_error: str | None
    retried_by: UUID | None
    retried_by_instance_id: UUID | None = None
    adapter_instance_id: UUID | None
    created_at: datetime
    updated_at: datetime


class FlowItemListFilter(BaseModel):
    flow_id: UUID | None = None
    instance_id: UUID | None = None
    status: FlowItemStatus | None = None
    limit: int | None = None
    offset: int | None = None


class FlowItemActionRequest(BaseModel):
    item_ids: list[UUID] | None = None
    instance_id: UUID | None = None
    flow_id: UUID | None = None


class FlowItemRetryResponse(BaseModel):
    retried: int
    skipped: int
    instance_ids: list[UUID]


class FlowItemDismissResponse(BaseModel):
    dismissed: int
    skipped: int


class FlowExecuteRequest(BaseModel):
    """Request body for executing a flow with optional node inclusions."""

    include_nodes: list[UUID] | None = None  # List of node IDs to run (None = run all)


class FlowNodeExecutionStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"


class FlowNodeExecution(BaseModel):
    """Execution details for a single node in a flow instance."""

    id: UUID
    flow_instance_id: UUID
    adapter_instance_id: UUID
    node_index: int
    status: FlowNodeExecutionStatus
    started_at: datetime
    finished_at: datetime | None
    message: str | None  # Getter: message IDs; others: empty
    error_message: str | None
    items_in: int
    items_out: int


class FlowInstanceDetail(FlowInstance):
    """FlowInstance with execution details for each node."""

    node_executions: list[FlowNodeExecution]
