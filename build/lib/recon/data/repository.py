"""
Data Repository Layer

Provides high-level CRUD operations with deduplication and relationship management.
All operations are performed within an existing SQLAlchemy session.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import structlog
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import (
    Asset,
    AssetType,
    Host,
    Domain,
    DNSRecord,
    Port,
    Service,
    Certificate,
    Technology,
)

logger = structlog.get_logger(__name__)


class AssetRepository:
    """Manages Asset entities and related sub-objects with deduplication."""

    def __init__(self, session: Session):
        self.session = session

    def get_or_create_asset(self, asset_type: AssetType, value: str) -> Asset:
        """
        Retrieve an existing asset or create a new one.
        Updates last_seen timestamp.

        Args:
            asset_type: Type of the asset (host, domain, ip, etc.).
            value: Normalized value (e.g., IP, domain name).

        Returns:
            The Asset instance.
        """
        asset = (
            self.session.query(Asset)
            .filter_by(type=asset_type, value=value)
            .first()
        )
        if asset:
            asset.last_seen = datetime.now(timezone.utc)
        else:
            asset = Asset(
                id=str(uuid.uuid4()),
                type=asset_type,
                value=value,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
            )
            self.session.add(asset)
        return asset

    def add_dns_records(self, domain: Domain, records: List[Dict[str, Any]]) -> List[DNSRecord]:
        """
        Add DNS records for a domain, skipping duplicates (same type+value for domain).

        Args:
            domain: Domain ORM object.
            records: List of dicts with keys 'record_type', 'value', 'ttl'.

        Returns:
            List of newly added DNSRecord instances (duplicates excluded).
        """
        new_records = []
        for rec in records:
            exists = (
                self.session.query(DNSRecord)
                .filter_by(
                    domain_id=domain.id,
                    record_type=rec["record_type"],
                    value=rec["value"],
                )
                .first()
            )
            if not exists:
                dns_rec = DNSRecord(
                    id=str(uuid.uuid4()),
                    domain_id=domain.id,
                    record_type=rec["record_type"],
                    value=rec["value"],
                    ttl=rec.get("ttl"),
                )
                self.session.add(dns_rec)
                new_records.append(dns_rec)
        return new_records

    def add_port(self, host: Host, port_number: int, protocol: str = "tcp",
                 service_name: Optional[str] = None, banner: Optional[str] = None) -> Port:
        """
        Add a port to a host, deduplicating by (host_id, port_number, protocol).

        Args:
            host: Host ORM object.
            port_number: Port number.
            protocol: 'tcp' or 'udp'.
            service_name: Optional identified service.
            banner: Optional banner grabbed.

        Returns:
            New or existing Port instance.
        """
        port = (
            self.session.query(Port)
            .filter_by(host_id=host.id, port_number=port_number, protocol=protocol)
            .first()
        )
        if not port:
            port = Port(
                id=str(uuid.uuid4()),
                host_id=host.id,
                port_number=port_number,
                protocol=protocol,
                service_name=service_name,
                banner=banner,
                state="open",
                last_seen=datetime.now(timezone.utc),
            )
            self.session.add(port)
        else:
            # Update banner/service if newer
            if banner:
                port.banner = banner
            if service_name:
                port.service_name = service_name
            port.last_seen = datetime.now(timezone.utc)
        return port

    def add_certificate(self, host: Optional[Host], domain: Optional[Domain],
                        fingerprint: str, issuer: str, subject: str,
                        valid_from: datetime, valid_to: datetime) -> Certificate:
        """Add or update a certificate, deduplicating by fingerprint."""
        cert = (
            self.session.query(Certificate)
            .filter_by(fingerprint=fingerprint)
            .first()
        )
        if not cert:
            cert = Certificate(
                id=str(uuid.uuid4()),
                host_id=host.id if host else None,
                domain_id=domain.id if domain else None,
                fingerprint=fingerprint,
                issuer=issuer,
                subject=subject,
                valid_from=valid_from,
                valid_to=valid_to,
                first_seen=datetime.now(timezone.utc),
            )
            self.session.add(cert)
        cert.last_seen = datetime.now(timezone.utc)
        return cert

    def add_technology(self, asset: Asset, name: str, version: Optional[str] = None,
                       category: Optional[str] = None, confidence: float = 1.0) -> Technology:
        """Add a technology fingerprint to an asset; dedup by (asset_id, name, version)."""
        tech = (
            self.session.query(Technology)
            .filter_by(asset_id=asset.id, name=name, version=version)
            .first()
        )
        if not tech:
            tech = Technology(
                id=str(uuid.uuid4()),
                asset_id=asset.id,
                name=name,
                version=version,
                category=category,
                confidence=confidence,
                first_seen=datetime.now(timezone.utc),
            )
            self.session.add(tech)
        tech.last_seen = datetime.now(timezone.utc)
        return tech


class ScanRepository:
    """Manages Scan entities and their status."""

    def __init__(self, session: Session):
        self.session = session

    def create_scan(self, project_id: str, scope: List[str] = None) -> Scan:
        scan = Scan(
            id=str(uuid.uuid4()),
            project_id=project_id,
            status="running",
            scope_json=scope or [],
        )
        self.session.add(scan)
        return scan

    def finish_scan(self, scan_id: str, status: str = "completed"):
        scan = self.session.query(Scan).get(scan_id)
        if scan:
            scan.finished_at = datetime.now(timezone.utc)
            scan.status = status