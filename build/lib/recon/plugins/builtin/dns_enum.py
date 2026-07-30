import asyncio
from typing import Dict, Any, Set
import dns.resolver, dns.exception
from recon.plugins.base import BasePlugin, PluginMetadata
from recon.core.target import Target, TargetType
from recon.data import models
import structlog

logger = structlog.get_logger(__name__)

class DNSEnumerator(BasePlugin):
    RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            name="dns_enum",
            version="1.0.0",
            description="Enumerate common DNS records for a domain",
            author="Recon Team",
            supported_target_types={"domain"},
            dependencies=["dnspython"],
            output_schema={"records": "list of {type, value, ttl}"}
        )

    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        if target.type != TargetType.DOMAIN:
            raise ValueError("DNS enumeration requires a domain target.")
        domain = target.value
        results = {"records": []}
        resolver = dns.resolver.Resolver()
        resolver.timeout = self.config.get("timeout", 5)
        resolver.lifetime = self.config.get("lifetime", 10)

        loop = asyncio.get_running_loop()
        for rtype in self.RECORD_TYPES:
            try:
                answers = await loop.run_in_executor(
                    None, lambda rt=rtype: resolver.resolve(domain, rt)
                )
                for rdata in answers:
                    results["records"].append({
                        "type": rtype,
                        "value": str(rdata),
                        "ttl": answers.ttl
                    })
            except dns.exception.DNSException as e:
                logger.warning(f"DNS {rtype} failed for {domain}", error=str(e))
            except Exception as e:
                logger.error(f"Unexpected error", exc_info=e)

        # Persist to database
        asset_domain = db_session.query(models.Asset).filter_by(
            type=models.AssetType.DOMAIN, value=domain
        ).first()
        if not asset_domain:
            asset_domain = models.Asset(
                type=models.AssetType.DOMAIN, value=domain
            )
            db_session.add(asset_domain)
            db_session.commit()
        # Store DNS records (simplified)
        for rec in results["records"]:
            dns_rec = models.DNSRecord(
                domain_id=asset_domain.id,
                record_type=rec["type"],
                value=rec["value"],
                ttl=rec["ttl"]
            )
            db_session.add(dns_rec)
        db_session.commit()
        return results