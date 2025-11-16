# ADR-0002: Pydantic v2 for Configuration and Data Models

**Status:** Accepted

**Date:** 2025-11-09

**Area:** Data Validation, Configuration Management

**Related:**
- [Configuration System](../../planning/architecture/configuration-system.md)
- [Implementation Notes](../../implementations/versions/v0.1/implementation-notes.md)

---

## Context

ragged needs type-safe configuration management for:
- Application settings (paths, model choices, chunk sizes)
- Environment variable parsing
- Document metadata models
- Data validation throughout the system

Without proper validation, configuration errors lead to runtime failures that are difficult to debug. We need a solution that provides compile-time type safety and runtime validation.

## Decision

Use **Pydantic v2** for all configuration and data models:
- `Settings` class in `src/config/settings.py`
- `Document` and `Chunk` models in `src/ingestion/models.py`
- All data structures requiring validation
- Environment variable parsing with type coercion

## Rationale

**Type Safety:**
- Runtime validation prevents configuration errors
- Type hints enable IDE autocomplete
- mypy integration for static type checking

**Developer Experience:**
- Automatic environment variable parsing
- Clear error messages when validation fails
- Self-documenting through type hints and Field() descriptions

**Performance:**
- Pydantic v2 has Rust core (significantly faster than v1)
- Lazy validation reduces overhead
- Efficient serialization/deserialization

**Ecosystem:**
- Wide adoption in Python ecosystem
- Excellent documentation and community
- FastAPI integration (useful for v0.2 web UI)

**Standards:**
- Pydantic v2 uses modern Python practices
- Compatible with dataclass protocol
- JSON Schema generation built-in

## Alternatives Considered

**1. dataclasses + manual validation**
- **Pros:** Standard library, lightweight
- **Cons:** More boilerplate, less validation, manual environment parsing
- **Decision:** Rejected—too much repetitive code

**2. attrs**
- **Pros:** Mature, well-tested
- **Cons:** Less ecosystem support, no environment variable parsing
- **Decision:** Rejected—Pydantic has better RAG ecosystem integration

**3. TypedDict**
- **Pros:** Simple, standard library
- **Cons:** No runtime validation, no nested model support
- **Decision:** Rejected—validation is critical

**4. Pydantic v1**
- **Pros:** Mature, stable
- **Cons:** Slower, deprecated patterns
- **Decision:** Rejected—v2 is current standard

## Consequences

### Positive

✅ **Early Error Detection:** Configuration errors caught at startup
✅ **Excellent DX:** Autocomplete, type checking, clear errors
✅ **Environment Variables:** Automatic parsing with `.env` support
✅ **Documentation:** Models are self-documenting
✅ **Validation:** Comprehensive validation rules
✅ **JSON Schema:** Auto-generation for API docs
✅ **FastAPI Ready:** Seamless integration for v0.2 web API

### Negative

⚠️ **External Dependency:** Adds ~15MB to installation
⚠️ **Learning Curve:** Contributors need to learn Pydantic patterns
⚠️ **Migration Overhead:** v1 → v2 required pattern changes
⚠️ **Complexity:** Overkill for simple configurations

### Trade-Offs Accepted

- Extra dependency justified by benefits
- Learning curve offset by excellent documentation
- v2 migration straightforward with clear migration guide

## Implementation Notes

**Configuration patterns:**
```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment variables with defaults
    embedding_model: str = Field(
        default="sentence-transformers",
        description="Embedding backend to use"
    )

    # Nested configuration
    chunk_size: int = Field(
        default=512,
        ge=100,
        le=2048,
        description="Maximum chunk size in tokens"
    )

    model_config = ConfigDict(
        env_file=".env",
        env_prefix="RAGGED_",
        case_sensitive=False
    )
```

**v2 Migration notes:**
- Changed `class Config` → `model_config = ConfigDict()`
- `validate_all=True` → handled automatically
- `.dict()` → `.model_dump()`
- `.parse_obj()` → `.model_validate()`

**Validation examples:**
- `ge=` (greater than or equal)
- `regex=` for string patterns
- Custom validators with `@field_validator`

## Testing Approach

- Test invalid configurations raise `ValidationError`
- Test environment variable parsing
- Test default values
- Test nested model validation
- Mock environment for testing

## Future Considerations

**v0.2:** Pydantic models for:
- API request/response validation
- Web form validation
- Configuration UI

**v1.0:** Consider:
- JSON Schema export for API documentation
- Configuration schema validation
- Plugin configuration schemas

---

**Last Updated:** 2025-11-13

**Supersedes:** None

**Superseded By:** None
