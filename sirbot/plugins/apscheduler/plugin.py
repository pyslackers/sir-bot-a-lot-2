import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

LOG = logging.getLogger(__name__)


class APSchedulerPlugin:
    """
    Handle code execution scheduling

    Register a new job running every hour with:

    .. code-block:: python

        APSchedulerPlugin.scheduler.add_job(job, 'cron', hour=1, kwargs={'bot': bot})

    Args:
        **kwargs: Arguments for :class:`apscheduler.schedulers.asyncio.AsyncIOScheduler`.

    **Variables**
        * **scheduler**: Instance of :class:`apscheduler.schedulers.asyncio.AsyncIOScheduler`.
    """

    __name__ = "scheduler"

    def __init__(self, **kwargs):
        self.scheduler = AsyncIOScheduler(**kwargs)

    def load(self, sirbot):
        LOG.info("Loading apscheduler plugin")
        sirbot.on_startup.append(self.start)

    async def start(self, sirbot):
        self.scheduler.start()
