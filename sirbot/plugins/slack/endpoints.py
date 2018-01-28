import asyncio
import logging

from aiohttp.web import Response
from slack.events import Event
from slack.actions import Action
from slack.commands import Command
from slack.exceptions import FailedVerification

LOG = logging.getLogger(__name__)


async def incoming_event(request):
    slack = request.app.plugins['slack']
    payload = await request.json()
    LOG.log(5, 'Incoming event payload: %s', payload)

    if 'challenge' in payload:
        if payload['token'] == slack.verify:
            return Response(body=payload['challenge'])
        else:
            return Response(status=500)

    try:
        event = Event.from_http(payload, verification_token=slack.verify)
    except FailedVerification:
        return Response(status=401)

    if event['type'] == 'message':
        return await _incoming_message(event, request)
    else:
        return await _wait_for_handler(slack.routers['event'], event, request.app)


async def _incoming_message(event, request):
    slack = request.app.plugins['slack']

    if slack.bot_id and (event.get('bot_id') == slack.bot_id or event.get('message', {}).get('bot_id') == slack.bot_id):
        return Response(status=200)

    LOG.debug('Incoming message: %s', event)
    text = event.get('text')
    if slack.bot_user_id and text:
        mention = slack.bot_user_id in event['text'] or event['channel'].startswith('D')
    else:
        mention = False

    if mention and text:
        event['text'] = event['text'].strip(f'<@{slack.bot_user_id}>').strip()

    coro = []
    for handler, configuration in slack.routers['message'].dispatch(event):
        if configuration['mention'] and not mention:
            continue
        elif configuration['admin'] and event['user'] not in slack.admins:
            continue

        f = asyncio.ensure_future(handler(event, request.app))
        if configuration['wait']:
            coro.append(f)
        else:
            f.add_done_callback(_callback)

    return await _run_coroutines(coro)


async def incoming_command(request):
    slack = request.app.plugins['slack']
    payload = await request.post()

    try:
        command = Command(payload, verification_token=slack.verify)
    except FailedVerification:
        return Response(status=401)

    LOG.debug('Incoming command: %s', command)
    return await _wait_for_handler(slack.routers['command'], command, request.app)


async def incoming_action(request):
    slack = request.app.plugins['slack']
    payload = await request.post()
    LOG.log(5, 'Incoming action payload: %s', payload)

    try:
        action = Action.from_http(payload, verification_token=slack.verify)
    except FailedVerification:
        return Response(status=401)

    LOG.debug('Incoming action: %s', action)
    return await _wait_for_handler(slack.routers['action'], action, request.app)


def _callback(f):
    try:
        f.result()
    except Exception as e:
        LOG.exception(e)


async def _wait_for_handler(router, event, app):
    coro = list()
    for handler, configuration in router.dispatch(event):
        f = asyncio.ensure_future(handler(event, app))
        if configuration['wait']:
            coro.append(f)
        else:
            f.add_done_callback(_callback)

    return await _run_coroutines(coro)


async def _run_coroutines(coroutines=None):
    try:
        if coroutines:
            futures, _ = await asyncio.wait(coroutines, return_when=asyncio.ALL_COMPLETED)
            for f in futures:
                f.result()
    except Exception as e:
        LOG.exception(e)
        return Response(status=500)

    return Response(status=200)
