class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def asdict(self):
        return {"role": self.role, "content": self.content}

    def __repr__(self):
        return f"{self.role}: {self.content}"


class Convo:
    def __init__(self):
        self.messages = list()

    def push(self, message: Message):
        self.messages.append(message)

    def __repr__(self):
        return str(self.messages)
