"""
HTTP header analysis – inspects response headers for security misconfigurations.
"""

import asyncio
from typing import Dict, Any, List
import structlog
import httpx

from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType
from recon.data.repository import AssetRepository
from recon.data.models import AssetType

logger = structlog.get_logger(__name__)

SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-XSS-Protection",
    "Referrer-Policy",
    "Permissions-Policy",
]


class HTTPHeadersPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="http_headers",
            version="1.0.0",
            description="Analyse HTTP response headers for security posture",
            author="Recon Team",
            supported_target_types={"domain", "url", "ipv4"},
            dependencies=["httpx"],
            output_schema={
                "headers": "dict",
                "missing_security_headers": "list",
            },
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        if target.type == TargetType.URL:
            url = target.value
        elif target.type == TargetType.DOMAIN:
            url = f"https://{target.value}"
        elif target.type == TargetType.IPV4:
            url = f"http://{target.value}"
        else:
            raise ValueError("Unsupported target type for HTTP header analysis")

        results = {"headers": {}, "missing_security_headers": [], "status_code": None}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "ReconFramework/1.0"})
                results["status_code"] = resp.status_code
                headers = dict(resp.headers)
                results["headers"] = headers

                missing = [h for h in SECURITY_HEADERS if h not in headers]
                results["missing_security_headers"] = missing
        except Exception as e:
            logger.warning("HTTP header analysis failed", url=url, error=str(e))
            results["error"] = str(e)

        # Optionally store as asset
        repo = AssetRepository(db_session)
        asset_val = target.value if target.type == TargetType.URL else url
        asset_type = AssetType.URL if "://" in asset_val else AssetType.DOMAIN
        repo.get_or_create_asset(asset_type, asset_val)
        db_session.commit()

        return results