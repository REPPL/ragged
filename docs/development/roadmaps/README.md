# Ragged Version Roadmaps

This directory contains detailed roadmaps for upcoming ragged versions, created on 2025-11-11 based on comprehensive codebase analysis.

## Overview

The roadmaps are organised into three major versions, each with distinct focus areas:

| Version | Focus | Timeline | Estimated Hours |
|---------|-------|----------|-----------------|
| [v0.2.5](version/v0.2.5/README.md) | Bug Fixes & Stability | 1-2 weeks | 40-50 hours |
| [v0.2.7](version/v0.2.7/README.md) | UX, Performance & CLI Foundation | 4-5 weeks | 137-151 hours |
| [v0.3.0](version/v0.3.0/README.md) | Advanced RAG & Interactive CLI | 8-10 weeks | 232-291 hours |
| [v0.4.0](version/v0.4.0/README.md) | Memory, Knowledge Graphs & Plugins | 6-8 weeks | 180-225 hours |

**Total Timeline**: 19-25 weeks for all four versions

**Total Effort**: 589-717 hours

## Version Summaries

### v0.2.5 - Bug Fixes & Improvements

**Priority**: CRITICAL - Start immediately

**Key Issues**:
- Fix non-functional API endpoints (Web UI currently broken)
- Add missing test coverage for new modules (scanner, batch, model_manager)
- Fix logger import bugs
- Improve error handling throughout codebase
- Fix memory leaks in batch processing
- Integrate existing hybrid retrieval and few-shot features

**Outcome**: Stable, well-tested codebase with all features functional

### v0.2.7 - UX & Performance

**Priority**: HIGH - High user value

**Key Improvements**:
- Runtime model switching without restarts
- Multi-collection support for organising documents
- Enhanced progress indicators and error messages
- Embedding caching (50-90% faster queries)
- Async document processing (2-4x faster batch ingestion)
- BM25 index persistence (instant startup)
- Configuration profiles and runtime updates

**Outcome**: Dramatically improved user experience and performance

### v0.3.0 - Advanced RAG Features

**Priority**: MEDIUM - Differentiation from other RAG systems

**New Capabilities**:
- Query decomposition for complex questions
- HyDE retrieval and cross-encoder reranking
- Semantic and hierarchical chunking
- Multi-modal support (images, tables)
- RAGAS evaluation framework
- Document version tracking
- Chain-of-thought reasoning
- Auto-tagging and classification

**Outcome**: State-of-the-art RAG system with advanced capabilities

### v0.4.0 - Personal Memory & Knowledge Graphs

**Priority**: MEDIUM-LOW - Future capabilities

**New Capabilities**:
- Personal memory system with personas
- Temporal knowledge graphs
- Behaviour learning from interactions
- Personalised document ranking
- Plugin architecture for extensibility

**Outcome**: Intelligent personal knowledge assistant with unlimited extensibility

---

## CLI Enhancements Matrix

ragged's CLI receives comprehensive enhancements across versions v0.2.7-v0.4.0, adding 23 new capabilities distributed strategically by version.

**Related Documentation:** [CLI Enhancements Catalogue](../planning/interfaces/cli/enhancements.md)

### Enhancement Distribution by Version

| Version | Enhancements | Hours | Focus Area |
|---------|--------------|-------|------------|
| v0.2.7 | 11 | 48-62 | Foundation (document management, UX basics) |
| v0.3.0 | 11 | 52-71 | Advanced (interactive, automation, developer tools) |
| v0.4.0 | 1 | 20-25 | Extensibility (plugin system) |
| **Total** | **23** | **120-158** | **Comprehensive CLI** |

### v0.2.7 CLI Foundation (11 enhancements, 48-62 hours)

Focus: Essential usability and document management

| # | Enhancement | Priority | Hours | Category |
|---|-------------|----------|-------|----------|
| CLI-001 | Advanced Search & Filtering | High | 3-4 | Document Management |
| CLI-002 | Metadata Management | High | 4-5 | Document Management |
| CLI-003 | Bulk Operations | Medium | 5-6 | Document Management |
| CLI-004 | Export/Import Utilities | Medium | 6-8 | Advanced Features |
| CLI-005 | Output Format Options | High | 3-4 | Query & Retrieval |
| CLI-006 | Query History & Replay | Medium | 4-5 | Query & Retrieval |
| CLI-007 | Verbose & Quiet Modes | High | 2-3 | User Experience |
| CLI-008 | Configuration Validation | High | 3-4 | Configuration & Setup |
| CLI-009 | Environment Information | Medium | 2-3 | Configuration & Setup |
| CLI-010 | Cache Management | Medium | 3-4 | Performance & Debugging |
| CLI-011 | Shell Completion | High | 4-5 | Configuration & Setup |

