import re
import hmac
import json
import time
import asyncio
import hashlib
import urllib.parse
from typing import Dict, Tuple, Union, Optional
from unittest import mock
from collections import MutableMapping

import pytest
import asynctest
from aiohttp.web import json_response
import slack
from sirbot import SirBot
from sirbot.plugins.slack import SlackPlugin


@pytest.fixture
async def bot():
    b = SirBot()
    b.load_plugin(
        SlackPlugin(
            token="foo",
            verify="supersecuretoken",
            bot_user_id="baz",
            bot_id="boo",
            admins=["aaa", "bbb"],
        )
    )
    return b


@pytest.fixture
async def bot_signing():
    b = SirBot()
    b.load_plugin(
        SlackPlugin(
            token="foo",
            signing_secret="sharedsigningkey",
            bot_user_id="baz",
            bot_id="boo",
            admins=["aaa", "bbb"],
        )
    )
    return b


def _sign_body(
    json_data: Optional[Dict] = None,
    post_data: Optional[Dict] = None,
    signing_secret: str = "sharedsigningkey",
    timestamp: Optional[int] = None,
) -> Tuple[Dict[str, str], bytes]:
    if json_data:
        headers = {"content-type": "application/json"}
        body = json.dumps(json_data).encode("utf-8")
    elif post_data:
        headers = {"content-type": "application/x-www-form-urlencoded"}
        body = urllib.parse.urlencode(post_data).encode("utf-8")
    else:
        raise ValueError("Unknown type of data to sign")
    if timestamp is None:
        timestamp = int(time.time())
    headers["X-Slack-Request-Timestamp"] = str(timestamp)
    headers["X-Slack-Signature"] = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"),
            f"""v0:{timestamp}:{body.decode("utf-8")}""".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
    )
    return headers, body


@pytest.fixture
def find_bot_id_query():
    async def query(*args, **kwargs):
        return {
            "ok": True,
            "user": {
                "id": "W012A3CDE",
                "team_id": "T012AB3C4",
                "name": "spengler",
                "deleted": False,
                "color": "9f69e7",
                "real_name": "episod",
                "tz": "America/Los_Angeles",
                "tz_label": "Pacific Daylight Time",
                "tz_offset": -25200,
                "profile": {
                    "avatar_hash": "ge3b51ca72de",
                    "status_text": "Print is dead",
                    "status_emoji": ":books:",
                    "real_name": "Egon Spengler",
                    "display_name": "spengler",
                    "real_name_normalized": "Egon Spengler",
                    "display_name_normalized": "spengler",
                    "email": "spengler@ghostbusters.example.com",
                    "image_24": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_32": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_48": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_72": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_192": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "image_512": "https://.../avatar/e3b51ca72dee4ef87916ae2b9240df50.jpg",
                    "team": "T012AB3C4",
                    "bot_id": "B00000000",
                },
                "is_admin": True,
                "is_owner": False,
                "is_primary_owner": False,
                "is_restricted": False,
                "is_ultra_restricted": False,
                "is_bot": True,
                "updated": 1_502_138_686,
                "is_app_user": False,
                "has_2fa": False,
            },
        }

    return query


