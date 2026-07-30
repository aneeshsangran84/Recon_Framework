# recon/core/engine.py
from recon.plugins.registry import PluginRegistry
from recon.core.target import Target
from recon.core.scheduler import TaskScheduler
import structlog

logger = structlog.get_logger(__name__)

class ReconEngine:
    def __init__(self, registry: PluginRegistry, settings):
        self.registry = registry
        self.settings = settings

    async def run_scan(self, target_str: str, db_session):
        target = Target.from_string(target_str)
        # Determine applicable plugins based on target type and config
        applicable_plugins = []
        for meta in self.registry.list_plugins():
            if meta.supported_target_types and target.type.name.lower() not in meta.supported_target_types:
                continue
            if meta.name in self.settings.disabled_plugins:
                continue
            applicable_plugins.append(meta.name)

        scheduler = TaskScheduler(max_concurrency=self.settings.threads)
        with scheduler.progress:
            for pname in applicable_plugins:
                plugin_instance = self.registry.instantiate(pname, config={"timeout": self.settings.timeout})
                coro = plugin_instance.run(target, db_session)
                scheduler.schedule(coro, name=pname)
            results = await scheduler.gather()
        return results