# Development Time Tracking Methodology

**Last Updated**: 2025-11-09
**Purpose**: Transparent time tracking for AI-assisted development
**Status**: Active from v0.1 onwards

---

## Overview

To enhance transparency and reproducibility of ragged's development process, we track **actual time spent** on specific tasks rather than providing vague estimates like "3-4 weeks." This is especially critical for AI-assisted development, where we want to understand:

- How much time AI saves vs. manual coding
- Where AI assistance is most/least effective
- True cost of implementing features
- Realistic expectations for similar projects

## Why Not "Weeks" Estimates?

**Problems with "3-4 weeks" estimates**:
- ❌ Ambiguous: Full-time? Part-time? Whose time?
- ❌ Not reproducible: Doesn't help others planning similar work
- ❌ Hides AI impact: Can't compare AI-assisted vs. manual time
- ❌ No learning: Don't track where time actually went

**What we track instead**:
- ✅ Actual hours spent on specific tasks
- ✅ Breakdown: implementation, debugging, testing, documentation
- ✅ AI vs. manual time
- ✅ What worked, what didn't

## Time Tracking Format

### Per-Feature Time Log

**Location**: `docs/development/time-logs/YYYY-MM-feature-name.md`

**Template**:

```markdown
# Feature: [Feature Name]

**Version**: v0.X
**Status**: Completed | In Progress | Blocked
**Developer**: [Name/Handle]
**Start Date**: YYYY-MM-DD
**Completion Date**: YYYY-MM-DD
**Total Time**: XX.X hours

---

## Time Breakdown

| Phase | Hours | AI-Assisted | Notes |
|-------|-------|-------------|-------|
| Research/Planning | 2.5 | No | Manual research, design decisions |
| Implementation | 8.0 | Yes (Claude Code) | Initial code generation |
| Debugging | 3.5 | Partial | AI helped with error messages |
| Testing | 4.0 | No | Manual test writing |
| Documentation | 2.0 | Yes (Claude Code) | Docstring generation |
| Code Review | 1.5 | No | Manual review and cleanup |
| **TOTAL** | **21.5** | **~50%** | |

## Detailed Log

### 2025-11-09 (3.0 hours)
- **09:00-10:30** (1.5h): Research document processing tools
  - AI: Web search for comparisons
  - Manual: Evaluated trade-offs
- **14:00-15:30** (1.5h): Design normalization pipeline
  - AI: Generated architecture diagram
  - Manual: Refined based on requirements

### 2025-11-10 (5.5 hours)
- **09:00-12:00** (3.0h): Implement Docling integration
  - AI: Initial code scaffolding (30 min equivalent manual: 2h)
  - Manual: Error handling, edge cases (2.5h)
  - **AI Time Saved**: ~1.5 hours
- **14:00-16:30** (2.5h): Write tests
  - Manual: All test code written by hand
  - Rationale: Critical code, need full understanding

### 2025-11-11 (4.0 hours)
- **09:00-11:00** (2.0h): Debug PDF parsing issues
  - AI: Helped interpret error messages
  - Manual: Root cause analysis, fix implementation
- **14:00-16:00** (2.0h): Documentation
  - AI: Generated initial docstrings
  - Manual: Reviewed, added examples, corrected errors

## AI Assistance Details

### Tools Used
- **Claude Code**: Code generation, documentation, debugging assistance
- **GitHub Copilot**: Code completions (enabled but minimal use)

### AI Effectiveness by Task

| Task Type | AI Effectiveness | Time Saved | Notes |
|-----------|------------------|------------|-------|
| Boilerplate code | ⭐⭐⭐⭐⭐ | ~60% | Excellent for setup, imports, class structures |
| Complex logic | ⭐⭐⭐ | ~30% | Good starting point, needs human refinement |
| Error handling | ⭐⭐⭐⭐ | ~40% | AI suggests patterns, human adapts to context |
| Testing | ⭐⭐ | ~10% | AI can generate basic tests, humans write edge cases |
| Documentation | ⭐⭐⭐⭐⭐ | ~70% | Excellent for docstrings, needs human review for accuracy |
| Debugging | ⭐⭐⭐ | ~25% | Helpful for error interpretation, manual fix implementation |

### What Worked Well
- AI scaffolding saved ~1.5 hours on boilerplate
- Documentation generation very effective
- Error message interpretation helped unblock quickly

### What Didn't Work
- AI-generated tests too simplistic, rewrote most
- Edge case handling required manual implementation
- Performance optimization needed human expertise

## Comparison to Estimates

**Original Estimate**: Part of "v0.2: 6-7 weeks"

**Actual Time**: 21.5 hours

**Context**:
- This specific feature (document normalization pipeline)
- Solo developer
- Part-time work (evenings/weekends)
- First time implementing this type of system

**Interpretation**:
- "6-7 weeks" estimate for entire v0.2 is ~100-140 hours (assuming 20h/week part-time)
- This feature: 21.5h (15-20% of v0.2)
- On track if other features similarly scoped

## Learning Points

### For Future Similar Work
1. AI excellent for initial structure, plan 30% time for refinement
2. Write tests manually for critical code
3. Use AI for documentation first draft, review carefully
4. Budget extra time for debugging AI-generated code

### For Reproducibility
- Another developer with similar AI tools: ~25-30 hours
- Experienced developer without AI: ~35-40 hours
- Junior developer without AI: ~60-80 hours

## Blockers & Delays

### Technical Blockers
- **GROBID Docker setup** (2 hours): Unexpected complexity with M1 Mac
- **PaddleOCR CUDA** (1.5 hours): GPU driver issues

### Context Switching
- **Total interruptions**: ~3 hours lost to context switching
- **Mitigation**: Block out focused 2-3 hour sessions

## Metrics Summary

- **Total Time**: 21.5 hours
- **AI-Assisted Time**: ~10.5 hours (49%)
- **Manual Time**: ~11 hours (51%)
- **Estimated Time Saved by AI**: ~8 hours (would have been ~29.5h manual)
- **AI Efficiency**: ~27% faster than manual for this feature
- **Code Written**: ~800 lines (implementation + tests)
- **Lines per Hour**: ~37 (including design, debugging, docs)

---

**Next Feature**: [Link to next time log]
**Previous Feature**: [Link to previous time log]
```

