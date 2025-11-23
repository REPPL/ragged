# Understanding Your Interest Profile

**Tutorial: Learn how ragged builds and uses your personal interest profile**

**Audience:** All ragged users
**Time:** 10-15 minutes
**Prerequisites:** Basic familiarity with ragged CLI

---

## What You'll Learn

By the end of this tutorial, you'll understand:
- What an interest profile is and why it matters
- How ragged automatically learns your interests
- How to view and manage your profile
- How to use profiles for privacy (GDPR compliance)

---

## What is an Interest Profile?

Your **interest profile** is a local, privacy-first record of your research interests that ragged automatically builds as you use the system. Think of it as ragged learning what topics you care about based on your queries and the documents you retrieve.

### Key Characteristics

- **100% Local**: Your profile never leaves your device
- **Automatic**: Built from your natural usage (no manual tagging)
- **Privacy-First**: Full GDPR compliance with erasure rights
- **Persona-Scoped**: Different personas have separate, isolated profiles

### How It Works

Every time you query ragged:

1. **Topic Extraction**: ragged identifies topics in your query (e.g., "RAG", "vector databases", "privacy")
2. **Document Analysis**: Topics are also extracted from retrieved document filenames
3. **Profile Update**: Your persona's interest profile is updated with:
   - Topic frequency (how often you query about it)
   - Topic recency (when you last queried about it)
   - Topic relationships (which topics co-occur in your queries)
   - Confidence scores (how confident ragged is in your interest)

---

## Viewing Your Profile

### Basic Profile View

To see your interest profile:

```bash
ragged memory profile
```

**Example Output:**
```
Interest Profile: researcher

Profile Age: 7 days
Total Topics: 23

Top Topics (by confidence):
1. rag (confidence: 0.85, frequency: 12, last seen: 2h ago)
2. vector databases (confidence: 0.78, frequency: 8, last seen: 5h ago)
3. privacy (confidence: 0.72, frequency: 6, last seen: 1d ago)
4. embeddings (confidence: 0.68, frequency: 5, last seen: 3h ago)
5. retrieval (confidence: 0.65, frequency: 7, last seen: 4h ago)
```

### Profile for Specific Persona

If you manage multiple personas:

```bash
ragged memory profile --persona researcher
ragged memory profile --persona developer
```

### JSON Output

For programmatic access:

```bash
ragged memory profile --format json
```

---

## Exploring Your Topics

### List All Topics

To see all tracked topics:

```bash
ragged memory topics
```

**Options:**
- `--min-confidence 0.5` - Show only high-confidence topics
- `--limit 10` - Limit number of results
- `--format json` - JSON output

**Example:**
```bash
ragged memory topics --min-confidence 0.6 --limit 15
```

### Detailed Topic Information

To learn more about a specific topic:

```bash
ragged memory topic-info "rag"
```

**Example Output:**
```
Topic: rag

Confidence: 0.850
Frequency: 12
Recency: 0.980
First Seen: 2025-11-16 14:23
Last Seen: 2025-11-23 16:45 (2h ago)

Related Documents (12):
  • rag_paper_2023.pdf
  • retrieval_optimization.md
  • rag_best_practices.md
  • hybrid_rag_techniques.pdf
  ... and 8 more

Co-occurring Topics (17):
  • vector databases (8 times)
  • embeddings (7 times)
  • retrieval (6 times)
  • privacy (5 times)
  ... and 13 more
```

### Finding Related Topics

To discover which topics co-occur with a specific topic:

```bash
ragged memory related-topics "rag"
```

**Example Output:**
```
Topics related to 'rag':

1. vector databases (co-occurred 8 times, confidence: 0.78)
2. embeddings (co-occurred 7 times, confidence: 0.68)
3. retrieval (co-occurred 6 times, confidence: 0.65)
4. privacy (co-occurred 5 times, confidence: 0.72)
```

**Use Case:** This helps you discover connections in your research - topics that frequently appear together in your queries.

---

## Understanding Confidence Scores

Each topic has a **confidence score** (0.0-1.0) indicating how confident ragged is that you're interested in this topic.

### Confidence Calculation

Confidence is calculated from four factors:

1. **Frequency (35%)**: How many times you've queried about this topic
   - More queries = higher confidence

2. **Recency (30%)**: How recently you queried about this topic
   - Recent queries = higher confidence
   - Old queries gradually decay

3. **Consistency (20%)**: How regularly you query about this topic
   - Regular queries over time = higher confidence
   - Single burst of queries = lower confidence

4. **Depth (15%)**: How many documents relate to this topic
   - More related documents = higher confidence

### Confidence Thresholds

