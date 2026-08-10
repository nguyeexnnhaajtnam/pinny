"""Enhance core chat lifecycle and generation metadata."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260810_02"
down_revision: str | None = "20260808_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("uq_messages_active_assistant", table_name="messages")
    op.drop_constraint("ck_messages_status", "messages", type_="check")
    op.execute("UPDATE messages SET status = 'streaming' WHERE status = 'in_progress'")
    op.execute("UPDATE messages SET status = 'cancelled' WHERE status = 'interrupted'")
    op.add_column("messages", sa.Column("provider", sa.String(length=32), nullable=True))
    op.add_column("messages", sa.Column("model", sa.String(length=255), nullable=True))
    op.add_column("messages", sa.Column("latency_ms", sa.Integer(), nullable=True))
    op.add_column("messages", sa.Column("input_tokens", sa.Integer(), nullable=True))
    op.add_column("messages", sa.Column("output_tokens", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_messages_status",
        "messages",
        "status IN ('pending', 'streaming', 'completed', 'failed', 'cancelled')",
    )
    op.create_check_constraint(
        "ck_messages_latency", "messages", "latency_ms IS NULL OR latency_ms >= 0"
    )
    op.create_check_constraint(
        "ck_messages_input_tokens", "messages", "input_tokens IS NULL OR input_tokens >= 0"
    )
    op.create_check_constraint(
        "ck_messages_output_tokens", "messages", "output_tokens IS NULL OR output_tokens >= 0"
    )
    op.create_index(
        "uq_messages_active_assistant",
        "messages",
        ["conversation_id"],
        unique=True,
        postgresql_where=sa.text("role = 'assistant' AND status IN ('pending', 'streaming')"),
    )


def downgrade() -> None:
    op.drop_index("uq_messages_active_assistant", table_name="messages")
    op.drop_constraint("ck_messages_output_tokens", "messages", type_="check")
    op.drop_constraint("ck_messages_input_tokens", "messages", type_="check")
    op.drop_constraint("ck_messages_latency", "messages", type_="check")
    op.drop_constraint("ck_messages_status", "messages", type_="check")
    op.execute(
        "UPDATE messages SET status = 'in_progress' WHERE status IN ('pending', 'streaming')"
    )
    op.execute("UPDATE messages SET status = 'interrupted' WHERE status = 'cancelled'")
    op.create_check_constraint(
        "ck_messages_status",
        "messages",
        "status IN ('in_progress', 'completed', 'failed', 'interrupted')",
    )
    op.drop_column("messages", "output_tokens")
    op.drop_column("messages", "input_tokens")
    op.drop_column("messages", "latency_ms")
    op.drop_column("messages", "model")
    op.drop_column("messages", "provider")
    op.create_index(
        "uq_messages_active_assistant",
        "messages",
        ["conversation_id"],
        unique=True,
        postgresql_where=sa.text("role = 'assistant' AND status = 'in_progress'"),
    )