---

## Summary Time Logs

### Version-Level Summary

**Location**: `docs/development/time-logs/v0.X-summary.md`

**Example**:

```markdown
# Version 0.2 Development Time Summary

**Version**: v0.2 (Document Normalization + Enhanced Retrieval + Web UI)
**Status**: Completed
**Start Date**: 2025-11-10
**Completion Date**: 2025-12-22
**Total Development Time**: 127.5 hours

---

## Feature Breakdown

| Feature | Hours | AI % | Status |
|---------|-------|------|--------|
| Document normalization pipeline | 21.5 | 49% | ✅ Complete |
| Docling integration | 8.5 | 60% | ✅ Complete |
| Trafilatura integration | 4.0 | 70% | ✅ Complete |
| PaddleOCR integration | 12.5 | 40% | ✅ Complete |
| GROBID integration | 6.0 | 30% | ✅ Complete |
| Metadata extraction | 9.5 | 55% | ✅ Complete |
| Duplicate detection (SHA256) | 3.5 | 80% | ✅ Complete |
| Duplicate detection (MinHash) | 7.5 | 50% | ✅ Complete |
| SQLite metadata database | 6.0 | 65% | ✅ Complete |
| Hybrid search (BM25 + vector) | 11.0 | 45% | ✅ Complete |
| Cross-encoder reranking | 8.5 | 55% | ✅ Complete |
| Query expansion | 5.5 | 50% | ✅ Complete |
| Caching layer | 4.0 | 70% | ✅ Complete |
| Basic Gradio web UI | 12.0 | 60% | ✅ Complete |
| FastAPI backend | 7.5 | 65% | ✅ Complete |
| **TOTAL** | **127.5** | **~54%** | |

## Phase Breakdown

| Phase | Hours | % of Total |
|-------|-------|------------|
| Implementation | 68.5 | 54% |
| Testing | 25.0 | 20% |
| Documentation | 18.5 | 15% |
| Debugging | 12.5 | 10% |
| Research/Planning | 3.0 | 2% |

## Original Estimate vs. Actual

- **Original Estimate**: "6-7 weeks"
  - Assuming 20h/week: 120-140 hours
  - **Actual**: 127.5 hours ✅ Within estimate

- **Calendar Time**: 42 days (6 weeks)
  - **Average**: 3.0 hours/day
  - **Pattern**: Weekday evenings (1-2h), weekends (5-8h)

## AI Impact Analysis

- **Total Development Time**: 127.5 hours
- **AI-Assisted**: ~69 hours (54%)
- **Manual**: ~58.5 hours (46%)
- **Estimated Manual Time**: ~185 hours
- **Time Saved by AI**: ~57.5 hours (31% faster)

### AI Effectiveness by Task Type

| Task | AI Saves | Works Well For | Struggles With |
|------|----------|----------------|----------------|
| Boilerplate | 60% | Class structures, imports, setup | N/A |
| Business logic | 30% | Initial patterns | Domain-specific logic |
| Testing | 15% | Basic happy-path tests | Edge cases, integration tests |
| Documentation | 70% | Docstrings, READMEs | Accuracy, context |
| Debugging | 25% | Error interpretation | Root cause analysis |
| Architecture | 20% | Pattern suggestions | Design decisions |

## Productivity Metrics

- **Average coding speed**: ~37 lines/hour (including all activities)
- **Peak productivity**: Saturday mornings (8-12h blocks)
- **Lowest productivity**: Weekday evenings after work (context switching)
- **Optimal session length**: 2-3 hours (focused work)

## Blockers & Delays

| Blocker | Time Lost | Category |
|---------|-----------|----------|
| GROBID Docker M1 issues | 2.5h | Technical |
| PaddleOCR CUDA setup | 2.0h | Technical |
| MinHash LSH tuning | 3.5h | Learning |
| Gradio layout bugs | 2.5h | Framework |
| **Total** | **10.5h** | |

## Learning Outcomes

### What Worked
- AI scaffolding for new libraries saved significant time
- Block out 2-3 hour focused sessions on weekends
- Write tests manually for complex logic
- Use AI for documentation first drafts

### What Didn't Work
- AI-generated tests too basic, most rewritten
- Weekday evenings too fragmented for complex work
- Trusting AI for domain-specific logic without review

### For Next Version
- Plan 30% buffer for AI code refinement
- All critical paths tested manually
- Document architectural decisions as we go
- Use devlog for daily progress tracking

## Code Metrics

- **Lines of Code Added**: ~4,850
- **Lines of Tests Added**: ~2,100
- **Test Coverage**: 87%
- **Files Created**: 43
- **Files Modified**: 28

## Comparison to Industry

- **Solo developer, part-time**: 127.5 hours over 6 weeks
- **Experienced team estimate**: ~80-100 hours (full-time, experienced devs)
- **Junior solo estimate**: ~200-250 hours (without AI)
- **Our efficiency**: ~1.3-1.6x faster than junior, ~0.7-0.8x slower than experienced team

---

**Next Version**: [v0.3 summary](./v0.3-summary.md)
**Detailed Logs**: [v0.2 feature logs](./v0.2/)
```

