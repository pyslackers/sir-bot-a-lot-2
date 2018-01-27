import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

LOG = logging.getLogger(__name__)


class APSchedulerPlugin:
    __name__ = 'scheduler'

    def __init__(self, **kwargs):
        self.scheduler = AsyncIOScheduler(**kwargs)

    def load(self, sirbot):
        LOG.info('Loading apscheduler plugin')
        sirbot.on_startup.append(self.start)

    async def start(self, sirbot):
        self.scheduler.start()
