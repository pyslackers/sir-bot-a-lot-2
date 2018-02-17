import asyncio
import logging
import aiohttp.web

from . import endpoints

LOG = logging.getLogger(__name__)


class SirBot(aiohttp.web.Application):
    def __init__(self, user_agent=None, **kwargs):
        super().__init__(**kwargs)

        self.router.add_route('GET', '/sirbot/plugins', endpoints.plugins)

        self['plugins'] = dict()
        self['http_session'] = aiohttp.ClientSession(loop=kwargs.get('loop') or asyncio.get_event_loop())
        self['user_agent'] = user_agent or 'sir-bot-a-lot'

        self.on_shutdown.append(self.stop)

    def start(self, **kwargs):
        LOG.info('Starting SirBot')
        aiohttp.web.run_app(self, **kwargs)

    def load_plugin(self, plugin, name=None):
        name = name or plugin.__name__
        self['plugins'][name] = plugin
        plugin.load(self)

    async def stop(self, sirbot):
        await self['http_session'].close()

    @property
    def plugins(self):
        return self['plugins']

    @property
    def http_session(self):
        return self['http_session']

    @property
    def user_agent(self):
        return self['user_agent']