---

## Daily Development Log (devlog)

**Location**: `docs/development/devlog/YYYY-MM-DD.md`

**Purpose**: Capture daily progress, decisions, blockers

**Template**:

```markdown
# Development Log - 2025-11-09

**Focus**: Document normalization pipeline design
**Time Spent**: 4.5 hours
**Status**: On track

---

## What I Did Today

### Morning Session (09:00-12:00) - 3.0 hours

#### Researched document processing tools
- Compared Docling, Marker, PyMuPDF4LLM
- Read benchmarks and documentation
- **AI Used**: Claude Code for web search synthesis
- **Decision**: Use Docling as primary (best table extraction)

#### Designed normalization pipeline
- Created architecture diagram
- Identified format-specific processors
- **AI Used**: Claude Code generated initial diagram, I refined
- **Output**: `docs/implementation/plan/core-concepts/document-normalization.md`

### Afternoon Session (14:00-16:00) - 1.5 hours

#### Started metadata schema design
- Defined base metadata fields
- Researched GROBID output format
- **AI Used**: Minimal (reading docs manually)
- **Output**: Draft schema in notes

---

## Decisions Made

### Use Docling over Marker for primary PDF processing
- **Reason**: 97.9% table accuracy critical for academic papers
- **Trade-off**: Slightly slower, but quality matters more
- **Recorded in**: ADR-0015

### Store metadata in SQLite + JSON sidecar files
- **Reason**: SQLite for queries, JSON for flexibility/backup
- **Alternative considered**: PostgreSQL (overkill for local use)
- **Recorded in**: ADR-0016

---

## Blockers

None today

---

## For Tomorrow

- [ ] Complete metadata schema spec
- [ ] Design duplicate detection strategy
- [ ] Start MinHash research

---

## AI Assistance Today

**Tools Used**: Claude Code

**Tasks**:
1. Web research synthesis (1.0h) - ⭐⭐⭐⭐⭐ Very effective
2. Architecture diagram generation (0.5h) - ⭐⭐⭐⭐ Good, needed refinement
3. Documentation drafting (0.5h) - ⭐⭐⭐⭐⭐ Excellent first draft

**Time Saved**: ~1.5 hours (would have been ~6h manual research/writing)

**What Worked**: AI excellent at synthesizing research, creating first drafts
**What Didn't**: Needed manual refinement for domain-specific accuracy

---

## Code Stats

- **Lines written**: 0 (design day)
- **Documentation written**: ~3,500 words

---

## Energy & Focus

- **Energy**: High (weekend, well-rested)
- **Focus**: Good (2-3 hour blocks ideal)
- **Interruptions**: 2 (took breaks, didn't impact flow)

---

**Previous**: [2025-11-08](./2025-11-08.md)
**Next**: [2025-11-10](./2025-11-10.md)
```

