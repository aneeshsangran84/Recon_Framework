# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-10-15

### Added
- Initial release of Recon Framework.
- Core CLI with project, scan, report, plugin, and config commands.
- Plugin system with automatic discovery and metadata interface.
- Built-in plugins:
  - DNS enumeration (A, AAAA, MX, NS, TXT, SOA, CNAME)
  - WHOIS lookup (basic)
  - Certificate transparency log query
  - SSL/TLS certificate inspection
  - HTTP header analysis
  - Technology fingerprinting (Wappalyzer-like)
  - Favicon hash matching
  - Reverse DNS
  - Geolocation (MaxMind GeoLite2)
  - CDN and WAF detection
- Target parsing for IPv4, IPv6, CIDR, domains, URLs, ASNs.
- Unified data model with SQLite backend (SQLAlchemy).
- Concurrent task scheduler with configurable threading, retries, and progress bars.
- Multi-format reporting: HTML, PDF (via WeasyPrint), Markdown, JSON, CSV, XML.
- Jinja2-based report templates with customizable company branding.
- Professional logging (text and JSON) with rotation.
- Configuration via TOML files, environment variables, and command-line overrides.
- Workspace and project management for isolated assessments.
- Extensive documentation, developer guide, and example workflows.
- Test suite with pytest, coverage > 85%.

### Changed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- No unauthorized exploitation or credential harvesting functionality included.
- All external calls validated and timed out. Sensitive configuration values only accepted via env vars.