# Pinny Engineering Decision Policy

## General

- Prefer simple implementation before distributed architecture.
- Do not add infrastructure without a concrete requirement.
- Do not introduce technology only for learning purposes
  if it harms architecture.

## AI

- Do not use RAG when deterministic structured querying is sufficient.
- Use tools for structured Pinus data.
- Use RAG for semantic retrieval.
- LLM output must not be treated as verified structured data
  without validation.

## Files

- File extension does not determine document intent.
- File type and document type are separate concepts.
- File processors must use a common abstraction.
- Support ephemeral and persistent processing separately.

## Data

- Preserve source/provenance.
- File ingestion must be idempotent.
- Invalid records must not silently enter normalized data.

## Architecture

- Pinny remains independent from Pinus business backend.
- Pinus owns Pinus domain data.
- Pinny accesses Pinus data through defined interfaces.