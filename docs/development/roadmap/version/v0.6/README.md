# Ragged v0.6 Roadmap - Web UI Security & API Maturity

**Status:** Planned

**Duration:** 32-48 hours (AI implementation)

**Focus:** Web UI security enhancements, API improvements, Gradio interface refinements

**Breaking Changes:** None

---

## Overview

Version 0.6 focuses on securing and maturing the web interface and API layer. This release transitions from the security-focused v0.5.x series to user-facing improvements while maintaining architectural quality.

**Dependencies:** Requires v0.5.x completion (security implementation, vision RAG, GPU management)

**Strategic Context:** Prepares foundation for v0.6.7 Svelte UI redesign and v0.7.x query optimisation by ensuring secure, stable API and web layers.

**Note:** Data connectivity features (Google Drive, Dropbox, Notion) deferred to v0.8.x or v0.9.x. Query optimisation features deferred to v0.7.x series.

---

## SECURITY-WEB-001: Web UI Security Enhancements (6-8 hours)

**Problem:** Current Gradio web UI lacks enterprise-grade security headers and session management.

**Implementation:**

1. **Content Security Policy (CSP) Headers** (2 hours)
   - Prevent XSS attacks
   - Restrict resource loading
   - Monitor violations

2. **HTTP Strict Transport Security (HSTS)** (1 hour)
   - Force HTTPS connections
   - Prevent downgrade attacks
   - Improve transport security

3. **Session Security Improvements** (2 hours)
   - Secure session storage
   - Session timeout enforcement
   - CSRF token improvements
   - Session hijacking prevention

4. **XSS Protection Enhancements** (1-2 hours)
   - Input sanitization
   - Output encoding
   - DOM-based XSS prevention
   - Template injection prevention

**Implementation:**
```python
# CSP Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:;"
    )
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    return response
```

**Files:**
- `src/web/api.py`
- `src/web/middleware/security.py` (new)
- `src/web/gradio_ui.py`

**Success:** ✅ Security headers active, session management hardened, XSS protection enforced

---

## SECURITY-API-001: FastAPI Security Middleware (4-6 hours)

**Problem:** API layer needs comprehensive request validation and security middleware.

**Implementation:**

1. **Request Validation Middleware** (2 hours)
   - Schema validation
   - Input sanitization
   - Size limits enforcement
   - Type checking

2. **Response Sanitization Middleware** (1 hour)
   - Remove sensitive headers
   - Sanitize error messages
   - Consistent response format

3. **API Versioning Security** (1-2 hours)
   - Version-specific security policies
   - Deprecation warnings
   - Migration paths

4. **JWT Improvements** (1 hour)
   - Token rotation
   - Refresh token security
   - Audience validation
   - Claims verification

**Implementation:**
```python
# Request Validation Middleware
@app.middleware("http")
async def validate_request(request, call_next):
    # Validate content-type
    # Check request size
    # Sanitize input
    # Validate JSON schema
    response = await call_next(request)
    return response
```

**Files:**
- `src/web/api.py`
- `src/web/middleware/validation.py` (new)
- `src/web/middleware/jwt.py`

**Success:** ✅ Request validation enforced, JWT security improved, API versioning operational

---

## SECURITY-RATE-001: Advanced Rate Limiting (3-4 hours)

**Problem:** Current rate limiting is basic in-memory; need distributed, per-user, per-endpoint support.

**Implementation:**

1. **Per-User Rate Limiting** (1 hour)
   - User-specific quotas
   - Role-based limits
   - Custom tier support

2. **Per-Endpoint Limits** (1 hour)
   - Different limits for different endpoints
   - Cost-based limiting
   - Burst handling

3. **Redis-backed Storage** (1-2 hours)
   - Distributed rate limiting
   - Persistent state
   - Better performance

4. **Advanced Features** (1 hour)
   - Rate limit headers (X-RateLimit-*)
   - Quota warnings
   - Dynamic adjustment

**Implementation:**
```python
# Redis-backed Rate Limiter
class DistributedRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        limit: int,
        window: int
    ) -> bool:
        key = f"rate_limit:{user_id}:{endpoint}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, window)
        return count <= limit
```

**Files:**
- `src/web/middleware/rate_limit.py`
- `src/config/rate_limits.py` (new)

