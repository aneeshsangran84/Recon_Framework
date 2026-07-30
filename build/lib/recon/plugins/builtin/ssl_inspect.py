"""
SSL/TLS certificate inspection and chain analysis.
"""

import asyncio
import ssl
import socket
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType
from recon.data.repository import AssetRepository
from recon.data.models import AssetType, Host, Certificate

logger = structlog.get_logger(__name__)


class SSLInspectPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="ssl_inspect",
            version="1.0.0",
            description="Inspect SSL/TLS certificates (default port 443)",
            author="Recon Team",
            supported_target_types={"ipv4", "domain"},
            dependencies=[],
            output_schema={
                "certificate": {
                    "subject": "dict",
                    "issuer": "dict",
                    "serial_number": "str",
                    "not_before": "str",
                    "not_after": "str",
                    "san": "list",
                    "fingerprint_sha256": "str",
                }
            },
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        host = target.value
        port = self.config.get("port", 443)
        timeout = self.config.get("timeout", 10)

        cert_info = await self._fetch_cert(host, port, timeout)
        if cert_info is None:
            return {"error": "Could not retrieve certificate"}

        repo = AssetRepository(db_session)
        # Create asset and host
        asset = repo.get_or_create_asset(AssetType.IP, host)  # simplified; could also be domain
        host_obj = db_session.query(Host).filter_by(ip_address=host).first()
        if not host_obj:
            host_obj = Host(ip_address=host, ip_version=4, asset_id=asset.id)
            db_session.add(host_obj)

        # Store certificate
        cert = Certificate(
            fingerprint=cert_info["fingerprint_sha256"],
            subject=str(cert_info["subject"]),
            issuer=str(cert_info["issuer"]),
            valid_from=datetime.fromisoformat(cert_info["not_before"].replace("Z", "+00:00")),
            valid_to=datetime.fromisoformat(cert_info["not_after"].replace("Z", "+00:00")),
            host_id=host_obj.id,
        )
        db_session.add(cert)
        db_session.commit()
        logger.info("SSL certificate stored", host=host)

        return cert_info

    async def _fetch_cert(self, host: str, port: int, timeout: int) -> Optional[Dict[str, Any]]:
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, self._sync_fetch_cert, host, port),
                timeout=timeout,
            )
        except Exception as e:
            logger.warning("SSL inspection failed", host=host, error=str(e))
            return None

    def _sync_fetch_cert(self, host: str, port: int) -> Dict[str, Any]:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert(binary_form=False)
                der = ssock.getpeercert(binary_form=True)
                sha256 = hashlib.sha256(der).hexdigest()
                return {
                    "subject": dict(x[0] for x in cert["subject"]),
                    "issuer": dict(x[0] for x in cert["issuer"]),
                    "serial_number": cert.get("serialNumber"),
                    "not_before": cert.get("notBefore"),
                    "not_after": cert.get("notAfter"),
                    "san": [v[1] for v in cert.get("subjectAltName", []) if v[0] == "DNS"],
                    "fingerprint_sha256": sha256,
                }