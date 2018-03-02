import asyncio
import logging

from aiohttp.web import Response

LOG = logging.getLogger(__name__)


class RTDPlugin:
    __name__ = 'readthedocs'

    def __init__(self):

        self._projects = {}
        self._session = None

    def load(self, sirbot):
        LOG.info('Loading read the docs plugin')
        sirbot.router.add_route('POST', '/readthedocs', incoming_notification)
        self._session = sirbot['http_session']

    async def build(self, project, branch='latest'):
        url = self._projects[project]['build_url']
        token = self._projects[project]['jeton']
        return await self._session.post(url, json={'branch': branch, 'token': token})

    def register_project(self, project, build_url, jeton, handlers=None):
        if project not in self._projects:
            self._projects[project] = {}

        if handlers:
            self._projects[project]['handlers'] = handlers
        elif 'handlers' not in self._projects[project]:
            self._projects[project]['handlers'] = []

        self._projects[project]['build_url'] = build_url
        self._projects[project]['jeton'] = jeton

    def register_handler(self, project, handler):
        if project not in self._projects:
            self._projects[project] = {'handlers': [handler, ]}
        else:
            self._projects[project]['handlers'].append(handler)

    def dispatch(self, payload):
        for handler in self._projects[payload['slug']].get('handlers', []):
            yield handler


async def incoming_notification(request):
    try:
        payload = await request.json()
    except Exception as e:
        LOG.debug(e)
        return Response(status=400)

    if 'build' not in payload or 'success' not in payload['build'] or 'slug' not in payload:
        return Response(status=400)

    LOG.debug('Incoming readthedocs notification: %s', payload)
    handlers = []

    try:
        for handler in request.app['plugins']['readthedocs'].dispatch(payload):
            handlers.append(handler(payload, request.app))
    except KeyError:
        return Response(status=400)

    if handlers:
        finished, _ = await asyncio.wait(handlers, return_when=asyncio.ALL_COMPLETED)
        for f in finished:
            f.result()

    return Response(status=200)
