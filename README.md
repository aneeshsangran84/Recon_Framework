# Recon Framework

**Enterprise Reconnaissance Framework for Authorized Security Assessments**

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![License](https://img.shields.io/badge/license-GPL--3.0-orange)
![Platform](https://img.shields.io/badge/platform-Linux-red)

Recon Framework is an extensible, modular reconnaissance platform designed for penetration testers, security researchers, and defensive teams. It runs natively on Kali Linux, Parrot OS, Ubuntu, Debian, Arch Linux, and other common distributions.

---

## ⚠️ Legal Disclaimer

This tool is intended **ONLY** for:
- Authorized security assessments
- Penetration testing with explicit written permission
- Defensive security research
- Asset inventory on systems you own
- Cybersecurity education in controlled environments

**Unauthorized scanning of systems without permission is illegal.** The developers assume no liability for misuse.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
  - [Method 1: One-Line Install](#method-1-one-line-install)
  - [Method 2: Using requirements.txt](#method-2-using-requirementstxt)
  - [Method 3: pip Install](#method-3-pip-install)
  - [Method 4: Development Install](#method-4-development-install)
- [Usage](#usage)
  - [Project Management](#project-management)
  - [Running Scans](#running-scans)
  - [Plugin Management](#plugin-management)
  - [Generating Reports](#generating-reports)
  - [Configuration](#configuration)
- [Supported Target Types](#supported-target-types)
- [Built-in Plugins](#built-in-plugins)
- [Project Structure](#project-structure)
- [Report Formats](#report-formats)
- [Configuration File](#configuration-file)
- [Developing Custom Plugins](#developing-custom-plugins)
- [Logging](#logging)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Feature | Description |
|---------|-------------|
| 🔌 **Plugin Architecture** | Every reconnaissance capability is an independent, auto-discovered plugin |
| 🎯 **Broad Target Support** | IPv4, IPv6, CIDR ranges, domains, URLs, ASNs |
| 🔍 **Passive & Active Recon** | DNS, WHOIS, SSL/TLS, HTTP headers, technology fingerprinting, reverse DNS, geolocation, CDN/WAF detection |
| 🗄️ **Unified Data Model** | All findings stored in SQLite with deduplication and relationship mapping |
| 📊 **Professional Reports** | HTML, PDF, Markdown, JSON, CSV, XML with charts and tables |
| ⚡ **Concurrent Execution** | Async task scheduler with progress bars and retry logic |
| 📁 **Project Workspaces** | Organize assessments, resume interrupted scans |
| 📝 **Structured Logging** | Text and JSON logs with rotation |
| ⚙️ **Configurable** | TOML-based settings with environment variable overrides |

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/aneeshsangran84/recon_framework.git
cd recon_framework
pip install -r requirements.txt
pip install .

# Verify
recon --version

# Start using
recon project create my-assessment
recon scan --project my-assessment example.com
recon report generate --project my-assessment --format html --output report.html
