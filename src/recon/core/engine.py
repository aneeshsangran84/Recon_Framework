"""Reconnaissance Engine - orchestrates scan execution."""

import structlog
from recon.plugins.registry import PluginRegistry
from recon.core.target import Target
from recon.core.scheduler import TaskScheduler

logger = structlog.get_logger(__name__)


class ReconEngine:
    def __init__(self, registry: PluginRegistry, settings):
        self.registry = registry
        self.settings = settings

    async def run_scan(self, target_str: str, db_session):
        target = Target.from_string(target_str)
        target_type_str = target.type.name.lower()

        # Find applicable plugins
        applicable_plugins = []
        for meta in self.registry.list_plugins():
            if meta.supported_target_types and target_type_str not in meta.supported_target_types:
                continue
            if meta.name in self.settings.disabled_plugins:
                continue
            applicable_plugins.append(meta.name)

        if not applicable_plugins:
            logger.warning("No plugins found for target", target=target_str)
            return []

        scheduler = TaskScheduler(max_concurrency=self.settings.threads)
        with scheduler.progress:
            for pname in applicable_plugins:
                plugin_instance = self.registry.instantiate(
                    pname, config={"timeout": self.settings.timeout}
                )
                coro = plugin_instance.run(target, db_session)
                await scheduler.schedule(coro, name=pname)

            results = await scheduler.gather()
        return results