class TestPluginSlack:
    async def test_start(self, bot, aiohttp_server):
        await aiohttp_server(bot)
        assert isinstance(bot["plugins"]["slack"], SlackPlugin)

    async def test_start_no_bot_user_id(self, caplog):
        SlackPlugin(token="foo", verify="bar", bot_id="boo", admins=["aaa", "bbb"])
        assert "`SLACK_BOT_USER_ID` not set" in caplog.text

    async def test_register_event(self, bot):
        async def handler():
            pass

        def handler2():
            pass

        bot["plugins"]["slack"].on_event("team_join", handler)
        bot["plugins"]["slack"].on_event("team_join", handler2)

        assert (
            bot["plugins"]["slack"]
            .routers["event"]
            ._routes["team_join"]["*"]["*"][0][0]
            is handler
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"]
            .routers["event"]
            ._routes["team_join"]["*"]["*"][0][0]
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"]
            .routers["event"]
            ._routes["team_join"]["*"]["*"][1][0]
        )

    async def test_register_command(self, bot):
        async def handler():
            pass

        def handler2():
            pass

        bot["plugins"]["slack"].on_command("/hello", handler)
        bot["plugins"]["slack"].on_command("/hello", handler2)

        assert (
            bot["plugins"]["slack"].routers["command"]._routes["/hello"][0][0]
            is handler
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"].routers["command"]._routes["/hello"][0][0]
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"].routers["command"]._routes["/hello"][1][0]
        )

    async def test_register_message(self, bot):
        async def handler():
            pass

        def handler2():
            pass

        msg = "hello"
        bot["plugins"]["slack"].on_message(msg, handler)
        bot["plugins"]["slack"].on_message(msg, handler2)
        msg_compile = re.compile(msg)
        assert (
            bot["plugins"]["slack"]
            .routers["message"]
            ._routes["*"][None][msg_compile][0][0]
            is handler
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"]
            .routers["message"]
            ._routes["*"][None][msg_compile][0][0]
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"]
            .routers["message"]
            ._routes["*"][None][msg_compile][1][0]
        )

    async def test_register_admin_message_no_admin(self, caplog):
        async def handler():
            pass

        bot = SirBot()
        bot.load_plugin(
            SlackPlugin(token="foo", verify="bar", bot_user_id="baz", bot_id="boo")
        )
        bot["plugins"]["slack"].on_message("hello", handler, admin=True)
        assert (
            "Slack admins ids are not set. Admin limited endpoint will not work."
            in caplog.text
        )

    async def test_register_action(self, bot: SirBot):
        async def handler():
            pass

        def handler2():
            pass

        bot["plugins"]["slack"].on_action("hello", handler)
        bot["plugins"]["slack"].on_action("hello", handler2)

        assert (
            bot["plugins"]["slack"].routers["action"]._routes["hello"]["*"][0][0]
            is handler
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"].routers["action"]._routes["hello"]["*"][0][0]
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"].routers["action"]._routes["hello"]["*"][1][0]
        )

    async def test_register_block_action(self, bot: SirBot):
        async def handler():
            pass

        def handler2():
            pass

        bot["plugins"]["slack"].on_block("hello", handler)
        bot["plugins"]["slack"].on_block("hello", handler2)

        assert (
            bot["plugins"]["slack"].routers["action"]._routes["hello"]["*"][0][0]
            is handler
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"].routers["action"]._routes["hello"]["*"][0][0]
        )
        assert asyncio.iscoroutinefunction(
            bot["plugins"]["slack"].routers["action"]._routes["hello"]["*"][1][0]
        )

    async def test_find_bot_id(self, bot, aiohttp_server, find_bot_id_query):
        await aiohttp_server(bot)
        bot["plugins"]["slack"].api.query = find_bot_id_query
        await bot["plugins"]["slack"].find_bot_id(bot)
        assert bot["plugins"]["slack"].bot_id == "B00000000"

    async def test_start_find_bot_id(self, aiohttp_server, find_bot_id_query):
        bot = SirBot()
        bot.load_plugin(SlackPlugin(token="foo", verify="bar", bot_user_id="baz"))
        bot["plugins"]["slack"].api.query = find_bot_id_query
        await aiohttp_server(bot)
        assert bot["plugins"]["slack"].bot_id == "B00000000"