- **0.8-1.0**: Very high confidence - core research interest
- **0.6-0.8**: High confidence - regular interest
- **0.4-0.6**: Medium confidence - occasional interest
- **0.2-0.4**: Low confidence - explored once or twice
- **0.0-0.2**: Very low confidence - barely mentioned

---

## Managing Your Profile: Privacy & GDPR

### Removing a Topic (Right to Erasure)

If you want to remove a specific topic from your profile:

```bash
ragged memory forget-topic "sensitive-topic"
```

**With confirmation prompt:**
```
About to remove topic: sensitive-topic
Persona: researcher
Frequency: 3
Confidence: 0.456

⚠ This action cannot be undone!

Continue? [y/N]: y

✓ Removed topic 'sensitive-topic' from researcher
```

**Skip confirmation (for scripts):**
```bash
ragged memory forget-topic "topic-name" --yes
```

### Clearing Entire Profile

To completely reset your profile (GDPR Article 17 - Right to Erasure):

```bash
ragged persona reset researcher
```

This removes all interests and interaction history for the specified persona.

### Exporting Your Data

To export your profile (GDPR Article 20 - Data Portability):

```bash
ragged memory export profile.json --persona researcher
```

This creates a JSON file with your complete profile that you can:
- Archive for your records
- Transfer between systems
- Audit what data ragged has stored

---

## Real-World Usage Examples

### Example 1: Research Progress Tracking

**Scenario:** You're researching RAG techniques over several weeks.

```bash
# Week 1: Starting research
$ ragged query "What is RAG?"

# Week 2: Going deeper
$ ragged query "Advanced RAG techniques for improving accuracy"
$ ragged query "RAG with vector databases"

# Week 3: Check your progress
$ ragged memory profile
```

**Profile shows:**
```
Top Topics:
1. rag (confidence: 0.75, frequency: 8, last seen: 1d ago)
2. vector databases (confidence: 0.68, frequency: 5, last seen: 2d ago)
3. retrieval accuracy (confidence: 0.62, frequency: 4, last seen: 3d ago)
```

You can see your research focus has evolved from basic RAG to advanced techniques and databases.

### Example 2: Multi-Persona Workflows

**Scenario:** You use ragged for both research and development.

```bash
# Research persona
$ ragged persona switch researcher
$ ragged query "Latest academic papers on RAG"

# Development persona
$ ragged persona switch developer
$ ragged query "How to implement RAG in Python"

# Compare profiles
$ ragged memory profile --persona researcher
$ ragged memory profile --persona developer
```

**researcher profile:**
```
Top Topics: rag, academic papers, research methods, citations
```

**developer profile:**
```
Top Topics: python, implementation, rag, code examples, api design
```

Personas keep your interests separate and organised.

### Example 3: Privacy Management

**Scenario:** You researched a sensitive topic and want to remove it.

```bash
# After researching
$ ragged memory topics
```

**Output shows:**
```
Topics:
1. rag (confidence: 0.85)
2. sensitive-medical-condition (confidence: 0.45)
3. privacy (confidence: 0.72)
```

```bash
# Remove sensitive topic
$ ragged memory forget-topic "sensitive-medical-condition" --yes

# Verify removal
$ ragged memory topic-info "sensitive-medical-condition"
```

**Output:**
```
Topic 'sensitive-medical-condition' not found in profile for researcher
```

The topic is completely erased from your local profile.

---

## How Profiles Improve Your Experience

### Adaptive Retrieval (Future)

In future versions (v0.5.x+), your interest profile will enable:

- **Personalised Ranking**: Documents matching your interests ranked higher
- **Query Expansion**: Automatic addition of related terms based on your profile
- **Context Awareness**: Understanding query intent based on your research patterns
- **Smart Suggestions**: Proactive suggestions based on your interests

**Example:**
```
Query: "latest techniques"

Without profile: Generic results about "techniques"
With profile (rag-focused): Results about latest RAG techniques
```

### Privacy-First Design

Your profile enables personalisation **without compromising privacy**:

- ✅ All data stored locally
- ✅ No cloud synchronisation
- ✅ No external API calls
- ✅ Full user control (view, edit, delete)
- ✅ GDPR compliant by design
- ✅ Persona isolation (no cross-contamination)

---

## Best Practices

### 1. Use Separate Personas

Create different personas for different contexts:

```bash
ragged persona create work
ragged persona create personal
ragged persona create research
```

This keeps your interests organised and prevents mixing professional and personal queries.

### 2. Regular Profile Reviews

Periodically review your profile to:
- Ensure accuracy
- Remove outdated interests
- Discover research patterns

```bash
# Monthly review
ragged memory profile
ragged memory topics --min-confidence 0.5
```

### 3. Clean Up Old Topics

