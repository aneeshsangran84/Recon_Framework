import importlib
import pkgutil
from typing import Dict, Type, List
from recon.plugins.base import BasePlugin, PluginMetadata
import structlog

logger = structlog.get_logger(__name__)

class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, Type[BasePlugin]] = {}
        self._discover()

    def _discover(self):
        """Automatically discover plugins in the 'recon.plugins.builtin' package."""
        import recon.plugins.builtin as builtin_pkg
        for _, name, _ in pkgutil.iter_modules(builtin_pkg.__path__):
            module = importlib.import_module(f"recon.plugins.builtin.{name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                    try:
                        meta = attr.get_metadata()
                        self._plugins[meta.name] = attr
                        logger.debug("Discovered plugin", name=meta.name)
                    except Exception as e:
                        logger.error("Plugin load error", module=name, error=str(e))

        # Additionally, load from installed packages via entry points (future)

    def get_plugin(self, name: str) -> Type[BasePlugin]:
        return self._plugins[name]

    def list_plugins(self) -> List[PluginMetadata]:
        return [cls.get_metadata() for cls in self._plugins.values()]

    def instantiate(self, name: str, config: dict = None) -> BasePlugin:
        cls = self.get_plugin(name)
        return cls(config or {})