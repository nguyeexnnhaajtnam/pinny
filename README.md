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

Copy `.env.example` to `.env` and adjust values. Never commit `.env`. Select one provider with
`LLM_PROVIDER=openai` or `LLM_PROVIDER=gemini`, then configure only its required key and model.
Use `PINNY_OPENAI_API_KEY` for OpenAI or `GEMINI_API_KEY` for Gemini. Keep keys only in `.env`
or a deployment secret store; changing provider configuration requires a service restart.
`PINNY_DEV_USER_ID` is a **non-production identity shortcut**; production configuration rejects
the development identity provider. Replace it with trusted Pinus authentication before launch.
Standalone runtime facts come from `PINNY_CHAT_TIMEZONE` (IANA) and `PINNY_CHAT_LOCALE`; they are
added to prompts in memory and never stored as messages. `PINNY_CHAT_HISTORY_MAX_MESSAGES` bounds
completed history. `PINNY_CHAT_GENERATION_TIMEOUT`, `PINNY_CHAT_RETRY_ATTEMPTS`, and
`PINNY_CHAT_RETRY_DELAY_SECONDS` control finite provider-neutral timeout and pre-delta retries.

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
- `delta`: an ordered assistant text fragment with conversation and assistant-message IDs.
- `completed`: emitted only after the full assistant message commits.
- `error`: terminal sanitized failure after streaming begins; no `completed` follows.

Before streaming, invalid input uses HTTP 422, unknown or differently owned conversations use
404, overlapping turns use 409, excessive context uses 413, and unavailable provider or
persistence dependencies use sanitized 503 errors. Assistant lifecycle is `pending` → `streaming`
→ exactly one of `completed`, `failed`, or `cancelled`. Failed and disconnected generations are
never completed and are excluded from future history.

SSE exposes only provider-neutral `conversation`, `delta`, `completed`, and `error` events.
Conversation events carry the accepted user-message ID; delta/error/completed events carry the
assistant-message ID. Error codes include `provider_rate_limit`, `provider_timeout`,
`provider_unavailable`, `provider_invalid_request`, `provider_authentication_failed`, and
`provider_error`. Provider bodies, SDK exceptions, prompts, and credentials are never returned.
Transient failures retry only before the first delta; invalid/auth/config/cancellation and
post-delta failures never retry.

```console
curl -N -H "Content-Type: application/json" -d '{"message":"Hello Pinny"}' http://localhost:8000/api/v1/chat
```

Never log or return provider keys, provider response bodies, prompts, or message content.

Both providers use the same chat endpoint, SSE events, and PostgreSQL lifecycle. Provider
selection happens once during application startup; invalid provider values or missing settings
for the selected provider prevent startup. Credentials for the inactive provider are optional.
There is no automatic routing, fallback, or load balancing.

## Quality and migrations

```console
ruff format --check .
ruff check .
pytest
```

Unit tests do not need PostgreSQL. For integration tests, configure `PINNY_DATABASE_*`, migrate
an isolated database, then set `PINNY_RUN_INTEGRATION=1`. Provider tests use mocked OpenAI and
Gemini streams and require no real key. The API/SSE contract test is
`pytest tests/unit/test_chat_api.py`.

For an opt-in real-provider smoke test, place the selected credential only in `.env`, restart
with `docker compose up -d --build`, and call the endpoint without putting a key in the command:

```console
curl -N -H "Content-Type: application/json" -d '{"message":"Reply with one short sentence"}' http://localhost:8000/api/v1/chat
docker compose exec postgres psql -U pinny -d pinny -c "SELECT role,status,provider,model,latency_ms,input_tokens,output_tokens,content FROM messages ORDER BY created_at DESC LIMIT 2;"
```

Repeat once with OpenAI and once with Gemini, restarting after changing `LLM_PROVIDER`. Expect a
terminal `completed` event and completed user/assistant rows; assistant metadata contains
provider/model/latency and token usage when available. A provider error or disconnect must leave
the assistant row `failed` or `cancelled`, never `completed`. Never record provider secrets.

Validate downgrade behavior only against an empty disposable database:

```console
alembic upgrade head
alembic downgrade base
alembic upgrade head
```

```command test model
curl.exe -N `
  -X POST "http://localhost:8000/api/v1/chat" `
  -H "Content-Type: application/json" `
  --data-binary "@request.json"
```
