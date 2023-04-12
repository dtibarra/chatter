from lib.chatter import Chatter
from models import ConfigRepository, PromptRepository
import sys
from prompt_toolkit import PromptSession
import asyncio

openai_key = asyncio.run(ConfigRepository.get_config_by_name("openapi_key"))

if not openai_key:
    print("omg no config")
    sys.exit(1)

prompt_text = asyncio.run(PromptRepository.get_prompt_by_name("txsysops"))

c = Chatter(openai_key, prompt_text)

chat_session = asyncio.run(c.new_session(1))
session = PromptSession()

while True:
    chat_input = session.prompt("> ")
    response_message = asyncio.run(chat_session.chat("user", chat_input))
    print(response_message.content)
