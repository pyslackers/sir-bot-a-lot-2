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
        callbacks = list(_incoming_message(event, request))
    else:
        callbacks = list(_incoming_event(event, request))

    if callbacks:
        try:
            asyncio.wait(callbacks, return_when=asyncio.ALL_COMPLETED)
        except Exception as e:
            LOG.exception(e)
            return Response(status=500)

    return Response(status=200)


def _incoming_event(event, request):
    LOG.debug('Incoming event: %s', event)
    slack = request.app.plugins['slack']
    for handler in slack.routers['event'].dispatch(event):
        yield asyncio.ensure_future(handler(event, request.app))


def _incoming_message(event, request):
    slack = request.app.plugins['slack']
    if event.get('bot_id') == slack.bot_id or event.get('message', {}).get('bot_id') == slack.bot_id:
        return

    LOG.debug('Incoming message: %s', event)
    mention = slack.bot_user_id in event.get('text', '') or event['channel'].startswith('D')

    if mention and 'text' in event:
        event['text'] = event['text'].strip('<@{}>'.format(slack.bot_user_id)).strip()

    for handler in slack.routers['message'].dispatch(event):
        option = slack.handlers_option[handler]
        if option['mention'] and not mention:
            continue
        elif option['admin'] and event['user'] not in slack.admins:
            continue

        yield asyncio.ensure_future(handler(event, request.app))


async def incoming_command(request):
    slack = request.app.plugins['slack']
    payload = await request.post()

    try:
        command = Command(payload, verification_token=slack.verify)
    except FailedVerification:
        return Response(status=401)

    LOG.debug('Incoming command: %s', command)
    callbacks = list()
    for callback in slack.routers['command'].dispatch(command):
        callbacks.append(asyncio.ensure_future(callback(command, request.app)))

    if callbacks:
        try:
            asyncio.wait(callbacks, return_when=asyncio.ALL_COMPLETED)
        except Exception as e:
            LOG.exception(e)
            return Response(status=500)

    return Response(status=200)


async def incoming_actions(request):
    slack = request.app.plugins['slack']
    payload = await request.post()
    LOG.log(5, 'Incoming action payload: %s', payload)

    try:
        action = Action.from_http(payload, verification_token=slack.verify)
    except FailedVerification:
        return Response(status=401)

    LOG.debug('Incoming action: %s', action)
    callbacks = list()
    for callback in slack.routers['action'].dispatch(action):
        callbacks.append(asyncio.ensure_future(callback(action, request.app)))

    if callbacks:
        try:
            asyncio.wait(callbacks, return_when=asyncio.ALL_COMPLETED)
        except Exception as e:
            LOG.exception(e)
            return Response(status=500)

    return Response(status=200)
