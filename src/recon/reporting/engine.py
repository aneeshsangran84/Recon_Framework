"""
Report Generation Orchestrator.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from sqlalchemy.orm import Session

from recon.config.settings import Settings
from recon.data import models
from .charts import (
    generate_port_distribution_chart,
    generate_dns_record_chart,
)

logger = structlog.get_logger(__name__)


class ReportEngine:
    def __init__(self, settings: Settings, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
        )
        self.settings = settings

    def _collect_project_data(self, session: Session, project_name: str) -> Dict[str, Any]:
        project = session.query(models.Project).filter_by(name=project_name).first()
        if not project:
            raise ValueError(f"Project '{project_name}' not found")

        # Assets
        assets = session.query(models.Asset).all()
        assets_data = []
        for a in assets:
            assets_data.append({
                "type": str(a.type) if hasattr(a.type, 'value') else str(a.type),
                "value": a.value,
                "first_seen": str(a.first_seen) if a.first_seen else "",
            })

        # Hosts
        hosts = session.query(models.Host).all() if hasattr(models, "Host") else []
        hosts_data = [{"ip": h.ip_address, "hostnames": str(h.hostnames or "")} for h in hosts]

        # DNS records
        dns_records = session.query(models.DNSRecord).all() if hasattr(models, "DNSRecord") else []
        dns_data = [{"type": r.record_type, "value": r.value, "ttl": r.ttl or ""} for r in dns_records]

        # Ports
        ports = session.query(models.Port).all() if hasattr(models, "Port") else []
        ports_data = []
        for p in ports:
            host_ip = p.host.ip_address if p.host else ""
            ports_data.append({
                "host": host_ip,
                "port": p.port_number,
                "service": p.service_name or "",
            })

        # Certificates
        certificates = session.query(models.Certificate).all() if hasattr(models, "Certificate") else []
        certs_data = [{"subject": c.subject or "", "issuer": c.issuer or ""} for c in certificates]

        # Technologies
        technologies = session.query(models.Technology).all() if hasattr(models, "Technology") else []
        techs_data = [{"name": t.name, "version": t.version or ""} for t in technologies]

        # Count port distribution
        port_counts = {}
        for p in ports:
            svc = p.service_name or "unknown"
            port_counts[svc] = port_counts.get(svc, 0) + 1

        # Count DNS types
        dns_counts = {}
        for r in dns_records:
            dns_counts[r.record_type] = dns_counts.get(r.record_type, 0) + 1

        context = {
            "project_name": project.name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "company_name": self.settings.company_name,
            "assets_count": len(assets),
            "assets": assets_data,
            "hosts": hosts_data,
            "dns_records": dns_data,
            "ports": ports_data,
            "certificates": certs_data,
            "technologies": techs_data,
            "port_distribution": port_counts,
            "dns_record_summary": dns_counts,
        }
        return context

    def generate(
        self,
        session: Session,
        project_name: str,
        output_format: str = "html",
        output_path: Optional[Path] = None,
        template_name: Optional[str] = None,
    ) -> Union[str, Path]:
        context = self._collect_project_data(session, project_name)

        # Handle data exports
        if output_format in ("json", "csv", "xml"):
            from .exporters import export_json, export_csv, export_xml
            if output_format == "json":
                content = export_json(context)
            elif output_format == "csv":
                content = export_csv(context)
            else:
                content = export_xml(context)
            if output_path:
                output_path.write_text(content, encoding="utf-8")
                return output_path
            return content

        # Generate charts
        port_chart = generate_port_distribution_chart(context.get("port_distribution", {}))
        dns_chart = generate_dns_record_chart(context.get("dns_record_summary", {}))
        context["port_chart_svg"] = port_chart.svg_data if port_chart else ""
        context["dns_chart_svg"] = dns_chart.svg_data if dns_chart else ""

        # Template selection
        if template_name is None:
            template_map = {
                "html": "pdf_report.html",
                "pdf": "pdf_report.html",
                "md": "report.md",
            }
            template_name = template_map.get(output_format, "pdf_report.html")

        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise ValueError(f"Template '{template_name}' not found")

        rendered = template.render(**context)

        if output_format == "pdf":
            try:
                import weasyprint
            except ImportError:
                raise RuntimeError("PDF generation requires weasyprint. Install: pip install weasyprint")
            if output_path is None:
                output_path = Path(f"{project_name}_report.pdf")
            weasyprint.HTML(string=rendered).write_pdf(output_path)
            return output_path

        if output_path:
            output_path.write_text(rendered, encoding="utf-8")
            return output_path
        return rendered
