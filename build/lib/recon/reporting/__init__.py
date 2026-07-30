"""
Recon Framework Reporting Package.

Generates professional assessment reports in multiple formats
using Jinja2 templates, matplotlib charts, and data export utilities.
"""

from .engine import ReportEngine
from .exporters import export_json, export_csv, export_xml
from .charts import (
    generate_port_distribution_chart,
    generate_dns_record_chart,
    generate_timeline_chart,
    ChartOutput,
)

__all__ = [
    "ReportEngine",
    "export_json",
    "export_csv",
    "export_xml",
    "generate_port_distribution_chart",
    "generate_dns_record_chart",
    "generate_timeline_chart",
    "ChartOutput",
]