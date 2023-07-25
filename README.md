# Chatter Chat Bot

Chatter is a simple OpenAI chat bot for Slack that can have conversations with users. It is built using Python/starlette, slack_bolt, and openai.

## Usage

To use Chatter, you can add it to your Slack workspace. Once you mention the bot, it will respond to your message. If you reply to the bot, you can start a conversation without pinging the bot, and it will keep up with context.

## Features

Chatter currently has the following features:
  * Can support any publically available text model from OpenAI.
  * Responds when you ping the bot.
  * Carries a full conversation if you reply to the bot in a thread.
  * Can continue replying in a thread if you restart the daemon.

Chatter currently has these issues:
  * Conversation LRU cache is set to 100. If it has too many top level messages, some old conversation contexts will get evicted.
  * On that note, if you restart Chatter, it'll forget all conversations, so it won't understand the conversation in existing threads.
  * Chatter will only take the last 4 messages into account, so lengthy conversations will eventually drift off topic.
  * Prompt config is needlessly bulky, probably could do with removing all of these example conversations in a future release.
  * There is currently a bug with threads. If I @ chatter, and chatter replies, and then I reply to chatter in a thread, the context of the conversation is localized to only messages in the thread, which doesn't pull in the very first @ message. In my opinion, it should pull in the originating message as well.

## Getting Started

If you want to run Chatter locally or make changes to the code, follow these steps:
  * Install Python (starlette needs 3.7+, so probably start there.)
  * Clone this repository.
  * Make a venv, e.g. `python3 -m venv .venv`
  * Enter the venv, e.g. `source .venv/bin/activate`
  * `pip install -r requirements.txt`
  * If you want to use systemd, check my systemd unit files, you may need to adjust paths.
  * I deploy this with nginx. I make an upstream, e.g. `server unix:/run/gunicorn.sock fail_timeout=0;`, and then proxy_pass to that upstream.
  * Follow these steps to hook it up to your workspace: https://api.slack.com/start/building/bolt-python
  * App defaults to using the `gpt-4` model by default, this can be overriden with GPT_MODEL environment variable.
  * On first start, the app will create an empty database with `null` values if none have been specified via ENV. You can either inject them using environment variables as mentioned below, or just manually insert your values into the sqlite db. 

## Running in docker/k8s

The included dockerfile should get you a usable image. You'll need to build it and push it to a registry. Some things to note:
  * By defaujlt, the containerized version of the bot will output to STDOUT to fit into k8s a little nicer. If you want to override this and log to /app/chatter.log, override the ENV variable `STDOUT_LOGGING` to anything other than `true` on deployment.
  * Persistence is stored in `/var/lib/chatter/chatter.db` by default, you'll need to mount this directory from a persistent volume if you want the configuration to pursist over restarts. 
  * App Config can be defined via the environment variables:
    - SLACK_BOT_TOKEN
    - SLACK_SIGNING_SECRET
    - OPENAI_KEY
    - PROMPT_TEXT

## Contributing

If you want to contribute to Chatter, please follow these steps:
  * Fork this repository
  * Create a new branch for your changes
  * Make your changes and commit them
  * Push your changes to your forked repository
  * Submit a pull request to this repository

## License
GNU Affero General Public License version 3
