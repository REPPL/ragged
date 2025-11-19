# CLI Features & Interactive REPL

Interactive REPL interface and enhanced CLI commands for exploratory workflows, debugging, and developer productivity.

## Feature Overview

CLI Features transforms ragged from a batch-oriented tool into an interactive platform for exploratory RAG workflows. The centerpiece is an interactive REPL (Read-Eval-Print Loop) similar to Python's interactive shell, enabling iterative query refinement, configuration testing, and rapid experimentation. Complementing the REPL are debug mode (step-by-step pipeline visualisation), enhanced output formats, and developer-friendly commands.

The REPL addresses a key limitation: batch commands (`ragged query "..."`) require restarting for each iteration, making exploration tedious. The interactive mode maintains session state, allowing users to refine queries, adjust configurations, and explore documents interactively. Debug mode visualises each pipeline step (embedding, retrieval, reranking, generation) with timing and intermediate results, essential for understanding and troubleshooting.

## Design Goals

1. **Interactive Exploration**: Python-like REPL for rapid iteration
   - Persistent session state
   - Configuration live updates
   - Command history with tab completion
   - Multi-line input support

2. **Developer Debugging**: Step-by-step pipeline visibility
   - Debug mode shows each stage (timing, intermediate results)
   - Chunk inspection commands
   - Configuration introspection
   - Error diagnostics

3. **Privacy Protection**: REPL session security (CRITICAL)
   - Encrypted session files (v0.2.11)
   - PII warnings for user queries
   - Session isolation (v0.2.10)
   - TTL-based cleanup

## Technical Architecture

### Module Structure

```
src/ragged/cli/
├── interactive.py                  # REPL shell (400 lines)
│   └── class InteractiveShell
├── debug.py                        # Debug mode (250 lines)
│   └── class DebugPipeline
└── commands/
    ├── inspect.py                  # Inspection commands (150 lines)
    └── session.py                  # Session management (120 lines)
```

### REPL Commands

```bash
# Document management
add <path>              # Add document to collection
remove <doc_id>         # Remove document
list                    # List all documents

# Querying
query <text>            # Run query with current config
show chunks             # Display retrieved chunks
show reasoning          # Display chain-of-thought

# Configuration
set <key> <value>       # Set config value
get <key>               # Get config value
show config             # Display all configuration
reset config            # Reset to defaults

# Session management
save session <name>     # Save current session
load session <name>     # Load previous session
history                 # Show command history
clear                   # Clear session state

# Utilities
help [command]          # Show help
exit                    # Exit REPL
```

### API Interfaces

```python
from cmd import Cmd
from typing import List, Optional

class InteractiveShell(Cmd):
    """Interactive REPL for ragged."""

    prompt = "ragged> "
    intro = "🔍 ragged Interactive Mode\nType 'help' for commands, 'exit' to quit"

    def __init__(self):
        """Initialize REPL with session management."""
        super().__init__()
        self.session = self._create_session()  # v0.2.10 session isolation
        self.config = RaggedConfig.load()
        self.retriever = Retriever(self.config)
        self.generator = Generator(self.config)

    def do_query(self, query: str):
        """Execute query with current configuration."""
        pass

    def do_set(self, args: str):
        """Set configuration value: set key value"""
        pass

    def do_add(self, path: str):
        """Add document to collection."""
        pass

class DebugPipeline:
    """Step-by-step pipeline visualisation."""

    def run_debug(self, query: str) -> DebugReport:
        """
        Execute query with debug information.

        Returns timing, intermediate results, and diagnostics
        for each pipeline stage.
        """
        pass
```

## Security & Privacy

**Privacy Risk Score**: 90/100 (Excellent, with critical security requirements)

**Risk Factors**:
- REPL history may contain sensitive user queries
- Session state persisted to disk
- Multi-user scenarios require session isolation

**Mitigation** (ALL from v0.2.10/v0.2.11):
- **Session isolation**: UUID-based session IDs (v0.2.10)
- **Encrypted history**: Session files encrypted with Fernet (v0.2.11)
- **PII warnings**: Detect PII in queries and warn user (v0.2.11)
- **TTL cleanup**: Session files deleted after 7 days (v0.2.11)
- **Query hashing**: Logs contain only hashed queries (v0.2.11)

### Integration with Security Foundation

**CRITICAL**: REPL requires v0.2.10 and v0.2.11