**Key Capabilities After v0.2.7:**
- ✅ Advanced document search with multiple filters
- ✅ Metadata management without re-ingestion
- ✅ Batch operations for large-scale management
- ✅ Export/import for backup and migration
- ✅ Multiple output formats (JSON, CSV, Markdown)
- ✅ Query history for iterative refinement
- ✅ Configurable verbosity for debugging
- ✅ Configuration validation and diagnostics
- ✅ System information for support requests
- ✅ Cache management for performance tuning
- ✅ Shell completion for bash/zsh/fish

### v0.3.0 Advanced CLI (11 enhancements, 52-71 hours)

Focus: Interactive workflows, automation, and developer productivity

| # | Enhancement | Priority | Hours | Category |
|---|-------------|----------|-------|----------|
| CLI-012 | Interactive Mode (REPL) | High | 8-10 | User Experience |
| CLI-013 | Query Templates & Saved Queries | Medium | 5-6 | Query & Retrieval |
| CLI-014 | Performance Profiling | Medium | 5-6 | Performance & Debugging |
| CLI-015 | Quality Metrics | Medium | 6-8 | Performance & Debugging |
| CLI-016 | Watch Mode | Low | 4-5 | Advanced Features |
| CLI-017 | Scheduled Operations | Low | 5-6 | Advanced Features |
| CLI-018 | Debug Mode | High | 4-5 | Performance & Debugging |
| CLI-019 | Testing Utilities | Medium | 6-8 | Developer Tools |
| CLI-020 | API Server Mode | Low | 8-10 | Advanced Features |
| CLI-021 | Smart Suggestions | Low | 5-6 | Developer Tools |
| CLI-022 | Color Themes & Customisation | Low | 3-4 | User Experience |

**Key Capabilities After v0.3.0:**
- ✅ REPL for exploratory workflows
- ✅ Query templates with parameter substitution
- ✅ Performance profiling for optimisation
- ✅ Quality metrics (RAGAS integration)
- ✅ Automatic document ingestion (watch mode)
- ✅ Scheduled maintenance operations
- ✅ Enhanced debugging with execution traces
- ✅ Testing utilities for custom configurations
- ✅ Local API server for integrations
- ✅ AI-powered query suggestions
- ✅ Customisable colour themes

### v0.4.0 Plugin Architecture (1 enhancement, 20-25 hours)

Focus: Unlimited extensibility

| # | Enhancement | Priority | Hours | Category |
|---|-------------|----------|-------|----------|
| CLI-023 | Plugin System | High | 20-25 | Advanced Features |

**Plugin Interfaces:**
- **Embedder Interface** - Custom embedding models
- **Retriever Interface** - Custom retrieval strategies
- **Processor Interface** - Custom document processors
- **Command Interface** - Custom CLI commands

**Key Capabilities After v0.4.0:**
- ✅ Install/manage plugins via CLI
- ✅ Custom embedders (domain-specific models)
- ✅ Custom retrievers (e.g., graph-based)
- ✅ Custom processors (e.g., LaTeX support)
- ✅ Custom commands (e.g., batch analysis)
- ✅ Plugin discovery via entry points
- ✅ Plugin configuration and validation
- ✅ Security sandboxing for plugins

### Category Summary

| Category | Enhancements | Hours | Examples |
|----------|--------------|-------|----------|
| Document Management | 3 | 12-15 | Search, Metadata, Bulk Ops |
| Query & Retrieval | 3 | 12-15 | Output Formats, History, Templates |
| User Experience | 4 | 18-23 | Verbose/Quiet, Interactive, Themes, Completion |
| Configuration & Setup | 3 | 9-12 | Validation, Env Info, Shell Completion |
| Performance & Debugging | 4 | 18-23 | Cache Mgmt, Profiling, Quality Metrics, Debug |
| Advanced Features | 5 | 37-48 | Export/Import, Watch, Schedule, API, Plugins |
| Developer Tools | 2 | 11-14 | Testing Utilities, Smart Suggestions |

### Implementation Strategy

**Progressive Enhancement Approach:**

