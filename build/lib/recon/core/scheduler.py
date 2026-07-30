import asyncio
from typing import List, Coroutine, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from rich.progress import Progress, TaskID

logger = structlog.get_logger(__name__)

class TaskScheduler:
    def __init__(self, max_concurrency: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.tasks: List[asyncio.Task] = []
        self.progress = Progress()
        self.task_ids: Dict[str, TaskID] = {}

    async def _run_with_semaphore(self, coro, task_name: str) -> Any:
        async with self.semaphore:
            task_id = self.progress.add_task(f"[cyan]{task_name}", total=None)
            try:
                result = await coro
                self.progress.update(task_id, completed=True, description=f"[green]{task_name}")
                return result
            except Exception as e:
                self.progress.update(task_id, description=f"[red]{task_name} failed")
                logger.exception(f"Task {task_name} failed")
                raise

    async def schedule(self, coro, name: str):
        task = asyncio.create_task(self._run_with_semaphore(coro, name))
        self.tasks.append(task)
        return task

    async def gather(self):
        results = await asyncio.gather(*self.tasks, return_exceptions=True)
        return results