import pytest

from sirbot import SirBot
from sirbot.plugins.apscheduler import APSchedulerPlugin


@pytest.fixture
async def bot():
    b = SirBot()
    b.load_plugin(APSchedulerPlugin())
    return b


class TestPluginAPscheduler:
    async def test_start(self, bot, test_server):
        await test_server(bot)
        assert isinstance(bot['plugins']['scheduler'], APSchedulerPlugin)
