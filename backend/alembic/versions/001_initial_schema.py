"""Initial schema for doctors, appointments, and webhook messages.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-14 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create doctors table
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("specialty", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_doctors_id", "doctors", ["id"], unique=False)
    op.create_index("ix_doctors_name", "doctors", ["name"], unique=False)

    # 2. Create whatsapp_appointments table
    op.create_table(
        "whatsapp_appointments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_phone", sa.String(length=32), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("slot", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="CONFIRMED"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doctor_id", "slot", name="uq_doctor_slot")
    )
    op.create_index("ix_whatsapp_appointments_id", "whatsapp_appointments", ["id"], unique=False)
    op.create_index("ix_whatsapp_appointments_user_phone", "whatsapp_appointments", ["user_phone"], unique=False)
    op.create_index("ix_whatsapp_appointments_doctor_id", "whatsapp_appointments", ["doctor_id"], unique=False)
    op.create_index("ix_whatsapp_appointments_slot", "whatsapp_appointments", ["slot"], unique=False)
    op.create_index("idx_doctor_slot", "whatsapp_appointments", ["doctor_id", "slot"], unique=False)

    # 3. Create webhook_messages table
    op.create_table(
        "webhook_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.String(length=128), nullable=False),
        sa.Column("sender_phone", sa.String(length=32), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("response_sent", sa.Text(), nullable=True),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.ForeignKeyConstraint(["appointment_id"], ["whatsapp_appointments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", name="uq_webhook_message_id")
    )
    op.create_index("ix_webhook_messages_id", "webhook_messages", ["id"], unique=False)
    op.create_index("ix_webhook_messages_message_id", "webhook_messages", ["message_id"], unique=True)
    op.create_index("ix_webhook_messages_sender_phone", "webhook_messages", ["sender_phone"], unique=False)


def downgrade() -> None:
    op.drop_table("webhook_messages")
    op.drop_table("whatsapp_appointments")
    op.drop_table("doctors")
