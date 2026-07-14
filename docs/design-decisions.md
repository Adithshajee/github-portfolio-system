# Architecture Decision Records (ADR)

This page lists key architectural and design decisions made during the v2.0 development cycle.

## ADR-001: Provider Plugin System
- **Decision:** Implement a registry pattern where providers inherit from `BaseProvider` and use `@register` decorator.
- **Consequence:** Easy to add new developer profile integrations without modifying GPSEngine core loops.

## ADR-002: Pydantic v2 Core Config
- **Decision:** Utilize Pydantic Models for settings loading and API schema translation.
- **Consequence:** Strong types, fail-fast validations, and strict type casting for timezone-aware date parsing.
