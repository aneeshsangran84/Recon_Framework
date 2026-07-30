from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional, Type
from recon.core.target import Target  # we'll define shortly

@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    supported_target_types: Set[str]  # e.g., 'domain', 'ipv4'
    dependencies: List[str] = field(default_factory=list)
    system_tools: List[str] = field(default_factory=list)
    required_config: Dict[str, str] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

class BasePlugin(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metadata = self.get_metadata()

    @staticmethod
    @abstractmethod
    def get_metadata() -> PluginMetadata:
        ...

    @abstractmethod
    async def run(self, target: Target, db_session) -> Dict[str, Any]:
        """Execute recon, return results dict."""
        ...