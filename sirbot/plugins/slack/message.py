import re
import asyncio
import logging
import itertools

from collections import defaultdict

LOG = logging.getLogger(__name__)


class MessageRouter:
    def __init__(self):
        self._routes = defaultdict(dict)

    def register(self, *, pattern, endpoint, flags=0, channel='*', mention=False):
        LOG.debug('Registering message endpoint "%s: %s"', pattern, endpoint)
        match = re.compile(pattern, flags)

        if not asyncio.iscoroutinefunction(endpoint):
            endpoint = asyncio.coroutine(endpoint)

        if match in self._routes[channel]:
            self._routes[channel][match].append((endpoint, mention))
        else:
            self._routes[channel][match] = [(endpoint, mention)]

    def dispatch(self, message):
        for match, endpoints in itertools.chain(self._routes[message['channel']].items(), self._routes['*'].items()):
            if 'text' in message and match.search(message['text']):
                yield from endpoints
            elif 'message' in message and match.search(message['message']['text']):
                yield from endpoints
