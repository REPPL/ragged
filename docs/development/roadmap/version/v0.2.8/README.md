# v0.2.8 Roadmap: CLI Enhancements + Documentation Consistency

**Status**: 🔄 IN PROGRESS - Core CLI features implemented, testing and documentation pending
**Estimated Effort**: 40-60 hours (original), TBD actual
**Timeline**: November 2025
**Dependencies**: v0.2.7 (in progress, concurrent work)

---

## Vision

Transform ragged's CLI from functional to exceptional by implementing state-of-the-art CLI patterns and ensuring documentation consistency across the codebase.

**Guiding Principles**:
1. Every interaction should feel polished, helpful, and efficient
2. Documentation follows Single Source of Truth - no duplication
3. Professional CLI experience matching or exceeding industry leaders
4. Backwards compatibility maintained

**Current Status:**
- ✅ 10 major CLI enhancements implemented
- 🔄 Testing and documentation in progress
- 📅 Documentation consistency work ongoing

**See:** [v0.2.8 Implementation Record (In Progress)](../../implementation/version/v0.2/v0.2.8-in-progress.md)

---

## Success Criteria

### Documentation
- ✅ All README files summarise and link (not duplicate content)
- ✅ No content duplication in docs/
- ✅ All internal links validated and working
- ✅ Consistent structure across documentation

### CLI Features
- ✅ Shell completion working in bash/zsh/fish
- ✅ Output formats support JSON, CSV, table, markdown
- ✅ Configuration validation catches issues before operations fail
- ✅ Environment info helps users report bugs effectively
- ✅ Metadata manageable without re-ingestion
- ✅ Search and filter make finding documents easy
- ✅ Query history enables iterative refinement
- ✅ Export/import enables backup and migration

---

## Phases

### Phase 1: Documentation Consistency (CRITICAL) - 3-5 hours

Audit and fix all documentation to follow Single Source of Truth principle.

**Tasks**:
1. Run documentation-auditor agent
2. Audit all README.md files in docs/
3. Identify and remove content duplication
4. Fix internal links
5. Verify consistent structure
6. Focus areas: roadmap/ directory, planning docs

**Deliverable**: Clean, consistent documentation structure

**Priority**: MUST-HAVE (blocks other documentation work)

---

### Phase 2: Core CLI Enhancements (MUST-HAVE) - 37-47 hours

Implement state-of-the-art CLI features in priority order:

1. **Shell Completion** (4-5h) - bash/zsh/fish support
2. **Configuration Validation** (3-4h) - proactive issue detection
3. **Environment Information** (2-3h) - effective bug reports
4. **Output Format Options** (3-4h) - JSON, CSV, markdown, table
5. **Verbose/Quiet Modes** (2-3h) - control output verbosity
6. **Metadata Management** (4-5h) - update without re-ingestion
7. **Advanced Search & Filtering** (3-4h) - flexible document finding
8. **Query History & Replay** (4-5h) - iterative refinement
9. **Export/Import Utilities** (6-8h) - backup and migration

**Deliverable**: Production-quality CLI with modern features

**Priority**: MUST-HAVE (core v0.2.8 scope)

---

### Phase 3: Nice-to-Have Enhancements - 10-13 hours

**Only if time permits**:

10. **Bulk Operations** (5-6h) - parallel processing, dry-run
11. **Cache Management** (3-4h) - stats, clear, warm
12. **Improved Help & Documentation** (2-3h) - examples, tutorials

**Priority**: NICE-TO-HAVE (defer if schedule pressure)

---

## Detailed Feature Specifications

See individual feature documents:
- [Shell Completion](./features/shell-completion.md)
- [Output Formats](./features/output-formats.md)
- [Configuration Validation](./features/config-validation.md)
- [Environment Info](./features/environment-info.md)
- [Metadata Management](./features/metadata-management.md)
- [Search & Filtering](./features/search-filtering.md)
- [Query History](./features/query-history.md)
- [Export/Import](./features/export-import.md)
- [Documentation Consistency](./features/documentation-consistency.md)

---

## Breaking Changes

**None**. All features are additive and backwards-compatible.

---

## Testing Strategy

### Documentation Testing
- Run documentation-auditor agent
- Validate all internal links
- Check for content duplication
- Verify consistent structure

### CLI Testing
- Manual testing of all new commands
- Shell completion across bash/zsh/fish
- Output format validation (JSON, CSV, etc.)
- Integration with existing workflows
- Error message clarity
- Help text completeness

---

## Timeline

**Week 1**: Documentation Consistency (3-5h)
**Week 2-3**: Core CLI Features 1-5 (15-19h)
**Week 3-4**: Core CLI Features 6-9 (22-28h)
**Week 5**: Testing, polish, nice-to-have if time (10-13h)

---

## Related Documentation

- [v0.2.7 Implementation](../../implementation/version/v0.2/README.md) - Previous version
- [v0.2.9 Roadmap](../v0.2.9/README.md) - Next version
- [CLI Planning](../../../planning/interfaces/cli/README.md) - CLI vision
- [LEANN Integration Analysis](../../../decisions/2025-11-16-leann-integration-analysis.md) - Lessons learned

