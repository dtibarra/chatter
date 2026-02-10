# Chatter v2 - Revamp Plan

## Vision

Transform Chatter from a simple prompt-response Slack bot into a **modern agentic
assistant** with MCP tool integration, multi-step reasoning, persistent long-term
memory, and a web UI for configuration and memory inspection.

---

## Technology Choices

### Agent Framework: PydanticAI

**Why PydanticAI over alternatives:**
- Type-safe, Python-native agent development ("FastAPI-style DX for GenAI")
- **Native MCP support** (first-class, not bolted on)
- Model-agnostic (OpenAI, Anthropic, Gemini, Ollama, Groq, Mistral)
- Structured outputs with Pydantic validation
- Fastest framework in raw execution speed benchmarks
- Hit v1 in September 2025, mature and production-ready
- ReAct-style reasoning loop is implicit (agent reasons, calls tools, observes, continues)

**Rejected alternatives:**
- LangGraph: heavier abstraction, MCP is adapter-based not native, steeper learning curve
- OpenAI Agents SDK: less customizable, smaller community
- CrewAI: overkill for single-agent bot, multi-agent focus
- mcp-agent: narrower scope, less mature

### MCP Integration: Official MCP Python SDK (`mcp`)

**Servers we'll integrate:**
- **Brave Search MCP** - web search capabilities
- **Fetch MCP** - raw HTTP fetch for reading web pages
- **Filesystem MCP** - read/write files in sandboxed directories
- **Memory MCP** - persistent knowledge graph (official server)
- **Custom MCP servers** - for any domain-specific tools

**Architecture:**
```
PydanticAI Agent
    │
    ├── MCP Client → Brave Search Server (web search)
    ├── MCP Client → Fetch Server (read web pages)
    ├── MCP Client → Filesystem Server (file operations)
    ├── MCP Client → Memory Server (knowledge graph)
    └── MCP Client → Custom servers (user-configured)
```

### Long-Term Memory: ChromaDB + SQLite

**Why ChromaDB:**
- Embedded (no external service needed), zero-ops
- Deep Python integration, simple API
- Perfect for self-hosted chatbot (no cloud dependency)
- Stores both embeddings and metadata

**Memory architecture:**
```
┌─────────────────────────────────────────────┐
│  Memory System                              │
│                                             │
│  ┌───────────────┐  ┌───────────────────┐   │
│  │ Episodic      │  │ Semantic          │   │
│  │ (ChromaDB)    │  │ (ChromaDB)        │   │
│  │               │  │                   │   │
│  │ Raw events:   │  │ Extracted facts:  │   │
│  │ - Convos      │  │ - User prefs      │   │
│  │ - Tool calls  │  │ - Learned facts   │   │
│  │ - Outcomes    │  │ - Entity info     │   │
│  └───────────────┘  └───────────────────┘   │
│                                             │
│  ┌───────────────────────────────────────┐   │
│  │ Conversation History (SQLite/Postgres) │  │
│  │ - Full message logs                   │   │
│  │ - Thread metadata                     │   │
│  │ - Timestamps, user IDs               │   │
│  └───────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Slack Integration: slack-bolt + Socket Mode

**Why Socket Mode over HTTP webhooks:**
- No public endpoint needed (WebSocket-based)
- Works behind corporate firewalls
- Simpler deployment (no nginx/reverse proxy needed)
- Built into slack-bolt

### Web UI: FastAPI + Jinja2 + Tailwind CSS + HTMX

**Why this stack over React/Next.js:**
- Pure Python backend (no Node.js build step)
- HTMX provides interactivity without a JS framework
- Tailwind CSS + DaisyUI for beautiful, modern styling
- Fast to build, easy to maintain
- Jinja2 templates are simple and well-understood

**Why not Reflex/NiceGUI/Streamlit:**
- More control over the UI
- Better for a proper admin dashboard
- No Python-to-JS compilation overhead
- HTMX is lightweight and fits the project's philosophy

**UI Features:**
- Dashboard with bot status and recent activity
- Memory browser: search, inspect, delete memories
- Soul editor: system prompts, personality, behavior rules
- MCP tool manager: enable/disable servers, configure tools
- Conversation history viewer with search
- Settings: API keys, model selection, memory config

### Database: SQLAlchemy + SQLite (dev) / PostgreSQL (prod)

- SQLAlchemy 2.0+ with async support
- Alembic for migrations
- SQLite for development, PostgreSQL for production
- Stores: config, conversations, prompts, memory metadata

### Testing: pytest + pytest-asyncio

- Unit tests for agent logic, memory, schemas
- Integration tests for MCP tool calls
- Mock-based tests for Slack events
- Coverage target: 80%+

---

## New Project Structure

```
chatter/
├── pyproject.toml              # Modern Python packaging
├── alembic.ini                 # Database migrations config
├── Dockerfile
├── docker-compose.yml          # Local dev with all services
├── .env.example                # Environment variable template
│
├── src/
│   └── chatter/
│       ├── __init__.py
│       ├── __main__.py         # CLI entry point
│       │
│       ├── config.py           # Pydantic Settings
│       │
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── core.py         # PydanticAI agent definition
│       │   ├── tools.py        # Built-in tools (non-MCP)
│       │   ├── prompts.py      # System prompts / soul
│       │   └── reasoning.py    # Reasoning step tracking
│       │
│       ├── mcp/
│       │   ├── __init__.py
│       │   ├── manager.py      # MCP server lifecycle management
│       │   ├── registry.py     # Available MCP servers registry
│       │   └── servers/        # Custom MCP server definitions
│       │       └── __init__.py
│       │
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── store.py        # ChromaDB vector store
│       │   ├── episodic.py     # Episodic memory (events)
│       │   ├── semantic.py     # Semantic memory (facts)
│       │   └── consolidation.py # Memory cleanup/merging
│       │
│       ├── slack/
│       │   ├── __init__.py
│       │   ├── bot.py          # Slack bolt app + Socket Mode
│       │   ├── events.py       # Event handlers
│       │   └── formatters.py   # Message formatting
│       │
│       ├── web/
│       │   ├── __init__.py
│       │   ├── app.py          # FastAPI application
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── dashboard.py
│       │   │   ├── memory.py
│       │   │   ├── soul.py
│       │   │   ├── tools.py
│       │   │   ├── conversations.py
│       │   │   └── settings.py
│       │   ├── templates/      # Jinja2 templates
│       │   │   ├── base.html
│       │   │   ├── dashboard.html
│       │   │   ├── memory.html
│       │   │   ├── soul.html
│       │   │   ├── tools.html
│       │   │   ├── conversations.html
│       │   │   └── settings.html
│       │   └── static/
│       │       └── css/
│       │           └── output.css  # Compiled Tailwind
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   ├── engine.py       # SQLAlchemy engine setup
│       │   ├── models.py       # ORM models
│       │   └── repositories.py # Data access layer
│       │
│       └── migrations/         # Alembic migrations
│           ├── env.py
│           └── versions/
│
├── tests/
│   ├── conftest.py
│   ├── test_agent.py
│   ├── test_memory.py
│   ├── test_slack.py
│   ├── test_web.py
│   └── test_db.py
│
└── docs/
    ├── CURRENT_ARCHITECTURE.md
    └── REVAMP_PLAN.md
