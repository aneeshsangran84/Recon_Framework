"""
Input validation for target types used throughout the framework.

Every validator returns True/False and does not raise exceptions,
so they are safe for use in conditional checks and plugins.
"""

import ipaddress
import re
from urllib.parse import urlparse

# Regular expression for a basic domain name (no protocol)
_DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)

# ASN format: AS followed by digits
_ASN_REGEX = re.compile(r"^AS\d+$", re.IGNORECASE)

def validate_ip(value: str) -> bool:
    """
    Check if a string is a valid IPv4 or IPv6 address.

    Args:
        value: String to check.

    Returns:
        True if a valid IP address.
    """
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False

def validate_domain(value: str) -> bool:
    """
    Validate a domain name (no protocol, no path).

    Args:
        value: Domain string.

    Returns:
        True if it looks like a valid domain name.
    """
    if not value or len(value) > 253:
        return False
    return bool(_DOMAIN_REGEX.match(value))

def validate_url(value: str) -> bool:
    """
    Validate a URL with http or https scheme.

    Args:
        value: URL string.

    Returns:
        True if URL is well‑formed and uses http/https.
    """
    try:
        result = urlparse(value)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False

def validate_cidr(value: str) -> bool:
    """
    Validate an IPv4 or IPv6 CIDR notation.

    Args:
        value: CIDR string.

    Returns:
        True if valid network.
    """
    try:
        ipaddress.ip_network(value, strict=False)
        return True
    except ValueError:
        return False

def validate_asn(value: str) -> bool:
    """
    Validate an ASN string (e.g., AS1234).

    Args:
        value: ASN string.

    Returns:
        True if format matches.
    """
    return bool(_ASN_REGEX.match(value))

def validate_target(target: str) -> str:
    """
    Determine the type of a target string.

    Returns one of: 'ipv4', 'ipv6', 'domain', 'url', 'cidr', 'asn',
    or 'unknown'.

    Args:
        target: Target string.

    Returns:
        Target type identifier.
    """
    # check IPs and CIDR
    try:
        ip = ipaddress.ip_address(target)
        return "ipv6" if ip.version == 6 else "ipv4"
    except ValueError:
        pass
    if validate_cidr(target):
        return "cidr"
    if validate_url(target):
        return "url"
    if validate_domain(target):
        return "domain"
    if validate_asn(target):
        return "asn"
    return "unknown"