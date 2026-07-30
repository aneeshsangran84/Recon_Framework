"""
Technology fingerprinting using Wappalyzer-like approach.
Checks HTTP responses and JavaScript variables.
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog
import httpx
import re

from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType
from recon.data.repository import AssetRepository
from recon.data.models import AssetType, Technology

logger = structlog.get_logger(__name__)

# Basic signatures (simplified)
TECH_SIGNATURES = {
    "Apache": {"headers": {"Server": r"Apache"}},
    "Nginx": {"headers": {"Server": r"nginx"}},
    "Cloudflare": {"headers": {"Server": r"cloudflare", "CF-Ray": r".+"}},
    "jQuery": {"js": r"jquery[.-](\d+\.\d+\.\d+)"},
    "Bootstrap": {"html": r'bootstrap(?:\.min)?\.css'},
    "WordPress": {"meta": {"generator": r"WordPress\s*([\d.]+)"}},
}


class TechFingerprintPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="tech_fingerprint",
            version="1.0.0",
            description="Detect web technologies from HTTP response",
            author="Recon Team",
            supported_target_types={"domain", "url"},
            dependencies=["httpx"],
            output_schema={
                "technologies": "list of {name, version, category, confidence}"
            },
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        url = target.value if target.type == TargetType.URL else f"https://{target.value}"
        results = {"technologies": []}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url)
                html = resp.text
                headers = resp.headers

                detected = self._detect(html, headers)
                results["technologies"] = detected

                repo = AssetRepository(db_session)
                asset_type = AssetType.URL if "://" in url else AssetType.DOMAIN
                asset = repo.get_or_create_asset(asset_type, url)
                for tech in detected:
                    repo.add_technology(
                        asset, name=tech["name"], version=tech.get("version"),
                        category=tech.get("category"), confidence=tech.get("confidence", 1.0),
                    )
                db_session.commit()
        except Exception as e:
            logger.warning("Technology fingerprinting failed", url=url, error=str(e))
            results["error"] = str(e)
        return results

    def _detect(self, html: str, headers: httpx.Headers) -> List[Dict[str, Any]]:
        found = []
        for tech, sig in TECH_SIGNATURES.items():
            if "headers" in sig:
                for hdr, pattern in sig["headers"].items():
                    value = headers.get(hdr, "")
                    if re.search(pattern, value, re.I):
                        found.append({"name": tech, "category": "web server", "confidence": 0.9})
                        break
            if "html" in sig:
                pattern = sig["html"]
                if re.search(pattern, html, re.I):
                    found.append({"name": tech, "category": "framework", "confidence": 0.8})
            if "js" in sig:
                pattern = sig["js"]
                match = re.search(pattern, html, re.I)
                if match:
                    version = match.group(1) if match.lastindex else None
                    found.append({"name": tech, "version": version, "category": "library", "confidence": 0.9})
            if "meta" in sig:
                for meta_name, meta_pattern in sig["meta"].items():
                    meta_re = re.compile(rf'<meta\s+name=["\']{meta_name}["\']\s+content=["\']({meta_pattern})["\']', re.I)
                    match = meta_re.search(html)
                    if match:
                        version = match.group(1) if match.lastindex else None
                        found.append({"name": tech, "version": version, "category": "CMS", "confidence": 0.95})
        return found