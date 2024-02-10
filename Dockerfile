FROM python:3.11.4-bullseye

RUN apt update && \
    apt install sqlite3 && \
    apt clean all

RUN mkdir /app
WORKDIR /app/

RUN python3 -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py /app/
COPY lib /app/lib

RUN mkdir /var/lib/chatter && \
    chown nobody /var/lib/chatter

ENV DATABASE_PATH="/var/lib/chatter/chatter.db"
ENV STDOUT_LOGGING="true"

USER nobody

CMD ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:3000", "--timeout", "180", "-k", "uvicorn.workers.UvicornWorker", "slackbot:api", "--threads", "4"]