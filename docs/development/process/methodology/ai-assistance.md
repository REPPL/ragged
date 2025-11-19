# Policy for using AI Assistance


**Next planned Review**: After v0.3 completion (assess effectiveness and refine)

*The aim of the `ragged` project is to learn about **transparent use of AI coding assistants**. This document explains which tools are used, how they're used, and the policies around AI-assisted development.*

---

## Philosophy

**AI as a synthetic teammate**

I used to view AI [as a synthetic teammate](https://doi.org/10.1016/j.bushor.2025.02.008) to be treated as a junior colleage. While this remains a useful framing, my aim for this project is to push the concept of a `synthetic teammate` further. Instead of a junior collaborator, I am treating an AI coding assistant as the main (i.e., only) developer, while my role is to direct the project.

In other words, my aim is to explore whether it is possible for a non-programmer (i.e., me) (a) to develop a fairly sophisticated software and (b) to document the use of AI in a transparent and (to some extend) reproducible way.

*Source:* [https://doi.org/10.1016/j.bushor.2025.02.008](https://doi.org/10.1016/j.bushor.2025.02.008)

Consequently, instead of a junior developer where:

- AI tools **amplify human expertise** but don't replace it
- All AI-generated code is **reviewed and understood** by human developers
- Developers are **fully accountable** for all submitted code
- Critical code paths (security, core algorithms) are **written manually**

This project treats the AI coding assistant as a senior developer where:

- AI usage is **disclosed openly** in commits, PRs, and documentation
- We track **what works and what doesn't** with AI assistance
- **Time savings** are measured and reported honestly
- **Failures and limitations** are documented, not hidden

---

## Acknowledgments

This AI assistance policy was developed with assistance from **Claude Code** (Anthropic, model: claude-sonnet-4-5-20250929) during `ragged`'s planning phase (November 2025). This project is informed by:

- Ghostty project's AI disclosure requirements
- AIDA (AI Included Disclosure Acknowledgment) framework
- Academic AI disclosure standards (ICMJE 2024)
- GitHub's AI governance best practices

---

## Tools

### Claude Code (Primary tool)

**Version**: claude-sonnet-4-5-20250929
**Usage**: Primary AI assistant for `ragged` development

**Owns**:

- Code (incl. docstrings)
- Documentation (implementation plan)
- Debugging (error interpretation)
- Architectural design (proposals & discussion)
- Initial research (SOTA)
- Test cases

**Supports**:

- Architectural decisions
- Documentation (user facing)

*(See also [Time Tracking](./time-tracking-methodology.md) for detailed metrics.)*

---

## Learnings (so far)

### What AI is and is not good at

**AI is Exceptionally Good At**:

- Boilerplate and repetitive code
- Documentation first drafts
- Suggesting libraries and patterns
- Explaining error messages
- Generating initial test structures

**AI Struggles With**:

- Domain-specific logic
- Complex error handling
- Edge cases

**AI Sometimes Struggles With**:

- Understanding project context
- Performance optimisation

**Human Essential For**:

- Understanding user needs
- Architectural decisions (balancing trade-offs)
- Creative problem solving
- Performance tuning (real-world testing)
- Security review (ignored in this project)

### Current DOs and DON'Ts

1. Give AI clear, specific prompts
2. Provide project context in prompts
3. Use AI output as starting point, not end
4. Iterate with AI (don't accept first try)

✅ **DO use AI for**:

- Initial code structure and boilerplate
- Documentation first drafts
- Researching libraries and APIs
- Understanding error messages
- Generating test case ideas
- Refactoring suggestions

✅ **DO disclose AI usage** in:

- Commit messages
- Development logs
- Time tracking records

❌ **DO NOT use AI for**:

- Final architectural decisions
- Accepting code you don't understand
- Critical algorithms without deep review

### Best Practice (ignored in this Project)

1. Code reviewed line-by-line by a human
2. Code understood by the reviewer
3. Tests written manually
4. Security code written 100% manually

### Planned Evolution of AI Use

**v0.1** (learning phase):

- AI: ~45% of time
- Time saved: ~25% (learning overhead)
- Lots of trial and error

**v0.2** (improving):

- AI: ~54% of time
- Time saved: ~31% (better prompting)
- Clear patterns emerging

**v0.3+** (expected):

- AI: ~55-60% of time
- Time saved: ~35-40% (optimised workflow)
- Know exactly when/how to use AI

---

## Disclosure Statements

### In Pull Requests

**PR Template includes**:

```markdown
## AI Assistance Used?

- [ ] No AI tools were used
- [ ] Minor AI assistance (autocomplete, suggestions < 20% of code)
- [ ] Significant AI assistance (code generation ≥ 20% of code)

If AI was used, please describe:
- **Tool(s)**: (Claude Code, GitHub Copilot, etc.)
- **Affected files/sections**:
- **Level of human review**: (Modified significantly / Minor changes / Used as-is)
- **Justification for using AI**:
```

**Example**:

```markdown
## AI Assistance Used?

- [x] Significant AI assistance

- **Tool(s)**: Claude Code
- **Affected files/sections**:
  - `src/ragged/document_processor.py` (initial class structure)
  - `docs/guides/document-processing.md` (first draft)
- **Level of human review**: Modified significantly
  - Added custom error handling
  - Rewrote validation logic
  - Added domain-specific optimisations
- **Justification**: Accelerated boilerplate generation for new module
```

### In Commit Messages

**For significant AI use** (>30% of commit content):

```bash
git commit -m "feat: Add document normalisation pipeline

Implemented markdown conversion for PDF, HTML, DOCX formats.

AI-Assisted: Claude Code (initial structure)
Human: Error handling, edge cases, optimisation
Time: 3.5h (1.5h AI scaffolding + 2h human work)"
```

**For minor AI use** (<30%):
```bash
git commit -m "feat: Add caching layer

Implemented Redis-based query caching.

Time: 2.0h"
```

*(Minor AI assistance doesn't require explicit mention.)*


### In Development Logs

**Daily devlog** includes AI effectiveness:

```markdown
### 2025-11-10

**AI Assistance Today**:
- **Tools**: Claude Code
- **Tasks**:
  1. Code scaffolding (1.5h) - ⭐⭐⭐⭐⭐ Excellent
  2. Documentation (0.5h) - ⭐⭐⭐⭐ Good, needed edits
- **Time Saved**: ~1.5 hours vs. manual
- **What Worked**: Initial structure generation
- **What Didn't**: Tests too simplistic, rewrote manually
```

**Feature time log** includes AI breakdown:

```markdown
| Phase | Hours | AI-Assisted | Notes |
|-------|-------|-------------|-------|
| Implementation | 8.0 | Yes (Claude Code) | Initial scaffolding |
| Debugging | 3.5 | Partial | AI helped with errors |
| Testing | 4.0 | No | Manual test writing |
```

---

## Tracking of AI Use

### By Task Type

Based on actual `ragged` development data:

| Task | AI Tool | Time Saved | Quality | Best For |
|------|---------|------------|---------|----------|
| **Boilerplate code** | Claude Code | ~60% | ⭐⭐⭐⭐⭐ | Class structures, imports, setup |
| **Documentation** | Claude Code | ~70% | ⭐⭐⭐⭐⭐ | Docstrings, guides, explanations |
| **Complex logic** | Claude Code | ~30% | ⭐⭐⭐ | Starting point, needs refinement |
| **Testing** | Claude Code | ~15% | ⭐⭐ | Basic tests only, edge cases manual |
| **Debugging** | Claude Code | ~25% | ⭐⭐⭐ | Error interpretation, suggestions |
| **Research** | Claude Code | ~50% | ⭐⭐⭐⭐ | Summarizing docs, comparisons |
| **Code completion** | GitHub Copilot | ~10% | ⭐⭐ | Reducing typing, minor help |


### Overall Metrics (Target)

Based on `ragged`'s [Time Tracking Methodology](./time-tracking-methodology.md):

- **Overall AI-assisted time**: ~50-55% of development
- **Overall time saved**: ~30-35% faster than manual
- **Code quality**: Same or better than manual (due to forced review)
- **Learning**: Slower initially, faster as patterns emerge

*(See [`time-logs/`](./time-logs/) for actual version-by-version data.)*

---

## Code Review Standards

**All code** must meet:

- ✅ Passes all tests (>80% coverage)
- ✅ Follows PEP 8 (black, ruff)
- ✅ Type hints (mypy strict mode)
- ✅ Documented (Google-style docstrings)
- ✅ Understandable to reviewers
- ✅ Edge cases are handled (AI often misses these)
- ✅ Error handling is robust

---

## Further Research

### Data for AI Coding Research

`ragged`'s development provides quantitative and qualitative data on:

- Time savings per task type
- Learning curve with AI tools
- Effectiveness across project phases
- Real-world AI coding patterns
- Qualitative observations in devlogs
- Version-to-version changes

See also [`time-logs/`](./time-logs/) and [`devlog/`](./devlog/).

### Academic Context

**Disclosure Standards**:

- Follows ICMJE 2024 guidelines
- AI usage in acknowledgments (writing assistance)
- AI usage in methods (if applicable to research)

**Transparency Goal**:

- Contribute to understanding AI-assisted development
- Provide reproducible case study
- Share lessons learned openly

---

## Feedback

Have suggestions for improving AI usage transparency?

- **Discuss**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **Propose Changes**: [GitHub Issues](https://github.com/REPPL/ragged/issues)

---

## Related Documentation

- [Time Tracking Methodology](./time-tracking-methodology.md) - How we track AI vs. manual time
- [Development Logs](./devlog/) - Daily AI effectiveness ratings
- [Contributing Guide](../../../../CONTRIBUTING.md) - General contribution guidelines


