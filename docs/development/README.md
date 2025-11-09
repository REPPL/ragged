# Development Process Documentation

**Transparency in AI-Assisted Software Development**

---

## Overview

This directory contains comprehensive documentation of ragged's development process. Unlike typical project documentation, we document **how the software is being built**, not just what it does.

## Why Document Development Process?

1. **Transparency**: Show how AI tools (Claude Code, etc.) are used in development
2. **Reproducibility**: Enable others to understand and replicate our approach
3. **Learning**: Share lessons learned from AI-assisted development
4. **Research**: Contribute data to understanding AI coding effectiveness
5. **Accountability**: Honest tracking of time, effort, and challenges

## Directory Structure

```
development/
├── README.md (this file)
├── ai-assistance.md              # How AI tools are used in ragged
├── time-tracking-methodology.md  # How we track actual development time
│
├── devlog/                       # Daily development logs
│   ├── 2025-11-09.md
│   ├── 2025-11-10.md
│   └── ...
│
├── decisions/                    # Architecture Decision Records (ADRs)
│   ├── 0001-use-diataxis.md
│   ├── 0002-markdown-normalization.md
│   └── ...
│
├── rfcs/                         # Request for Comments (major features)
│   └── (Will be added for major feature proposals)
│
├── time-logs/                    # Actual time tracking per feature/version
│   ├── v0.1-summary.md
│   ├── v0.2-summary.md
│   ├── 2025-11-doc-normalization.md
│   └── ...
│
└── templates/                    # Templates for development docs
    ├── adr-template.md
    ├── devlog-template.md
    ├── feature-time-log-template.md
    └── version-summary-template.md
```

## Key Documents

### AI Assistance Documentation

**[ai-assistance.md](./ai-assistance.md)** (coming soon)

Documents how AI tools are used:
- Which tools (Claude Code, GitHub Copilot, etc.)
- For what tasks (scaffolding, documentation, debugging)
- Effectiveness ratings by task type
- Guidelines for contributors using AI

### Time Tracking

**[time-tracking-methodology.md](./time-tracking-methodology.md)**

Explains our approach to tracking **actual time spent** instead of vague estimates:
- Per-feature time logs with hour breakdowns
- AI vs. manual time comparison
- What worked, what didn't
- Realistic expectations for similar work

**Time Logs** (`time-logs/`):
- Actual hours spent on each feature
- Breakdown: implementation, testing, debugging, documentation
- AI assistance percentage
- Learning outcomes

### Development Logs

**Daily Devlogs** (`devlog/`):
- What was accomplished each day
- Decisions made
- Blockers encountered
- AI tool effectiveness
- Energy and focus levels

**Purpose**: Chronicle the actual development journey, not just outcomes.

### Architecture Decision Records

**ADRs** (`decisions/`):
- Why we made specific architectural choices
- Alternatives considered
- Trade-offs accepted
- Context for future maintainers

**Format**: Numbered sequentially (0001, 0002, etc.)

### Request for Comments

**RFCs** (`rfcs/`):
- Major feature proposals
- Seeking community feedback
- Technical design discussions

**When to use**: Substantial changes that need discussion (not bug fixes)

## Using This Documentation

### For Users

- **Curious about AI development?** Read `ai-assistance.md` and time logs
- **Want to understand decisions?** Check ADRs in `decisions/`
- **See actual progress?** Read devlogs

### For Contributors

- **Using AI tools?** Follow guidelines in `ai-assistance.md`
- **Making architectural decisions?** Create an ADR
- **Proposing major features?** Write an RFC
- **Tracking your time?** Use templates in `templates/`

### For Researchers

- **Studying AI coding?** Time logs provide quantitative data
- **Reproducibility?** Devlogs and ADRs show full process
- **Case study material?** Complete development history

### For Future You

- **"Why did we do X?"** → Check ADRs
- **"How long did Y take?"** → Check time logs
- **"What happened on date Z?"** → Check devlogs

## Transparency Principles

### We Document

✅ Actual time spent (hours, not "weeks")
✅ AI tool usage and effectiveness
✅ Decisions and trade-offs
✅ Blockers and how they were resolved
✅ What worked and what didn't
✅ Learning outcomes

### We Don't Hide

❌ Mistakes or failed approaches
❌ AI-generated code (disclosed openly)
❌ Time spent debugging
❌ Learning curves
❌ Challenges encountered

## Development Philosophy

### AI as Aid, Not Substitute

- AI tools amplify human expertise, don't replace it
- All AI-generated code is reviewed and understood
- Developers are accountable for all submitted code
- Critical code paths are written manually

### Empirical Over Aspirational

- Track actual time, not estimates
- Document real decisions, not ideal ones
- Share failures alongside successes
- Learn from data, not assumptions

### Open Development

- Development process is public
- Decisions are documented
- Community can see how ragged is built
- Academic research can use our data

## Timeline

**Established**: 2025-11-09 (during planning phase)
**Applied from**: v0.1 onwards (all development tracked)
**Review cadence**: After each version release

## Templates

All templates are in `templates/` directory:

- **ADR Template**: For architecture decisions
- **Devlog Template**: For daily development logs
- **Feature Time Log Template**: For tracking feature development time
- **Version Summary Template**: For version-level time summaries

## Contributing

When contributing to ragged (post-v0.1):

1. **Use AI tools?** Disclose in PR (see `ai-assistance.md`)
2. **Making architectural decisions?** Create ADR
3. **Proposing major features?** Write RFC
4. **Significant time investment?** Create time log

See [Contributing Guide](../contributing/README.md) for details.

## Example: Transparency in Action

**Instead of saying**:
> "v0.2 will take 6-7 weeks and add document normalization"

**We document**:
> **v0.2 Development Summary**
> - **Actual time**: 127.5 hours over 42 days
> - **AI assistance**: 54% of time (~31% faster than manual)
> - **Features**: 15 completed, each with individual time log
> - **Challenges**: GROBID Docker setup (2.5h), MinHash tuning (3.5h)
> - **Learning**: AI excellent for boilerplate, tests need manual work
> - **Full breakdown**: [v0.2-summary.md](./time-logs/v0.2-summary.md)

This gives:
- **Realistic expectations** for similar work
- **Insight into AI effectiveness** for different tasks
- **Honest accounting** of challenges
- **Reproducible data** for research

## Questions?

- **About development process**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **About specific decisions**: Check ADRs in `decisions/`
- **About time estimates**: See `time-tracking-methodology.md`

---

**This is a living process.** We'll refine our transparency practices as we learn what's most valuable for the community and research.

**Last updated**: 2025-11-09
**Status**: Active - all ragged development tracked from v0.1 onwards