---

## Aggregated Metrics Dashboard

**Location**: `docs/development/metrics-dashboard.md`

**Purpose**: High-level overview of entire project progress

```markdown
# ragged Development Metrics Dashboard

**Last Updated**: 2025-12-22
**Current Version**: v0.2 (in development)

---

## Project Timeline

```
v0.1: 2025-10-15 to 2025-11-05 (21 days, 52.5 hours)
v0.2: 2025-11-10 to 2025-12-22 (42 days, 127.5 hours)
v0.3: Not started
```

## Cumulative Time

- **Total Development Time**: 180.0 hours
- **AI-Assisted Time**: 95.4 hours (53%)
- **Manual Time**: 84.6 hours (47%)
- **Estimated Manual Equivalent**: ~265 hours
- **Time Saved by AI**: ~85 hours (32% faster overall)

## Version Breakdown

| Version | Status | Hours | AI % | Features |
|---------|--------|-------|------|----------|
| v0.1 | ✅ Complete | 52.5 | 48% | 5 |
| v0.2 | ✅ Complete | 127.5 | 54% | 15 |
| v0.3 | 🔄 In Progress | 28.0 | 58% | 3/8 |
| v0.4 | ⏸️ Not Started | 0 | - | 0 |
| v0.5 | ⏸️ Not Started | 0 | - | 0 |
| v1.0 | ⏸️ Not Started | 0 | - | 0 |

## Code Metrics

- **Total Lines of Code**: 12,450
- **Total Test Code**: 5,230
- **Test Coverage**: 85%
- **Files**: 127
- **Commits**: 342

## AI Effectiveness Trends

```
v0.1: 48% AI-assisted → 28% time saved
v0.2: 54% AI-assisted → 31% time saved
v0.3: 58% AI-assisted → 35% time saved (so far)

Trend: AI effectiveness improving as I learn to use it better
```

## Productivity Patterns

**Best Times**:
- Saturday mornings: 4.2 hours/session average
- Sunday afternoons: 3.8 hours/session average

**Worst Times**:
- Weekday evenings: 1.3 hours/session (too fragmented)

**Optimal Session Length**: 2-3 hours (diminishing returns after 4h)

## Common Blockers

| Blocker Type | Frequency | Avg Time Lost |
|--------------|-----------|---------------|
| Dependency issues | 8 | 2.1h |
| Learning curve | 12 | 3.2h |
| Context switching | 24 | 0.8h |
| AI code refinement | 18 | 1.5h |

## Learning Velocity

**Time to Implement Similar Features**:
- v0.1: First hybrid search implementation: 11.0h
- v0.2: Second search feature (reranking): 8.5h
- v0.3: Third search feature (query expansion): 5.5h

**Improvement**: ~50% faster by third iteration (learning curve + AI)

---

## Comparison to Estimates

| Metric | Original Plan | Actual | Variance |
|--------|---------------|--------|----------|
| v0.1 timeline | "2-3 weeks" | 21 days | ✅ On track |
| v0.1 hours | ~40-60h (assumed) | 52.5h | ✅ Within range |
| v0.2 timeline | "6-7 weeks" | 42 days (6 weeks) | ✅ On track |
| v0.2 hours | ~120-140h (assumed) | 127.5h | ✅ Within range |

**Accuracy**: Original estimates surprisingly close (assuming 20h/week part-time)
```

---

## How to Use This System

### Daily

1. **Start of day**: Review yesterday's devlog, plan today
2. **During work**: Note start/stop times, track what you're doing
3. **End of day**: Fill out daily devlog (10-15 minutes)

### Per Feature

1. **Start feature**: Create feature time log from template
2. **During work**: Update detailed log with sessions
3. **Complete feature**: Fill out summary sections, metrics

### Per Version

1. **Start version**: Note start date
2. **Complete version**: Create version summary
3. **Analyze**: Compare to estimates, document learnings

### Quarterly Review

