"""
Certificate Transparency log search using crt.sh.
No API key required.
"""

import asyncio
from typing import Dict, Any, List
import structlog
import httpx

from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType
from recon.data.repository import AssetRepository
from recon.data.models import AssetType, Domain

logger = structlog.get_logger(__name__)


class CertTransparencyPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="cert_transparency",
            version="1.0.0",
            description="Query Certificate Transparency logs for subdomains",
            author="Recon Team",
            supported_target_types={"domain"},
            dependencies=["httpx"],
            output_schema={
                "subdomains": "list of strings",
                "total": "int",
            },
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        if target.type != TargetType.DOMAIN:
            raise ValueError("Certificate transparency lookup requires a domain target.")
        domain = target.value
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        results = {"subdomains": [], "total": 0}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers={"User-Agent": "ReconFramework/1.0"})
                if resp.status_code == 200:
                    entries = resp.json()
                    names = set()
                    for entry in entries:
                        name_value = entry.get("name_value", "")
                        for name in name_value.split("\n"):
                            name = name.strip().lower()
                            if name.endswith(f".{domain}") or name == domain:
                                names.add(name)
                    results["subdomains"] = sorted(names)
                    results["total"] = len(names)

                    # Persist subdomains as domain assets
                    repo = AssetRepository(db_session)
                    for sub in names:
                        asset = repo.get_or_create_asset(AssetType.DOMAIN, sub)
                        # optionally create Domain record
                        dom = db_session.query(Domain).filter_by(domain_name=sub).first()
                        if not dom:
                            dom = Domain(domain_name=sub, asset_id=asset.id)
                            db_session.add(dom)
                    db_session.commit()
        except Exception as e:
            logger.error("Certificate transparency query failed", domain=domain, error=str(e))
            results["error"] = str(e)

        return results