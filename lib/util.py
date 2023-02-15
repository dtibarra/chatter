from collections import OrderedDict

# conversation LRU. Prob could replace some of this with langchain, but this will work for now.
class LRUConvo:
    # initialising capacity
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def convo_get(self, key: int) -> int:
        if key not in self.cache:
            return False
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def convo_push(self, parent_key: int, child_key: int, value: int) -> None:
        if parent_key not in self.cache:
            self.cache[parent_key] = OrderedDict([(child_key, value)])
        else:
            self.cache[parent_key][child_key] = value
        self.cache.move_to_end(parent_key)

        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def convo_render(self, key: int) -> str:
        conversation = self.convo_get(key)
        if not conversation:
            return False
        conversation_portion = []
        while len(conversation) > 0 and len(conversation_portion) < 4:
            conversation_portion.insert(0, conversation.popitem())
        rendered_text = ""
        for message in conversation_portion:
            rendered_text += f"<{message[1]['user']}>: {message[1]['text']}\n"
        return rendered_text
