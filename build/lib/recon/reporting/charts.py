"""
Chart generation using matplotlib.

Charts are created in SVG format so they can be embedded directly
into HTML reports (or converted to PNG for PDF if needed).
"""

import io
from dataclasses import dataclass
from typing import Dict, Optional

import structlog

logger = structlog.get_logger(__name__)

@dataclass
class ChartOutput:
    """Container for a generated chart."""
    svg_data: str
    png_data: Optional[bytes] = None


def generate_port_distribution_chart(port_counts: Dict[str, int]) -> Optional[ChartOutput]:
    """
    Create a pie chart of open ports by service name.

    Args:
        port_counts: Mapping of service name to count.

    Returns:
        ChartOutput with SVG string, or None if no data.
    """
    if not port_counts:
        return None

    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not installed – cannot generate chart")
        return None

    labels = list(port_counts.keys())
    sizes = list(port_counts.values())

    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct="%1.1f%%",
        startangle=90, pctdistance=0.85,
    )
    ax.axis("equal")
    plt.title("Port / Service Distribution", fontweight="bold")

    # Save to SVG buffer
    svg_io = io.StringIO()
    fig.savefig(svg_io, format="svg", bbox_inches="tight")
    plt.close(fig)
    svg_io.seek(0)
    svg_data = svg_io.read()
    return ChartOutput(svg_data=svg_data)


def generate_dns_record_chart(dns_counts: Dict[str, int]) -> Optional[ChartOutput]:
    """
    Create a bar chart summarising DNS record types.

    Args:
        dns_counts: Mapping of record type to count.

    Returns:
        ChartOutput or None.
    """
    if not dns_counts:
        return None

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not installed")
        return None

    types = list(dns_counts.keys())
    counts = list(dns_counts.values())

    fig, ax = plt.subplots()
    bars = ax.bar(types, counts, color="skyblue", edgecolor="black")
    ax.set_xlabel("DNS Record Type")
    ax.set_ylabel("Count")
    ax.set_title("DNS Record Distribution", fontweight="bold")
    ax.bar_label(bars)

    svg_io = io.StringIO()
    fig.savefig(svg_io, format="svg", bbox_inches="tight")
    plt.close(fig)
    svg_io.seek(0)
    return ChartOutput(svg_data=svg_io.read())


def generate_timeline_chart(events: list) -> Optional[ChartOutput]:
    """
    (Optional) Generate a Gantt-like timeline of scan activities.

    Placeholder – returns None until implemented.
    """
    # Could use plotly or matplotlib's broken_barh.
    return None