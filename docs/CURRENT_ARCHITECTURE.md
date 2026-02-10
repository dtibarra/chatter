# Chatter - Current Architecture Overview

## What Is Chatter?

Chatter is a Slack chatbot powered by OpenAI that can have threaded conversations
and generate images via DALL-E 3. It's built in Python (~450 lines) using Starlette
as the web framework and slack-bolt for Slack event handling.

## How It Works (Request Flow)

```
Slack Event (mention or thread reply)
        │
        ▼
┌─────────────────────────────────────┐
│  Starlette ASGI App (slackbot.py)   │
│  POST /slack/events                 │
│  ┌───────────────────────────────┐  │
│  │  slack-bolt AsyncApp          │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ Middleware: set bot ID  │  │  │
│  │  └────────────┬────────────┘  │  │
│  │               │               │  │
│  │  ┌────────────▼────────────┐  │  │
│  │  │ @app.event("app_mention")│ │  │
│  │  │ - New conversation       │ │  │
│  │  │ - Skip if threaded       │ │  │
│  │  └────────────┬────────────┘  │  │
│  │               │               │  │
│  │  ┌────────────▼────────────┐  │  │
│  │  │ @app.event("message")   │  │  │
│  │  │ - Thread replies         │  │  │
│  │  │ - Bot self-awareness     │  │  │
│  │  │ - LRU conversation ctx   │  │  │
│  │  └────────────┬────────────┘  │  │
│  └───────────────┼───────────────┘  │
└──────────────────┼──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Chatter Core (lib/chatter.py)      │
│                                     │
│  1. Route: GPT-3.5 classifies       │
│     intent (text vs image)          │
│                                     │
│  2a. Text → GPT-4 completion        │
│      with conversation history      │
│                                     │
│  2b. Image → DALL-E 3 generation    │
│      → HTTP download → binary       │
│                                     │
│  Conversations: OrderedDict LRU     │
│  (capacity=10, RAM only)            │
└─────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  OpenAI API                         │
│  - gpt-3.5-turbo (routing)          │
│  - gpt-4 (chat, configurable)       │
│  - dall-e-3 (images)                │
└─────────────────────────────────────┘
```

## File Structure

```
chatter/
├── slackbot.py          # Entry point: Starlette + slack-bolt app
│                        #   - Event handlers for mentions and messages
│                        #   - Bootstraps config from DB via asyncio.run()
│
├── models.py            # SQLAlchemy async models + repositories
│                        #   - Config: stores API keys in SQLite
│                        #   - Prompt: stores system prompts
│                        #   - Runs init_models() at import time (!)
│
├── cli.py               # Interactive CLI for local testing
│
├── lib/
│   ├── chatter.py       # Core bot logic
│   │                    #   - Conversations class (LRU via OrderedDict)
│   │                    #   - Chatter class (routing + completions)
│   │
│   ├── schemas.py       # Data classes
│   │                    #   - AIMessage, SlackMessage
│   │                    #   - TextResponse, ImageResponse
│   │                    #   - Convo (unused)
│   │
│   ├── util.py          # Dead code (unused LRUConvo class)
│   └── async_serve.py   # Dead code (unused uvicorn runner)
│
├── requirements.txt     # Flat dependency list (no versions pinned)
├── Dockerfile           # Python 3.11.4 + gunicorn/uvicorn
├── systemd/             # systemd unit files for deployment
├── .gitignore
├── README.md
└── LICENSE              # AGPL-3.0
```

## Key Design Decisions (and Problems)

### Configuration
- API keys stored in SQLite via SQLAlchemy async ORM
- Environment variables override DB values on startup
- `asyncio.run()` called at module import time (blocks, fragile)
- Typo: stored as `openapi_key` instead of `openai_key`

### Conversation Memory
- RAM-only OrderedDict LRU cache (capacity: 10 conversations)
- Lost on restart
- No persistence layer for conversation history
- Only system prompt + last few messages kept in context

### AI Integration
- Direct OpenAI API calls (no framework/abstraction)
- GPT-3.5-turbo used as a "router" via JSON prompt hacking
- No proper tool/function calling (uses string-based JSON parsing)
- No streaming, no retry logic, no token tracking
- Synchronous HTTP for image downloads (`requests.get`)

### Error Handling
- Catches `RateLimitError` and `BadRequestError` only
- No logging of errors, no metrics, no health checks
- Silent failures possible (e.g., image generation returns None)

### Deployment
- Gunicorn + Uvicorn workers
- Starlette receives Slack webhook POSTs
- No Socket Mode (requires public HTTP endpoint)
- No health check endpoint

## What's Missing

- **No tests** of any kind
- **No type hints** (except a few scattered ones)
- **No proper packaging** (no pyproject.toml, no versioning)
- **No long-term memory** (conversations vanish on restart)
- **No tool calling** (MCP, function calling, or otherwise)
- **No reasoning** (single-shot prompt → response)
- **No web UI** for management
- **No observability** (no structured logging, no tracing)
- **Dead code** in util.py and async_serve.py
