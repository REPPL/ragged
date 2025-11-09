# ragged v0.1 Implementation Checklist

Track your progress through all implementation phases.

## ✅ Phase 1: Foundation (COMPLETE)
- [x] Package structure created
- [x] pyproject.toml configured
- [x] Configuration system (16 tests passing, 92% coverage)
- [x] Logging system (12 tests passing, 100% coverage)
- [x] Pre-commit hooks configured
- [x] Test infrastructure working

**Status:** 28 tests passing, 96% coverage

---

## 🔄 Phase 2: Document Ingestion (PARTIAL)
- [x] Document models (Pydantic) - 16 tests passing, 97% coverage
- [x] Security utilities created
- [ ] PDF loader (`src/ingestion/loaders.py`)
- [ ] TXT loader
- [ ] Markdown loader
- [ ] HTML loader
- [ ] Parser implementations
- [ ] Loader tests (20+ tests needed)

**Next:** Finish document loaders

---

## Phase 3: Chunking System
- [ ] Token counter (`src/chunking/token_counter.py`) - 5 functions
- [ ] Recursive text splitter (`src/chunking/splitters.py`) - 3 functions
- [ ] Token counter tests (8 tests)
- [ ] Splitter tests (10 tests)

**Dependencies:** `pip install tiktoken`

**Files:** 2 implementation + 2 test files

---

## Phase 4: Embeddings System
- [ ] Base embedder interface (`src/embeddings/base.py`)
- [ ] SentenceTransformer embedder (`src/embeddings/sentence_transformer.py`)
- [ ] Ollama embedder (`src/embeddings/ollama_embedder.py`)
- [ ] Embedder factory (`src/embeddings/factory.py`)
- [ ] Tests for each embedder (15+ tests total)

**Dependencies:** `pip install sentence-transformers torch ollama`

**Files:** 4 implementation + 4 test files

---

## Phase 5: Vector Storage
- [ ] ChromaDB wrapper (`src/storage/vector_store.py`) - 9 methods
- [ ] Vector store tests (12+ tests)
- [ ] Persistence tests (marked integration)

**Dependencies:** `pip install chromadb-client`

**Files:** 1 implementation + 2 test files

---

## Phase 6: Retrieval System
- [ ] Retriever class (`src/retrieval/retriever.py`) - 4 methods
- [ ] Retrieved chunk dataclass
- [ ] Retrieval tests (10+ tests)
- [ ] Evaluation tests with test questions (20+ questions)

**Dependencies:** None (uses embeddings + storage)

**Files:** 1 implementation + 2 test files

---

## Phase 7: Generation System
- [ ] Ollama client (`src/generation/ollama_client.py`) - 5 methods
- [ ] Prompt templates (`src/generation/prompts.py`) - 2 functions
- [ ] Response parser (`src/generation/response_parser.py`) - 2 functions
- [ ] Generation tests (12+ tests)

**Dependencies:** `pip install ollama` (if not already)

**Files:** 3 implementation + 3 test files

---

## Phase 8: CLI Interface
- [ ] Main CLI (`src/main.py`) - 6 commands
  - [ ] `ragged add <file>`
  - [ ] `ragged query "<question>"`
  - [ ] `ragged list`
  - [ ] `ragged clear`
  - [ ] `ragged config [show|set]`
  - [ ] `ragged health`
- [ ] CLI tests using Click's CliRunner (10+ tests)

**Dependencies:** `pip install click rich`

**Files:** 1 implementation + 1 test file

---

## Phase 9: End-to-End Integration
- [ ] E2E tests (`tests/integration/test_end_to_end.py`)
  - [ ] Single document ingest + query
  - [ ] Multiple documents
  - [ ] Cross-format tests
  - [ ] Error recovery
- [ ] Quality validation (`tests/integration/test_quality.py`)
  - [ ] Retrieval relevance >70%
  - [ ] Answer faithfulness >80%
  - [ ] Query latency <5s
- [ ] Performance benchmarks (`tests/performance/test_benchmarks.py`)

**Files:** 3 test files (10+ tests)

---

## Phase 10: Docker Integration
- [ ] Fix `Dockerfile`
  - [ ] Correct PYTHONPATH
  - [ ] Install all dependencies
  - [ ] Non-root user
  - [ ] Working health check
- [ ] Update `docker-compose.yml`
  - [ ] Proper volume mounts
  - [ ] Environment variables
  - [ ] Service dependencies
- [ ] Docker tests (`tests/integration/test_docker.py`)

**Files:** 2 config + 1 test file

---

## Phase 11: Documentation
- [ ] Update `README.md`
- [ ] `docs/user-guide/installation.md`
- [ ] `docs/user-guide/quick-start.md`
- [ ] `docs/user-guide/cli-reference.md`
- [ ] `docs/user-guide/configuration.md`
- [ ] `docs/user-guide/troubleshooting.md`
- [ ] `docs/developer/architecture.md`
- [ ] `docs/developer/contributing.md`
- [ ] `docs/developer/testing.md`
- [ ] Update `CHANGELOG.md`