```python
from ragged.session import SessionManager
from ragged.privacy import EncryptionManager, contains_pii, hash_query

# Create isolated session
session_mgr = SessionManager()
session = session_mgr.get_or_create_session()

# Warn about PII
if contains_pii(user_input):
    print("⚠ Warning: Input contains PII (will be encrypted, deleted after 7 days)")

# Encrypt session history before saving
encryption = EncryptionManager()
history_data = repl.get_history()
encrypted = encryption.encrypt(history_data.encode())

# Log only hashed queries
query_hash = hash_query(user_query)
logger.info(f"REPL query: {query_hash}")
```

## Implementation Phases

1. **REPL Shell** (8-10h): Interactive shell with cmd module
2. **Debug Mode** (4-5h): Step-by-step visualisation
3. **Session Management** (4-5h): Save/load with encryption
4. **Privacy Integration** (4-6h): v0.2.10/v0.2.11 integration

## Code Examples

### Interactive Mode
```bash
$ ragged interactive

🔍 ragged v0.3.0 - Interactive Mode
Type 'help' for commands, 'exit' to quit

ragged> add documents/paper.pdf
✓ Added paper.pdf with 127 chunks

ragged> set retrieval.top_k 10
✓ retrieval.top_k = 10

ragged> query "what are the main findings?"
📄 Retrieved 10 chunks (0.87 avg confidence)

Answer: The main findings include...

ragged> show chunks
Chunk 1: [paper.pdf, page 3, confidence: 0.95]
"The primary discovery was that..."

ragged> exit
Session saved (encrypted)
```

### Debug Mode
```bash
$ ragged query --debug "machine learning"

🔍 Debug Mode: Query Pipeline

[Step 1/6] Query Preprocessing
  Original: "machine learning"
  Duration: 2ms

[Step 2/6] Query Embedding
  Model: all-MiniLM-L6-v2
  Dimensions: 384
  Duration: 45ms

[Step 3/6] Vector Retrieval
  Retrieved: 5 chunks
  Duration: 23ms

[Step 4/6] Reranking
  Model: ms-marco-MiniLM-L-6-v2
  Duration: 67ms

[Step 5/6] Context Building
  Final chunks: 5
  Total context: 2,450 tokens

[Step 6/6] LLM Generation
  Model: llama3.2
  Duration: 1,234ms

Total Pipeline Duration: 1,371ms
```

## Testing Requirements

- [ ] REPL commands working (add, query, set, show)
- [ ] Command history persisted (encrypted)
- [ ] Session save/load functional
- [ ] Debug mode visualises all pipeline steps
- [ ] PII warnings triggered correctly
- [ ] Session isolation verified (no cross-user leakage)
- [ ] TTL cleanup removes old sessions

## Acceptance Criteria

- [ ] Interactive mode working
- [ ] Debug mode implemented
- [ ] Session management with encryption
- [ ] Privacy integration complete (v0.2.10/v0.2.11)
- [ ] Tab completion working
- [ ] Help system comprehensive
- [ ] Documentation complete

## Related Versions

- **v0.3.0** - Interactive mode & debug (20-24h)

See [v0.3.0 roadmap](../v0.3.0.md) for detailed implementation with privacy sections.

## Dependencies

**From v0.2.10/v0.2.11 (CRITICAL)**:
- SessionManager - Session isolation
- EncryptionManager - Session file encryption
- hash_query() - Query hashing for logs
- contains_pii() - PII detection and warnings
- CleanupScheduler - TTL-based session cleanup

**External**:
- prompt_toolkit (>= 3.0.0) - BSD - Enhanced input/completion

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Session files contain sensitive data | Encryption (v0.2.11), TTL cleanup |
| Cross-user session leakage | Session isolation (v0.2.10) |
| PII in command history | Detection + warnings (v0.2.11) |

## Related Documentation

- [v0.3.0 Roadmap](../v0.3.0.md) - Detailed implementation with privacy sections
- [v0.3 Planning](../../../planning/version/v0.3/README.md) - Design goals
- [v0.3 Master Roadmap](../README.md) - Complete v0.3 overview
- [Security Policy](../../../../security/policy.md) - Session security requirements
- [Privacy Architecture](../../../../security/privacy-architecture.md) - Session encryption

---

**Total Feature Effort:** 20-26 hours
