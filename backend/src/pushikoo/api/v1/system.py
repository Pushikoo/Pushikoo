import datetime
from typing import Any

from fastapi import APIRouter
from sqlalchemy import delete
from sqlmodel import select

from pushikoo.db import FlowInstance, FlowNodeExecution, get_session
from pushikoo.model.config import SystemConfig
from pushikoo.service.config import ConfigService

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/config")
def get_system_config() -> SystemConfig:
    return ConfigService(id_="system", model_type=SystemConfig).get()


@router.put("/config")
def set_system_config(config: dict[str, Any]) -> SystemConfig:
    cfg = SystemConfig.model_validate(config)
    service = ConfigService(id_="system", model_type=SystemConfig)
    service.set(cfg)
    return service.get()


@router.get("/config/schema")
def get_system_config_schema() -> dict:
    return SystemConfig.model_json_schema()


@router.post("/prune")
def prune(seconds: int = 14 * 24 * 3600) -> dict:
    """Delete FlowInstance and FlowNodeExecution records older than the given seconds."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=seconds)
    with get_session() as session:
        old_instance_ids = session.exec(
            select(FlowInstance.id).where(FlowInstance.created_at < cutoff)
        ).all()

        if not old_instance_ids:
            return {"deleted_instances": 0, "deleted_node_executions": 0}

        # Bulk delete associated node executions
        node_result = session.execute(
            delete(FlowNodeExecution).where(
                FlowNodeExecution.flow_instance_id.in_(old_instance_ids)  # type: ignore[union-attr]
            )
        )

        # Bulk delete expired flow instances
        inst_result = session.execute(
            delete(FlowInstance).where(
                FlowInstance.id.in_(old_instance_ids)  # type: ignore[union-attr]
            )
        )

        session.commit()
        return {
            "deleted_instances": inst_result.rowcount,
            "deleted_node_executions": node_result.rowcount,
        }
