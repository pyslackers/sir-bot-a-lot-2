import json
import pytest

from sirbot import SirBot
from sirbot.plugins.github import GithubPlugin


@pytest.fixture
async def bot():
    b = SirBot()
    b.load_plugin(GithubPlugin(verify='supersecrettoken'))
    return b


@pytest.fixture(params=['pr_merged', 'issue_closed'])
async def event(request):
    with open(f'tests/data/github/events/{request.param}.json') as f:
        body = json.loads(f.read())

    with open(f'tests/data/github/events/{request.param}.headers.json') as f:
        headers = json.loads(f.read())

    return body, headers


class TestPluginGithub:
    async def test_start(self, bot, test_server):
        await test_server(bot)
        assert isinstance(bot['plugins']['github'], GithubPlugin)

    async def test_incoming_event(self, bot, test_client, event):
        client = await test_client(bot)
        r = await client.post('/github', json=event[0], headers=event[1])
        assert r.status == 200

    async def test_incoming_event_401(self, bot, test_client, event):
        bot['plugins']['github'].verify = 'wrongsupersecrettoken'
        client = await test_client(bot)
        r = await client.post('/github', json=event[0], headers=event[1])
        assert r.status == 401

    async def test_incoming_event_handler_error(self, bot, test_client, event):
        async def handler(event, app):
            raise RuntimeError()

        bot['plugins']['github'].router.add(handler, event[1]['X-GitHub-Event'], action=event[0]['action'])
        client = await test_client(bot)
        r = await client.post('/github', json=event[0], headers=event[1])
        assert r.status == 500