1. **v0.2.7** establishes the **foundation**
   - Essential CLI capabilities for document management
   - Basic UX improvements (verbosity, output formats)
   - Troubleshooting tools (config validation, env info)
   - Shell completion for discoverability

2. **v0.3.0** adds **advanced capabilities**
   - Interactive mode for exploratory workflows
   - Automation features (watch, schedule)
   - Developer productivity (profiling, testing, debug)
   - API server for programmatic access

3. **v0.4.0** enables **unlimited extensibility**
   - Plugin architecture allows community contributions
   - Custom embedders, retrievers, processors, commands
   - Security-first plugin sandboxing
   - Foundation for ecosystem growth

**Benefits:**
- Each version delivers complete, usable functionality
- Later versions build on earlier foundations
- Users get value incrementally
- Reduced risk through staged rollout

---

## Priority Recommendations

Based on the analysis, the recommended development sequence is:

1. **v0.2.5 First** (CRITICAL)
   - The API endpoints are currently non-functional, making the Web UI unusable
   - Test coverage gaps create risk for future development
   - Several critical bugs need fixing before adding new features

2. **v0.2.7 Second** (HIGH VALUE)
   - UX improvements have the highest immediate user value
   - Performance optimisations provide measurable benefits
   - These improvements set a strong foundation for v0.3

3. **v0.3.0 Last** (DIFFERENTIATION)
   - Advanced features require stable foundation
   - More complex implementations benefit from improved testing/tooling from earlier versions
   - State-of-the-art features will differentiate ragged from other RAG systems

## Codebase Health (as of v0.2.2)

### Strengths
- ✅ Clean, modular architecture with good separation of concerns
- ✅ Solid test coverage (68%, 262 tests)
- ✅ Excellent documentation culture (devlogs, ADRs, implementation plans)
- ✅ Privacy-first design (100% local processing)
- ✅ Advanced features already implemented (hybrid retrieval, few-shot, contextual chunking)

### Weaknesses
- ❌ API endpoints are placeholder stubs (critical)
- ❌ New modules lack test coverage (0%)
- ❌ Some advanced features not integrated into main workflows
- ❌ Configuration requires file editing
- ❌ No caching or async operations
- ❌ Limited error recovery

## Development Approach

### For v0.2.5
Focus on **quality and stability**:
- Test-first approach: Write tests before fixes
- Thorough error handling audit
- Code review for all changes
- No new features, only fixes and integration

### For v0.2.7
Focus on **measurable improvements**:
- Benchmark before/after for performance changes
- User testing for UX improvements
- Maintain backward compatibility
- Provide migration tools where needed

### For v0.3
Focus on **state-of-the-art**:
- Research-backed implementations (cite papers)
- Comparative evaluation (RAGAS metrics)
- Optional features with feature flags
- Comprehensive documentation for advanced usage

## Using These Roadmaps

Each roadmap document contains:

1. **Detailed Issue Descriptions**
   - Problem statement
   - File locations and line numbers
   - Implementation guidance
   - Code examples

2. **Priority Rankings**
   - P0: Critical - Must fix immediately
   - P1: High - Should fix in this version
   - P2: Medium - Nice to have in this version
   - P3: Low - Can defer to next version

3. **Time Estimates**
   - Hours per issue
   - Total time per version
   - Assumes AI-assisted development

4. **Testing Requirements**
   - Unit tests needed
   - Integration tests needed
   - Edge cases to cover

5. **Implementation Details**
   - Specific code changes
   - Files to modify
   - Breaking changes
   - Migration paths

## Tracking Progress

As you work through these roadmaps:

1. **Update the roadmap documents** to mark completed items
2. **Create time logs** in `docs/development/time-logs/`
3. **Update devlogs** in `docs/development/devlog/`
4. **Reference roadmap items in commits**: `fix(api): BUG-001 - Make API endpoints functional`

## Questions or Changes?

These roadmaps are living documents. If you:
- Discover new issues → Add them to the appropriate roadmap
- Complete items faster → Move ahead to next priority items
- Find items are more complex → Revise time estimates
- Want to reprioritise → Update the priority rankings

The goal is sustainable, high-quality development that builds ragged into a best-in-class RAG system.

---

**Analysis Date**: 2025-11-11
**Current Version**: v0.2.2
**Analysed By**: Claude Code (Sonnet 4.5)
**Total Lines Analysed**: ~15,000 lines across src/, tests/, docs/
