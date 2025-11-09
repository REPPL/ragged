# AI Assistance in ragged Development

**Last Updated**: 2025-11-09
**Purpose**: Transparent documentation of AI tool usage in ragged development
**Status**: Active policy from v0.1 onwards

---

## Overview

ragged is developed with **transparent use of AI coding assistants**. This document explains which tools are used, how they're used, and our policies around AI-assisted development.

## Philosophy

**AI as Aid, Not Substitute**

- AI tools **amplify human expertise**, they don't replace it
- All AI-generated code is **reviewed and understood** by human developers
- Developers are **fully accountable** for all submitted code
- Critical code paths (security, core algorithms) are **written manually**

**Transparency First**

- AI usage is **disclosed openly** in commits, PRs, and documentation
- We track **what works and what doesn't** with AI assistance
- **Time savings** are measured and reported honestly
- **Failures and limitations** are documented, not hidden

---

## Tools Used

### Primary Tools

#### Claude Code (Anthropic)

**Version**: claude-sonnet-4-5-20250929
**Usage**: Primary AI assistant for ragged development

**Used For**:
- Code scaffolding and boilerplate generation
- Documentation drafting (docstrings, markdown)
- Architectural design discussions
- Debugging assistance (error interpretation)
- Research synthesis
- Test case generation (initial drafts)

**Not Used For**:
- Final decision-making (human makes all architectural decisions)
- Security-critical code (written manually)
- Direct code commits without human review

**Effectiveness** (based on tracked data):
- Boilerplate code: ⭐⭐⭐⭐⭐ (60% time saved)
- Documentation: ⭐⭐⭐⭐⭐ (70% time saved)
- Complex logic: ⭐⭐⭐ (30% time saved)
- Testing: ⭐⭐ (15% time saved)
- Debugging: ⭐⭐⭐ (25% time saved)

See [Time Tracking](./time-tracking-methodology.md) for detailed metrics.

#### GitHub Copilot (Optional)

**Usage**: Code completions within IDE

**Used For**:
- In-line code suggestions
- Auto-completing common patterns
- Suggesting function signatures

**Effectiveness**:
- Helpful for reducing typing, not strategic coding
- Most suggestions require modification
- Not tracked separately from manual coding

---

## Use Cases and Guidelines

### When to Use AI

✅ **DO use AI for**:
- Initial code structure and boilerplate
- Documentation first drafts
- Researching libraries and APIs
- Understanding error messages
- Generating test case ideas
- Refactoring suggestions

✅ **DO disclose AI usage** in:
- Pull request descriptions
- Commit messages (for significant AI use)
- Development logs
- Time tracking records

### When NOT to Use AI

❌ **DO NOT use AI for**:
- Security-critical authentication/authorization code
- Cryptographic implementations
- Final architectural decisions
- Accepting code you don't understand
- Critical algorithms without deep review

❌ **DO NOT**:
- Submit AI code without reviewing and understanding it
- Use AI as excuse for lower code quality
- Hide or obscure AI usage
- Trust AI blindly for correctness

### Review Requirements

**All AI-generated code must**:
1. Be reviewed line-by-line by a human
2. Be understood by the reviewer
3. Have tests written (often manually)
4. Meet the same quality standards as manual code
5. Be modified where necessary

**Critical Code Requirements**:
- Security code: 100% manual
- Core algorithms: >75% manual, AI only for boilerplate
- Tests for critical code: 100% manual

---

## Disclosure Standards

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
  - Added domain-specific optimizations
- **Justification**: Accelerated boilerplate generation for new module
```

### In Commit Messages

**For significant AI use** (>30% of commit content):

```bash
git commit -m "feat: Add document normalization pipeline

Implemented markdown conversion for PDF, HTML, DOCX formats.

AI-Assisted: Claude Code (initial structure)
Human: Error handling, edge cases, optimization
Time: 3.5h (1.5h AI scaffolding + 2h human work)"
```

**For minor AI use** (<30%):
```bash
git commit -m "feat: Add caching layer

Implemented Redis-based query caching.

