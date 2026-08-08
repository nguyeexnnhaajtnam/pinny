# Pinny

Pinny is the independent Python/FastAPI intelligence service for Pinus. Phase 1 provides
persistent, contextual AI chat through a streaming API while keeping Pinus domain ownership
and future intelligence capabilities behind explicit boundaries.

## Architecture boundaries

- `api` owns HTTP validation, transport responses, and SSE framing.
- `core` owns configuration, logging, and cross-cutting runtime concerns.
- `db` owns PostgreSQL connectivity and persistence, not Pinus domain data.
- `chat` owns provider-neutral orchestration, identity/provider ports, and message lifecycle.
- Pinny remains independently deployable from the Pinus NestJS backend.
- LangChain, LangGraph, RAG, vector retrieval, tools, files, and memory remain absent.

## Local development

Requirements: Python 3.12+ for host development, or Docker with Compose.

Copy `.env.example` to `.env` and adjust values. Never commit `.env`. Set
`PINNY_OPENAI_API_KEY` only in that file or a deployment secret store.
`PINNY_DEV_USER_ID` is a **non-production identity shortcut**; production configuration rejects
the development identity provider. Replace it with trusted Pinus authentication before launch.

Start the environment (migrations run before the API starts):

```console
docker compose up --build
```

Stop it while preserving the database volume:

```console
docker compose down
```

The API is at `http://localhost:8000`. Use `GET /health/live` for liveness and
`GET /health/ready` for PostgreSQL-backed readiness.

Host development:

```console
python -m venv .venv
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn pinny.main:app --reload
```

Validate PostgreSQL independently with `python -m pinny.db.validate`.

## Core AI chat API

Start a conversation with `POST /api/v1/chat`:

```json
{"message": "Mùa hè nên đi ăn gì?"}
```

For a follow-up, include the returned conversation UUID:

```json
{
  "conversation_id": "00000000-0000-0000-0000-000000000000",
  "message": "Còn món nào nhẹ hơn không?"
}
```

The strict schema rejects unknown fields, including `user_id`. The server resolves identity and
returns `text/event-stream` with JSON data in this order:

- `conversation`: conversation and accepted user-message IDs.
- `delta`: an ordered assistant text fragment.
- `completed`: emitted only after the full assistant message commits.
- `error`: terminal sanitized failure after streaming begins; no `completed` follows.

Before streaming, invalid input uses HTTP 422, unknown or differently owned conversations use
404, overlapping turns use 409, excessive context uses 413, and unavailable provider or
persistence dependencies use sanitized 503 errors. Failed and disconnected generations become
`failed` or `interrupted`, never `completed`, and are excluded from future history.

```console
curl -N -H "Content-Type: application/json" -d '{"message":"Hello Pinny"}' http://localhost:8000/api/v1/chat
```

Never log or return the OpenAI key, provider response bodies, prompts, or message content.

## Quality and migrations

```console
ruff format --check .
ruff check .
pytest
```

Unit tests do not need PostgreSQL. For integration tests, configure `PINNY_DATABASE_*`, migrate
an isolated database, then set `PINNY_RUN_INTEGRATION=1`. Provider tests use mocked OpenAI
streams and require no real key. The containerized API/SSE smoke test is
`pytest tests/unit/test_chat_api.py`.

Validate downgrade behavior only against an empty disposable database:

```console
alembic upgrade head
alembic downgrade base
alembic upgrade head
```
