import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, CheckConstraint, Text, BigInteger, Integer, text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    cpu_usage = mapped_column(DECIMAL(5, 2), nullable=True)
    memory_usage = mapped_column(DECIMAL(5, 2), nullable=True)
    latency_ms = mapped_column(DECIMAL(10, 2), nullable=True)
    packet_loss_pct = mapped_column(DECIMAL(5, 2), nullable=True)
    snapshot_source: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'simulation'")
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB(), server_default=text("'{}'::jsonb")
    )
    tags = mapped_column(ARRAY(Text), server_default=text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )

    device = relationship("Device", back_populates="snapshots")
    interface_snapshots = relationship(
        "InterfaceSnapshot", back_populates="snapshot", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("cpu_usage >= 0 AND cpu_usage <= 100", name="valid_cpu"),
        CheckConstraint("memory_usage >= 0 AND memory_usage <= 100", name="valid_memory"),
        CheckConstraint("latency_ms >= 0", name="valid_latency"),
        CheckConstraint("packet_loss_pct >= 0 AND packet_loss_pct <= 100", name="valid_packet_loss"),
        CheckConstraint(
            "snapshot_source IN ('simulation', 'ssh', 'snmp', 'api')",
            name="valid_snapshot_source",
        ),
    )


class InterfaceSnapshot(Base):
    __tablename__ = "interface_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False
    )
    interface_name: Mapped[str] = mapped_column(String(100), nullable=False)
    admin_state: Mapped[str] = mapped_column(String(20), nullable=False)
    oper_state: Mapped[str] = mapped_column(String(20), nullable=False)
    rx_errors: Mapped[int] = mapped_column(BigInteger, default=0)
    tx_errors: Mapped[int] = mapped_column(BigInteger, default=0)
    rx_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    tx_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET(), nullable=True)
    speed_mbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duplex: Mapped[str | None] = mapped_column(String(20), nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB(), server_default=text("'{}'::jsonb")
    )

    snapshot = relationship("Snapshot", back_populates="interface_snapshots")

    __table_args__ = (
        CheckConstraint("admin_state IN ('up', 'down')", name="valid_admin_state"),
        CheckConstraint("oper_state IN ('up', 'down', 'degraded')", name="valid_oper_state"),
    )