Remove topics you're no longer interested in:

```bash
ragged memory topics --min-confidence 0.0  # Show all topics
ragged memory forget-topic "old-topic" --yes
```

### 4. Export for Backup

Regularly export your profile as a backup:

```bash
# Monthly backup
ragged memory export backups/profile-2025-11.json
```

### 5. Leverage JSON Output

For automation and analysis:

```bash
# Get top topics as JSON
ragged memory profile --format json > profile-snapshot.json

# Analyse with jq
ragged memory profile --format json | jq '.top_topics[0:5]'
```

---

## Privacy & Security Considerations

### What Data is Stored?

Your interest profile contains:
- Topic names (extracted from your queries)
- Frequency counts (how many times you queried each topic)
- Timestamps (when topics were first/last seen)
- Document IDs (which documents relate to each topic)
- Co-occurrence relationships (which topics appear together)

### What Data is NOT Stored?

- ❌ Full query text (only extracted topics)
- ❌ Document content (only document IDs/filenames)
- ❌ Your location, IP address, or device identifiers
- ❌ Any external or cloud-based data

### Where is Data Stored?

```
~/.ragged/memory/
├── profiles.db          # Interest profiles (SQLite)
└── interactions/
    └── queries.db       # Interaction history (SQLite)
```

All data is stored locally in your home directory with standard file permissions.

### GDPR Rights

ragged fully supports your GDPR rights:

| Right | ragged Implementation |
|-------|---------------------|
| **Right to Access (Article 15)** | `ragged memory profile`, `ragged memory export` |
| **Right to Erasure (Article 17)** | `ragged memory forget-topic`, `ragged persona reset` |
| **Right to Data Portability (Article 20)** | `ragged memory export` (JSON format) |

---

## Troubleshooting

### Profile Not Building

**Problem:** No topics showing in profile after multiple queries.

**Solutions:**
1. Ensure you're using the correct persona:
   ```bash
   ragged persona list
   ragged persona switch your-persona
   ```

2. Check if interactions are being recorded:
   ```bash
   ragged memory list
   ```

3. Verify behaviour learning is enabled (v0.4.7+):
   ```bash
   ragged --version  # Should be >= 0.4.7
   ```

### Topics Too Generic

**Problem:** Profile shows very generic topics like "the", "what", "how".

**Solutions:**
- This shouldn't happen due to stop-word filtering
- If it does, report as a bug with example queries
- Workaround: Remove unwanted topics:
  ```bash
  ragged memory forget-topic "generic-word" --yes
  ```

### Incorrect Confidence Scores

**Problem:** Confidence scores seem wrong for your actual interests.

**Explanation:** Confidence is based on:
- Query frequency
- Query recency
- Query consistency
- Document relationships

**Solutions:**
- Continue using ragged naturally - confidence improves over time
- Topics queried once will have low confidence (0.3-0.5)
- Topics queried regularly will have high confidence (0.7-0.9)

### Profile Too Large

**Problem:** Hundreds of low-confidence topics cluttering your profile.

**Solution:** Filter by confidence when viewing:
```bash
ragged memory topics --min-confidence 0.5
```

Or remove low-confidence topics:
```bash
# List low-confidence topics
ragged memory topics --min-confidence 0.0 | grep "conf: 0.[0-3]"

# Remove manually
ragged memory forget-topic "low-confidence-topic" --yes
```

---

## Next Steps

Now that you understand interest profiles, explore:

- **[Behaviour Learning System Guide](../guides/behaviour-learning.md)** - Technical details on how learning works
<!-- TODO v0.4.8+: Add Persona Management Tutorial -->
<!-- TODO v0.4.8+: Add Privacy Features Guide -->

---

## Summary

**Key Takeaways:**

1. ✅ Interest profiles automatically learn your research interests
2. ✅ Profiles are 100% local and privacy-first
3. ✅ View your profile with `ragged memory profile`
4. ✅ Explore topics with `ragged memory topics` and `ragged memory topic-info`
5. ✅ Manage privacy with `ragged memory forget-topic`
6. ✅ Full GDPR compliance (access, erasure, portability)
7. ✅ Confidence scores reflect query frequency, recency, and consistency
8. ✅ Separate personas maintain isolated interest profiles

**Remember:** Your interest profile is a tool to help you, not to track you. You have complete control over what's stored and can remove any data at any time.

---

## Related Documentation

- [Behaviour Learning System Guide](../guides/behaviour-learning.md) - How behaviour learning works
- [Behaviour Learning API Reference](../reference/behaviour-learning-api.md) - API documentation
<!-- TODO v0.4.8+: Add Memory Management Guide -->
<!-- TODO v0.4.8+: Add Privacy Features Guide -->

---

