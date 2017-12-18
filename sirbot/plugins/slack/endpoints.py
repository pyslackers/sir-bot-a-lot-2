import asyncio
import logging

from slack.events import Event
from slack.commands import Command
from aiohttp.web import Response

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

    event = Event.from_http(payload, verification_token=slack.verify)

    if event['type'] == 'message':
        callbacks = await _incoming_message(event, request)
    else:
        callbacks = await _incoming_event(event, request)

    if callbacks:
        try:
            asyncio.wait(callbacks, return_when=asyncio.ALL_COMPLETED)
        except Exception as e:
            LOG.exception(e)
            return Response(status=500)

    return Response(status=200)


async def _incoming_event(event, request):
    LOG.debug('Incoming event: %s', event)
    slack = request.app.plugins['slack']
    callbacks = list()
    for callback in slack.routers['router'].dispatch(event):
        callbacks.append(asyncio.ensure_future(callback(event, request.app)))
    return callbacks


async def _incoming_message(event, request):
    slack = request.app.plugins['slack']
    if event.get('bot_id') == slack.bot_id or event.get('message', {}).get('bot_id') == slack.bot_id:
        return list()

    LOG.debug('Incoming message: %s', event)
    callbacks = list()
    mention = slack.bot_user_id in event.get('text', '') or event['channel'].startswith('D')
    if mention and 'text' in event:
        event['text'] = event['text'].strip('<@{}>'.format(slack.bot_user_id)).strip()

    for func, need_mention in slack.routers['message'].dispatch(event):
        if not need_mention or mention:
            callbacks.append(asyncio.ensure_future(func(event, request.app)))
    return callbacks


async def incoming_command(request):
    slack = request.app.plugins['slack']
    payload = await request.post()

    try:
        command = Command(payload, verification_token=slack.verify)
    except Exception as e:
        LOG.exception(e)
        raise

    callbacks = list()
    LOG.debug('Incoming command: %s', command)

    try:
        for callback in slack.routers['command'].dispatch(command):
            callbacks.append(asyncio.ensure_future(callback(command, request.app)))
        if callbacks:
            asyncio.wait(callbacks, return_when=asyncio.ALL_COMPLETED)
    except Exception as e:
        LOG.exception(e)
        return Response(status=500)
    else:
        return Response(status=200)
