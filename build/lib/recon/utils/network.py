"""
Network utility functions for safe, timeout‑aware operations.

These are designed for passive reconnaissance tasks that require
direct network interaction (e.g., banner grabbing, basic connectivity
checks). They are intentionally conservative with timeouts and
error handling.
"""

import asyncio
import socket
from typing import Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)

async def resolve_host(host: str) -> Optional[str]:
    """
    Resolve a hostname to an IPv4 address asynchronously.

    Args:
        host: Hostname to resolve.

    Returns:
        IP address string, or None if resolution fails.
    """
    try:
        loop = asyncio.get_running_loop()
        addr_info = await loop.getaddrinfo(host, None, family=socket.AF_INET)
        if addr_info:
            return addr_info[0][4][0]
    except socket.gaierror as e:
        logger.debug("DNS resolution failed", host=host, error=str(e))
    except Exception:
        logger.exception("Unexpected error during DNS resolution", host=host)
    return None

async def is_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
    """
    Check if a TCP port is open on a remote host.

    Args:
        host: Target hostname or IP.
        port: TCP port number.
        timeout: Connection timeout in seconds.

    Returns:
        True if the port is open, False otherwise.
    """
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False
    except Exception:
        logger.warning("Unexpected port check error", host=host, port=port)
        return False

async def get_banner(host: str, port: int, timeout: float = 3.0) -> Optional[str]:
    """
    Attempt to read a service banner from a TCP port.

    Sends a single newline and reads up to 1024 bytes of response.
    Useful for SMTP, SSH, FTP, etc.

    Args:
        host: Target hostname or IP.
        port: TCP port number.
        timeout: Connection and read timeout in seconds.

    Returns:
        Decoded banner string, or None if no banner could be read.
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        # Some services need a prompt; sending empty line often triggers a banner.
        writer.write(b"\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(1024), timeout=timeout)
        writer.close()
        await writer.wait_closed()
        if data:
            return data.decode("utf-8", errors="replace").strip()
    except Exception:
        logger.debug("Failed to grab banner", host=host, port=port)
    return None