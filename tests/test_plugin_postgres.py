import pytest

from sirbot import SirBot
from sirbot.plugins.postgres import PgPlugin


@pytest.fixture
@pytest.mark.asyncio
async def bot():
    b = SirBot()
    b.load_plugin(PgPlugin(sql_migration_directory='tests/data/sql'))
    return b


class TestPluginPostgres:

    def test_find_sql_migration(self, bot):
        files = bot['plugins']['pg']._find_update_version([0, 0, 0], [0, 4, 6])
        assert files == [[0, 0, 1], [0, 1, 9], [0, 1, 12]]
