import os
import asyncio
import logging

from slack import methods
from slack.events import EventRouter, MessageRouter
from slack.actions import Router as ActionRouter
from slack.commands import Router as CommandRouter
from slack.io.aiohttp import SlackAPI

from . import endpoints

LOG = logging.getLogger(__name__)


class SlackPlugin:
    """
    Handle communication from and to slack

    **Endpoints**:
        * ``/slack/events``: Incoming events.
        * ``/slack/commands``: Incoming commands.
        * ``/slack/actions``: Incoming actions.

    Args:
        token: slack authentication token (env var: `SLACK_TOKEN`).
        bot_id: bot id (env var: `SLACK_BOT_ID`).
        bot_user_id: user id of the bot (env var: `SLACK_BOT_USER_ID`).
        admins: list of slack admins user id (env var: `SLACK_ADMINS`).
        verify: slack verification token (env var: `SLACK_VERIFY`).
        signing_secret: slack signing secret key (env var: `SLACK_SIGNING_SECRET`).
                        (disables verification token if provided).

    **Variables**:
        * **api**: Slack client. Instance of :class:`slack.io.aiohttp.SlackAPI`.
    """

    __name__ = "slack"

    def __init__(
        self,
        *,
        token=None,
        bot_id=None,
        bot_user_id=None,
        admins=None,
        verify=None,
        signing_secret=None
    ):
        self.api = None
        self.token = token or os.environ["SLACK_TOKEN"]
        self.admins = admins or os.environ.get("SLACK_ADMINS", [])
        if signing_secret or "SLACK_SIGNING_SECRET" in os.environ:
            self.signing_secret = signing_secret or os.environ["SLACK_SIGNING_SECRET"]
            self.verify = None
        else:
            self.verify = verify or os.environ["SLACK_VERIFY"]
            self.signing_secret = None
        self.bot_id = bot_id or os.environ.get("SLACK_BOT_ID")
        self.bot_user_id = bot_user_id or os.environ.get("SLACK_BOT_USER_ID")
        self.handlers_option = {}

        if not self.bot_user_id:
            LOG.warning(
                "`SLACK_BOT_USER_ID` not set. It is required for `on mention` routing and discarding "
                "message coming from Sir Bot-a-lot to avoid loops."
            )

        self.routers = {
            "event": EventRouter(),
            "command": CommandRouter(),
            "message": MessageRouter(),
            "action": ActionRouter(),
        }

    def load(self, sirbot):
        LOG.info("Loading slack plugin")
        self.api = SlackAPI(session=sirbot.http_session, token=self.token)

        sirbot.router.add_route("POST", "/slack/events", endpoints.incoming_event)
        sirbot.router.add_route("POST", "/slack/commands", endpoints.incoming_command)
        sirbot.router.add_route("POST", "/slack/actions", endpoints.incoming_action)

        if self.bot_user_id and not self.bot_id:
            sirbot.on_startup.append(self.find_bot_id)

    def on_event(self, event_type, handler, wait=True):
        """
        Register handler for an event

        Args:
            event_type: Incoming event type.
            handler: Handler to call.
            wait: Wait for handler execution before responding to the slack API.
        """

        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)
        configuration = {"wait": wait}
        self.routers["event"].register(event_type, (handler, configuration))

    def on_command(self, command, handler, wait=True):
        """
        Register handler for a command

        Args:
            command: Incoming command.
            handler: Handler to call.
            wait: Wait for handler execution before responding to the slack API.
        """
        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)
        configuration = {"wait": wait}
        self.routers["command"].register(command, (handler, configuration))

    def on_message(
        self, pattern, handler, mention=False, admin=False, wait=True, **kwargs
    ):
        """
        Register handler for a message

        kwargs are passed to :meth:`slack.events.MessageRouter.register`

        Args:
            pattern: Regex pattern matching the message text.
            handler: Handler to call.
            mention: Only trigger handler when the bot is mentioned.
            admin: Only trigger handler if posted by an admin.
            wait: Wait for handler execution before responding to the slack API.
        """
        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)

        if admin and not self.admins:
            LOG.warning(
                "Slack admins ids are not set. Admin limited endpoint will not work."
            )

        configuration = {"mention": mention, "admin": admin, "wait": wait}
        self.routers["message"].register(
            pattern=pattern, handler=(handler, configuration), **kwargs
        )

    def on_action(self, action, handler, name="*", wait=True):
        """
        Register handler for an action

        Args:
            action: `callback_id` of the incoming action.
            handler: Handler to call.
            name: Choice name of the action.
            wait: Wait for handler execution before responding to the slack API.
        """
        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)
        configuration = {"wait": wait}
        self.routers["action"].register(action, (handler, configuration), name)

    def on_block(self, block_id, handler, action_id="*", wait=True):
        """
        Register handler for a `block_actions` type action

        Args:
            block_id: `block_id` of the incoming action.
            handler: Handler to call.
            action_id: `action_id` of the incoming action
            wait: Wait for handler execution before responding to the slack API.
        """

        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)

        configuration = {"wait": wait}
        self.routers["action"].register_block_action(
            block_id, (handler, configuration), action_id
        )

    def on_dialog_submission(self, callback_id, handler, wait=True):
        """
        Register handler for a `dialog_submission` type action

        Args:
            callback_id: `callback_id` of the incoming action.
            handler: Handler to call.
            wait: Wait for handler execution before responding to the slack API.
        """

        if not asyncio.iscoroutinefunction(handler):
            handler = asyncio.coroutine(handler)

        configuration = {"wait": wait}
        self.routers["action"].register_dialog_submission(
            callback_id, (handler, configuration)
        )

    async def find_bot_id(self, app):
        rep = await self.api.query(
            url=methods.USERS_INFO, data={"user": self.bot_user_id}
        )
        self.bot_id = rep["user"]["profile"]["bot_id"]
        LOG.warning(
            '`SLACK_BOT_ID` not set. For a faster start time set it to: "%s"',
            self.bot_id,
        )
