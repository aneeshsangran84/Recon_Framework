"""
CDN and WAF detection based on HTTP headers and known ranges.
"""

import asyncio
from typing import Dict, Any, List
import structlog
import httpx

from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType

logger = structlog.get_logger(__name__)

CDN_HEADERS = {
    "Cloudflare": ["cf-ray", "cf-cache-status"],
    "Akamai": ["x-akamai-transformed"],
    "Fastly": ["x-served-by", "x-cache"],
    "Amazon CloudFront": ["x-amz-cf-id", "x-amz-cf-pop"],
}

WAF_HEADERS = {
    "Cloudflare WAF": ["cf-waf-state"],
    "AWS WAF": ["x-amzn-waf-"],
    "ModSecurity": ["x-modsecurity"],
}


class CDNWAFDetectPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="cdn_waf_detect",
            version="1.0.0",
            description="Detect CDN and WAF presence from HTTP response headers",
            author="Recon Team",
            supported_target_types={"domain", "url"},
            dependencies=["httpx"],
            output_schema={
                "cdn": "list of strings",
                "waf": "list of strings",
                "is_behind_cdn": "bool",
            },
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        url = target.value if target.type == TargetType.URL else f"https://{target.value}"
        results = {"cdn": [], "waf": [], "is_behind_cdn": False}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url)
                headers_lower = {k.lower(): v for k, v in resp.headers.items()}
                # Detect CDN
                for name, markers in CDN_HEADERS.items():
                    if any(marker.lower() in headers_lower for marker in markers):
                        results["cdn"].append(name)
                # Detect WAF
                for name, markers in WAF_HEADERS.items():
                    if any(marker.lower() in headers_lower for marker in markers):
                        results["waf"].append(name)
                results["is_behind_cdn"] = len(results["cdn"]) > 0
        except Exception as e:
            logger.warning("CDN/WAF detection failed", url=url, error=str(e))
            results["error"] = str(e)
        return results