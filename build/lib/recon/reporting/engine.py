"""
Report Generation Orchestrator.

Collects data from the database, enriches it with computed statistics,
passes everything to a Jinja2 template, and renders output in the
requested format (HTML, PDF via WeasyPrint, Markdown).
"""

import json
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
    ChartOutput,
)
from .exporters import export_json, export_csv, export_xml

logger = structlog.get_logger(__name__)


class ReportEngine:
    """
    Orchestrates report generation.

    Automatically gathers all project data, enriches it,
    and renders templates with embedded charts.
    """

    def __init__(
        self,
        settings: Settings,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize the reporting engine.

        Args:
            settings: Framework configuration (used for branding, etc.).
            template_dir: Custom template directory. If None, use built-in.
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
        )
        self.settings = settings

    def _collect_project_data(self, session: Session, project_name: str) -> Dict[str, Any]:
        """
        Query all assets and findings for a project and build a context dict.

        Args:
            session: SQLAlchemy database session.
            project_name: Name of the project.

        Returns:
            Nested dictionary ready for Jinja2 rendering.
        """
        project = session.query(models.Project).filter_by(name=project_name).first()
        if not project:
            raise ValueError(f"Project '{project_name}' not found")

        # Gather assets
        assets = session.query(models.Asset).all()
        hosts = session.query(models.Host).all() if hasattr(models, "Host") else []
        domains = session.query(models.Domain).all() if hasattr(models, "Domain") else []
        dns_records = session.query(models.DNSRecord).all() if hasattr(models, "DNSRecord") else []
        ports = session.query(models.Port).all() if hasattr(models, "Port") else []
        certificates = session.query(models.Certificate).all() if hasattr(models, "Certificate") else []
        technologies = session.query(models.Technology).all() if hasattr(models, "Technology") else []

        # Build context
        context = {
            "project_name": project.name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "company_name": self.settings.company_name,
            "assets_count": len(assets),
            "assets": [{"type": a.type.value, "value": a.value, "first_seen": a.first_seen} for a in assets],
            "hosts": [{"ip": h.ip_address, "hostnames": h.hostnames} for h in hosts],
            "domains": [{"name": d.domain_name} for d in domains],
            "dns_records": [{"type": r.record_type, "value": r.value, "ttl": r.ttl} for r in dns_records],
            "ports": [{"host": p.host.ip_address if p.host else "", "port": p.port_number, "service": p.service_name} for p in ports],
            "certificates": [{"subject": c.subject, "issuer": c.issuer} for c in certificates],
            "technologies": [{"name": t.name, "version": t.version} for t in technologies],
            # Additional computed stats for charts
            "port_distribution": self._count_ports(ports),
            "dns_record_summary": self._count_dns_types(dns_records),
        }
        return context

    def _count_ports(self, ports: List) -> Dict[str, int]:
        """Summarise ports by service name."""
        counts = {}
        for p in ports:
            counts[p.service_name] = counts.get(p.service_name, 0) + 1
        return counts

    def _count_dns_types(self, records: List) -> Dict[str, int]:
        """Count DNS record types."""
        counts = {}
        for r in records:
            counts[r.record_type] = counts.get(r.record_type, 0) + 1
        return counts

    def generate(
        self,
        session: Session,
        project_name: str,
        output_format: str = "html",
        output_path: Optional[Path] = None,
        template_name: Optional[str] = None,
    ) -> Union[str, Path]:
        """
        Generate a report.

        Args:
            session: Database session.
            project_name: Project to report on.
            output_format: One of 'html', 'pdf', 'md', 'json', 'csv', 'xml'.
            output_path: If provided, write to this file. Otherwise return string.
            template_name: Override template name. Defaults based on format.

        Returns:
            Path to written file if output_path given, else the rendered string.
        """
        context = self._collect_project_data(session, project_name)

        # Handle pure data exports
        if output_format in ("json", "csv", "xml"):
            data = self._collect_project_data(session, project_name)
            if output_format == "json":
                content = export_json(data)
            elif output_format == "csv":
                content = export_csv(data)
            else:
                content = export_xml(data)
            if output_path:
                output_path.write_text(content, encoding="utf-8")
                logger.info("Report exported", format=output_format, path=str(output_path))
                return output_path
            return content

        # For template-based formats, generate charts and embed them
        port_chart = generate_port_distribution_chart(context.get("port_distribution", {}))
        dns_chart = generate_dns_record_chart(context.get("dns_record_summary", {}))
        context["port_chart_svg"] = port_chart.svg_data if port_chart else ""
        context["dns_chart_svg"] = dns_chart.svg_data if dns_chart else ""
        # (timeline chart could be added similarly)

        # Pick template name
        if template_name is None:
            template_map = {
                "html": "pdf_report.html",  # main HTML template
                "pdf": "pdf_report.html",   # WeasyPrint from same HTML
                "md": "report.md",
            }
            template_name = template_map.get(output_format, "pdf_report.html")

        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            raise ValueError(f"Template '{template_name}' not found")

        rendered = template.render(**context)

        if output_format == "pdf":
            # Use WeasyPrint to convert HTML to PDF
            try:
                import weasyprint
            except ImportError:
                raise RuntimeError(
                    "PDF generation requires the 'weasyprint' package. "
                    "Install with: pip install weasyprint"
                )
            if output_path is None:
                output_path = Path(f"{project_name}_report.pdf")
            weasyprint.HTML(string=rendered).write_pdf(output_path)
            logger.info("PDF report generated", path=str(output_path))
            return output_path

        if output_format in ("html", "md"):
            if output_path:
                output_path.write_text(rendered, encoding="utf-8")
                logger.info("Report written", format=output_format, path=str(output_path))
                return output_path
            return rendered

        raise ValueError(f"Unsupported output format: {output_format}")