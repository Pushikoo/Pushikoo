from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from pushikoo.model.flow import (
    Flow,
    FlowCreate,
    FlowExecuteRequest,
    FlowInstance,
    FlowInstanceDetail,
    FlowInstanceKind,
    FlowInstanceListFilter,
    FlowInstanceOrder,
    FlowInstanceStatus,
    FlowItem,
    FlowItemActionRequest,
    FlowItemDismissResponse,
    FlowItemListFilter,
    FlowItemRetryResponse,
    FlowItemStatus,
    FlowListFilter,
    FlowUpdate,
    ManualSendRequest,
    ManualSendResponse,
)
from pushikoo.model.pagination import Page
from pushikoo.service.refresh import (
    FlowInstanceRunner,
    FlowInstanceService,
    FlowItemService,
    FlowNodeExecutionService,
    FlowService,
    ManualSendService,
)
from pushikoo.service.base import (
    ConflictException,
    InvalidInputException,
    NotFoundException,
)


router = APIRouter(prefix="/flows", tags=["flows"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_flow(payload: FlowCreate) -> Flow:
    return FlowService.create(payload)


@router.get("")
def list_flows(
    getter_instance_id: UUID | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> Page[Flow]:
    filter_obj = FlowListFilter(
        getter_instance_id=getter_instance_id,
        limit=limit,
        offset=offset,
    )
    return FlowService.list_(filter_obj)


@router.get("/instances")
def list_flow_instances(
    flow_id: UUID | None = None,
    flow_id_is_null: bool = False,
    status: FlowInstanceStatus | None = None,
    kind: FlowInstanceKind | None = None,
    limit: int | None = None,
    offset: int | None = None,
    order: FlowInstanceOrder = FlowInstanceOrder.CREATED_AT_DESC,
) -> Page[FlowInstance]:
    filter_obj = FlowInstanceListFilter(
        flow_id=flow_id,
        flow_id_is_null=flow_id_is_null,
        status=status,
        kind=kind,
        limit=limit,
        offset=offset,
        order=order,
    )
    return FlowInstanceService.list_(filter_obj)


@router.get("/items")
def list_flow_items(
    flow_id: UUID | None = None,
    instance_id: UUID | None = None,
    status: FlowItemStatus | None = None,
    manual_only: bool = False,
    limit: int | None = None,
    offset: int | None = None,
) -> Page[FlowItem]:
    return FlowItemService.list_(
        FlowItemListFilter(
            flow_id=flow_id,
            instance_id=instance_id,
            status=status,
            manual_only=manual_only,
            limit=limit,
            offset=offset,
        )
    )


@router.post("/manual-send", status_code=status.HTTP_201_CREATED)
def manual_send(payload: ManualSendRequest) -> ManualSendResponse:
    try:
        return ManualSendService.send(payload)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidInputException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/items/retry")
def retry_flow_items(payload: FlowItemActionRequest) -> FlowItemRetryResponse:
    try:
        return FlowItemService.retry(payload)
    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.post("/items/dismiss")
def dismiss_flow_items(payload: FlowItemActionRequest) -> FlowItemDismissResponse:
    try:
        return FlowItemService.dismiss(payload)
    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/instances/{instance_id}/items")
def list_flow_instance_items(instance_id: UUID) -> list[FlowItem]:
    try:
        FlowInstanceService.get(instance_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return FlowItemService.list_by_instance(instance_id)


@router.get("/instances/{instance_id}")
def get_flow_instance(instance_id: UUID) -> FlowInstance:
    try:
        return FlowInstanceService.get(instance_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/instances/{instance_id}/detail")
def get_flow_instance_detail(instance_id: UUID) -> FlowInstanceDetail:
    """Get detailed execution information for a flow instance."""
    try:
        instance = FlowInstanceService.get(instance_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    node_executions = FlowNodeExecutionService.list_by_instance(instance_id)

    return FlowInstanceDetail(
        **instance.model_dump(),
        node_executions=node_executions,
    )


@router.get("/{flow_id}")
def get_flow(flow_id: UUID) -> Flow:
    try:
        return FlowService.get(flow_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{flow_id}")
def update_flow(flow_id: UUID, payload: FlowUpdate) -> Flow:
    try:
        return FlowService.update(flow_id, payload)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flow(flow_id: UUID) -> Response:
    try:
        FlowService.delete(flow_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{flow_id}/execute", status_code=status.HTTP_204_NO_CONTENT)
def execute_flow(flow_id: UUID, payload: FlowExecuteRequest | None = None) -> Response:
    """Manually trigger a flow execution with optional node exclusions."""
    try:
        FlowService.get(flow_id)  # Validate flow exists
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    include_nodes = payload.include_nodes if payload else None
    runner = FlowInstanceRunner(flow_id, include_nodes=include_nodes)
    try:
        runner.do()
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
