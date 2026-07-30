# Reconnaissance Report: {{ project_name }}

**Generated:** {{ generated_at }}  
**Company:** {{ company_name }}

---

## Executive Summary

This report covers the reconnaissance assessment for **{{ project_name }}**.
A total of **{{ assets_count }}** assets were identified.

## Methodology

Passive and limited active reconnaissance techniques were used,
including DNS enumeration, certificate transparency lookups, WHOIS,
HTTP header analysis, and banner grabbing where authorized.

## Findings

### Assets Discovered

| Type   | Value          | First Seen               |
|--------|----------------|--------------------------|
{% for asset in assets -%}
| {{ asset.type }} | {{ asset.value }} | {{ asset.first_seen }} |
{% endfor %}

### DNS Records

| Type | Value | TTL |
|------|-------|-----|
{% for rec in dns_records -%}
| {{ rec.type }} | {{ rec.value }} | {{ rec.ttl }} |
{% endfor %}

### Open Ports

| Host | Port | Service |
|------|------|---------|
{% for port in ports -%}
| {{ port.host }} | {{ port.port }} | {{ port.service }} |
{% endfor %}

## Appendix

- Tool: Recon Framework
- Limitations: Data reflects point-in-time assessment. No exploitation performed.