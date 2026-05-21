import uuid
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy import String, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    management_ip: Mapped[str] = mapped_column(INET(), nullable=False)
    vendor: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB(), server_default=text("'{}'::jsonb")
    )

    snapshots = relationship("Snapshot", back_populates="device", cascade="all, delete-orphan")
    config_versions = relationship("ConfigVersion", back_populates="device", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="device", cascade="all, delete-orphan")

    __table_args__ = (
        sa.UniqueConstraint("scenario_id", "hostname", name="uq_devices_scenario_hostname"),
        CheckConstraint(
            "vendor IN ('cisco-ios', 'junos', 'nokia-sros', 'other')",
            name="valid_vendor",
        ),
        CheckConstraint(
            "role IN ('edge-router', 'core-router', 'dist-switch', 'access-switch', 'firewall', 'load-balancer', 'other')",
            name="valid_role",
        ),
    )
