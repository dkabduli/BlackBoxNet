"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-11-15 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hostname", sa.String(255), nullable=False, unique=True),
        sa.Column("management_ip", postgresql.INET(), nullable=False),
        sa.Column("vendor", sa.String(50), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("vendor IN ('cisco-ios', 'junos', 'nokia-sros', 'other')", name="valid_vendor"),
        sa.CheckConstraint("role IN ('edge-router', 'core-router', 'dist-switch', 'access-switch', 'firewall', 'load-balancer', 'other')", name="valid_role"),
    )
    op.create_index("idx_devices_hostname", "devices", ["hostname"])
    op.create_index("idx_devices_vendor", "devices", ["vendor"])
    op.create_index("idx_devices_role", "devices", ["role"])

    op.create_table(
        "snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("cpu_usage", sa.DECIMAL(5, 2)),
        sa.Column("memory_usage", sa.DECIMAL(5, 2)),
        sa.Column("latency_ms", sa.DECIMAL(10, 2)),
        sa.Column("packet_loss_pct", sa.DECIMAL(5, 2)),
        sa.Column("snapshot_source", sa.String(50), nullable=False, server_default="simulation"),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("tags", postgresql.ARRAY(sa.Text), server_default=sa.text("'{}'::text[]")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("cpu_usage >= 0 AND cpu_usage <= 100", name="valid_cpu"),
        sa.CheckConstraint("memory_usage >= 0 AND memory_usage <= 100", name="valid_memory"),
        sa.CheckConstraint("latency_ms >= 0", name="valid_latency"),
        sa.CheckConstraint("packet_loss_pct >= 0 AND packet_loss_pct <= 100", name="valid_packet_loss"),
        sa.CheckConstraint("snapshot_source IN ('simulation', 'ssh', 'snmp', 'api')", name="valid_snapshot_source"),
    )
    op.create_index("idx_snapshots_device_timestamp", "snapshots", ["device_id", sa.text("timestamp DESC")])
    op.create_index("idx_snapshots_timestamp", "snapshots", [sa.text("timestamp DESC")])
    op.create_index("idx_snapshots_config_hash", "snapshots", ["config_hash"])

    op.create_table(
        "interface_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interface_name", sa.String(100), nullable=False),
        sa.Column("admin_state", sa.String(20), nullable=False),
        sa.Column("oper_state", sa.String(20), nullable=False),
        sa.Column("rx_errors", sa.BigInteger, default=0),
        sa.Column("tx_errors", sa.BigInteger, default=0),
        sa.Column("rx_bytes", sa.BigInteger, default=0),
        sa.Column("tx_bytes", sa.BigInteger, default=0),
        sa.Column("description", sa.Text),
        sa.Column("ip_address", postgresql.INET()),
        sa.Column("speed_mbps", sa.Integer),
        sa.Column("duplex", sa.String(20)),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("admin_state IN ('up', 'down')", name="valid_admin_state"),
        sa.CheckConstraint("oper_state IN ('up', 'down', 'degraded')", name="valid_oper_state"),
    )
    op.create_index("idx_interface_snapshots_snapshot", "interface_snapshots", ["snapshot_id"])
    op.create_index("idx_interface_snapshots_name", "interface_snapshots", ["interface_name"])

    op.create_table(
        "config_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("git_commit_hash", sa.String(40), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("config_path", sa.Text, nullable=False),
        sa.Column("config_size_bytes", sa.Integer),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_config_versions_device_timestamp", "config_versions", ["device_id", sa.text("timestamp DESC")])
    op.create_index("idx_config_versions_commit_hash", "config_versions", ["git_commit_hash"])
    op.create_index("idx_config_versions_config_hash", "config_versions", ["config_hash"])

    op.create_table(
        "config_diffs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_config_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("config_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("current_config_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("config_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("diff_text", sa.Text, nullable=False),
        sa.Column("lines_added", sa.Integer, default=0),
        sa.Column("lines_removed", sa.Integer, default=0),
        sa.Column("lines_changed", sa.Integer, default=0),
        sa.Column("semantic_summary", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("suspicion_level", sa.String(20), server_default="low"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("suspicion_level IN ('low', 'medium', 'high', 'critical')", name="valid_suspicion_level"),
    )
    op.create_index("idx_config_diffs_device", "config_diffs", ["device_id"])
    op.create_index("idx_config_diffs_timestamp", "config_diffs", [sa.text("timestamp DESC")])

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("related_config_diff_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("config_diffs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("related_snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("snapshots.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "event_type IN ('CONFIG_CHANGE', 'LATENCY_SPIKE', 'PACKET_LOSS_INCREASE', "
            "'INTERFACE_DEGRADED', 'INTERFACE_ERRORS', 'CPU_RISE', 'MEMORY_RISE', "
            "'OUTAGE_STARTED', 'OUTAGE_ENDED', 'CORRELATION_FLAG', "
            "'DEVICE_UNREACHABLE', 'DEVICE_RECOVERED')",
            name="valid_event_type",
        ),
        sa.CheckConstraint("severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL')", name="valid_severity"),
    )
    op.create_index("idx_events_device_timestamp", "events", ["device_id", sa.text("timestamp DESC")])
    op.create_index("idx_events_timestamp", "events", [sa.text("timestamp DESC")])
    op.create_index("idx_events_event_type", "events", ["event_type"])
    op.create_index("idx_events_severity", "events", ["severity"])

    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("affected_scope", sa.Text),
        sa.Column("root_device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="SET NULL")),
        sa.Column("summary", sa.Text),
        sa.Column("suspicion_summary", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("status IN ('active', 'resolved', 'investigating', 'acknowledged')", name="valid_status"),
    )
    op.create_index("idx_incidents_start_time", "incidents", [sa.text("start_time DESC")])
    op.create_index("idx_incidents_status", "incidents", ["status"])

    op.create_table(
        "incident_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relevance_score", sa.DECIMAL(3, 2), server_default="1.0"),
        sa.Column("is_primary_cause", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("incident_id", "event_id", name="unique_incident_event"),
        sa.CheckConstraint("relevance_score >= 0 AND relevance_score <= 1", name="valid_relevance"),
    )
    op.create_index("idx_incident_events_incident", "incident_events", ["incident_id"])
    op.create_index("idx_incident_events_event", "incident_events", ["event_id"])

    op.create_table(
        "incident_affected_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("impact_level", sa.String(20), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("incident_id", "device_id", name="unique_incident_device"),
        sa.CheckConstraint("impact_level IN ('low', 'medium', 'high', 'critical')", name="valid_impact_level"),
    )
    op.create_index("idx_incident_affected_devices_incident", "incident_affected_devices", ["incident_id"])
    op.create_index("idx_incident_affected_devices_device", "incident_affected_devices", ["device_id"])


def downgrade() -> None:
    op.drop_table("incident_affected_devices")
    op.drop_table("incident_events")
    op.drop_table("incidents")
    op.drop_table("events")
    op.drop_table("config_diffs")
    op.drop_table("config_versions")
    op.drop_table("interface_snapshots")
    op.drop_table("snapshots")
    op.drop_table("devices")
