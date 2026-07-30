"""
Data exporters for raw reporting formats: JSON, CSV, XML.

Each function receives the same context dictionary used for
template rendering and returns a formatted string.
"""

import csv
import io
import json
from typing import Any, Dict, List
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def export_json(data: Dict[str, Any]) -> str:
    """Serialize the report context to a JSON string."""
    # Remove non-serializable items (like datetime objects) – convert to string
    def default_serializer(obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return str(obj)

    return json.dumps(data, indent=2, default=default_serializer, ensure_ascii=False)


def export_csv(data: Dict[str, Any]) -> str:
    """
    Export core tabular data to CSV.

    Creates separate sections for assets, DNS records, ports.
    Returns a multi-section CSV as a string (with separators).
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Assets
    writer.writerow(["# Assets"])
    writer.writerow(["type", "value", "first_seen"])
    for asset in data.get("assets", []):
        writer.writerow([asset.get("type", ""), asset.get("value", ""), asset.get("first_seen", "")])

    writer.writerow([])
    # DNS records
    writer.writerow(["# DNS Records"])
    writer.writerow(["type", "value", "ttl"])
    for rec in data.get("dns_records", []):
        writer.writerow([rec.get("type", ""), rec.get("value", ""), rec.get("ttl", "")])

    writer.writerow([])
    # Ports
    writer.writerow(["# Ports"])
    writer.writerow(["host", "port", "service"])
    for port in data.get("ports", []):
        writer.writerow([port.get("host", ""), port.get("port", ""), port.get("service", "")])

    return output.getvalue()


def export_xml(data: Dict[str, Any]) -> str:
    """Convert report context to a basic XML structure."""
    root = Element("ReconReport")
    root.set("project", data.get("project_name", ""))
    root.set("generated_at", data.get("generated_at", ""))

    # Assets
    assets_elem = SubElement(root, "Assets")
    for asset in data.get("assets", []):
        asset_elem = SubElement(assets_elem, "Asset")
        asset_elem.set("type", asset.get("type", ""))
        asset_elem.text = asset.get("value", "")

    # DNS records
    dns_elem = SubElement(root, "DNSRecords")
    for rec in data.get("dns_records", []):
        rec_elem = SubElement(dns_elem, "Record")
        rec_elem.set("type", rec.get("type", ""))
        rec_elem.set("ttl", str(rec.get("ttl", "")))
        rec_elem.text = rec.get("value", "")

    # Ports
    ports_elem = SubElement(root, "Ports")
    for port in data.get("ports", []):
        port_elem = SubElement(ports_elem, "Port")
        port_elem.set("host", port.get("host", ""))
        port_elem.set("port", str(port.get("port", "")))
        port_elem.set("service", port.get("service", ""))

    # Pretty print
    xml_str = tostring(root, encoding="unicode")
    pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
    return pretty