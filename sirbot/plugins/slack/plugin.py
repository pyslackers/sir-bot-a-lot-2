import os
import logging
import asyncio

from slack import methods
from slack.io.aiohttp import SlackAPI
from slack.actions import Router as ActionRouter
from slack.commands import Router as CommandRouter
from slack.events import EventRouter, MessageRouter

from . import endpoints

LOG = logging.getLogger(__name__)


class SlackPlugin:
    __name__ = 'slack'

    def __init__(self, *, token=None, verify=None, bot_id=None, bot_user_id=None, admins=None):
        self.api = None
        self.token = token or os.environ['SLACK_TOKEN']
        self.admins = admins or os.environ.get('SLACK_ADMINS', [])
        self.verify = verify or os.environ['SLACK_VERIFY']
        self.bot_id = bot_id or os.environ.get('SLACK_BOT_ID')
        self.bot_user_id = bot_user_id or os.environ.get('SLACK_BOT_USER_ID')
        self.handlers_option = {}

        if not self.bot_user_id and not self.bot_id:
            LOG.warning('`SLACK_BOT_USER_ID` or `SLACK_BOT_ID` required to use `on_mention` routing.')

        self.routers = {
            'event': EventRouter(),
            'command': CommandRouter(),
            'message': MessageRouter(),
            'action': ActionRouter(),
        }

    def load(self, sirbot):
        LOG.info('Loading slack plugin')
        self.api = SlackAPI(session=sirbot.http_session, token=self.token)

        sirbot.router.add_route('POST', '/slack/events', endpoints.incoming_event)
        sirbot.router.add_route('POST', '/slack/commands', endpoints.incoming_command)
        sirbot.router.add_route('POST', '/slack/actions', endpoints.incoming_actions)

        if self.bot_user_id and not self.bot_id:
            sirbot.on_startup.append(self.find_bot_id)
        elif not self.bot_user_id and not self.bot_id:
            sirbot.on_startup.append(self.find_bot_user_id)

    def on_event(self, event_type, handler):
        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)
        self.routers['event'].register(event_type, handler)

    def on_command(self, command, handler):
        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)
        self.routers['command'].register(command, handler)

    def on_message(self, pattern, handler, flags=0, channel='*', mention=False, admin=False):
        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)

        if admin and not self.admins:
            LOG.warning('Slack admins ids are not set. Admin limited endpoint will not work.')

        self.handlers_option[handler] = {'mention': mention, 'admin': admin}
        self.routers['message'].register(pattern=pattern, handler=handler, flags=flags, channel=channel)

    def on_action(self, action, handler, name='*'):
        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)
        self.routers['action'].register(action, handler, name)

    async def find_bot_id(self, app):
        rep = await self.api.query(url=methods.USERS_INFO, data={'user': self.bot_user_id})
        self.bot_id = rep['user']['profile']['bot_id']

    async def find_bot_user_id(self, app):
        rep = await self.api.query(
            url=methods.CHAT_POST_MESSAGE,
            data={'channel': 'general', 'text': 'Looking for bot id'}
        )
        LOG.warning('The BOT_USER_ID is : "%s"', rep['message']['user'])
