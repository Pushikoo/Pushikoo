"""persist flow execution state

Revision ID: 8c20e88b6a5c
Revises: 3a95bd2df2c0
Create Date: 2026-11-09 16:33:22.289472

"""

import datetime
import json
import uuid
from typing import Sequence, Union

from alembic import op
import pushikoo
import sqlalchemy as sa
import sqlalchemy_utc
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "8c20e88b6a5c"
down_revision: Union[str, None] = "3a95bd2df2c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _as_uuid(value) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _nodes(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = json.loads(value)
    return [str(node) for node in value]


def upgrade() -> None:
    """Upgrade schema and backfill snapshots and per-flow message claims."""
    op.create_table(
        "flowmessage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("flow_id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sqlalchemy_utc.sqltypes.UtcDateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["flow_id"], ["flow.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["message.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("flow_id", "message_id", name="uix_flow_message"),
    )
    op.create_table(
        "flowitem",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("flow_instance_id", sa.Uuid(), nullable=False),
        sa.Column("message_id", sa.Uuid(), nullable=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("last_error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "created_at",
            sqlalchemy_utc.sqltypes.UtcDateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sqlalchemy_utc.sqltypes.UtcDateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["flow_instance_id"], ["flowinstance.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["message.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("flowinstance", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("nodes", pushikoo.util.db.JSONField(), nullable=True)
        )
        batch_op.add_column(sa.Column("cursor", sa.Integer(), nullable=True))

    connection = op.get_bind()
    metadata = sa.MetaData()
    flow = sa.Table("flow", metadata, autoload_with=connection)
    flowinstance = sa.Table("flowinstance", metadata, autoload_with=connection)
    adapterinstance = sa.Table("adapterinstance", metadata, autoload_with=connection)
    message = sa.Table("message", metadata, autoload_with=connection)
    flowmessage = sa.Table("flowmessage", metadata, autoload_with=connection)

    flow_rows = connection.execute(sa.select(flow.c.id, flow.c.nodes)).all()
    flow_nodes = {_as_uuid(row.id): _nodes(row.nodes) for row in flow_rows}
    for row in connection.execute(sa.select(flowinstance.c.id, flowinstance.c.flow_id)):
        nodes = flow_nodes.get(_as_uuid(row.flow_id), [])
        connection.execute(
            flowinstance.update()
            .where(flowinstance.c.id == row.id)
            .values(nodes=json.dumps(nodes), cursor=len(nodes))
        )

    adapters = {
        _as_uuid(row.id): row.adapter_name
        for row in connection.execute(
            sa.select(adapterinstance.c.id, adapterinstance.c.adapter_name)
        )
    }
    getter_flows: dict[str, set[uuid.UUID]] = {}
    for flow_id, nodes in flow_nodes.items():
        for node in nodes:
            try:
                adapter_name = adapters.get(_as_uuid(node))
            except (TypeError, ValueError):
                adapter_name = None
            if adapter_name:
                getter_flows.setdefault(adapter_name, set()).add(flow_id)

    now = datetime.datetime.now(datetime.timezone.utc)
    claims = []
    for row in connection.execute(sa.select(message.c.id, message.c.getter_name)):
        for flow_id in getter_flows.get(row.getter_name, ()):
            claims.append(
                {
                    "id": uuid.uuid4().hex,
                    "flow_id": flow_id.hex,
                    "message_id": _as_uuid(row.id).hex,
                    "created_at": now,
                }
            )
    if claims:
        connection.execute(flowmessage.insert(), claims)

    with op.batch_alter_table("flowinstance", schema=None) as batch_op:
        batch_op.alter_column("nodes", nullable=False)
        batch_op.alter_column("cursor", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("flowinstance", schema=None) as batch_op:
        batch_op.drop_column("cursor")
        batch_op.drop_column("nodes")

    op.drop_table("flowitem")
    op.drop_table("flowmessage")
