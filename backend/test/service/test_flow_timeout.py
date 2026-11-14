import datetime
import uuid
from unittest.mock import Mock

from sqlmodel import select

import pushikoo.service.refresh as refresh_module
from pushikoo.db import Flow, FlowInstance, FlowItem, FlowNodeExecution, get_session
from pushikoo.model.config import SystemConfig
from pushikoo.service.config import ConfigService
from pushikoo.service.refresh import FlowInstanceRunner


class FakeProcess:
    def __init__(self, *, start_error: Exception | None = None):
        self.start_error = start_error
        self.exitcode = None
        self.alive = False
        self.terminated = False
        self.killed = False
        self.join_timeouts = []

    def start(self):
        if self.start_error is not None:
            raise self.start_error
        self.alive = True

    def join(self, timeout=None):
        self.join_timeouts.append(timeout)

    def is_alive(self):
        return self.alive

    def terminate(self):
        self.terminated = True
        self.alive = False

    def kill(self):
        self.killed = True
        self.alive = False


class FakeContext:
    def __init__(self, process):
        self.process = process

    def Process(self, **_kwargs):
        return self.process


def _create_running_instance():
    flow_id = uuid.uuid4()
    instance_id = uuid.uuid4()
    adapter_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.timezone.utc)
    with get_session() as session:
        session.add(Flow(id=flow_id, name="timeout-test", nodes=[str(adapter_id)]))
        session.add(
            FlowInstance(
                id=instance_id,
                flow_id=flow_id,
                status="running",
                nodes=[str(adapter_id)],
                cursor=0,
                created_at=now,
            )
        )
        session.add(
            FlowNodeExecution(
                flow_instance_id=instance_id,
                adapter_instance_id=adapter_id,
                node_index=0,
                status="running",
                started_at=now,
            )
        )
        session.add(
            FlowItem(
                flow_instance_id=instance_id,
                content={},
                cursor=0,
                status="pending",
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()
    return instance_id


def _set_timeout(seconds: int):
    config = SystemConfig()
    config.policy.flow_run_timeout_seconds = seconds
    ConfigService("system", SystemConfig).set(config)


def _assert_aborted(instance_id, expected_error):
    with get_session() as session:
        instance = session.get(FlowInstance, instance_id)
        nodes = session.exec(
            select(FlowNodeExecution).where(
                FlowNodeExecution.flow_instance_id == instance_id
            )
        ).all()
        items = session.exec(
            select(FlowItem).where(FlowItem.flow_instance_id == instance_id)
        ).all()
    assert instance.status == "failed"
    assert [node.status for node in nodes] == ["failed"]
    assert [node.error_message for node in nodes] == [expected_error]
    assert [item.status for item in items] == ["failed"]
    assert [item.last_error for item in items] == [expected_error]


def test_timeout_terminates_process_and_aborts_records(monkeypatch):
    instance_id = _create_running_instance()
    _set_timeout(7)
    process = FakeProcess()
    monkeypatch.setattr(
        refresh_module.multiprocessing,
        "get_context",
        lambda _method: FakeContext(process),
    )
    runner = FlowInstanceRunner.resume(instance_id)
    runner._issue_warning = Mock()

    runner._refresh_worker()

    assert process.terminated is True
    assert process.killed is False
    assert process.join_timeouts == [7, 5]
    assert runner._process is None
    runner._issue_warning.assert_called_once()
    _assert_aborted(instance_id, "aborted: flow run timed out after 7 seconds")


def test_process_start_failure_aborts_records(monkeypatch):
    instance_id = _create_running_instance()
    _set_timeout(7)
    process = FakeProcess(start_error=RuntimeError("spawn failed"))
    monkeypatch.setattr(
        refresh_module.multiprocessing,
        "get_context",
        lambda _method: FakeContext(process),
    )
    runner = FlowInstanceRunner.resume(instance_id)

    runner._refresh_worker()

    assert process.terminated is False
    assert runner._process is None
    _assert_aborted(instance_id, "aborted: spawn failed")
