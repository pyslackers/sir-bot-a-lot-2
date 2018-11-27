import pytest
from sirbot import SirBot
from sirbot.plugins.apscheduler import APSchedulerPlugin


@pytest.fixture
async def bot():
    b = SirBot()
    b.load_plugin(APSchedulerPlugin())
    return b


class TestPluginAPscheduler:
    async def test_start(self, bot, aiohttp_server):
        await aiohttp_server(bot)
        assert isinstance(bot["plugins"]["scheduler"], APSchedulerPlugin)
