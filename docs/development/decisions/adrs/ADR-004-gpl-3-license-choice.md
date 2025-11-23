# ADR-004: GPL-3.0 License Choice

**Status:** Accepted

---

## Context and Problem Statement

ragged requires an open-source license. The choice affects:
- What derivatives can do with the code
- Commercial use permissions
- Contribution dynamics
- Community growth
- Alignment with project philosophy

## Decision Drivers

1. **Copyleft Protection**: Ensure derivatives remain open-source
2. **Privacy Philosophy**: Prevent proprietary forks that compromise privacy
3. **Community Contribution**: Encourage improvements to flow back
4. **Commercial Compatibility**: Allow business use while preserving openness
5. **Dependency Compatibility**: Must work with chosen dependencies (ChromaDB-Apache 2.0, PyTorch-BSD)

## Considered Options

### Option 1: GPL-3.0 (Chosen)

**Pros**:
- Strong copyleft - derivatives must remain open-source
- Protects privacy-first philosophy (can't make closed version)
- Compatible with Apache 2.0, BSD dependencies
- Commercial use allowed (with source disclosure)
- Well-understood, battle-tested license

**Cons**:
- Some companies avoid GPL
- Cannot be embedded in proprietary software
- More restrictive than permissive licenses

### Option 2: MIT/Apache 2.0

**Pros**:
- Maximum permissiveness
- Corporate-friendly
- Simple, short license text

**Cons**:
- Allows proprietary forks
- Privacy-first philosophy could be compromised in closed derivatives
- Improvements may not flow back to community

### Option 3: AGPL-3.0

**Pros**:
- Strongest copyleft (network use triggers obligations)
- Prevents SaaS loopholes

**Cons**:
- Even more restrictive than GPL
- Discourages commercial adoption
- May be too aggressive for target audience

## Decision Outcome

**Chosen Option**: "GPL-3.0"

**Justification**:

GPL-3.0 protects ragged's core values while enabling legitimate use:

1. **Privacy Protection**: Anyone who forks ragged must keep source open. Cannot create closed, privacy-compromising version.

2. **Copyleft Balance**: Strong enough to protect principles, not so aggressive (like AGPL) to prevent reasonable commercial use.

3. **Commercial Compatible**: Companies can use ragged internally, even modify it, as long as they share improvements with employees. Only distribution triggers obligations.

4. **Community Growth**: Improvements to ragged must be contributed back (if distributed), creating positive feedback loop.

**Consequences**:
- **Positive**:
  - Privacy-first philosophy protected from proprietary compromise
  - Community improvements flow back
  - Clear legal framework for contributions
  - Compatible with all chosen dependencies

- **Negative**:
  - Some corporations avoid GPL projects
  - Cannot be embedded in proprietary products
  - More complex than permissive licenses

## References

- [GPL-3.0 Full Text](https://www.gnu.org/licenses/gpl-3.0.en.html)
- [ADR-003: Privacy-First Design](./ADR-003-privacy-first-local-only-design.md) - Philosophy protected by GPL

---

**Supersedes**: N/A

**Superseded By**: N/A
