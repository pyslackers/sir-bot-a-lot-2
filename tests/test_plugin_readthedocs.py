import pytest
import asynctest

from sirbot import SirBot
from sirbot.plugins.readthedocs import RTDPlugin


@pytest.fixture
async def bot():
    b = SirBot()
    b.load_plugin(RTDPlugin())
    return b


class TestPluginReadTheDocs:
    async def test_start(self, bot, test_server):
        await test_server(bot)
        assert isinstance(bot['plugins']['readthedocs'], RTDPlugin)

    async def test_register_project(self, bot):
        bot['plugins']['readthedocs'].register_project('test', build_url='https://example.com', jeton='aaaaaa')
        assert 'test' in bot['plugins']['readthedocs']._projects

    async def test_build_project(self, bot):
        bot['plugins']['readthedocs']._session.post = asynctest.CoroutineMock()
        bot['plugins']['readthedocs'].register_project('test', build_url='https://example.com', jeton='aaaaaa')
        await bot['plugins']['readthedocs'].build('test')

        assert bot['plugins']['readthedocs']._session.post.call_count == 1
        bot['plugins']['readthedocs']._session.post.assert_called_with(
            'https://example.com', json={'branch': 'latest', 'token': 'aaaaaa'}
        )

    async def test_build_project_branch(self, bot):
        bot['plugins']['readthedocs']._session.post = asynctest.CoroutineMock()
        bot['plugins']['readthedocs'].register_project('test', build_url='https://example.com', jeton='aaaaaa')
        await bot['plugins']['readthedocs'].build('test', branch='dev')

        assert bot['plugins']['readthedocs']._session.post.call_count == 1
        bot['plugins']['readthedocs']._session.post.assert_called_with(
            'https://example.com', json={'branch': 'dev', 'token': 'aaaaaa'}
        )

    async def test_register_handler(self, bot):
        def handler():
            pass

        bot['plugins']['readthedocs'].register_handler('test', handler)

        h = []
        for f in bot['plugins']['readthedocs'].dispatch({'slug': 'test'}):
            h.append(f)

        assert len(h) == 1
        assert h[0] is handler

    async def test_register_multiple_handlers(self, bot):
        def handler():
            pass

        def handler_bis():
            pass

        bot['plugins']['readthedocs'].register_handler('test', handler)
        bot['plugins']['readthedocs'].register_handler('test', handler_bis)

        h = []
        for f in bot['plugins']['readthedocs'].dispatch({'slug': 'test'}):
            h.append(f)

        assert len(h) == 2
        assert h[0] is handler
        assert h[1] is handler_bis

    async def test_register_handler_then_project(self, bot):
        def handler():
            pass

        bot['plugins']['readthedocs'].register_handler('test', handler)
        bot['plugins']['readthedocs'].register_project('test', build_url='https://example.com', jeton='aaaaaa')

        h = []
        for f in bot['plugins']['readthedocs'].dispatch({'slug': 'test'}):
            h.append(f)

        assert len(h) == 1
        assert h[0] is handler
        assert 'test' in bot['plugins']['readthedocs']._projects

    async def test_register_project_then_handler(self, bot):
        def handler():
            pass

        bot['plugins']['readthedocs'].register_project('test', build_url='https://example.com', jeton='aaaaaa')
        bot['plugins']['readthedocs'].register_handler('test', handler)

        h = []
        for f in bot['plugins']['readthedocs'].dispatch({'slug': 'test'}):
            h.append(f)

        assert len(h) == 1
        assert h[0] is handler
        assert 'test' in bot['plugins']['readthedocs']._projects

    async def test_register_project_and_handlers(self, bot):
        def handler():
            pass

        def handler_bis():
            pass

        bot['plugins']['readthedocs'].register_project(
            'test', build_url='https://example.com', jeton='aaaaaa', handlers=[handler, handler_bis]
        )

        h = []
        for f in bot['plugins']['readthedocs'].dispatch({'slug': 'test'}):
            h.append(f)

        assert len(h) == 2
        assert h[0] is handler
        assert h[1] is handler_bis
        assert 'test' in bot['plugins']['readthedocs']._projects

    async def test_incoming(self, bot, test_client):
        async def handler(payload, app):
            assert payload == {
                'build': {'date': '2018-03-02 11:33:05', 'id': 6831644, 'success': False},
                'name': 'Sir Bot-a-lot',
                'slug': 'sir-bot-a-lot'
            }
            assert app is bot

        client = await test_client(bot)
        bot['plugins']['readthedocs'].register_handler('sir-bot-a-lot', handler=handler)

        r = await client.post('/readthedocs', json={
            'build': {'date': '2018-03-02 11:33:05', 'id': 6831644, 'success': False},
            'name': 'Sir Bot-a-lot',
            'slug': 'sir-bot-a-lot'
        })
        assert r.status == 200

    async def test_incoming_handler_error(self, bot, test_client):
        async def handler(payload, app):
            raise RuntimeError()

        client = await test_client(bot)
        bot['plugins']['readthedocs'].register_handler('sir-bot-a-lot', handler=handler)

        r = await client.post('/readthedocs', json={
            'build': {'date': '2018-03-02 11:33:05', 'id': 6831644, 'success': False},
            'name': 'Sir Bot-a-lot',
            'slug': 'sir-bot-a-lot'
        })
        assert r.status == 500

    async def test_incoming_no_project(self, bot, test_client):
        client = await test_client(bot)
        r = await client.post('/readthedocs', json={
            'build': {'date': '2018-03-02 11:33:05', 'id': 6831644, 'success': False},
            'name': 'Sir Bot-a-lot',
            'slug': 'sir-bot-a-lot'
        })
        assert r.status == 400

    async def test_incoming_project_no_handler(self, bot, test_client):
        client = await test_client(bot)
        bot['plugins']['readthedocs'].register_project('sir-bot-a-lot', build_url='https://example.com', jeton='aaaaaa')
        r = await client.post('/readthedocs', json={
            'build': {'date': '2018-03-02 11:33:05', 'id': 6831644, 'success': False},
            'name': 'Sir Bot-a-lot',
            'slug': 'sir-bot-a-lot'
        })
        assert r.status == 200

    async def test_incoming_bad_json(self, bot, test_client):
        client = await test_client(bot)
        r = await client.post('/readthedocs', json={'a': 'b'})
        assert r.status == 400

        r = await client.post('/readthedocs', json={
            'build': {'date': '2018-03-02 11:33:05', 'id': 6831644, 'success': False},
            'name': 'Sir Bot-a-lot'
        })
        assert r.status == 400
