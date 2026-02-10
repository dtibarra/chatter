"""Entry point for the Chatter application."""

import argparse
import asyncio
import logging
import sys

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Chatter - Agentic Slack Chatbot")
    sub = parser.add_subparsers(dest="command")

    # Web UI server
    web_cmd = sub.add_parser("web", help="Start the admin web UI")
    web_cmd.add_argument("--host", default=None)
    web_cmd.add_argument("--port", type=int, default=None)

    # Slack bot
    sub.add_parser("slack", help="Start the Slack bot (Socket Mode)")

    # Both
    sub.add_parser("run", help="Start both the web UI and Slack bot")

    # Init DB
    sub.add_parser("init-db", help="Initialize the database")

    args = parser.parse_args()

    from chatter.config import settings

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if args.command == "web":
        _run_web(
            host=args.host or settings.web_host,
            port=args.port or settings.web_port,
        )
    elif args.command == "slack":
        _run_slack()
    elif args.command == "run":
        _run_both()
    elif args.command == "init-db":
        _init_db()
    else:
        parser.print_help()
        sys.exit(1)


def _run_web(host: str = "0.0.0.0", port: int = 8080):
    """Start the web UI server."""
    uvicorn.run(
        "chatter.web.app:create_web_app",
        factory=True,
        host=host,
        port=port,
        reload=False,
    )


def _run_slack():
    """Start the Slack bot."""
    from chatter.slack.bot import start_slack_bot

    asyncio.run(start_slack_bot())


def _run_both():
    """Start both web UI and Slack bot concurrently."""
    import threading

    from chatter.config import settings

    # Run web server in a thread
    web_thread = threading.Thread(
        target=_run_web,
        kwargs={"host": settings.web_host, "port": settings.web_port},
        daemon=True,
    )
    web_thread.start()

    # Run Slack bot in the main thread
    _run_slack()


def _init_db():
    """Initialize the database tables."""
    from chatter.db.engine import init_db

    asyncio.run(init_db())
    print("Database initialized.")


if __name__ == "__main__":
    main()
