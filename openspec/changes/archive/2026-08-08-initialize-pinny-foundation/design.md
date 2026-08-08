## Context

The Pinny backend is expected to begin as a simple, production-oriented Python service that can be developed and tested independently from the Pinus backend and future AI capabilities. The foundation must support a clean local workflow, environment-driven configuration, and reliable quality checks without introducing unnecessary infrastructure complexity.

## Goals / Non-Goals

**Goals:**
- Establish a minimal but durable FastAPI service structure.
- Provide a developer-friendly local environment with PostgreSQL and Docker support.
- Make the service observable, configurable, and testable from the start.

**Non-Goals:**
- OpenAI integration, chat features, streaming, LangChain, LangGraph, RAG, pgvector, Pinus tool calling, file work, and memory are explicitly excluded.

## Decisions

- Use FastAPI as the application framework because it aligns with the Pinny backend stack and supports straightforward health endpoints and API growth.
- Keep configuration centralized in environment variables with a small config layer rather than introducing a heavier framework-specific configuration system.
- Use Docker Compose for local development so the service and PostgreSQL can be started consistently without platform-specific setup.
- Use Ruff for linting and formatting and pytest as the test runner.
  This keeps the initial Python quality toolchain small while supporting
  consistent local and CI validation.
- Keep logging structured and non-sensitive by using a JSON-style or key-value format with redaction rules for secrets.
- Separate the application runtime from the database connectivity checks so the service can be tested without relying on a live database during every unit test run.
- Use a small modular application package with `core`, `api`, and `db`
  boundaries. Feature-specific modules will be introduced only when
  their corresponding capabilities are implemented.

## Risks / Trade-offs

- [Minimal architecture may need refinement later] → The initial foundation is intentionally simple, but future feature work may require additional structure and dependency injection patterns.
- [Docker-based setup adds startup complexity] → The workflow is more repeatable and portable, but developers must have Docker available locally.
- [Environment configuration may be too lightweight for complex deployments] → The design favors simplicity now, with room to evolve into a more formal config strategy if deployment needs grow.

## Migration Plan

- Introduce the foundation in a standalone service module and make it runnable locally before adding any feature-specific endpoints.
- Validate the health endpoint, configuration loading, and database connectivity flow in local development before expanding the service.
- Roll out the quality gate commands in CI and document the expected local workflow so future contributors follow the same standards.

## Open Questions

- None for this change.
