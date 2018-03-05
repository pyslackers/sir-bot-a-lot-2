import pytest
import asyncpg

from sirbot import SirBot
from sirbot.plugins.postgres import PgPlugin


@pytest.fixture
async def bot(request, loop):
    b = SirBot()
    pg = PgPlugin(
        dsn='postgres://postgres@127.0.0.1:5432/sirbot',
        sql_migration_directory='tests/data/sql',
        version='0.0.2',
    )
    b.load_plugin(pg)
    yield b


@pytest.mark.skipif(not pytest.config.getoption('--postgres'), reason='PostgreSQL testing not enabled')
class TestPluginPostgres:

    async def _teardown(self, bot):
        async with bot['plugins']['pg'].connection() as pg_con:
            await pg_con.execute('''DROP SCHEMA IF EXISTS sirbot_test CASCADE''')
            await pg_con.execute('''DROP TABLE IF EXISTS metadata''')

    async def test_start(self, bot, test_server):
        try:
            await test_server(bot)
            assert isinstance(bot['plugins']['pg'], PgPlugin)
        finally:
            await self._teardown(bot)

    async def test_no_migration(self, bot, test_server):
        try:
            bot['plugins']['pg'].sql_migration_directory = None
            await test_server(bot)

            with pytest.raises(asyncpg.exceptions.UndefinedTableError):
                async with bot['plugins']['pg'].connection() as pg_con:
                    await pg_con.fetchval('''SELECT db_version FROM metadata''')
        finally:
            await self._teardown(bot)

    async def test_initial_migration(self, bot, test_server):
        try:
            bot['plugins']['pg'].version = '0.0.1'
            await test_server(bot)
            async with bot['plugins']['pg'].connection() as pg_con:
                version = await pg_con.fetchval('''SELECT db_version FROM metadata''')
                count = await pg_con.fetchval('''SELECT count(*) FROM sirbot_test.hello''')

            assert version == '0.0.1'
            assert count == 0
        finally:
            await self._teardown(bot)

    async def test_migration_to_0_0_2(self, bot, test_server):
        try:
            await test_server(bot)

            async with bot['plugins']['pg'].connection() as pg_con:
                version = await pg_con.fetchval('''SELECT db_version FROM metadata''')
                await pg_con.execute('''INSERT INTO sirbot_test.foo (bar) VALUES ($1)''', 'baz')

            async with bot['plugins']['pg'].connection() as pg_con:
                baz = await pg_con.fetchval('''SELECT bar FROM sirbot_test.foo WHERE id = 1''')
                name = await pg_con.fetchval('''SELECT name FROM sirbot_test.hello WHERE id =1''')

            assert version == '0.0.2'
            assert baz == 'baz'
            assert name == 'world'
        finally:
            await self._teardown(bot)

    async def test_no_migration_needed(self, bot, test_server):
        try:
            bot['plugins']['pg'].version = '0.1.9'
            await test_server(bot)

            async with bot['plugins']['pg'].connection() as pg_con:
                count_start = await pg_con.fetchval('''SELECT count(*) FROM sirbot_test.hello''')

            await bot['plugins']['pg'].migrate()

            async with bot['plugins']['pg'].connection() as pg_con:
                count_end = await pg_con.fetchval('''SELECT count(*) FROM sirbot_test.hello''')

            assert count_end == count_start
            assert count_start == 2
        finally:
            await self._teardown(bot)

    async def test_failed_migration(self, bot, test_server):
        try:
            bot['plugins']['pg'].version = '0.2.0'

            with pytest.raises(asyncpg.exceptions.UndefinedColumnError):
                await test_server(bot)

            with pytest.raises(asyncpg.exceptions.UndefinedTableError):
                async with bot['plugins']['pg'].connection() as pg_con:
                    await pg_con.fetchval('''SELECT db_version FROM metadata''')
        finally:
            await self._teardown(bot)

    def test_find_sql_migration(self, bot):
        files = bot['plugins']['pg']._find_update_version([0, 0, 0], [0, 4, 6])
        assert files == ["0.0.2", "0.1.9", "0.1.12"]
