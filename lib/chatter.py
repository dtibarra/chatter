import openai

SEPARATOR_TOKEN = ""


class Chatter:
    def __init__(self, openai_config, openai_prompt_config):
        self.openai_config = openai_config
        openai.api_key = self.openai_config["OPENAI_KEY"]
        self.openai_prompt_config = openai_prompt_config
        self.user_id = None

    async def render_prompt(
        self, requesting_user, requesting_message, conversation_context=None
    ):
        # Prompt
        template = f"System: Instructions for {self.openai_prompt_config['bot_name']}: {self.openai_prompt_config['instructions']}\n"
        # Example conversations. Might want to remove these, they do help add flavor to the bot, but they increase my openai bill.
        template += "System: Example conversations:\n"
        for example_convo in self.openai_prompt_config["example_conversations"]:
            for example_message in example_convo["messages"]:
                template += f"<@{example_message['user']}>: {example_message['text']}\n"
            template += "\n"
        # Current conversation.
        template += f"System: Current conversation:\n"
        if conversation_context:
            template += conversation_context
        template += f"<@{requesting_user}>: {requesting_message}\n"
        if self.user_id:
            template += f"<@{self.user_id}>:"
        else:
            template += f"<@{self.openai_prompt_config['bot_name']}>:"

        return template

    async def get_id(self):
        return self.user_id

    async def set_id(self, user_id):
        self.user_id = user_id

    async def openai_response(
        self, requesting_user, message, conversation_context=None
    ):
        prompt = await self.render_prompt(
            requesting_user, message, conversation_context
        )
        # generate response. Note the stop sequence, it should prevent the bot from hallucinating more of a conversaton.
        response = openai.Completion.create(
            engine=self.openai_config["OPENAI_MODEL"],
            prompt=prompt,
            temperature=1.0,
            top_p=0.9,
            max_tokens=512,
            stop="\n<@",
        )

        return response.choices[0].text.strip()
