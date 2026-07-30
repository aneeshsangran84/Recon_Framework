"""initial migration

Revision ID: 001
Revises: None
Create Date: 2024-10-15 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Assets
    op.create_table(
        "assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("value", sa.String(255), nullable=False),
        sa.Column("first_seen", sa.DateTime(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("type", "value", name="uq_asset_type_value"),
    )

    # Projects
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # Scans
    op.create_table(
        "scans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(20), default="running"),
        sa.Column("scope_json", sa.JSON(), nullable=True),
    )

    # Hosts
    op.create_table(
        "hosts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("ip_version", sa.Integer(), nullable=False),
        sa.Column("hostnames", sa.JSON(), nullable=True),
        sa.Column("os_guess", sa.String(255), nullable=True),
    )

    # Domains
    op.create_table(
        "domains",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("domain_name", sa.String(255), unique=True, nullable=False),
        sa.Column("registrar", sa.String(255), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("expiration_date", sa.DateTime(), nullable=True),
    )

    # DNS Records
    op.create_table(
        "dns_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domain_id", sa.String(36), sa.ForeignKey("domains.id"), nullable=False),
        sa.Column("record_type", sa.String(10), nullable=False),
        sa.Column("value", sa.String(1024), nullable=False),
        sa.Column("ttl", sa.Integer(), nullable=True),
    )

    # Ports
    op.create_table(
        "ports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("host_id", sa.String(36), sa.ForeignKey("hosts.id"), nullable=False),
        sa.Column("port_number", sa.Integer(), nullable=False),
        sa.Column("protocol", sa.String(5), default="tcp"),
        sa.Column("service_name", sa.String(100), nullable=True),
        sa.Column("banner", sa.Text(), nullable=True),
        sa.Column("state", sa.String(10), default="open"),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("host_id", "port_number", "protocol", name="uq_host_port_proto"),
    )

    # Certificates
    op.create_table(
        "certificates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("host_id", sa.String(36), sa.ForeignKey("hosts.id"), nullable=True),
        sa.Column("domain_id", sa.String(36), sa.ForeignKey("domains.id"), nullable=True),
        sa.Column("fingerprint", sa.String(64), unique=True, nullable=False),
        sa.Column("issuer", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("valid_from", sa.DateTime(), nullable=True),
        sa.Column("valid_to", sa.DateTime(), nullable=True),
        sa.Column("first_seen", sa.DateTime(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
    )

    # Technologies
    op.create_table(
        "technologies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("confidence", sa.Float(), default=1.0),
        sa.Column("first_seen", sa.DateTime(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("technologies")
    op.drop_table("certificates")
    op.drop_table("ports")
    op.drop_table("dns_records")
    op.drop_table("domains")
    op.drop_table("hosts")
    op.drop_table("scans")
    op.drop_table("projects")
    op.drop_table("assets")