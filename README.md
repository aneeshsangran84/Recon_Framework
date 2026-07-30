# Recon Framework

**Enterprise Reconnaissance Framework for Authorized Security Assessments**

Recon Framework is an extensible, modular, and production-ready reconnaissance platform designed for penetration testers, security researchers, and defensive teams. It runs natively on Linux (Kali, Parrot, Ubuntu, Debian, Arch) and provides a professional CLI, plugin-based reconnaissance modules, a unified data model, and powerful multi-format reporting.

---

## ⚠️ Important

This tool is intended **only** for:
- Authorized security assessments
- Defensive security research
- Penetration testing with explicit permission
- Asset inventory and cybersecurity education

**Unauthorized use against systems you do not own or have explicit permission to test is illegal and unethical.** The developers assume no liability for misuse.

---

## Features

- **Plugin Architecture** – Every reconnaissance capability is an independent, auto-discovered plugin. Add new modules without touching the core.
- **Broad Target Support** – IPv4, IPv6, CIDR ranges, domains, URLs, ASNs, and network ranges. Automatic input type detection.
- **Safe Passive & Active Recon** – DNS enumeration, WHOIS, certificate transparency, SSL/TLS analysis, HTTP headers, technology fingerprinting, reverse DNS, geolocation, CDN/WAF detection, and more.
- **Normalized Data Model** – All findings stored in SQLite (migratable to PostgreSQL) with deduplication, versioning, and relationship mapping.
- **Professional Reporting** – Generate PDF, HTML, Markdown, JSON, CSV, and XML reports with customizable templates, charts, executive summaries, and defensive recommendations.
- **Concurrent Execution** – Async task scheduler with configurable concurrency, retries, timeouts, and real‑time progress via Rich.
- **Workspaces & Projects** – Organise assessments, resume interrupted scans, compare historical data.
- **Comprehensive Logging** – Structured logs (text/JSON) with rotation, suitable for SIEM ingestion.
- **Secure Configuration** – TOML‑based settings with environment variable overrides, secret storage via OS keyring or environment variables.
- **Cross‑Platform Linux** – Native integration with common penetration testing distributions. Installable via `pip`.

---

## Quick Start

### Prerequisites
- Python 3.10 or higher
- `pip` and `virtualenv` (recommended)
- External tools: `whois`, `dig` (optional, for some plugins)

### Installation
```bash
git clone https://github.com/your-org/recon-framework.git
cd recon-framework
python3 -m venv venv
source venv/bin/activate
pip install .