from openai import AsyncOpenAI
import json
from collections import OrderedDict
from lib.schemas import AIMessage, Convo, TextResponse, ImageResponse
import requests
class Conversations:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    # return a convo
    def get(self, thread_timestamp: int) -> int:
        if thread_timestamp in self.cache:
            return self.cache[thread_timestamp]
        return None

    def exists(self, thread_timestamp: int) -> int:
        if thread_timestamp in self.cache:
            return True
        return False    

    def bump_thread(self, thread_timestamp: int) -> None:
        self.cache.move_to_end(thread_timestamp)

    # save a convo
    def create(self, thread_timestamp: int, message: AIMessage) -> None:
        if thread_timestamp not in self.cache:
            self.cache[thread_timestamp] = []
            self.cache[thread_timestamp].append(message)

    def append(self,thread_timestamp: int, message: AIMessage) -> None:
        self.cache[thread_timestamp].append(message)
        self.cache.move_to_end(thread_timestamp)

        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)


class Chatter:
    def __init__(self, openapi_key):
        self.o = AsyncOpenAI(api_key = openapi_key)
        self.tool_prompt = AIMessage("system", """You are bot who will always respond in the form of the following JSON:

        {"generate_image": false, "image_prompt": "", "generate_text": false}

        If a request seems like it is asking you to generate an image, set "generate_image" to true, and set "image_prompt" to what the user is requesting.
        For all other requests, set "generate_text" to true.""")

        self.chat_prompt = AIMessage("system", """You are a generic bot who is happy to respond to requests to the best of his abilities.""")
        self.conversations = Conversations(10)
        self.slack_id = None

    async def get_conversation(self, thread_timestamp):
        s = self.conversations.get(thread_timestamp)
        self.conversations.bump_thread(thread_timestamp)
        return s
    async def conversation_exists(self, thread_timestamp):
        if self.conversations.get(thread_timestamp):
            return True
        return False

    async def create_conversation(self, thread_timestamp, message: AIMessage):
        self.conversations.create(thread_timestamp, self.chat_prompt)
        self.conversations.append(thread_timestamp, message)
        
    async def append_conversation(self, thread_timestamp, message: AIMessage):
        self.conversations.append(thread_timestamp, message)

    async def process_message(self, message: AIMessage, chat_conversation = None):
        tool_prompt_response = await self.o.chat.completions.create(
            model="gpt-3.5-turbo", messages=[self.tool_prompt.asdict(), message.asdict()]
        )
        try:
            parsed_response = json.loads(tool_prompt_response.choices[0].message.content)
        except json.decoder.JSONDecodeError:
            parsed_response = {"generate_text": True}
        if "generate_text" in parsed_response and parsed_response["generate_text"] is True:
            if chat_conversation:
                messages = [m.asdict() for m in chat_conversation]
                messages.append(message.asdict()) 
            else:
                messages = [self.chat_prompt.asdict(), message.asdict()]
            chat_prompt_response = await self.o.chat.completions.create(
                model="gpt-4", messages=messages
            )
            text_response = TextResponse(chat_prompt_response.choices[0].message.content)
            return text_response
        elif "generate_image" in parsed_response and parsed_response["generate_image"] is True and "image_prompt" in parsed_response and parsed_response["image_prompt"]:
            image_prompt_response = await self.o.images.generate(
                model="dall-e-3", 
                prompt=parsed_response["image_prompt"],
                size="1024x1024",
                quality="standard",
                n=1
            )
            url = image_prompt_response.data[0].url
            image_response = ImageResponse(requests.get(url).content)
            return image_response

    async def set_id(self, id):
        self.slack_id = id

    async def get_id(self):
        return self.slack_id