```

---

## Agent Behavior (The "Soul")

The revamped Chatter will have a configurable "soul" - a set of system prompts
and behavior rules that define its personality. This replaces the single hardcoded
prompt.

### Default Soul

```
You are Chatter, a helpful and knowledgeable assistant.

You have access to tools that let you search the web, read web pages,
and manage files. Use these tools proactively when they'd help answer
a question or complete a task.

When reasoning through complex problems:
1. Break the problem down into steps
2. Use available tools to gather information
3. Think through the evidence before answering
4. Be transparent about your reasoning process

You have long-term memory. You remember past conversations and facts
you've learned about users. Use this context naturally without being
creepy about it.
```

### Reasoning Flow

```
User Message
    │
    ▼
┌─────────────────────────────────┐
│  1. Retrieve relevant memories  │
│     (episodic + semantic)       │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  2. Build context               │
│     - Soul/system prompt        │
│     - Retrieved memories        │
│     - Conversation history      │
│     - Available MCP tools       │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  3. PydanticAI Agent Loop       │
│     (ReAct pattern, implicit)   │
│                                 │
│     Think → Act → Observe       │
│         ↑         │             │
│         └─────────┘             │
│                                 │
│     May call MCP tools:         │
│     - Web search                │
│     - Read web pages            │
│     - File operations           │
│     - Custom tools              │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  4. Store memories              │
│     - Save conversation         │
│     - Extract & store facts     │
│     - Log reasoning steps       │
└──────────────┬──────────────────┘
               │
               ▼
          Final Response
```

---

## Implementation Phases

### Phase 1: Foundation
- Project structure (pyproject.toml, src layout)
- Configuration (pydantic-settings)
- Database models + migrations
- Basic PydanticAI agent (no MCP yet)

### Phase 2: Memory
- ChromaDB integration
- Episodic memory (conversation storage + retrieval)
- Semantic memory (fact extraction + storage)
- Memory search and retrieval at query time

### Phase 3: MCP Integration
- MCP client manager
- Web search tool (Brave Search)
- Web page reader (Fetch)
- Tool configuration storage

### Phase 4: Slack Bot
- Socket Mode integration
- Thread-aware conversations
- Streaming responses (post + edit pattern)
- Error handling and retries

### Phase 5: Web UI
- FastAPI + Jinja2 + Tailwind + HTMX
- Dashboard
- Memory browser
- Soul editor
- MCP tool manager
- Conversation viewer
- Settings

### Phase 6: Testing & Polish
- pytest suite
- Docker + docker-compose
- README
- Deployment docs

---

## Configuration (.env)

```env
# LLM Provider
LLM_PROVIDER=openai           # openai, anthropic, ollama
LLM_MODEL=gpt-4o              # model name
LLM_API_KEY=sk-...            # API key

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...      # For Socket Mode
SLACK_SIGNING_SECRET=...

# Database
DATABASE_URL=sqlite+aiosqlite:///chatter.db

# Memory
CHROMADB_PATH=./chroma_data

# MCP Tools
BRAVE_SEARCH_API_KEY=...      # For web search

# Web UI
WEB_HOST=0.0.0.0
WEB_PORT=8080
SECRET_KEY=...                # For session management
```
