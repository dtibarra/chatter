# Chatter

An agentic Slack chatbot with MCP tool integration, long-term memory, and a web admin UI.

Built with **PydanticAI** for the agent core, **MCP** (Model Context Protocol) for extensible tool calling, **ChromaDB** for persistent long-term memory, and **FastAPI** for the admin dashboard.

## Features

- **Agentic reasoning** - Multi-step ReAct loop powered by PydanticAI. The bot thinks, uses tools, observes results, and iterates before responding.
- **MCP tool integration** - Connect any MCP-compatible server (web search, file access, databases, custom tools). Configure via the web UI.
- **Long-term memory** - Episodic memory (conversation history) and semantic memory (extracted facts) stored in ChromaDB. Persists across restarts.
- **Configurable soul** - Edit the bot's personality, behavior rules, and system prompts through the web UI. Create and switch between multiple personas.
- **Web admin dashboard** - Browse memories, edit the soul, manage MCP tools, view conversation history, and check settings. Built with Tailwind CSS + DaisyUI + HTMX.
- **Slack Socket Mode** - WebSocket-based connection, no public HTTP endpoint needed. Works behind firewalls.
- **Model agnostic** - Supports OpenAI, Anthropic, Google Gemini, Ollama, and more via PydanticAI.
- **Persistent conversations** - Full conversation history stored in SQLite/PostgreSQL. Threads survive restarts.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/dtibarra/chatter.git
cd chatter
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your API keys

# Initialize the database
python -m chatter init-db

# Start everything (web UI + Slack bot)
python -m chatter run
```

The web admin UI will be available at `http://localhost:8080`.

## Commands

```bash
python -m chatter run        # Start web UI + Slack bot
python -m chatter web        # Start only the web UI
python -m chatter slack      # Start only the Slack bot
python -m chatter init-db    # Initialize database tables
```

## Configuration

All configuration is done via environment variables or a `.env` file. See `.env.example` for all options.

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_MODEL` | PydanticAI model string | `openai:gpt-4o` |
| `LLM_API_KEY` | API key for your LLM provider | |
| `SLACK_BOT_TOKEN` | Slack bot token (`xoxb-...`) | |
| `SLACK_APP_TOKEN` | Slack app token for Socket Mode (`xapp-...`) | |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite+aiosqlite:///chatter.db` |
| `CHROMADB_PATH` | Path for ChromaDB storage | `./chroma_data` |
| `BRAVE_SEARCH_API_KEY` | API key for Brave Search MCP server | |
| `WEB_HOST` | Web UI bind address | `0.0.0.0` |
| `WEB_PORT` | Web UI port | `8080` |
| `SECRET_KEY` | Session secret key | `change-me-in-production` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Slack App Setup

1. Create a new Slack app at https://api.slack.com/apps
2. Enable **Socket Mode** and generate an app-level token (`xapp-...`)
3. Add a bot user and get the bot token (`xoxb-...`)
4. Add these bot scopes: `channels:history`, `app_mentions:read`, `chat:write`, `files:write`
5. Subscribe to events: `app_mention`, `message.channels`
6. Install the app to your workspace

## Docker

```bash
# Build and run
docker compose up -d

# Or manually
docker build -t chatter .
docker run -d --env-file .env -p 8080:8080 -v chatter-data:/var/lib/chatter chatter
```

Data is persisted in `/var/lib/chatter` (SQLite database + ChromaDB storage).

## Architecture

```
Slack (Socket Mode)
    │
    ▼
PydanticAI Agent ──── MCP Servers (web search, fetch, custom...)
    │
    ├── ChromaDB (episodic + semantic memory)
    ├── SQLite/PostgreSQL (conversations, config, souls)
    └── FastAPI Web UI (admin dashboard)
```

See `docs/REVAMP_PLAN.md` for the full architecture document.

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## Project Structure

```
src/chatter/
├── __main__.py         # CLI entry point
├── config.py           # Pydantic Settings
├── agent/              # PydanticAI agent (core, prompts, tools)
├── mcp/                # MCP server management
├── memory/             # ChromaDB memory store
├── slack/              # Slack bot (Socket Mode)
├── web/                # FastAPI admin UI
│   ├── routes/         # Dashboard, memory, soul, tools, etc.
│   └── templates/      # Jinja2 + Tailwind + DaisyUI + HTMX
└── db/                 # SQLAlchemy models + repositories
```

## License

GNU Affero General Public License version 3
