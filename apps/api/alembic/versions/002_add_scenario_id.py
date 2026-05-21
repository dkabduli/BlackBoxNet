"""add scenario_id namespacing

Revision ID: 002
Revises: 001
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "devices",
        sa.Column("scenario_id", sa.String(64), nullable=False, server_default="acl-regression"),
    )
    op.drop_constraint("devices_hostname_key", "devices", type_="unique")
    op.create_unique_constraint("uq_devices_scenario_hostname", "devices", ["scenario_id", "hostname"])
    op.create_index("ix_devices_scenario_id", "devices", ["scenario_id"])

    op.add_column(
        "incidents",
        sa.Column("scenario_id", sa.String(64), nullable=False, server_default="acl-regression"),
    )
    op.create_index("ix_incidents_scenario_id", "incidents", ["scenario_id"])

    op.add_column(
        "events",
        sa.Column("scenario_id", sa.String(64), nullable=False, server_default="acl-regression"),
    )
    op.create_index("ix_events_scenario_id", "events", ["scenario_id"])

    op.add_column(
        "snapshots",
        sa.Column("scenario_id", sa.String(64), nullable=False, server_default="acl-regression"),
    )
    op.create_index("ix_snapshots_scenario_id", "snapshots", ["scenario_id"])

    op.add_column(
        "config_versions",
        sa.Column("scenario_id", sa.String(64), nullable=False, server_default="acl-regression"),
    )

    op.add_column(
        "config_diffs",
        sa.Column("scenario_id", sa.String(64), nullable=False, server_default="acl-regression"),
    )

    for table in ("devices", "incidents", "events", "snapshots", "config_versions", "config_diffs"):
        op.alter_column(table, "scenario_id", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_snapshots_scenario_id", table_name="snapshots")
    op.drop_column("snapshots", "scenario_id")
    op.drop_index("ix_events_scenario_id", table_name="events")
    op.drop_column("events", "scenario_id")
    op.drop_index("ix_incidents_scenario_id", table_name="incidents")
    op.drop_column("incidents", "scenario_id")
    op.drop_column("config_diffs", "scenario_id")
    op.drop_column("config_versions", "scenario_id")
    op.drop_index("ix_devices_scenario_id", table_name="devices")
    op.drop_constraint("uq_devices_scenario_hostname", "devices", type_="unique")
    op.drop_column("devices", "scenario_id")
    op.create_unique_constraint("devices_hostname_key", "devices", ["hostname"])
