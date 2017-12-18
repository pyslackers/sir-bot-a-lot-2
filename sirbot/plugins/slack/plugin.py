import os
import logging
import asyncio

from slack import methods
from slack.io.aiohttp import SlackAPI
from slack.events import Router as EventRouter
from slack.commands import Router as CommandRouter

from . import endpoints
from .message import MessageRouter

LOG = logging.getLogger(__name__)


class SlackPlugin:
    __name__ = 'slack'

    def __init__(self, *, token=None, verify=None, bot_id=None, bot_user_id=None):
        self.api = None
        self.token = token or os.environ['SLACK_TOKEN']
        self.verify = verify or os.environ['SLACK_VERIFY']
        self.bot_id = bot_id or os.environ.get('SLACK_BOT_ID')
        self.bot_user_id = bot_user_id or os.environ.get('SLACK_BOT_USER_ID')

        if not self.bot_user_id and not self.bot_id:
            LOG.warning('`SLACK_BOT_USER_ID` or `SLACK_BOT_ID` required to use `on_mention` routing.')

        self.routers = {
            'event': EventRouter(),
            'command': CommandRouter(),
            'message': MessageRouter()
        }

    def load(self, sirbot):
        LOG.info('Loading slack plugin')
        self.api = SlackAPI(session=sirbot.http_session, token=self.token)

        sirbot.router.add_route('POST', '/slack/events', endpoints.incoming_event)
        sirbot.router.add_route('POST', '/slack/commands', endpoints.incoming_command)

        if self.bot_user_id and not self.bot_id:
            sirbot.on_startup.append(self.find_bot_id)

    def on_event(self, event_type, endpoint):
        if not asyncio.iscoroutinefunction(endpoint):
            endpoint = asyncio.coroutine(endpoint)
        self.routers['event'].register(event_type, endpoint)

    def on_command(self, command, endpoint):
        if not asyncio.iscoroutinefunction(endpoint):
            endpoint = asyncio.coroutine(endpoint)
        self.routers['command'].register(command, endpoint)
    
    def on_message(self, pattern, endpoint, flags=0, channel='*', mention=False):
        if not asyncio.iscoroutinefunction(endpoint):
            endpoint = asyncio.coroutine(endpoint)
        self.routers['message'].register(pattern=pattern, endpoint=endpoint, flags=flags, channel=channel,
                                         mention=mention)

    async def find_bot_id(self, app):
        rep = await self.api.query(url=methods.USERS_INFO, data={'user': self.bot_user_id})
        self.bot_id = rep['user']['profile']['bot_id']
