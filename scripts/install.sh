#!/bin/bash
# Recon Framework - Simple Installer
set -e

echo "[*] Installing Recon Framework..."

# Install system dependencies
if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip python3-venv whois dnsutils
elif command -v pacman &>/dev/null; then
    sudo pacman -S --noconfirm python python-pip whois bind
fi

# Install Python package globally
pip3 install --break-system-packages . 2>/dev/null || pip3 install .

# Install optional tools
pip3 install --break-system-packages python-whois geoip2 weasyprint 2>/dev/null || \
    pip3 install python-whois geoip2 weasyprint

echo ""
echo "[+] Recon Framework installed!"
echo "[+] Run: recon --help"
