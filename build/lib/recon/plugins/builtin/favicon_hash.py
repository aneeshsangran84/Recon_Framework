"""
Favicon hashing – retrieves the favicon.ico and computes MurmurHash3 (used by Shodan).
"""

import asyncio
import struct
import hashlib
from typing import Dict, Any, Optional
import structlog
import httpx

from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType

logger = structlog.get_logger(__name__)


class FaviconHashPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="favicon_hash",
            version="1.0.0",
            description="Compute MurmurHash3 hash of favicon.ico for Shodan searches",
            author="Recon Team",
            supported_target_types={"domain", "url"},
            dependencies=["httpx"],
            output_schema={
                "favicon_url": "string",
                "murmur_hash": "int",
            },
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        base_url = target.value if target.type == TargetType.URL else f"https://{target.value}"
        results = {"favicon_url": None, "murmur_hash": None}
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                # Try fetching the page to find favicon link
                resp = await client.get(base_url)
                # Simple regex to find favicon
                import re
                match = re.search(r'<link[^>]+rel=["\'](?:shortcut )?icon["\'] [^>]+href=["\']([^"\']+)', resp.text, re.I)
                favicon_path = match.group(1) if match else "/favicon.ico"
                if not favicon_path.startswith("http"):
                    favicon_url = httpx.URL(base_url).join(httpx.URL(favicon_path)).__str__()
                else:
                    favicon_url = favicon_path

                results["favicon_url"] = favicon_url
                fav_resp = await client.get(favicon_url)
                if fav_resp.status_code == 200:
                    # Compute MurmurHash3
                    hash_val = self._murmur3_32(fav_resp.content)
                    results["murmur_hash"] = hash_val
        except Exception as e:
            logger.warning("Favicon hash failed", target=base_url, error=str(e))
            results["error"] = str(e)

        return results

    def _murmur3_32(self, data: bytes, seed: int = 0) -> int:
        """MurmurHash3 32-bit implementation for Shodan compatibility."""
        c1 = 0xcc9e2d51
        c2 = 0x1b873593

        length = len(data)
        h1 = seed
        roundedEnd = (length & 0xfffffffc)  # round down to 4 byte block
        for i in range(0, roundedEnd, 4):
            # little endian load order
            k1 = (data[i] & 0xff) | ((data[i + 1] & 0xff) << 8) | \
                 ((data[i + 2] & 0xff) << 16) | (data[i + 3] << 24)
            k1 *= c1
            k1 = (k1 << 15) | ((k1 & 0xffffffff) >> 17)  # ROTL32(k1,15)
            k1 *= c2

            h1 ^= k1
            h1 = (h1 << 13) | ((h1 & 0xffffffff) >> 19)  # ROTL32(h1,13)
            h1 = h1 * 5 + 0xe6546b64

        # tail
        k1 = 0
        val = length & 0x03
        if val == 3:
            k1 = (data[roundedEnd + 2] & 0xff) << 16
        if val >= 2:
            k1 |= (data[roundedEnd + 1] & 0xff) << 8
        if val >= 1:
            k1 |= data[roundedEnd] & 0xff
            k1 *= c1
            k1 = (k1 << 15) | ((k1 & 0xffffffff) >> 17)
            k1 *= c2
            h1 ^= k1

        # finalization
        h1 ^= length
        h1 ^= ((h1 & 0xffffffff) >> 16)
        h1 *= 0x85ebca6b
        h1 ^= ((h1 & 0xffffffff) >> 13)
        h1 *= 0xc2b2ae35
        h1 ^= ((h1 & 0xffffffff) >> 16)

        return h1 & 0xffffffff