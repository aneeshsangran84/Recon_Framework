"""
Tests for the reporting engine: context generation, export, and PDF/HTML rendering.
"""

import json
from pathlib import Path

import pytest
from recon.reporting.engine import ReportEngine
from recon.reporting.exporters import export_json, export_csv, export_xml
from recon.reporting.charts import (
    generate_port_distribution_chart,
    generate_dns_record_chart,
)


def test_export_json():
    data = {
        "project_name": "test",
        "assets": [{"type": "domain", "value": "example.com", "first_seen": "2023-01-01T00:00:00"}]
    }
    result = export_json(data)
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert parsed["project_name"] == "test"


def test_export_csv():
    data = {
        "assets": [{"type": "domain", "value": "example.com", "first_seen": "2023-01-01"}],
        "dns_records": [],
        "ports": [],
    }
    result = export_csv(data)
    assert "# Assets" in result
    assert "example.com" in result


def test_export_xml():
    data = {
        "project_name": "TestProject",
        "assets": [{"type": "ip", "value": "1.1.1.1"}],
        "dns_records": [],
        "ports": [],
    }
    result = export_xml(data)
    assert "<ReconReport" in result
    assert "TestProject" in result


def test_port_distribution_chart():
    port_counts = {"http": 5, "https": 3, "ssh": 2}
    chart = generate_port_distribution_chart(port_counts)
    assert chart is not None
    assert "<svg" in chart.svg_data


def test_dns_record_chart():
    dns_counts = {"A": 10, "MX": 3, "TXT": 1}
    chart = generate_dns_record_chart(dns_counts)
    assert chart is not None
    assert "<svg" in chart.svg_data


def test_empty_charts_return_none():
    assert generate_port_distribution_chart({}) is None
    assert generate_dns_record_chart({}) is None


@pytest.mark.integration
def test_report_engine_html_generation(db_session, test_settings, tmp_path):
    """Integration test: create a project with sample data, then generate an HTML report."""
    from recon.data.repository import AssetRepository
    from recon.data.models import AssetType, Project, Domain, DNSRecord
    import uuid

    # Set up a project and some data
    proj = Project(id=str(uuid.uuid4()), name="integration_test")
    db_session.add(proj)
    db_session.commit()

    repo = AssetRepository(db_session)
    asset = repo.get_or_create_asset(AssetType.DOMAIN, "example.com")
    domain = Domain(id=str(uuid.uuid4()), domain_name="example.com", asset_id=asset.id)
    db_session.add(domain)
    db_session.commit()
    repo.add_dns_records(domain, [
        {"record_type": "A", "value": "93.184.216.34", "ttl": 3600}
    ])
    db_session.commit()

    engine = ReportEngine(settings=test_settings)
    output_path = tmp_path / "report.html"
    result = engine.generate(
        session=db_session,
        project_name="integration_test",
        output_format="html",
        output_path=output_path,
    )
    assert output_path.exists()
    content = output_path.read_text()
    assert "example.com" in content
    assert "93.184.216.34" in content


# PDF test requires weasyprint; skip if not installed
@pytest.mark.skipif(not __import__("importlib.util").util.find_spec("weasyprint"), reason="weasyprint not installed")
def test_report_engine_pdf_generation(db_session, test_settings, tmp_path):
    """Test PDF generation using the same setup as HTML (requires weasyprint)."""
    from recon.data.repository import AssetRepository
    from recon.data.models import AssetType, Project, Domain
    import uuid

    proj = Project(id=str(uuid.uuid4()), name="pdf_test")
    db_session.add(proj)
    db_session.commit()

    repo = AssetRepository(db_session)
    asset = repo.get_or_create_asset(AssetType.DOMAIN, "example.com")
    domain = Domain(id=str(uuid.uuid4()), domain_name="example.com", asset_id=asset.id)
    db_session.add(domain)
    db_session.commit()

    engine = ReportEngine(settings=test_settings)
    output_path = tmp_path / "report.pdf"
    result = engine.generate(
        session=db_session,
        project_name="pdf_test",
        output_format="pdf",
        output_path=output_path,
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0