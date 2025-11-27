# Documentation Audits

Documentation quality audits assess documentation structure, completeness, accuracy, and adherence to project standards.

## Audit Reports

All audit reports use the format: `YYYY-MM-DD-description.md`

### Quality Audits

Assess overall documentation quality:
- Structure and organisation
- Completeness and coverage
- Accuracy and currency
- Adherence to standards (British English, SSOT, etc.)

### Metadata Audits

Review documentation metadata and cross-references:
- Lineage tracking (planning → roadmap → implementation)
- Cross-reference validation
- "Related Documentation" sections
- Bidirectional linking

### Version-Specific Audits

Pre-release documentation reviews:
- Version-specific documentation completeness
- Release readiness assessment
- CHANGELOG accuracy

## Documentation Standards

Documentation audits verify adherence to:
- Single Source of Truth principle
- British English compliance
- Directory naming conventions (singular vs plural)
- Complete directory coverage (README files)
- Cross-reference standards
- Footer standards (minimal metadata)

For complete standards, see the project's documentation standards hierarchy (global → development → sandboxed → project-specific).

## Conducting Documentation Audits

Use the `/verify-docs` command or documentation-auditor agent to:
1. Check SSOT violations
2. Verify directory naming
3. Validate complete coverage
4. Check cross-references
5. Verify British English compliance
6. Validate "Related Documentation" sections

## Related Documentation

- [Documentation Hub](../../../README.md) - Main documentation entry point
- [Development Documentation](../../README.md) - Development documentation overview
