import logging

logging.basicConfig(level=logging.DEBUG, filename="chatter.log")

from lib.chatter import Chatter
import toml
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.starlette.async_handler import AsyncSlackRequestHandler

from slack_bolt.oauth.async_oauth_settings import AsyncOAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route
from collections import deque
from lib.util import LRUConvo
import openai

with open("config.toml", "r") as config_file:
    config = toml.load(config_file)

slack_bot_token = config["slack_config"]["SLACK_BOT_TOKEN"]
slack_signing_secret = config["slack_config"]["SLACK_SIGNING_SECRET"]

chatter = Chatter(config["openai_config"], config["prompt_config"])

app = AsyncApp(
    token=slack_bot_token,
    signing_secret=slack_signing_secret,
    ignoring_self_events_enabled=False,
)
app_handler = AsyncSlackRequestHandler(app)

# Could probably use something like langchain instead, but meh
recent_convo_lru = LRUConvo(200)


@app.middleware
async def log_request(logger, body, next):
    # middleware so that our bot can become aware of our user id, so that we can differentiate in the message event.
    # i believe the alternative to this hack is to go full on oauth to get access to the full suite of api calls, and that sounds awful.
    if not await chatter.get_id():
        await chatter.set_id(body["authorizations"][0]["user_id"])
    return await next()


# if someone mentions the app
@app.event("app_mention")
async def handle_app_mentions(body, say, logger):
    # the convo LRU is for storing top-level mentions of the bot, for the conversation feature to work.
    # if this mention is in a thread, and there's a convo attached to it, the bail, because we're gonna let
    # the message event capture this message.
    if "thread_ts" in body["event"]:
        convo = recent_convo_lru.convo_get(body["event"]["thread_ts"])
        if convo:
            return
    # try to get a completion and then reply to the mention either in a thread, or top-level message.
    try:
        response = await chatter.openai_response(
            body["event"]["user"], body["event"]["text"]
        )
    except openai.error.RateLimitError:
        response = "OpenAI is having problems, I can't respond right now :("
    if "thread_ts" in body["event"]:
        await say({"text": response, "thread_ts": body["event"]["thread_ts"]})
    else:
        await say(response)


@app.event("message")
async def handle_message_events(body, say, logger):
    # message event listens for all messages in a channel.
    # if a message comes from the bot's own user id, then we need to store the message in our LRU to maintain convo context.
    # check if it's a top level message, or a thread reply, and store accordingly.
    if body["event"]["user"] == await chatter.get_id():
        if "thread_ts" in body["event"]:
            # it's a chatter reply to a threaded convo
            recent_convo_lru.convo_push(
                body["event"]["thread_ts"],
                body["event"]["event_ts"],
                {"user": body["event"]["user"], "text": body["event"]["text"]},
            )
        else:
            # it's a top level chatter message
            recent_convo_lru.convo_push(
                body["event"]["ts"],
                body["event"]["event_ts"],
                {"user": body["event"]["user"], "text": body["event"]["text"]},
            )
    else:
        # if it's a non-chatter reply to a chatter thread, we need to fetch a completion and reply, and then store the response in the LRU.
        if "thread_ts" in body["event"]:
            convo = recent_convo_lru.convo_get(body["event"]["thread_ts"])
            if convo:
                try:
                    response = await chatter.openai_response(
                        body["event"]["user"],
                        body["event"]["text"],
                        recent_convo_lru.convo_render(body["event"]["thread_ts"]),
                    )
                except openai.error.RateLimitError:
                    response = "OpenAI is having problems, I can't respond right now :("
                else:
                    recent_convo_lru.convo_push(
                        body["event"]["thread_ts"],
                        body["event"]["event_ts"],
                        {"user": body["event"]["user"], "text": body["event"]["text"]},
                    )
                await say({"text": response, "thread_ts": body["event"]["thread_ts"]})


async def endpoint(req: Request):
    return await app_handler.handle(req)


api = Starlette(
    debug=False, routes=[Route("/slack/events", endpoint=endpoint, methods=["POST"])]
)
