import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, CheckConstraint, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_config_diff_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("config_diffs.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB(), server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )

    device = relationship("Device", back_populates="events")

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('CONFIG_CHANGE', 'LATENCY_SPIKE', 'PACKET_LOSS_INCREASE', "
            "'INTERFACE_DEGRADED', 'INTERFACE_ERRORS', 'CPU_RISE', 'MEMORY_RISE', "
            "'OUTAGE_STARTED', 'OUTAGE_ENDED', 'CORRELATION_FLAG', "
            "'DEVICE_UNREACHABLE', 'DEVICE_RECOVERED')",
            name="valid_event_type",
        ),
        CheckConstraint(
            "severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')",
            name="valid_severity",
        ),
    )
