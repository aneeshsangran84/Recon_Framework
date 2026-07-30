"""
Geolocation lookup using MaxMind GeoLite2 database (local).
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import structlog

from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType

logger = structlog.get_logger(__name__)


class GeolocationPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="geolocation",
            version="1.0.0",
            description="IP geolocation using MaxMind GeoLite2 database",
            author="Recon Team",
            supported_target_types={"ipv4", "ipv6"},
            dependencies=["geoip2"],
            required_config={"maxmind_db_path": "path to GeoLite2-City.mmdb"},
            output_schema={
                "country": "string",
                "city": "string",
                "latitude": "float",
                "longitude": "float",
                "isp": "string",
            },
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        if not target.is_ip:
            raise ValueError("Geolocation requires an IP address.")
        db_path = self.config.get("maxmind_db_path")
        if not db_path or not Path(db_path).exists():
            logger.error("MaxMind DB not found or configured")
            return {"error": "MaxMind database missing"}

        try:
            import geoip2.database
        except ImportError:
            return {"error": "geoip2 package not installed"}

        results = {}
        try:
            loop = asyncio.get_running_loop()
            reader = geoip2.database.Reader(db_path)
            response = await loop.run_in_executor(None, reader.city, target.value)
            results["country"] = response.country.name
            results["city"] = response.city.name
            results["latitude"] = response.location.latitude
            results["longitude"] = response.location.longitude
            # ISP often available in ASN database, not City; simplified
            results["isp"] = ""
        except Exception as e:
            logger.warning("Geolocation lookup failed", ip=target.value, error=str(e))
            results["error"] = str(e)
        return results