1. Review all metrics
2. Identify patterns (what works, what doesn't)
3. Adjust processes
4. Update methodology if needed

---

## Benefits

### For You (Developer)

- **Accountability**: Know where time actually goes
- **Learning**: See AI effectiveness patterns
- **Planning**: Better estimates for future work
- **Motivation**: Visible progress tracking

### For Users

- **Transparency**: Understand development effort
- **Reproducibility**: Others can estimate similar projects
- **Trust**: Shows honest, rigorous development process

### For Researchers

- **Data**: Quantitative AI-assisted development data
- **Case Study**: Real-world AI coding effectiveness
- **Reproducibility**: Can replicate development approach

### For Future You

- **Reference**: "How long did X take?"
- **Comparison**: "Am I getting faster?"
- **Validation**: "Was AI actually helpful?"

---

## Privacy Considerations

**What to Share Publicly**:
- ✅ Time spent (aggregated)
- ✅ AI effectiveness ratings
- ✅ General task types
- ✅ Feature completion times
- ✅ Blockers and solutions

**What to Keep Private** (if sensitive):
- ❌ Exact hourly rates / compensation
- ❌ Specific client/employer information
- ❌ Proprietary algorithms (if applicable)
- ❌ Personal calendar details

**For ragged** (open source, personal project):
- Share everything - full transparency
- Helps community understand AI development
- Contributes to research on AI coding assistants

---

## Integration with Version Control

### Commit Messages

Include time in relevant commits:

```
feat: Add document normalization pipeline

Implemented Docling integration for PDF processing.

Time: 3.5 hours (implementation), 1.5 hours (testing)
AI-Assisted: Claude Code (initial scaffolding)
Closes #42
```

### Git Tags

Tag time logs with versions:

```bash
git tag -a v0.2-complete -m "v0.2 development complete (127.5 hours)"
```

### Branch Naming

Include tracking reference:

```
feature/document-normalization-TL-2025-11
```

Where `TL-2025-11` = Time Log November 2025

---

## Example: Replacing Vague Estimates

### Before (Vague)

> **v0.2: Enhanced Retrieval** (3-4 weeks)
>
> Add hybrid search and reranking.

### After (Transparent)

> **v0.2: Document Normalization + Enhanced Retrieval**
>
> **Actual Development Time**: 127.5 hours (tracked)
> **Calendar Time**: 42 days (part-time, weekends + evenings)
> **Working Pattern**: ~3 hours/day average (weekday 1-2h, weekend 5-8h)
> **AI Assistance**: 54% of time (~31% faster than manual)
>
> **Features Completed** (with individual time logs):
> - Document normalization: [21.5h](./time-logs/2025-11-doc-normalization.md)
> - Hybrid search: [11.0h](./time-logs/2025-11-hybrid-search.md)
> - Web UI: [12.0h](./time-logs/2025-12-web-ui.md)
> - [Full breakdown](./time-logs/v0.2-summary.md)

---

## Tools to Help

### Time Tracking Apps

- **Toggl Track**: Simple start/stop timer
- **Clockify**: Free, unlimited tracking
- **Timeular**: Physical tracker for focus
- **WakaTime**: Automatic coding time (IDE plugin)

### Git-Based Tracking

```bash
# Commit with time info
git commit -m "feat: Add feature X

Time: 2.5 hours
AI: Claude Code (scaffolding)"

# Extract time from git log
git log --grep="Time:" --pretty=format:"%s %b"
```

### Automation

```python
# Script to parse time from commits
import re

def extract_time_from_commits():
    commits = get_git_log()
    total_hours = 0

    for commit in commits:
        match = re.search(r'Time: ([\d.]+) hours', commit.message)
        if match:
            total_hours += float(match.group(1))

    return total_hours
```

---

## Template Files

All templates available in `docs/development/templates/`:

- `feature-time-log-template.md`
- `daily-devlog-template.md`
- `version-summary-template.md`
- `metrics-dashboard-template.md`

---

## Conclusion

By tracking **actual time spent** instead of vague "weeks" estimates, we achieve:

1. **Transparency**: Others can see real development effort
2. **Reproducibility**: Similar projects can use our data for planning
3. **AI Insights**: Quantify AI effectiveness for different tasks
4. **Learning**: Identify productivity patterns and improve
5. **Accountability**: Honest reporting of work done
6. **Research Value**: Contribute data to AI-assisted development research

This methodology transforms development documentation from **aspirational estimates** to **empirical evidence**.

---

**Start Date**: 2025-11-09
**Status**: Active - applied to all ragged development from v0.1 onwards
**Next Review**: After v0.3 completion (assess methodology effectiveness)