**Files:** 10 documentation files

---

## Phase 12: Security Audit
- [ ] Run `bandit -r src/`
- [ ] Run `pip-audit`
- [ ] Run `safety check`
- [ ] Use `codebase-security-auditor` agent
- [ ] Fix all high/critical issues
- [ ] Document medium/low issues
- [ ] Manual security review

**Tools:** bandit, pip-audit, safety, Task agent

---

## Phase 13: Testing & Coverage
- [ ] Run full test suite
- [ ] Achieve 60-70% overall coverage
- [ ] Achieve 90%+ core logic coverage
- [ ] Manual testing on macOS
- [ ] Docker testing
- [ ] Real-world document testing
- [ ] Performance validation

**Target:** 60-70% coverage, all tests green

---

## Phase 14: Git Commit & Release
- [ ] Pre-commit checklist
  - [ ] All tests pass
  - [ ] Coverage targets met
  - [ ] Security audit passed
  - [ ] Documentation complete
  - [ ] British English verified
  - [ ] No debug code
- [ ] Use `git-documentation-committer` agent
- [ ] Tag release: `git tag -a v0.1.0 -m "ragged version 0.1.0"`
- [ ] Fresh clone validation
- [ ] Docker build validation

**Final Step:** Release v0.1.0!

---

## Progress Tracking

| Phase | Files | Tests | Status |
|-------|-------|-------|--------|
| 1. Foundation | 8 | 28 ✓ | ✅ Complete |
| 2. Ingestion | 6 | 16 ✓ | 🔄 Partial |
| 3. Chunking | 4 | 0 | ⬜ TODO |
| 4. Embeddings | 8 | 0 | ⬜ TODO |
| 5. Storage | 3 | 0 | ⬜ TODO |
| 6. Retrieval | 3 | 0 | ⬜ TODO |
| 7. Generation | 6 | 0 | ⬜ TODO |
| 8. CLI | 2 | 0 | ⬜ TODO |
| 9. Integration | 3 | 0 | ⬜ TODO |
| 10. Docker | 3 | 0 | ⬜ TODO |
| 11. Documentation | 10 | N/A | ⬜ TODO |
| 12. Security | N/A | N/A | ⬜ TODO |
| 13. Testing | N/A | N/A | ⬜ TODO |
| 14. Release | N/A | N/A | ⬜ TODO |

---

## Installation Commands

As you progress, install dependencies:

```bash
# Already installed
pip install pydantic pydantic-settings python-dotenv
pip install pytest pytest-cov pytest-mock
pip install python-json-logger

# Phase 3
pip install tiktoken

# Phase 4
pip install sentence-transformers torch ollama

# Phase 5
pip install chromadb-client

# Phase 8
pip install click rich

# Phase 12
pip install bandit pip-audit safety
```

Or install all at once:
```bash
pip install -e ".[dev]"  # After fixing chromadb dependency issue
```

---

## Success Criteria

Before marking v0.1 as complete:

### Functionality
- [ ] All 4 document formats working (PDF, TXT, MD, HTML)
- [ ] Both embedding models functional (sentence-transformers + Ollama)
- [ ] All 6 CLI commands working
- [ ] End-to-end pipeline functional

### Quality
- [ ] 60-70% test coverage overall
- [ ] 90%+ coverage on core logic
- [ ] All security checks passed
- [ ] Type checking passes (mypy strict)
- [ ] Linting passes (ruff)

### Performance
- [ ] Query latency <5s
- [ ] Supports files up to 100MB
- [ ] Handles 100+ documents
- [ ] Retrieval relevance >70%
- [ ] Answer faithfulness >80%

### Documentation
- [ ] User guide complete
- [ ] Developer docs complete
- [ ] All public APIs documented
- [ ] Examples provided

---

## Tips for Implementation

1. **Follow TDD** - Write tests first for core logic
2. **Run tests frequently** - `pytest -v`
3. **Check coverage** - `pytest --cov=src`
4. **Use type hints** - Run `mypy src/` regularly
5. **Format code** - Run `black src/ tests/`
6. **Lint code** - Run `ruff src/ tests/`
7. **Commit often** - Small, focused commits
8. **Reference Phase 1-2** - Follow established patterns

---

## Getting Help

- **Stuck?** Review IMPLEMENTATION_GUIDE.md
- **Patterns?** Check completed phases (1-2)
- **Debugging?** Enable DEBUG logging
- **Dependencies?** Check requirements-dev.txt
- **Documentation?** See docs/development/plans/v0.1-implementation-plan.md

---

**Current Status:** Phase 2 (Ingestion) in progress
**Next Action:** Complete document loaders
**Overall Progress:** ~15% complete
