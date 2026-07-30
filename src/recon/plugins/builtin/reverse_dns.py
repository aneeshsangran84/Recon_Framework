"""
Reverse DNS (PTR) lookup for IPv4 addresses.
"""

import asyncio
import socket
from typing import Dict, Any, Optional
import structlog

from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType
from recon.data.repository import AssetRepository
from recon.data.models import AssetType, Domain

logger = structlog.get_logger(__name__)


class ReverseDNSPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="reverse_dns",
            version="1.0.0",
            description="Perform reverse DNS (PTR) lookups for IP addresses",
            author="Recon Team",
            supported_target_types={"ipv4", "ipv6"},
            dependencies=[],
            output_schema={"hostnames": "list of strings"},
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        if not target.is_ip:
            raise ValueError("Reverse DNS requires an IP address target.")
        ip = target.value
        results = {"hostnames": []}
        try:
            loop = asyncio.get_running_loop()
            hostname, aliaslist, _ = await loop.run_in_executor(
                None, socket.gethostbyaddr, ip
            )
            if hostname:
                results["hostnames"].append(hostname)
            # Also add aliases
            results["hostnames"].extend(aliaslist)
        except socket.herror:
            logger.debug("No PTR record found", ip=ip)
        except Exception as e:
            logger.warning("Reverse DNS lookup error", ip=ip, error=str(e))
            results["error"] = str(e)

        # Store discovered hostnames as domains
        if results["hostnames"]:
            repo = AssetRepository(db_session)
            for name in results["hostnames"]:
                asset = repo.get_or_create_asset(AssetType.DOMAIN, name)
                dom = db_session.query(Domain).filter_by(domain_name=name).first()
                if not dom:
                    dom = Domain(domain_name=name, asset_id=asset.id)
                    db_session.add(dom)
            db_session.commit()

        return results