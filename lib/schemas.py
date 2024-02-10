import re
class AIMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        if role == 'user':
            self.content = re.sub(r"<@[A-Z0-9]+>", "", content)
        else:
            self.content = content

    def asdict(self):
        return {"role": self.role, "content": self.content}

    def __repr__(self):
        return f"{self.role}: {self.content}"

class SlackMessage:
    def __init__(self, body: str):
        self.body = body
        self.text = None
        self.timestamp = None
        self.thread_timestamp = None
        self.source_user_id = None
        if 'event' in body:
            if 'ts' in body['event']:
                self.timestamp = body['event']['ts']
            if 'text' in body['event']:
                self.text = body["event"]["text"]
            if 'thread_ts' in body['event']:
                self.thread_timestamp = body["event"]['thread_ts']
            if 'user' in body['event']:
                self.source_user_id = body['event']['user']
            if 'channel' in body['event']:
                self.channel = body['event']['channel']

    def is_threaded_message(self,):
        if "thread_ts" in self.body["event"]:
            return True
    def __repr__(self):
        return f"{self.body}"

class Convo:
    def __init__(self):
        self.messages = list()

    def push(self, message: AIMessage):
        self.messages.append(message)

    def __repr__(self):
        return str(self.messages)


class TextResponse():
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return str(self.text)

    def to_slack_response(self):
        return {
            "text": self.text
        }

class ImageResponse():
    def __init__(self, image_data):
        self.image_data = image_data
