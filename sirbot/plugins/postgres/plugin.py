import os
import ujson
import logging
import asyncpg
import aiofiles

from aiocontext import async_contextmanager

LOG = logging.getLogger(__name__)


class PgPlugin:
    __name__ = 'pg'

    def __init__(self, *, sql_migration_directory=None, version=None, **kwargs):
        self.pool_kwargs = kwargs
        self.pool = None
        self.version = version

        if sql_migration_directory:
            if not os.path.isabs(sql_migration_directory):
                sql_migration_directory = os.path.abspath(sql_migration_directory)
            self.sql_migration_directory = sql_migration_directory
        else:
            self.sql_migration_directory = None

    def load(self, sirbot):
        LOG.info('Loading postgres plugin')
        sirbot.on_startup.insert(0, self.startup)
        sirbot.on_shutdown.append(self.shutdown)

    async def startup(self, sirbot):
        self.pool = await asyncpg.create_pool(**self.pool_kwargs, init=self._init_connection)
        if self.sql_migration_directory and self.version:
            await self.migrate()

    async def shutdown(self, sirbot):
        await self.pool.close()

    @async_contextmanager
    async def connection(self):
        async with self.pool.acquire() as pg_con:
            yield pg_con

    async def migrate(self):
        LOG.info('Start of database migration')
        current_version = [int(n) for n in self.version.split('.')]
        async with self.connection() as connection:
            old_version = await self._check_database_version(connection)

            if current_version != old_version:
                async with connection.transaction():
                    if old_version is None:
                        await self._init_database(connection)
                        old_version = [0, 0, 0]

                    for version in self._find_update_version(start=old_version, end=current_version):
                        await self._execute_sql_file(connection, version)

                    await self._update_db_version(connection, current_version)
                    LOG.info('End of database migration')

    def _find_update_version(self, start, end):
        files = []
        for file in os.listdir(self.sql_migration_directory):
            if file == 'init.sql':
                continue

            name, _ = os.path.splitext(file)
            file_version = [int(n) for n in name.split('.')]
            if end >= file_version > start:
                files.append(file_version)
        files = sorted(files)
        files = ['.'.join(str(l) for l in f) for f in files]
        LOG.debug('Database migration versions: %s', files)
        return files

    async def _init_database(self, connection):
        LOG.debug('Executing initial migration')
        await connection.execute('''
                          CREATE TABLE metadata (db_version TEXT);
                          INSERT INTO metadata (db_version) VALUES ('0.0.0');
        ''')
        if os.path.exists(os.path.join(self.sql_migration_directory, 'init.sql')):
            await self._execute_sql_file(connection, 'init')

    async def _execute_sql_file(self, connection, version):
        LOG.debug('Database migration to version %s: STARTED', version)
        async with aiofiles.open(os.path.join(self.sql_migration_directory, f'{version}.sql'), mode='r') as f:
            await connection.execute((await f.read()))
        LOG.debug('Database migration to version %s: OK', version)

    @staticmethod
    async def _check_database_version(connection):
        try:
            metadata = await connection.fetchrow('''SELECT * FROM metadata''')
            return [int(n) for n in metadata['db_version'].split('.')]
        except asyncpg.exceptions.UndefinedTableError:
            LOG.debug('No "metadata" table found in database')

    @staticmethod
    async def _update_db_version(connection, version):
        await connection.execute('''UPDATE metadata SET db_version=$1''', '.'.join(str(l) for l in version))

    async def _init_connection(self, connection):
        await connection.set_type_codec(
            'jsonb', encoder=self._json_encoder, decoder=self._json_decoder, schema='pg_catalog'
        )

    @staticmethod
    def _json_encoder(value):
        return ujson.dumps(value)

    @staticmethod
    def _json_decoder(value):
        return ujson.loads(value)
