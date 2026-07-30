from dataclasses import dataclass
from enum import Enum, auto
import ipaddress
import re

class TargetType(Enum):
    IPV4 = auto()
    IPV6 = auto()
    DOMAIN = auto()
    URL = auto()
    CIDR = auto()
    ASN = auto()
    UNKNOWN = auto()

@dataclass
class Target:
    raw: str
    type: TargetType
    value: str  # normalized

    @classmethod
    def from_string(cls, raw: str) -> "Target":
        raw = raw.strip()
        # Try IPv4
        try:
            ip = ipaddress.IPv4Address(raw)
            return cls(raw=raw, type=TargetType.IPV4, value=str(ip))
        except:
            pass
        # Try IPv6
        try:
            ip = ipaddress.IPv6Address(raw)
            return cls(raw=raw, type=TargetType.IPV6, value=str(ip))
        except:
            pass
        # Try CIDR
        try:
            net = ipaddress.ip_network(raw, strict=False)
            return cls(raw=raw, type=TargetType.CIDR, value=str(net))
        except:
            pass
        # ASN (AS1234)
        if re.match(r'^AS\d+$', raw, re.IGNORECASE):
            return cls(raw=raw, type=TargetType.ASN, value=raw.upper())
        # URL
        if raw.startswith(('http://', 'https://')):
            return cls(raw=raw, type=TargetType.URL, value=raw)
        # Domain (basic validation)
        domain_pattern = r'^(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,}$'
        if re.match(domain_pattern, raw):
            return cls(raw=raw, type=TargetType.DOMAIN, value=raw.lower())
        return cls(raw=raw, type=TargetType.UNKNOWN, value=raw)

    @property
    def is_ip(self) -> bool:
        return self.type in (TargetType.IPV4, TargetType.IPV6)