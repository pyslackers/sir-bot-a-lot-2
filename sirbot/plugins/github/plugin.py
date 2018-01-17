import os
import logging

from gidgethub import ValidationFailure
from gidgethub.aiohttp import GitHubAPI
from gidgethub.sansio import Event
from gidgethub.routing import Router

from aiohttp.web import Response

LOG = logging.getLogger(__name__)


class GithubPlugin:
    __name__ = 'github'

    def __init__(self, *, verify=None):
        self.api = None
        self.router = Router()
        self.verify = verify or os.environ['GITHUB_VERIFY']

    def load(self, sirbot):
        LOG.info('Loading github plugin')
        self.api = GitHubAPI(session=sirbot.http_session, requester=sirbot.user_agent)

        sirbot.router.add_route('POST', '/github', dispatch)


async def dispatch(request):
    github = request.app.plugins['github']
    payload = await request.read()

    try:
        event = Event.from_http(request.headers, payload, secret=github.verify)
        await github.router.dispatch(event, app=request.app)
    except ValidationFailure as e:
        LOG.debug('Github webhook failed verification: %s, %s', request.headers, payload)
        return Response(status=401)
    except Exception as e:
        LOG.exception(e)
        return Response(status=500)
    else:
        return Response(status=200)
