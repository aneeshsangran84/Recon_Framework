"""SQLAlchemy ORM models for Recon Framework."""

import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Integer, ForeignKey, Float, Text, UniqueConstraint, Index
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, relationship


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
    type = Column(String(10), nullable=False)
    value = Column(String(255), nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("type", "value", name="uq_asset_type_value"),
        Index("idx_asset_type_value", "type", "value"),
    )


class Project(Base):
    __tablename__ = "projects"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    scans = relationship("Scan", back_populates="project")


class Scan(Base):
    __tablename__ = "scans"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")
    scope_json = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="scans")


class Host(Base):
    __tablename__ = "hosts"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False)
    ip_address = Column(String(45), nullable=False)
    ip_version = Column(Integer, nullable=False)
    hostnames = Column(JSON, nullable=True)
    os_guess = Column(String(255), nullable=True)

    asset = relationship("Asset", backref="hosts")
    ports = relationship("Port", back_populates="host")
    certificates = relationship("Certificate", back_populates="host")


class Domain(Base):
    __tablename__ = "domains"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False)
    domain_name = Column(String(255), unique=True, nullable=False)
    registrar = Column(String(255), nullable=True)
    creation_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)

    asset = relationship("Asset", backref="domains")
    dns_records = relationship("DNSRecord", back_populates="domain")
    certificates = relationship("Certificate", back_populates="domain")


class DNSRecord(Base):
    __tablename__ = "dns_records"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    domain_id = Column(String(36), ForeignKey("domains.id"), nullable=False)
    record_type = Column(String(10), nullable=False)
    value = Column(String(1024), nullable=False)
    ttl = Column(Integer, nullable=True)

    domain = relationship("Domain", back_populates="dns_records")


class Port(Base):
    __tablename__ = "ports"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    host_id = Column(String(36), ForeignKey("hosts.id"), nullable=False)
    port_number = Column(Integer, nullable=False)
    protocol = Column(String(5), default="tcp")
    service_name = Column(String(100), nullable=True)
    banner = Column(Text, nullable=True)
    state = Column(String(10), default="open")
    last_seen = Column(DateTime, default=datetime.utcnow)

    host = relationship("Host", back_populates="ports")
    services = relationship("Service", back_populates="port")

    __table_args__ = (
        UniqueConstraint("host_id", "port_number", "protocol", name="uq_host_port_proto"),
    )


class Service(Base):
    __tablename__ = "services"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    port_id = Column(String(36), ForeignKey("ports.id"), nullable=False)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=True)
    extra_info = Column(Text, nullable=True)

    port = relationship("Port", back_populates="services")


class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    host_id = Column(String(36), ForeignKey("hosts.id"), nullable=True)
    domain_id = Column(String(36), ForeignKey("domains.id"), nullable=True)
    fingerprint = Column(String(64), unique=True, nullable=False)
    issuer = Column(Text, nullable=True)
    subject = Column(Text, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    host = relationship("Host", back_populates="certificates")
    domain = relationship("Domain", back_populates="certificates")


class Technology(Base):
    __tablename__ = "technologies"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_id = Column(String(36), ForeignKey("assets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)
    confidence = Column(Float, default=1.0)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", backref="technologies")
