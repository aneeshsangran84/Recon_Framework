"""
General helper utilities for the Recon Framework.
"""

import re
import unicodedata
from datetime import datetime, timezone
from typing import List, TypeVar

T = TypeVar("T")

def chunk_list(data: List[T], size: int) -> List[List[T]]:
    """
    Split a list into smaller chunks of a given size.

    Args:
        data: List to split.
        size: Maximum number of items per chunk.

    Returns:
        List of chunks.

    Example:
        >>> chunk_list([1,2,3,4,5], 2)
        [[1, 2], [3, 4], [5]]
    """
    if size < 1:
        raise ValueError("Chunk size must be >= 1")
    return [data[i:i + size] for i in range(0, len(data), size)]

def safe_filename(name: str, replacement: str = "_") -> str:
    """
    Convert a string into a filesystem‑safe filename.

    Replaces spaces and non‑alphanumeric characters (except `-`, `.`, `_`)
    with a replacement string. Also limits length to 255 characters.

    Args:
        name: Original string.
        replacement: Character(s) used to replace unsafe ones. Defaults to '_'.

    Returns:
        Safe filename string.
    """
    # Normalize unicode
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    # Replace unsafe chars
    safe = re.sub(r"[^\w\-.]", replacement, name).strip(replacement)
    # Collapse multiple replacements
    safe = re.sub(f"{re.escape(replacement)}+", replacement, safe)
    # Limit length
    return safe[:255]

def timestamp_iso() -> str:
    """
    Return current UTC time as ISO 8601 string.

    Returns:
        ISO 8601 formatted string with timezone.
    """
    return datetime.now(timezone.utc).isoformat()

def mask_sensitive(text: str, visible: int = 4, mask_char: str = "*") -> str:
    """
    Mask a sensitive string (e.g. API key), showing only the last few characters.

    Args:
        text: The sensitive string.
        visible: Number of trailing characters to leave unmasked.
        mask_char: Character used to mask the rest.

    Returns:
        Masked string.
    """
    if len(text) <= visible:
        return text  # too short to mask usefully
    masked_len = len(text) - visible
    return mask_char * masked_len + text[-visible:]