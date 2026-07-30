"""
WHOIS lookup plugin – retrieves domain registration details.
"""

import asyncio
import re
from typing import Dict, Any, Optional
import structlog

from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType
from recon.data.repository import AssetRepository
from recon.data.models import AssetType

logger = structlog.get_logger(__name__)


class WhoisPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="whois",
            version="1.0.0",
            description="Retrieve WHOIS registration data for a domain or IP",
            author="Recon Team",
            supported_target_types={"domain", "ipv4", "ipv6"},
            dependencies=["python-whois"],
            system_tools=["whois"],
            output_schema={
                "registrar": "string",
                "creation_date": "datetime",
                "expiration_date": "datetime",
                "name_servers": "list of strings",
                "status": "list of strings",
                "emails": "list of strings",
            },
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        if target.type not in (TargetType.DOMAIN, TargetType.IPV4, TargetType.IPV6):
            raise ValueError("WHOIS requires a domain, IPv4, or IPv6 target.")

        # Run blocking whois in thread pool
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, self._whois_lookup, target.value
        )

        # Normalize and store
        repo = AssetRepository(db_session)
        asset_type = AssetType.DOMAIN if target.type == TargetType.DOMAIN else AssetType.IP
        asset = repo.get_or_create_asset(asset_type, target.value)

        # Store relevant data as domain if applicable
        if target.type == TargetType.DOMAIN:
            from recon.data.models import Domain
            domain = db_session.query(Domain).filter_by(domain_name=target.value).first()
            if not domain:
                domain = Domain(domain_name=target.value, asset_id=asset.id)
                db_session.add(domain)
            domain.registrar = result.get("registrar")
            domain.creation_date = result.get("creation_date")
            domain.expiration_date = result.get("expiration_date")

        db_session.commit()
        logger.info("WHOIS lookup complete", target=target.value)
        return result

    def _whois_lookup(self, target: str) -> Dict[str, Any]:
        """Perform synchronous WHOIS lookup."""
        try:
            import whois
        except ImportError:
            logger.error("python-whois not installed")
            return {"error": "python-whois package missing"}

        try:
            w = whois.whois(target)
            # Extract relevant fields
            return {
                "registrar": w.registrar,
                "creation_date": w.creation_date,
                "expiration_date": w.expiration_date,
                "name_servers": w.name_servers,
                "status": w.status,
                "emails": w.emails,
            }
        except Exception as e:
            logger.warning("WHOIS failed", target=target, error=str(e))
            return {"error": str(e)}