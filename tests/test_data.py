"""
Tests for data layer: models, repository, deduplication.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from recon.data.models import (
    Asset, AssetType, Project, Host, Domain, DNSRecord, Port, Certificate, Technology
)
from recon.data.repository import AssetRepository, ScanRepository


def test_asset_creation(db_session):
    repo = AssetRepository(db_session)
    asset1 = repo.get_or_create_asset(AssetType.DOMAIN, "example.com")
    assert asset1.id is not None
    assert asset1.type == AssetType.DOMAIN
    # Call again should return same asset
    asset2 = repo.get_or_create_asset(AssetType.DOMAIN, "example.com")
    assert asset2.id == asset1.id


def test_asset_dedup_across_types(db_session):
    repo = AssetRepository(db_session)
    domain_asset = repo.get_or_create_asset(AssetType.DOMAIN, "google.com")
    ip_asset = repo.get_or_create_asset(AssetType.IP, "google.com")
    assert domain_asset.id != ip_asset.id


def test_dns_record_dedup(db_session):
    # Create a domain
    repo = AssetRepository(db_session)
    asset = repo.get_or_create_asset(AssetType.DOMAIN, "example.org")
    domain = Domain(id=str(uuid.uuid4()), domain_name="example.org", asset_id=asset.id)
    db_session.add(domain)
    db_session.commit()

    records = [
        {"record_type": "A", "value": "93.184.216.34", "ttl": 3600},
        {"record_type": "A", "value": "93.184.216.34", "ttl": 7200},  # duplicate
        {"record_type": "MX", "value": "mail.example.org", "ttl": 300},
    ]
    new_recs = repo.add_dns_records(domain, records)
    assert len(new_recs) == 2  # only the two unique ones added

    # Try adding again, should return empty
    new_recs2 = repo.add_dns_records(domain, records)
    assert len(new_recs2) == 0


def test_port_dedup(db_session):
    repo = AssetRepository(db_session)
    asset = repo.get_or_create_asset(AssetType.IP, "192.0.2.1")
    host = Host(id=str(uuid.uuid4()), ip_address="192.0.2.1", ip_version=4, asset_id=asset.id)
    db_session.add(host)
    db_session.commit()

    port1 = repo.add_port(host, 80, "tcp", "http")
    port2 = repo.add_port(host, 80, "tcp", "http")  # same
    assert port1.id == port2.id

    port3 = repo.add_port(host, 443, "tcp", "https")
    assert port3.id != port1.id


def test_certificate_dedup_by_fingerprint(db_session):
    repo = AssetRepository(db_session)
    cert1 = repo.add_certificate(
        None, None,
        fingerprint="abc123",
        issuer="Test CA",
        subject="example.com",
        valid_from=datetime.now(timezone.utc),
        valid_to=datetime.now(timezone.utc),
    )
    cert2 = repo.add_certificate(
        None, None,
        fingerprint="abc123",
        issuer="Test CA",
        subject="example.com",
        valid_from=datetime.now(timezone.utc),
        valid_to=datetime.now(timezone.utc),
    )
    assert cert1.id == cert2.id


def test_scan_repository(db_session):
    repo = ScanRepository(db_session)
    scan = repo.create_scan("project-1", ["192.168.0.0/24"])
    assert scan.status == "running"
    repo.finish_scan(scan.id, "completed")
    assert scan.status == "completed"
    assert scan.finished_at is not None