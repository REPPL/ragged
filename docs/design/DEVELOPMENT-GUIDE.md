# Implementation Plan - Archived Development Documentation

**Note**: This documentation was originally created in a private `.claude/` folder (gitignored) during development. It has been archived here at `docs/implementation/plan/` for **academic reproducibility and transparency**. References to `.claude/` throughout these documents are preserved for historical accuracy but now refer to this location.

## Purpose

This archived planning documentation served as the blueprint for building the ragged project. It contains:
- **AI Assistant Prompts**: Instructions for Claude Code to build and enhance the project
- **Personal Notes**: Architecture decisions, experiments, and observations
- **Build Instructions**: Step-by-step guides for implementing the RAG system
- **References**: Collected resources, papers, and external documentation

## Original Folder Structure

This was the structure when located at `.claude/` during development. Now archived at `docs/implementation/plan/`:

```
docs/implementation/plan/  (originally .claude/)
├── README.md                           # This file - overview & navigation
├── prompts/                            # AI assistant instructions
│   ├── 01-github-setup.md             # GitHub repository configuration
│   ├── 02-documentation-guide.md      # Writing public documentation
│   ├── 03-project-structure.md        # Code organisation guidelines
│   └── templates/                      # Reusable documentation templates
│       ├── readme-template.md
│       ├── contributing-template.md
│       ├── security-template.md
│       └── issue-templates.md
├── notes/                              # Personal development notes
│   ├── project-vision.md              # Project goals & success criteria
│   ├── architecture.md                # RAG system design & tech stack
│   ├── decisions.md                   # Architecture Decision Records (ADRs)
│   ├── experiments.md                 # Test results & findings
│   └── todo.md                        # Project roadmap & TODOs
├── build-instructions/                 # Step-by-step build guides
│   ├── 01-environment-setup.md        # Python environment & dependencies
│   ├── 02-rag-core.md                 # Implement core RAG functionality
│   ├── 03-testing.md                  # Testing strategy & execution
│   └── 04-documentation.md            # Create user-facing documentation
└── references/                         # External resources
    └── rag-resources.md               # Papers, articles, tools, libraries
```

## Quick Navigation

### Getting Started
1. **New to this project?** Start with `notes/project-vision.md` to understand the goals
2. **Ready to build?** Follow `build-instructions/01-environment-setup.md`
3. **Working with Claude?** Check `prompts/` for AI assistant instructions

### Documentation
- **Architecture**: `notes/architecture.md` - System design and tech stack decisions
- **Decisions**: `notes/decisions.md` - Why we made certain choices (ADRs)
- **Experiments**: `notes/experiments.md` - What worked, what didn't

### Templates
- All reusable templates are in `prompts/templates/`
- Use these as starting points for public documentation

### Resources
- **RAG Resources**: `references/rag-resources.md` - Papers, libraries, tools

## Usage Guidelines

### For Claude Code Interactions
When working with Claude Code, reference the appropriate prompt files:
- Starting a new feature? Share `prompts/03-project-structure.md`
- Setting up GitHub? Use `prompts/01-github-setup.md`
- Writing docs? Reference `prompts/02-documentation-guide.md`

### For Personal Development
- Document architectural decisions in `notes/decisions.md` (ADR format)
- Record experiment results in `notes/experiments.md`
- Update `notes/todo.md` with project milestones
- Keep `notes/architecture.md` current with design changes

### For Build Process
Follow the build instructions in sequence:
1. Environment Setup
2. RAG Core Implementation
3. Testing
4. Documentation

## Historical Context: Separation of Concerns

During development, planning documentation was kept separate from public documentation:

**Originally Private (.claude/, gitignored)**:
- AI prompts and instructions
- Personal notes and experiments
- Build process documentation
- Architecture decision records

**Public (repository root)**:
- User-facing README.md
- CONTRIBUTING.md for contributors
- SECURITY.md for vulnerability reporting
- CODE_OF_CONDUCT.md for community standards
- Actual source code and tests

**After Phase 5C**: Planning documentation was archived to `docs/implementation/plan/` for academic reproducibility while actual development continues using a private `.claude/` folder (gitignored).

## Maintenance

- Keep this README updated as the structure evolves
- Archive old/obsolete instructions rather than deleting
- Cross-reference related documents
- Use clear, descriptive file names

---

**Last Updated**: 2025-11-02
**Project**: ragged - Privacy-first local RAG learning project
**License**: GPLv3 (see LICENSE in repository root)
