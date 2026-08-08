## Why

Pinny needs a dependable backend foundation before it can grow into richer AI capabilities. Establishing a clean Python service structure now will reduce rework, improve testability, and make future features easier to add safely.

## What Changes

- Create a Python service foundation for Pinny using FastAPI as the application entrypoint.
- Add environment-based configuration management, structured logging, and health monitoring for local and CI environments.
- Provide Docker-based local development support with PostgreSQL connectivity and a repeatable startup path.
- Establish linting, formatting, testing, and CI quality checks so the service can evolve with confidence.
- Document the initial architecture boundaries so future capabilities can build on a stable base.

## Capabilities

### New Capabilities
- service-foundation: establish the production-oriented technical foundation for the Pinny backend service.

### Modified Capabilities
- None.

## Impact

This change introduces the initial backend project structure, runtime configuration, developer environment tooling, quality gates, and observability patterns. It affects the new Pinny service codebase, containerized local development workflow, and CI pipeline, while remaining intentionally out of scope for AI chat, streaming, RAG, and Pinus integration features.
