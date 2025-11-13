# Ragged Version Roadmaps

This directory contains detailed roadmaps for upcoming ragged versions, created on 2025-11-11 based on comprehensive codebase analysis.

## Overview

The roadmaps are organised into three major versions, each with distinct focus areas:

| Version | Focus | Timeline | Estimated Hours |
|---------|-------|----------|-----------------|
| [v0.2.5](v0.2.5-roadmap.md) | Bug Fixes & Stability | 1-2 weeks | 40-50 hours |
| [v0.2.7](v0.2.7-roadmap.md) | UX & Performance | 3-4 weeks | 80-100 hours |
| [v0.3.0](v0.3.0-roadmap.md) | Advanced RAG Features | 6-8 weeks | 180-220 hours |

**Total Timeline**: 9-13 weeks for all three versions

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

## Priority Recommendations

Based on the analysis, the recommended development sequence is:

1. **v0.2.5 First** (CRITICAL)
   - The API endpoints are currently non-functional, making the Web UI unusable
   - Test coverage gaps create risk for future development
   - Several critical bugs need fixing before adding new features

2. **v0.2.7 Second** (HIGH VALUE)
   - UX improvements have the highest immediate user value
   - Performance optimizations provide measurable benefits
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
