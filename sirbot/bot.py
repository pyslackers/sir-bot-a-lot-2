import asyncio
import logging
import aiohttp.web

from . import endpoints

LOG = logging.getLogger(__name__)


class SirBot(aiohttp.web.Application):
    def __init__(self, user_agent=None, **kwargs):
        super().__init__(**kwargs)

        self.plugins = dict()
        self.http_session = aiohttp.ClientSession(loop=kwargs.get('loop') or asyncio.get_event_loop())
        self.user_agent = user_agent or 'sir-bot-a-lot'
        self.router.add_route('GET', '/sirbot/plugins', endpoints.plugins)

    def start(self, **kwargs):
        LOG.info('Starting SirBot')
        aiohttp.web.run_app(self, **kwargs)

    def load_plugin(self, plugin):
        self.plugins[plugin.__name__] = plugin
        plugin.load(self)

    async def shutdown(self):
        LOG.info('Stoppping SirBot')
        self.http_session.close()
        await super().shutdown()
        LOG.info('SirBot stopped')
