"""
Pydantic Schemas for Data Validation and Serialization.

Used for internal data transfer, API output (future), and plugin
output validation.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# ---------- Asset ----------
class AssetCreate(BaseModel):
    type: str  # 'host', 'domain', 'ip', etc.
    value: str

class AssetOut(BaseModel):
    id: UUID
    type: str
    value: str
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


# ---------- DNS ----------
class DNSRecordCreate(BaseModel):
    record_type: str = Field(..., examples=["A", "AAAA", "MX", "CNAME"])
    value: str
    ttl: Optional[int] = None

class DNSRecordOut(BaseModel):
    id: UUID
    domain_id: UUID
    record_type: str
    value: str
    ttl: Optional[int]

    class Config:
        from_attributes = True


# ---------- Port ----------
class PortOut(BaseModel):
    id: UUID
    host_id: UUID
    port_number: int
    protocol: str
    service_name: Optional[str]
    banner: Optional[str]
    state: str
    last_seen: datetime

    class Config:
        from_attributes = True


# ---------- Certificate ----------
class CertificateOut(BaseModel):
    id: UUID
    fingerprint: str
    issuer: str
    subject: str
    valid_from: datetime
    valid_to: datetime

    class Config:
        from_attributes = True


# ---------- Technology ----------
class TechnologyOut(BaseModel):
    id: UUID
    asset_id: UUID
    name: str
    version: Optional[str]
    category: Optional[str]
    confidence: float

    class Config:
        from_attributes = True