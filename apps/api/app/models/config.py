import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, CheckConstraint, Text, Integer, text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ConfigVersion(Base):
    __tablename__ = "config_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    git_commit_hash: Mapped[str] = mapped_column(String(40), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    config_path: Mapped[str] = mapped_column(Text, nullable=False)
    config_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB(), server_default=text("'{}'::jsonb")
    )

    device = relationship("Device", back_populates="config_versions")


class ConfigDiff(Base):
    __tablename__ = "config_diffs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    previous_config_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("config_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_config_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("config_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    diff_text: Mapped[str] = mapped_column(Text, nullable=False)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_removed: Mapped[int] = mapped_column(Integer, default=0)
    lines_changed: Mapped[int] = mapped_column(Integer, default=0)
    semantic_summary: Mapped[dict] = mapped_column(
        JSONB(), server_default=text("'[]'::jsonb")
    )
    suspicion_level: Mapped[str] = mapped_column(
        String(20), server_default=text("'low'")
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )

    previous_config_version = relationship(
        "ConfigVersion", foreign_keys=[previous_config_version_id]
    )
    current_config_version = relationship(
        "ConfigVersion", foreign_keys=[current_config_version_id]
    )

    __table_args__ = (
        CheckConstraint(
            "suspicion_level IN ('low', 'medium', 'high', 'critical')",
            name="valid_suspicion_level",
        ),
    )
