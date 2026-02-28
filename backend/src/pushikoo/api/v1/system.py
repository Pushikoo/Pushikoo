import datetime
from typing import Any

from fastapi import APIRouter
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

        node_count = 0
        for inst_id in old_instance_ids:
            nodes = session.exec(
                select(FlowNodeExecution).where(FlowNodeExecution.flow_instance_id == inst_id)
            ).all()
            for node in nodes:
                session.delete(node)
                node_count += 1

        for inst_id in old_instance_ids:
            inst = session.get(FlowInstance, inst_id)
            if inst:
                session.delete(inst)

        session.commit()
        return {"deleted_instances": len(old_instance_ids), "deleted_node_executions": node_count}
