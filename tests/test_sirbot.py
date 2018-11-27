import pytest
from sirbot import SirBot


@pytest.mark.asyncio
class TestSirBot:
    async def test_bot(self, aiohttp_server):
        bot = SirBot()
        await aiohttp_server(bot)

    async def test_load_plugin(self, aiohttp_server):
        class MyPlugin:
            __name__ = "myplugin"

            def __init__(self):
                pass

            def load(self, test_bot):
                pass

        bot = SirBot()
        bot.load_plugin(MyPlugin())
        assert "myplugin" in bot.plugins
        assert isinstance(bot["plugins"]["myplugin"], MyPlugin)
        await aiohttp_server(bot)

    async def test_load_plugin_no_name(self):
        class MyPlugin:
            def __init__(self):
                pass

            def load(self, test_bot):
                pass

        bot = SirBot()
        with pytest.raises(AttributeError):
            bot.load_plugin(MyPlugin())


class TestEndpoints:
    async def test_list_plugin_empty(self, aiohttp_client):
        bot = SirBot()
        client = await aiohttp_client(bot)
        rep = await client.get("/sirbot/plugins")
        data = await rep.json()
        assert data == {"plugins": []}

    async def test_list_plugin(self, aiohttp_client):
        class MyPlugin:
            __name__ = "myplugin"

            def __init__(self):
                pass

            def load(self, test_bot):
                pass

        bot = SirBot()
        bot.load_plugin(MyPlugin())
        client = await aiohttp_client(bot)
        rep = await client.get("/sirbot/plugins")
        data = await rep.json()
        assert data == {"plugins": ["myplugin"]}
