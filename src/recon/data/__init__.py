"""
Recon Framework - Data Layer

Provides ORM models (see models.py), database session management (database.py),
CRUD operations with deduplication (repository.py), and data validation schemas (schema.py).
"""

from .models import (
    Base,
    Asset,
    AssetType,
    Project,
    Scan,
    Host,
    Domain,
    DNSRecord,
    Port,
    Service,
    Certificate,
    Technology,
)
from .database import init_db, get_session
from .repository import AssetRepository, ScanRepository
from .schema import (
    AssetCreate,
    AssetOut,
    DNSRecordCreate,
    DNSRecordOut,
    PortOut,
    CertificateOut,
    TechnologyOut,
)

__all__ = [
    # models
    "Base",
    "Asset",
    "AssetType",
    "Project",
    "Scan",
    "Host",
    "Domain",
    "DNSRecord",
    "Port",
    "Service",
    "Certificate",
    "Technology",
    # database
    "init_db",
    "get_session",
    # repository
    "AssetRepository",
    "ScanRepository",
    # schema
    "AssetCreate",
    "AssetOut",
    "DNSRecordCreate",
    "DNSRecordOut",
    "PortOut",
    "CertificateOut",
    "TechnologyOut",
]