**Success:** ✅ Per-user and per-endpoint rate limiting operational, Redis integration complete

---

## UI-GRADIO-001: Gradio UI Improvements (10-15 hours)

**Problem:** Current Gradio UI is functional but lacks polish and real-time features.

**Note:** Full Svelte UI redesign (from `docs/design/webUI/`) deferred to v0.6.7.

**Implementation:**

1. **Real-time Query Results** (4-5 hours)
   - Streaming response display
   - Progressive result loading
   - Live status updates

2. **Better Document Visualization** (3-4 hours)
   - Improved result cards
   - Source preview integration
   - PDF thumbnail support

3. **Improved Search UX** (2-3 hours)
   - Enhanced error handling
   - Better loading states
   - Query history dropdown

4. **Enhanced Upload Experience** (1-2 hours)
   - Drag-and-drop improvements
   - Upload progress indicators
   - Batch upload support

5. **Dashboard Metrics** (1-2 hours)
   - Library statistics
   - Query performance metrics
   - System health indicators

**Files:**
- `src/web/gradio_ui.py`
- `src/web/gradio/components/` (new directory)
- `src/web/gradio/query.py`
- `src/web/gradio/upload.py`

**Success:** ✅ Real-time updates functional, document visualization improved, upload UX enhanced

---

## API-ENHANCE-001: API Enhancements (9-15 hours)

**Problem:** API needs WebSocket support, streaming, and batch operations for modern client requirements.

**Implementation:**

1. **GraphQL API Exploration** (3-4 hours)
   - Research GraphQL benefits for ragged
   - Create prototype schema
   - Evaluate integration with existing REST API
   - **Note:** Full implementation deferred to v0.7.0

2. **WebSocket Support** (3-4 hours)
   - Real-time query updates
   - Live document ingestion status
   - System event streaming

3. **Streaming Responses** (2-3 hours)
   - Server-Sent Events (SSE) implementation
   - Progressive query results
   - Chunk-by-chunk processing

4. **Batch Operations** (1-2 hours)
   - Batch document ingestion endpoint
   - Bulk query processing
   - Parallel processing support

**Files:**
- `src/web/api.py`
- `src/web/websocket.py` (new)
- `src/web/streaming.py` (new)
- `src/web/batch.py` (new)

**Success:** ✅ WebSocket operational, streaming responses working, batch endpoints functional

---

## Success Criteria

**Automated Tests:**
- [ ] Security headers active and tested
- [ ] Session security improvements verified
- [ ] Request validation enforcing schemas
- [ ] Rate limiting per-user and per-endpoint working
- [ ] WebSocket connections stable
- [ ] All existing tests pass

**Manual Testing:**
- [ ] Gradio UI real-time updates working
- [ ] Document visualization improved
- [ ] Upload experience enhanced
- [ ] Security headers present in all responses
- [ ] Rate limiting triggers correctly
- [ ] WebSocket events streaming properly

**Quality Gates:**
- [ ] No security regressions
- [ ] Performance maintained or improved
- [ ] All documentation updated
- [ ] API versioning operational
- [ ] Zero breaking API changes

---

## Known Risks

- **Security Configuration:** Overly strict CSP may break existing functionality
- **Rate Limiting:** Redis dependency adds complexity
- **WebSocket Support:** Connection management can be challenging
- **Gradio Limitations:** Some UI improvements constrained by Gradio framework
- **API Changes:** Streaming and batch operations require client updates

---

## Next Steps

After v0.6 completion:
- **v0.6.7:** Svelte UI Redesign (implementation of `docs/design/webUI/` mockups)
- **v0.7.x:** Query Optimisation (context management, classification, model routing)
- **v0.8.x or v0.9.x:** Data Connectivity (Google Drive, Dropbox, Notion connectors)

See: `roadmap/version/v0.7/README.md`, `roadmap/version/v0.8/README.md`

---

## Related Documentation

- [Previous Version](../v0.5/README.md) - Security implementation and vision RAG
- [Planning](../../planning/version/v0.6/) - Design goals for v0.6
- [Version Overview](../README.md) - Complete version comparison
- [Web UI Design](../../../../design/webUI) - Svelte UI mockups (v0.6.7 implementation)

---

**Status:** Planned - Web UI security and API maturity focus
