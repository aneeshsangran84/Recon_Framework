import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Integer, ForeignKey, Text, Enum, UniqueConstraint, Index
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, relationship
import enum

class Base(DeclarativeBase):
    pass

class AssetType(str, enum.Enum):
    HOST = "host"
    DOMAIN = "domain"
    IP = "ip"
    URL = "url"
    ASN = "asn"
    CIDR = "cidr"

class Asset(Base):
    __tablename__ = "assets"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(Enum(AssetType), nullable=False)
    value = Column(String(255), nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("type", "value", name="uq_asset_type_value"),
        Index("idx_asset_type_value", "type", "value"),
    )

class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Scan(Base):
    __tablename__ = "scans"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")
    scope_json = Column(JSON, nullable=True)

# ... additional models: Host, Domain, Port, Service, Certificate, Technology, etc.
# We'll add them as needed; for brevity, focus on core.

# We'll define Host, Domain, etc., in full during implementation.