class TestPluginSlackEndpoints:
    async def test_incoming_event(self, bot, aiohttp_client, slack_event):
        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_event)
        assert r.status == 200

    async def test_incoming_event_signed(
        self, bot_signing, aiohttp_client, slack_event
    ):
        client = await aiohttp_client(bot_signing)
        headers, body = _sign_body(json_data=slack_event)
        r = await client.post("/slack/events", headers=headers, data=body)
        assert r.status == 200

    async def test_incoming_command(self, bot, aiohttp_client, slack_command):
        client = await aiohttp_client(bot)
        r = await client.post("/slack/commands", data=slack_command)
        assert r.status == 200

    async def test_incoming_command_signed(
        self, bot_signing, aiohttp_client, slack_command
    ):
        client = await aiohttp_client(bot_signing)
        headers, body = _sign_body(post_data=slack_command)
        r = await client.post("/slack/commands", headers=headers, data=body)
        assert r.status == 200

    async def test_incoming_action(self, bot, aiohttp_client, slack_action):
        client = await aiohttp_client(bot)
        r = await client.post("/slack/actions", data=slack_action)
        assert r.status == 200

    async def test_incoming_action_signed(
        self, bot_signing, aiohttp_client, slack_action
    ):
        client = await aiohttp_client(bot_signing)
        headers, body = _sign_body(post_data=slack_action)
        r = await client.post("/slack/actions", headers=headers, data=body)
        assert r.status == 200

    async def test_incoming_event_wrong_token(self, bot, aiohttp_client, slack_event):
        bot["plugins"]["slack"].verify = "bar"
        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_event)
        assert r.status == 401

    async def test_incoming_command_wrong_token(
        self, bot, aiohttp_client, slack_command
    ):
        bot["plugins"]["slack"].verify = "bar"
        client = await aiohttp_client(bot)
        r = await client.post("/slack/commands", data=slack_command)
        assert r.status == 401

    async def test_incoming_action_wrong_token(self, bot, aiohttp_client, slack_action):
        bot["plugins"]["slack"].verify = "bar"
        client = await aiohttp_client(bot)
        r = await client.post("/slack/actions", data=slack_action)
        assert r.status == 401

    async def test_incoming_event_error(self, bot, aiohttp_client, slack_event):
        async def handler(*args, **kwargs):
            raise RuntimeError()

        bot["plugins"]["slack"].routers["event"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True})]
        )
        bot["plugins"]["slack"].routers["message"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True, "mention": False, "admin": False})]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_event)
        assert r.status == 500

    async def test_incoming_message_error(self, bot, aiohttp_client, slack_message):
        async def handler(*args, **kwargs):
            raise RuntimeError()

        bot["plugins"]["slack"].routers["message"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True, "mention": False, "admin": False})]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_message)
        assert r.status == 500

    async def test_incoming_command_error(self, bot, aiohttp_client, slack_command):
        async def handler(*args, **kwargs):
            raise RuntimeError()

        bot["plugins"]["slack"].routers["command"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True})]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/commands", data=slack_command)
        assert r.status == 500

    async def test_incoming_action_error(self, bot, aiohttp_client, slack_action):
        async def handler(*args, **kwargs):
            raise RuntimeError()

        bot["plugins"]["slack"].routers["action"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True})]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/actions", data=slack_action)
        assert r.status == 500

    async def test_incoming_event_handler_arg(self, bot, aiohttp_client, slack_event):
        async def handler(event, app):
            assert app is bot
            assert isinstance(event, slack.events.Event)

        bot["plugins"]["slack"].routers["event"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True})]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_event)
        assert r.status == 200

    async def test_incoming_message_handler_arg(
        self, bot, aiohttp_client, slack_message
    ):
        async def handler(event, app):
            assert app is bot
            assert isinstance(event, slack.events.Message)

        bot["plugins"]["slack"].routers["message"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True, "mention": False, "admin": False})]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_message)
        assert r.status == 200

    async def test_incoming_command_handler_arg(
        self, bot, aiohttp_client, slack_command
    ):
        async def handler(command, app):
            assert app is bot
            assert isinstance(command, slack.commands.Command)

        bot["plugins"]["slack"].routers["command"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True})]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/commands", data=slack_command)
        assert r.status == 200

    async def test_incoming_action_handler_arg(self, bot, aiohttp_client, slack_action):
        async def handler(action, app):
            assert app is bot
            assert isinstance(action, slack.actions.Action)

        bot["plugins"]["slack"].routers["action"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True})]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/actions", data=slack_action)
        assert r.status == 200

    async def test_event_challenge(self, bot, aiohttp_client):
        client = await aiohttp_client(bot)
        r = await client.post(
            "/slack/events",
            json={
                "token": "supersecuretoken",
                "challenge": "abcdefghij",
                "type": "url_verification",
            },
        )
        data = await r.text()
        assert r.status == 200
        assert data == "abcdefghij"
        assert r.status == 200

    async def test_event_challenge_signed(self, bot_signing, aiohttp_client):
        client = await aiohttp_client(bot_signing)
        headers, body = _sign_body(
            json_data={
                "token": "na",
                "challenge": "abcdefghij",
                "type": "url_verification",
            }
        )
        r = await client.post("/slack/events", data=body, headers=headers)
        data = await r.text()
        assert r.status == 200
        assert data == "abcdefghij"

    async def test_event_challenge_wrong_token(self, bot, aiohttp_client):
        client = await aiohttp_client(bot)
        r = await client.post(
            "/slack/events",
            json={
                "token": "wrongsupersecuretoken",
                "challenge": "abcdefghij",
                "type": "url_verification",
            },
        )
        assert r.status == 500

    async def test_event_challenge_signed_wrong(self, bot_signing, aiohttp_client):
        client = await aiohttp_client(bot_signing)
        headers, body = _sign_body(
            json_data={
                "token": "na",
                "challenge": "abcdefghij",
                "type": "url_verification",
            },
            signing_secret="notsharedsigningkey",
        )
        r = await client.post("/slack/events", data=body, headers=headers)
        assert r.status == 500

    @pytest.mark.parametrize("slack_message", ("bot",), indirect=True)
    async def test_message_from_bot(self, bot, aiohttp_client, slack_message):
        bot["plugins"]["slack"].bot_id = "B0AAA0A00"
        bot["plugins"]["slack"].routers["message"].dispatch = mock.MagicMock()

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_message)
        assert r.status == 200
        assert bot["plugins"]["slack"].routers["message"].dispatch.call_count == 0

    @pytest.mark.parametrize("slack_message", ("bot",), indirect=True)
    async def test_message_from_other_bot(self, bot, aiohttp_client, slack_message):
        bot["plugins"]["slack"].bot_id = "B0AAA0A01"
        bot["plugins"]["slack"].routers["message"].dispatch = mock.MagicMock()

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_message)
        assert r.status == 200
        assert bot["plugins"]["slack"].routers["message"].dispatch.call_count == 1

    @pytest.mark.parametrize("slack_message", ("simple",), indirect=True)
    async def test_admin_message_ok(self, bot, aiohttp_client, slack_message):
        handler = asynctest.CoroutineMock()
        bot["plugins"]["slack"].admins = ["U000AA000"]
        bot["plugins"]["slack"].on_message("hello", handler, admin=True)

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_message)
        assert r.status == 200
        assert handler.call_count == 1

    @pytest.mark.parametrize("slack_message", ("simple",), indirect=True)
    async def test_admin_message_skip(self, bot, aiohttp_client, slack_message):
        handler = asynctest.CoroutineMock()
        bot["plugins"]["slack"].admins = ["U000AA001"]
        bot["plugins"]["slack"].on_message("hello", handler, admin=True)

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_message)
        assert r.status == 200
        assert handler.call_count == 0

    @pytest.mark.parametrize("slack_message", ("mention",), indirect=True)
    async def test_message_mention_ok(self, bot, aiohttp_client, slack_message):
        handler = asynctest.CoroutineMock()
        bot["plugins"]["slack"].bot_user_id = "U0AAA0A00"
        bot["plugins"]["slack"].on_message("hello world", handler, mention=True)

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_message)
        assert r.status == 200
        assert handler.call_count == 1

    @pytest.mark.parametrize("slack_message", ("mention",), indirect=True)
    async def test_message_mention_skip(self, bot, aiohttp_client, slack_message):
        handler = asynctest.CoroutineMock()
        bot["plugins"]["slack"].bot_user_id = "U0AAA0A01"
        bot["plugins"]["slack"].on_message("hello world", handler, mention=True)

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_message)
        assert r.status == 200
        assert handler.call_count == 0

    @pytest.mark.parametrize("slack_message", ("mention",), indirect=True)
    async def test_message_mention_strip_bot(self, bot, aiohttp_client, slack_message):
        async def handler(message, app):
            assert message["text"] == "hello world"

        bot["plugins"]["slack"].bot_user_id = "U0AAA0A00"
        bot["plugins"]["slack"].on_message("hello world", handler, mention=True)
        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_message)
        assert r.status == 200

    async def test_event_handler_return_response(
        self, bot, aiohttp_client, slack_event
    ):
        async def handler(message, app):
            return json_response(data={"ok": True}, status=200)

        bot["plugins"]["slack"].routers["event"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True})]
        )
        bot["plugins"]["slack"].routers["message"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True, "mention": False, "admin": False})]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_event)
        assert r.status == 200
        assert (await r.json()) == {"ok": True}

    async def test_action_handler_return_response(
        self, bot, aiohttp_client, slack_action
    ):
        async def handler(message, app):
            print("AAAAA")
            return json_response(data={"ok": True}, status=200)

        bot["plugins"]["slack"].routers["action"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True})]
        )
        client = await aiohttp_client(bot)
        r = await client.post("/slack/actions", data=slack_action)
        assert r.status == 200
        assert (await r.json()) == {"ok": True}

    async def test_command_handler_return_response(
        self, bot, aiohttp_client, slack_command
    ):
        async def handler(message, app):
            return json_response(data={"ok": True}, status=200)

        bot["plugins"]["slack"].routers["command"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True})]
        )
        client = await aiohttp_client(bot)
        r = await client.post("/slack/commands", data=slack_command)
        assert r.status == 200
        assert (await r.json()) == {"ok": True}

    async def test_handler_multiple_response(self, bot, aiohttp_client, slack_event):
        async def handler(message, app):
            return json_response(data={"ok": True}, status=200)

        async def handler2(message, app):
            return json_response(data={"ok": False})

        bot["plugins"]["slack"].routers["event"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": True}), (handler2, {"wait": True})]
        )
        bot["plugins"]["slack"].routers["message"].dispatch = mock.MagicMock(
            return_value=[
                (handler, {"wait": True, "mention": False, "admin": False}),
                (handler2, {"wait": True, "mention": False, "admin": False}),
            ]
        )

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_event)
        assert r.status == 200
        assert (await r.text()) == ""

    async def test_handler_no_wait(self, bot, aiohttp_client, slack_event):
        global sentinel
        sentinel = False

        async def handler(message, app):
            global sentinel
            sentinel = True
            return json_response(data={"ok": True})

        bot["plugins"]["slack"].routers["event"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": False})]
        )
        bot["plugins"]["slack"].routers["message"].dispatch = mock.MagicMock(
            return_value=[(handler, {"wait": False, "mention": False, "admin": False})]
        )

        assert not sentinel

        client = await aiohttp_client(bot)
        r = await client.post("/slack/events", json=slack_event)

        assert r.status == 200
        assert (await r.text()) == ""

        await asyncio.sleep(0.5)
        assert sentinel
