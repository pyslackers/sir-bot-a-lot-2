import os
import logging

from gidgethub import ValidationFailure
from aiohttp.web import Response
from gidgethub.sansio import Event
from gidgethub.aiohttp import GitHubAPI
from gidgethub.routing import Router

LOG = logging.getLogger(__name__)


class GithubPlugin:
    """
    Handle GitHub webhook.
    The webhook must be set to ``<root_url>/github`` in your github account.

    Register a new event handler with:

    .. code-block:: python

        GithubPlugin.router.add(handler, event_type)

    **Endpoints**:
        * ``/github``: Github webhook.

    **Variables**:
        * **router**: Instance of :class:`gidgethub.routing.Router`.
        * **api**: Instance of :class:`gidgethub.aiohttp.GitHubAPI`.
    """

    __name__ = "github"

    def __init__(self, *, verify=None):
        self.api = None
        self.router = Router()
        self.verify = verify or os.environ["GITHUB_VERIFY"]

    def load(self, sirbot):
        LOG.info("Loading github plugin")
        self.api = GitHubAPI(session=sirbot.http_session, requester=sirbot.user_agent)

        sirbot.router.add_route("POST", "/github", dispatch)


async def dispatch(request):
    github = request.app.plugins["github"]
    payload = await request.read()

    try:
        event = Event.from_http(request.headers, payload, secret=github.verify)
        await github.router.dispatch(event, app=request.app)
    except ValidationFailure:
        LOG.debug(
            "Github webhook failed verification: %s, %s", request.headers, payload
        )
        return Response(status=401)
    except Exception as e:
        LOG.exception(e)
        return Response(status=500)
    else:
        return Response(status=200)
