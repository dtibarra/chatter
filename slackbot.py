import os
import logging

if os.getenv("STDOUT_LOGGING") != "true":
    logging.basicConfig(level=logging.DEBUG, filename="chatter.log")
else:
    logging.basicConfig(level=logging.DEBUG)
import asyncio
from lib.chatter import Chatter
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.starlette.async_handler import AsyncSlackRequestHandler
from models import ConfigRepository, PromptRepository

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route
import openai
from lib.schemas import AIMessage, SlackMessage, TextResponse, ImageResponse

slack_bot_token = asyncio.run(ConfigRepository.get_config_by_name("slack_bot_token"))
slack_signing_secret = asyncio.run(
    ConfigRepository.get_config_by_name("slack_signing_secret")
)
openai_key = asyncio.run(ConfigRepository.get_config_by_name("openapi_key"))
prompt_text = asyncio.run(PromptRepository.get_prompt_by_name("default"))

chatter = Chatter(openai_key)

app = AsyncApp(
    token=slack_bot_token,
    signing_secret=slack_signing_secret,
    ignoring_self_events_enabled=False,
)

app_handler = AsyncSlackRequestHandler(app)

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
    slack_message = SlackMessage(body)
    #handle in the message function
    if slack_message.is_threaded_message():
        return
    try:
        response = await chatter.process_message(
            AIMessage("user", slack_message.text)
        )
    except openai.RateLimitError:
        response = TextResponse("OpenAI is having problems, I can't respond right now :(")
    except openai.BadRequestError:
        response = TextResponse("OpenAI won't let me respond to that :(")
    if type(response) is ImageResponse: 
        await app.client.files_upload(channels=slack_message.channel, file=response.image_data, filename="dalle3-result.png",filetype="png")
    else: 
        await say(response.to_slack_response())

@app.event("message")
async def handle_message_events(body, say, logger):
    slack_message = SlackMessage(body)
    logger.info(body)
    if slack_message.source_user_id == await chatter.get_id():
        # if a top level chatter message comes our way, we need to remember it for future conversations.
        if not slack_message.is_threaded_message():
            # it's a top level chatter message, we need to go ahead and remember this convo
            await chatter.create_conversation(
                slack_message.timestamp, AIMessage("assistant", slack_message.text)
            )
    else:
        # if it's a non-chatter reply to a thread, we need to fetch a completion and reply, and then store the response in the LRU.
        if slack_message.is_threaded_message():
            # if chatter can remember the conversation, then build a session from it and then chat with it
            if await chatter.conversation_exists(slack_message.thread_timestamp):
                chat_conversation = await chatter.get_conversation(slack_message.thread_timestamp)
                if chat_conversation:
                    try:
                        response = await chatter.process_message(
                            AIMessage("user", slack_message.text),
                            chat_conversation
                        )
                    except openai.RateLimitError:
                        response = TextResponse("OpenAI is having problems, I can't respond right now :(")
                    except openai.BadRequestError:
                        response = TextResponse("OpenAI won't let me respond to that :(")
                    else:
                        await chatter.append_conversation(slack_message.thread_timestamp, AIMessage("user", slack_message.text))
                        await chatter.append_conversation(slack_message.thread_timestamp, AIMessage("assistant", response))
                        response['thread_ts'] = slack_message.thread_timestamp
                        await say(response)


async def endpoint(req: Request):
    return await app_handler.handle(req)

api = Starlette(
    debug=False, routes=[Route("/slack/events", endpoint=endpoint, methods=["POST"])]
)
