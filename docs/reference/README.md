# Reference

**Information-oriented** - Technical specifications for looking up details.

---

## What Is Reference Documentation?

Reference documentation is **information-oriented** material that provides precise technical details. It's for quick lookups when you need to know exact parameters, return values, or configuration options.

**Good for**:
- Looking up API methods and parameters
- Finding configuration option details
- Checking function signatures
- Verifying technical specifications

**Not good for**:
- Learning how to use ragged (see [tutorials](../tutorials/))
- Solving specific problems (see [guides](../guides/))
- Understanding concepts (see [explanation](../explanation/))

## Available Reference

### Core API

- [x] **[CLI Reference](./cli/)** - Command-line interface specifications (v0.2.8)
- [ ] **Python API Reference** - Complete API documentation (v0.3+)
- [ ] **REST API Reference** - FastAPI endpoints (v0.3+)

### Configuration
*Will be added in v0.1 release.*

- [ ] **Configuration Options** - All settings explained
- [ ] **Environment Variables** - Configuration via environment
- [ ] **Model Specifications** - Supported embedding/LLM models

### Data Formats
*Will be added in v0.2 release.*

- [ ] **Metadata Schema** - Document metadata structure
- [ ] **Input Formats** - Supported document types
- [ ] **Output Formats** - Export and citation formats

### Migrated from project-setup

- **[Terminology](./terminology/)** - Glossary of RAG and ragged-specific terms

## Reference Structure

Each reference page includes:
1. **Overview** - Brief description
2. **Syntax** - Function/method signatures
3. **Parameters** - All parameters with types and defaults
4. **Returns** - Return values and types
5. **Examples** - Brief usage examples (not tutorials)
6. **See Also** - Links to related reference pages

## Style

Reference documentation is:
- **Dry and precise** - No narrative, just facts
- **Complete** - Every parameter documented
- **Consistent** - Same format for similar items
- **Concise** - Brief descriptions, minimal examples

## Contributing

Reference documentation should be:
- Auto-generated from code docstrings where possible
- Manually maintained for configuration and specifications
- Reviewed for accuracy with each release

See [contributing guide](../../CONTRIBUTING.md) for how to help.

---


**See Also**:
- [API Source Code](../../src/ragged/) - Implementation
- [Tutorials](../tutorials/) - Learn to use the API
- [Guides](../guides/) - Solve specific problems