Time: 2.0h"
```

(Minor AI assistance doesn't require explicit mention)

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

## AI Effectiveness Tracking

### By Task Type

Based on actual ragged development data:

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

Based on ragged's time tracking methodology:

- **Overall AI-assisted time**: ~50-55% of development
- **Overall time saved**: ~30-35% faster than manual
- **Code quality**: Same or better than manual (due to forced review)
- **Learning**: Slower initially, faster as patterns emerge

See [`time-logs/`](./time-logs/) for actual version-by-version data.

---

## Contributor Guidelines

### If You Use AI Tools

**Required**:

1. **Disclose in PR**: Use PR template to indicate AI usage
2. **Understand the code**: You must be able to explain every line
3. **Review carefully**: AI code is starting point, not final product
4. **Test thoroughly**: Especially AI-generated code
5. **Document honestly**: What AI did vs. what you did

**Best Practices**:

- Use AI for scaffolding, human for refinement
- Write tests manually for complex code
- Review AI suggestions critically
- Modify AI code to fit ragged's patterns
- Learn from AI suggestions, don't blindly accept

### If You Don't Use AI Tools

**That's completely fine!**

- Manual coding is always welcome
- No pressure to use AI
- Sometimes manual is better (security, algorithms)
- Disclose "no AI used" in PR for transparency

### Code Review Standards

**All code** (AI-assisted or manual) must meet:

- ✅ Passes all tests (>80% coverage)
- ✅ Follows PEP 8 (black, ruff)
- ✅ Type hints (mypy strict mode)
- ✅ Documented (Google-style docstrings)
- ✅ Understandable to reviewers

**AI-assisted code** gets extra scrutiny:

- ✅ Reviewer confirms contributor understands code
- ✅ Edge cases are handled (AI often misses these)
- ✅ Error handling is robust
- ✅ Performance is acceptable
- ✅ Code fits ragged's architecture

---

## Learning from AI Assistance

### What We've Learned

**AI is Good At**:
- Boilerplate and repetitive code
- Documentation first drafts
- Suggesting libraries and patterns
- Explaining error messages
- Generating initial test structures

**AI Struggles With**:
- Domain-specific logic
- Complex error handling
- Edge cases and corner cases
- Performance optimization
- Understanding project context

**Human Essential For**:
- Architectural decisions
- Security review
- Performance tuning
- Understanding user needs
- Creative problem solving

### Improving AI Effectiveness

**Over time, we've learned to**:
1. Give AI clear, specific prompts
2. Provide project context in prompts
3. Use AI output as starting point, not end
4. Iterate with AI (don't accept first try)
5. Know when to switch to manual coding

### Evolution of AI Use

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
- Time saved: ~35-40% (optimized workflow)
- Know exactly when/how to use AI

---

## Research Contribution

### Data for AI Coding Research

ragged's development provides **quantitative data** on:

- Time savings per task type
- Quality comparison (AI vs. manual)
- Learning curve with AI tools
- Effectiveness across project phases
- Real-world AI coding patterns

**Available to researchers**:
- Aggregated time tracking data
- Task-level AI effectiveness ratings
- Qualitative observations in devlogs
- Version-to-version evolution

See [`time-logs/`](./time-logs/) and [`devlog/`](./devlog/).

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

## Policy Updates

This policy may be updated as:
- New AI tools emerge
- We learn better practices
- Community provides feedback
- Research standards evolve

**Changes will be**:
- Documented in git history
- Announced in changelogs
- Applied to future contributions
- Not retroactively applied to past work

---

## Questions and Discussion

### FAQs

**Q: Do I have to use AI tools to contribute?**
A: No! Manual contributions are always welcome.

**Q: What if I use AI but forget to disclose?**
A: Update your PR description when you remember. Honest mistake.

**Q: Can I use other AI tools besides those listed?**
A: Yes! Disclose which tools you used in your PR.

**Q: How detailed should AI disclosure be?**
A: Enough for reviewers to understand scope. See PR template.

**Q: What if AI generated most of the code?**
A: That's okay if you reviewed, understood, and tested it thoroughly. Disclose percentage and review depth.

### Feedback

Have suggestions for improving AI usage transparency?

- **Discuss**: [GitHub Discussions](https://github.com/REPPL/ragged/discussions)
- **Propose Changes**: [GitHub Issues](https://github.com/REPPL/ragged/issues)

---

## Related Documentation

- [Time Tracking Methodology](./time-tracking-methodology.md) - How we track AI vs. manual time
- [Development Logs](./devlog/) - Daily AI effectiveness ratings
- [Contributing Guide](../contributing/README.md) - General contribution guidelines

---

## Acknowledgment

This AI assistance policy was developed with assistance from **Claude Code** (Anthropic, model: claude-sonnet-4-5-20250929) during ragged's planning phase (November 2025).

The policy is informed by:
- Ghostty project's AI disclosure requirements
- AIDA (AI Included Disclosure Acknowledgment) framework
- Academic AI disclosure standards (ICMJE 2024)
- GitHub's AI governance best practices
- ragged development team's experience

---

**Status**: Active policy from v0.1 onwards
**Last Updated**: 2025-11-09
**Next Review**: After v0.3 completion (assess effectiveness and refine)
