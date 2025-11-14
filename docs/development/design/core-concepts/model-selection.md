# Dynamic Model Selection Strategy

**Document Version**: 1.0
**Date**: 2025-11-09
**Status**: Design Complete
**Related**: [Hardware Optimisation](./hardware-optimisation.md), [Personal Memory & Personas](./personal-memory-personas.md)

---

## Executive Summary

Dynamic model selection enables ragged to automatically choose the optimal language model for each query based on task complexity, available hardware, user preferences, and model capabilities. This document defines the architecture, routing strategies, and implementation approach for a flexible, persona-aware model selection system.

**Key Objectives**:
- **Automatic routing**: Select best model without user intervention
- **Task-aware**: Match model strengths to query requirements
- **Persona-aware**: Respect user preferences and context
- **Hardware-aware**: Work within available resources
- **Graceful fallback**: Handle model unavailability robustly

**Primary Benefits**:
- **Performance optimisation**: Fast responses for simple queries, quality for complex reasoning
- **Resource efficiency**: Avoid wasting 70B model capacity on trivial queries
- **User experience**: Transparent, intelligent routing without configuration burden
- **Extensibility**: Easy to add new models and routing strategies

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Performance Tiers](#performance-tiers)
3. [Routing Strategies](#routing-strategies)
4. [Task Classification](#task-classification)
5. [Complexity Analysis](#complexity-analysis)
6. [Capability Matching](#capability-matching)
7. [Persona Integration](#persona-integration)
8. [Fallback Handling](#fallback-handling)
9. [Implementation Architecture](#implementation-architecture)
10. [Model Registry](#model-registry)
11. [Performance Benchmarks](#performance-benchmarks)
12. [Configuration](#configuration)
13. [Implementation Timeline](#implementation-timeline)
14. [Testing Strategy](#testing-strategy)
15. [Future Enhancements](#future-enhancements)

---

## Architecture Overview

### Multi-Layer Routing Pipeline

The model selection system uses a **5-stage routing pipeline**:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Query Input                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 1: Explicit Override Check                               │
│  - Check for user-specified model (--model flag)                │
│  - Check for system-level model lock                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ [No override]
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 2: Persona Preference                                    │
│  - Check active persona's model preferences                     │
│  - Check task-specific overrides in persona config              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ [No persona preference]
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 3: Task Classification                                   │
│  - Identify query type (code, reasoning, QA, summarisation)     │
│  - Detect special requirements (vision, function calling)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 4: Complexity Analysis                                   │
│  - Score query complexity (1-10 scale)                          │
│  - Consider context length requirements                         │
│  - Determine tier (Fast/Balanced/Quality)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Stage 5: Capability Matching                                   │
│  - Filter available models by task capability                   │
│  - Match to tier and select best model                          │
│  - Generate fallback chain                                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Selected Model + Fallbacks                     │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

**1. Progressive Enhancement**: Simple queries get fast models, complex queries get quality models, without user configuration.

**2. Graceful Degradation**: If preferred model unavailable, system automatically falls back to next-best option.

**3. Persona Awareness**: User preferences and context influence routing decisions (e.g., researcher persona prefers quality tier).

**4. Hardware Awareness**: Only route to models that fit available hardware (integration with `HardwareDetector`).

**5. Transparency**: Log routing decisions for debugging and user understanding.

---

## Performance Tiers

### Tier Definitions

The system organises models into **3 performance tiers** based on size, speed, and quality:

| Tier | Model Size | Speed (t/s) | Quality | Memory | Use Case |
|------|------------|-------------|---------|--------|----------|
| **Fast** | 7B-13B | 40-70 | 60-75% | 4-8 GB | Simple QA, quick lookups, preprocessing |
| **Balanced** | 13B-34B | 20-35 | 75-85% | 8-25 GB | Standard tasks, code generation, RAG |
| **Quality** | 70B+ | 8-15 | 85-95% | 40-80 GB | Complex reasoning, research, multi-step |

**Speed measured on**: Mac Studio M4 Max 128GB (Q4_K_M quantisation)

### Tier Selection Criteria

**Fast Tier** - Use when:
- Query is simple factual lookup
- Complexity score < 3/10
- Query preprocessing/rewriting
- Quick follow-up questions
- Time-sensitive responses needed

**Balanced Tier** - Use when:
- Standard code generation tasks
- Medium-length document summarisation
- RAG queries with moderate context
- Complexity score 3-7/10
- Most general-purpose queries

**Quality Tier** - Use when:
- Complex multi-step reasoning required
- Research-level analysis needed
- Long document synthesis
- Code architecture decisions
- Complexity score > 7/10
- Persona explicitly prefers quality

### Tier Override Policies

Users and personas can override tier selection:

```yaml
# Persona configuration
persona:
  name: "researcher"
  preferred_model_tier: "quality"  # Always prefer quality tier
  tier_override_rules:
    - condition: "complexity < 3"
      tier: "balanced"              # But use balanced for simple queries
    - condition: "task == 'code_generation'"
      tier: "balanced"              # And balanced for code
```

---

## Routing Strategies

### Strategy 1: Task-Based Routing

Route based on detected task type, matching models to their strengths.

**Task Categories**:

1. **Code Generation**: `CodeLlama`, `DeepSeek-Coder`, `Qwen2.5-Coder`
2. **Complex Reasoning**: `Llama 3.3 70B`, `DeepSeek R1 70B`
3. **RAG Queries**: `Llama 3.1 8B` (simple) → `Llama 3.3 70B` (complex)
4. **Summarisation**: `Qwen 2.5 14B` → `Llama 3.3 70B` (long docs)
5. **Query Rewriting**: `Mistral 7B` (fast preprocessing)
6. **General QA**: Tier-based selection

**Routing Table**:

```python
TASK_MODEL_PREFERENCES = {
    'code_generation': {
        'fast': ['codellama:13b', 'deepseek-coder:6.7b'],
        'balanced': ['deepseek-coder:33b', 'qwen2.5-coder:32b'],
        'quality': ['deepseek-coder:33b', 'qwen2.5-coder:32b']  # No 70B code models
    },
    'reasoning': {
        'fast': ['llama3.2:8b', 'mistral:7b'],
        'balanced': ['qwen2.5:32b', 'llama3.1:30b'],
        'quality': ['llama3.3:70b', 'deepseek-r1:70b']
    },
    'summarisation': {
        'fast': ['llama3.2:8b', 'mistral:7b'],
        'balanced': ['qwen2.5:14b', 'llama3.1:30b'],
        'quality': ['llama3.3:70b', 'qwen2.5:72b']
    },
    'rag_query': {
        'fast': ['llama3.1:8b'],
        'balanced': ['llama3.1:30b', 'qwen2.5:32b'],
        'quality': ['llama3.3:70b']
    },
    'query_rewriting': {
        'fast': ['mistral:7b', 'llama3.2:8b'],
        'balanced': ['mistral:7b'],  # Fast is good enough
        'quality': ['mistral:7b']    # No need for quality tier
    }
}
```

### Strategy 2: Complexity-Based Routing

Route based on query complexity score (1-10).

**Complexity Scoring Factors**:

1. **Query length**: Longer queries suggest complexity
2. **Question structure**: "How" and "why" more complex than "what"
3. **Context requirements**: Multi-hop reasoning detection
4. **Domain specificity**: Technical domains increase complexity
5. **Temporal reasoning**: "Compare X from 2020 vs 2024" increases complexity

**Complexity Score Calculation**:

```python
class ComplexityAnalyser:
    """Analyse query complexity to determine appropriate model tier"""

    COMPLEXITY_INDICATORS = {
        'multi_step': 3.0,      # "First do X, then Y"
        'comparison': 2.0,      # "Compare A and B"
        'synthesis': 2.5,       # "Synthesise findings from..."
        'why_question': 1.5,    # "Why does..."
        'how_question': 1.5,    # "How does..."
        'temporal': 1.0,        # Time-based reasoning
        'multi_document': 2.0,  # Requires multiple sources
        'technical': 1.0,       # Domain-specific terminology
    }

    def score_complexity(self, query: str, context: dict = None) -> float:
        """
        Score query complexity from 1-10

        Args:
            query: User query text
            context: Additional context (e.g., retrieved documents)

        Returns:
            Complexity score (1=simple, 10=very complex)
        """
        score = 1.0  # Base score

        # Query length factor
        word_count = len(query.split())
        if word_count > 50:
            score += 1.5
        elif word_count > 20:
            score += 0.5

        # Detect complexity indicators
        query_lower = query.lower()
        for indicator, weight in self.COMPLEXITY_INDICATORS.items():
            if self._detect_indicator(indicator, query_lower):
                score += weight

        # Context complexity
        if context:
            # Multi-document queries are more complex
            if context.get('document_count', 0) > 3:
                score += 1.5
            # Long context increases complexity
            if context.get('total_tokens', 0) > 4000:
                score += 1.0

        # Cap at 10
        return min(score, 10.0)

    def _detect_indicator(self, indicator: str, query: str) -> bool:
        """Detect presence of complexity indicator in query"""
        patterns = {
            'multi_step': r'(first|then|next|after that|finally)',
            'comparison': r'(compare|contrast|difference|versus|vs)',
            'synthesis': r'(synthesi[sz]e|combine|integrate|overall)',
            'why_question': r'\bwhy\b',
            'how_question': r'\bhow\b',
            'temporal': r'(before|after|during|since|until|when)',
            'multi_document': r'(across|between|from multiple|various)',
            'technical': r'([A-Z]{2,}|[a-z]+\.[a-z]+|\b\w+\(\))',  # Acronyms, code-like
        }

        if indicator in patterns:
            return bool(re.search(patterns[indicator], query, re.IGNORECASE))
        return False

    def select_tier(self, complexity: float) -> str:
        """Map complexity score to tier"""
        if complexity < 3.5:
            return 'fast'
        elif complexity < 7.0:
            return 'balanced'
        else:
            return 'quality'
```

### Strategy 3: Persona-Based Routing

Integrate persona preferences into routing decisions.

**Persona Influence Points**:

1. **Preferred tier**: `researcher` → quality, `casual` → fast
2. **Task overrides**: Developer persona uses code-specific models
3. **Response style**: Academic persona may prefer more capable models
4. **Active projects**: Project context influences model selection

**Example Persona Configurations**:

```python
PERSONA_ROUTING_PROFILES = {
    'researcher': {
        'default_tier': 'quality',
        'tier_downgrade_threshold': 2,  # Only use fast tier if complexity < 2
        'task_preferences': {
            'code_generation': 'balanced',  # Don't need quality for code
            'rag_query': 'quality',         # Research needs thorough RAG
        },
        'min_context_window': 32000,  # Long documents common
    },
    'developer': {
        'default_tier': 'balanced',
        'tier_downgrade_threshold': 3,
        'task_preferences': {
            'code_generation': 'quality',   # Prioritise code quality
            'rag_query': 'balanced',        # Quick doc lookups
        },
        'specialised_models': {
            'code_generation': ['deepseek-coder:33b', 'codellama:34b'],
        },
    },
    'casual': {
        'default_tier': 'fast',
        'tier_upgrade_threshold': 8,   # Only use quality if very complex
        'task_preferences': {
            'code_generation': 'balanced',
            'rag_query': 'fast',
        },
    }
}
```

### Strategy 4: Hybrid Routing

Combine multiple strategies for optimal routing.

**Hybrid Decision Flow**:

```python
def route_hybrid(
    query: str,
    persona: Optional[Persona],
    context: dict,
    available_models: list[str]
) -> RoutingDecision:
    """
    Hybrid routing combining task, complexity, and persona

    Priority order:
    1. Explicit model override (user flag)
    2. Persona task-specific override
    3. Task-based specialisation
    4. Complexity-based tier selection
    5. Persona default tier
    """

    # 1. Check explicit override
    if context.get('explicit_model'):
        return RoutingDecision(
            model=context['explicit_model'],
            reason='explicit_override'
        )

    # 2. Check persona task override
    task_type = classify_task(query)
    if persona and task_type in persona.task_model_overrides:
        return RoutingDecision(
            model=persona.task_model_overrides[task_type],
            reason='persona_task_override'
        )

    # 3. Task-based specialisation
    if task_type in ['code_generation'] and has_specialised_model(task_type):
        complexity = score_complexity(query, context)
        tier = select_tier_for_complexity(complexity)
        return RoutingDecision(
            model=get_specialised_model(task_type, tier),
            reason='task_specialisation'
        )

    # 4. Complexity-based tier selection
    complexity = score_complexity(query, context)
    base_tier = select_tier_for_complexity(complexity)

    # 5. Apply persona tier preferences
    if persona:
        final_tier = apply_persona_tier_preference(
            base_tier, complexity, persona
        )
    else:
        final_tier = base_tier

    # Select best model for tier and task
    model = select_best_model(final_tier, task_type, available_models)

    return RoutingDecision(
        model=model,
        tier=final_tier,
        task_type=task_type,
        complexity=complexity,
        reason='hybrid_routing'
    )
```

---

## Task Classification

### Classification System

The system detects **7 primary task types**:

1. **code_generation**: Generate, modify, or explain code
2. **reasoning**: Multi-step logical reasoning, problem-solving
3. **rag_query**: RAG-enhanced question answering
4. **summarisation**: Condense long documents or conversations
5. **query_rewriting**: Optimise query for retrieval
6. **general_qa**: Standard question-answering
7. **creative**: Creative writing, ideation (future)

### Classification Implementation

```python
class TaskClassifier:
    """Classify query into task categories"""

    # Keyword patterns for task detection
    TASK_PATTERNS = {
        'code_generation': [
            r'\b(write|create|generate|implement|code)\s+(a\s+)?(function|class|script|program)',
            r'\b(debug|fix|refactor)\s+.*\b(code|function|method)',
            r'how\s+to\s+(implement|code|program)',
            r'(python|javascript|java|rust|go|cpp)\s+(code|function)',
        ],
        'reasoning': [
            r'\b(why|how|explain|analyse|reason)\b',
            r'\b(compare|contrast|evaluate|assess)\b',
            r'\b(prove|demonstrate|show|deduce)\b',
            r'(step\s+by\s+step|walk\s+through)',
        ],
        'summarisation': [
            r'\b(summari[sz]e|condense|brief|overview)\b',
            r'(tl;dr|tldr|key\s+points|main\s+idea)',
            r'give\s+me\s+(a\s+)?(summary|overview)',
        ],
        'query_rewriting': [
            r'(rephrase|rewrite|reformulate)\s+(query|question)',
            # Internal use, rarely user-facing
        ],
    }

    def classify(self, query: str, context: dict = None) -> str:
        """
        Classify query into primary task type

        Args:
            query: User query text
            context: Additional context (retrieved docs, etc.)

        Returns:
            Task type string
        """
        query_lower = query.lower()

        # Check code generation patterns
        for pattern in self.TASK_PATTERNS['code_generation']:
            if re.search(pattern, query_lower):
                return 'code_generation'

        # Check summarisation patterns
        for pattern in self.TASK_PATTERNS['summarisation']:
            if re.search(pattern, query_lower):
                return 'summarisation'

        # Check reasoning patterns
        for pattern in self.TASK_PATTERNS['reasoning']:
            if re.search(pattern, query_lower):
                return 'reasoning'

        # If RAG context provided, likely RAG query
        if context and context.get('retrieved_docs'):
            return 'rag_query'

        # Default to general QA
        return 'general_qa'

    def classify_with_confidence(self, query: str) -> tuple[str, float]:
        """Classify with confidence score"""
        # Count pattern matches per category
        scores = defaultdict(int)
        query_lower = query.lower()

        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    scores[task_type] += 1

        if not scores:
            return 'general_qa', 0.5

        # Get highest scoring task
        best_task = max(scores.items(), key=lambda x: x[1])
        confidence = min(best_task[1] * 0.3, 1.0)  # Cap at 1.0

        return best_task[0], confidence
```

### Task-Specific Requirements

Each task type has specific requirements that influence model selection:

```python
TASK_REQUIREMENTS = {
    'code_generation': {
        'capabilities': ['code'],
        'preferred_context_window': 16000,
        'specialised_models': True,
        'requires_function_calling': False,
    },
    'reasoning': {
        'capabilities': ['reasoning', 'analysis'],
        'preferred_context_window': 32000,
        'specialised_models': False,
        'requires_function_calling': False,
    },
    'rag_query': {
        'capabilities': ['retrieval_augmented'],
        'preferred_context_window': 32000,
        'specialised_models': False,
        'requires_function_calling': False,
    },
    'summarisation': {
        'capabilities': ['summarisation'],
        'preferred_context_window': 64000,  # Long input documents
        'specialised_models': False,
        'requires_function_calling': False,
    },
}
```

---

## Complexity Analysis

### Complexity Dimensions

Query complexity is assessed across **5 dimensions**:

1. **Structural Complexity**: Question structure, multi-part queries
2. **Reasoning Depth**: Number of logical steps required
3. **Context Requirements**: Amount and complexity of context needed
4. **Domain Specificity**: Technical vs. general knowledge
5. **Output Requirements**: Simple answer vs. detailed analysis

### Scoring Algorithm

```python
@dataclass
class ComplexityScore:
    """Detailed complexity assessment"""
    structural: float       # 0-2: Query structure complexity
    reasoning_depth: float  # 0-3: Logical reasoning required
    context_need: float     # 0-2: Context requirements
    domain_specific: float  # 0-2: Domain expertise needed
    output_detail: float    # 0-1: Output detail requirements

    @property
    def total(self) -> float:
        """Total complexity score (0-10)"""
        return (
            self.structural +
            self.reasoning_depth +
            self.context_need +
            self.domain_specific +
            self.output_detail
        )

    @property
    def tier(self) -> str:
        """Recommended tier based on total score"""
        if self.total < 3.5:
            return 'fast'
        elif self.total < 7.0:
            return 'balanced'
        else:
            return 'quality'

class ComplexityAnalyserV2:
    """Enhanced complexity analysis with detailed scoring"""

    def analyse(self, query: str, context: dict = None) -> ComplexityScore:
        """Perform multi-dimensional complexity analysis"""

        score = ComplexityScore(
            structural=self._score_structural(query),
            reasoning_depth=self._score_reasoning(query),
            context_need=self._score_context(query, context),
            domain_specific=self._score_domain(query),
            output_detail=self._score_output(query)
        )

        return score

    def _score_structural(self, query: str) -> float:
        """Score structural complexity (0-2)"""
        score = 0.0

        # Multi-part questions
        if re.search(r'(and|also|additionally)', query, re.IGNORECASE):
            score += 0.5

        # Sequential steps
        if re.search(r'(first|then|next|finally)', query, re.IGNORECASE):
            score += 1.0

        # Conditional logic
        if re.search(r'(if|when|unless|provided that)', query, re.IGNORECASE):
            score += 0.5

        return min(score, 2.0)

    def _score_reasoning(self, query: str) -> float:
        """Score reasoning depth (0-3)"""
        score = 0.0

        # Causal reasoning
        if re.search(r'\b(why|because|reason|cause)\b', query, re.IGNORECASE):
            score += 1.0

        # Comparative reasoning
        if re.search(r'\b(compare|contrast|difference|better|worse)\b', query, re.IGNORECASE):
            score += 1.0

        # Multi-step reasoning indicators
        if re.search(r'(implies|therefore|consequently|thus)', query, re.IGNORECASE):
            score += 1.0

        # Analysis required
        if re.search(r'(analy[sz]e|evaluate|assess|examine)', query, re.IGNORECASE):
            score += 1.0

        return min(score, 3.0)

    def _score_context(self, query: str, context: dict = None) -> float:
        """Score context requirements (0-2)"""
        score = 0.0

        # Requires external knowledge
        if context and context.get('retrieved_docs'):
            doc_count = len(context['retrieved_docs'])
            if doc_count > 5:
                score += 1.5
            elif doc_count > 2:
                score += 1.0
            else:
                score += 0.5

        # Multi-document synthesis
        if re.search(r'(across|between|from multiple)', query, re.IGNORECASE):
            score += 0.5

        return min(score, 2.0)

    def _score_domain(self, query: str) -> float:
        """Score domain specificity (0-2)"""
        score = 0.0

        # Technical terminology (rough heuristic)
        words = query.split()

        # Acronyms
        acronyms = [w for w in words if w.isupper() and len(w) > 1]
        score += min(len(acronyms) * 0.3, 1.0)

        # Code-like syntax
        if re.search(r'[a-z]+\.[a-z]+|\b\w+\(\)', query):
            score += 0.5

        # Domain keywords (expandable)
        domain_keywords = [
            'algorithm', 'architecture', 'protocol', 'framework',
            'quantum', 'neural', 'genomic', 'molecular'
        ]
        for keyword in domain_keywords:
            if keyword in query.lower():
                score += 0.5
                break

        return min(score, 2.0)

    def _score_output(self, query: str) -> float:
        """Score output detail requirements (0-1)"""
        score = 0.0

        # Detailed output requested
        if re.search(r'(detailed|comprehensive|thorough|in-depth)', query, re.IGNORECASE):
            score += 0.5

        # Simple/brief output requested
        if re.search(r'(brief|quick|simple|short)', query, re.IGNORECASE):
            score -= 0.3

        # Explanation requested
        if re.search(r'(explain|describe|elaborate)', query, re.IGNORECASE):
            score += 0.3

        return max(min(score, 1.0), 0.0)
```

### Complexity Examples

**Low Complexity (Score: 1.5-2.5)** → Fast Tier
- "What is the capital of France?"
- "Define recursion"
- "How do I install numpy?"

**Medium Complexity (Score: 4.0-6.0)** → Balanced Tier
- "Explain how quicksort works and compare it to mergesort"
- "Write a Python function to validate email addresses"
- "Summarise the key findings from these 3 research papers"

**High Complexity (Score: 7.5-9.5)** → Quality Tier
- "Analyse the architectural trade-offs between microservices and monoliths for a fintech startup, considering scalability, team structure, and regulatory compliance"
- "Compare the reasoning capabilities of transformer-based models versus recursive neural networks, synthesising findings from recent papers"
- "Design a distributed caching system for a social network handling 100M users, explaining design decisions step-by-step"

---

## Capability Matching

### Model Capability Registry

Each model is tagged with capabilities to enable precise matching:

```python
@dataclass
class ModelCapabilities:
    """Model capability profile"""
    name: str
    size_b: int                    # Billion parameters
    context_window: int            # Max context tokens
    capabilities: set[str]         # Capability tags
    performance_tier: str          # 'fast', 'balanced', 'quality'
    specialisations: list[str]     # Special strengths
    memory_gb: float              # Memory requirement
    speed_tokens_sec: float       # Inference speed estimate

MODEL_REGISTRY = {
    'llama3.3:70b': ModelCapabilities(
        name='llama3.3:70b',
        size_b=70,
        context_window=131072,
        capabilities={'general', 'reasoning', 'analysis', 'long_context'},
        performance_tier='quality',
        specialisations=['complex_reasoning', 'long_documents'],
        memory_gb=45.0,
        speed_tokens_sec=11.0,
    ),
    'deepseek-r1:70b': ModelCapabilities(
        name='deepseek-r1:70b',
        size_b=70,
        context_window=65536,
        capabilities={'reasoning', 'mathematics', 'analysis'},
        performance_tier='quality',
        specialisations=['chain_of_thought', 'mathematical_reasoning'],
        memory_gb=45.0,
        speed_tokens_sec=10.0,
    ),
    'qwen2.5-coder:32b': ModelCapabilities(
        name='qwen2.5-coder:32b',
        size_b=32,
        context_window=32768,
        capabilities={'code', 'general'},
        performance_tier='balanced',
        specialisations=['code_generation', 'code_explanation', 'debugging'],
        memory_gb=22.0,
        speed_tokens_sec=24.0,
    ),
    'deepseek-coder:33b': ModelCapabilities(
        name='deepseek-coder:33b',
        size_b=33,
        context_window=16384,
        capabilities={'code', 'general'},
        performance_tier='balanced',
        specialisations=['code_generation', 'code_completion'],
        memory_gb=23.0,
        speed_tokens_sec=23.0,
    ),
    'codellama:34b': ModelCapabilities(
        name='codellama:34b',
        size_b=34,
        context_window=16384,
        capabilities={'code'},
        performance_tier='balanced',
        specialisations=['code_generation', 'infilling'],
        memory_gb=24.0,
        speed_tokens_sec=22.0,
    ),
    'llama3.1:30b': ModelCapabilities(
        name='llama3.1:30b',
        size_b=30,
        context_window=131072,
        capabilities={'general', 'long_context'},
        performance_tier='balanced',
        specialisations=['long_documents', 'general_purpose'],
        memory_gb=20.0,
        speed_tokens_sec=26.0,
    ),
    'qwen2.5:14b': ModelCapabilities(
        name='qwen2.5:14b',
        size_b=14,
        context_window=32768,
        capabilities={'general', 'summarisation'},
        performance_tier='balanced',
        specialisations=['multilingual', 'summarisation'],
        memory_gb=10.0,
        speed_tokens_sec=35.0,
    ),
    'llama3.2:8b': ModelCapabilities(
        name='llama3.2:8b',
        size_b=8,
        context_window=131072,
        capabilities={'general', 'long_context'},
        performance_tier='fast',
        specialisations=['general_purpose', 'long_context'],
        memory_gb=6.0,
        speed_tokens_sec=65.0,
    ),
    'mistral:7b': ModelCapabilities(
        name='mistral:7b',
        size_b=7,
        context_window=32768,
        capabilities={'general'},
        performance_tier='fast',
        specialisations=['general_purpose', 'efficient'],
        memory_gb=5.0,
        speed_tokens_sec=70.0,
    ),
}
```

### Capability Matching Algorithm

```python
class CapabilityMatcher:
    """Match requirements to model capabilities"""

    def __init__(self, model_registry: dict[str, ModelCapabilities]):
        self.registry = model_registry

    def find_best_match(
        self,
        requirements: dict,
        available_models: list[str],
        hardware: HardwareProfile
    ) -> Optional[str]:
        """
        Find best model matching requirements

        Args:
            requirements: {
                'task_type': str,
                'tier': str,
                'min_context': int,
                'specialisations': list[str],
                'capabilities': set[str],
            }
            available_models: List of installed model names
            hardware: Hardware capabilities

        Returns:
            Best matching model name or None
        """

        # Filter to available models
        candidates = {
            name: caps for name, caps in self.registry.items()
            if name in available_models
        }

        if not candidates:
            return None

        # Filter by hardware constraints
        candidates = {
            name: caps for name, caps in candidates.items()
            if caps.memory_gb <= hardware.available_ram_gb * 0.75
        }

        # Filter by tier
        tier = requirements.get('tier', 'balanced')
        candidates = {
            name: caps for name, caps in candidates.items()
            if caps.performance_tier == tier
        }

        # If no exact tier match, relax constraint
        if not candidates:
            # Fall back to balanced tier
            candidates = {
                name: caps for name, caps in self.registry.items()
                if name in available_models and
                caps.performance_tier == 'balanced' and
                caps.memory_gb <= hardware.available_ram_gb * 0.75
            }

        # Filter by capabilities
        required_caps = requirements.get('capabilities', set())
        if required_caps:
            candidates = {
                name: caps for name, caps in candidates.items()
                if required_caps.issubset(caps.capabilities)
            }

        # Score by specialisation match
        specialisations = requirements.get('specialisations', [])
        scores = {}
        for name, caps in candidates.items():
            score = 0
            for spec in specialisations:
                if spec in caps.specialisations:
                    score += 2

            # Context window bonus
            min_context = requirements.get('min_context', 8192)
            if caps.context_window >= min_context:
                score += 1

            # Size bonus (larger generally better within tier)
            score += caps.size_b / 100.0

            scores[name] = score

        # Return highest scoring
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        # Fallback: return any available model
        if candidates:
            return list(candidates.keys())[0]

        return None
```

---

## Persona Integration

### Persona-Aware Routing

Personas influence routing at multiple levels:

**Level 1: Default Tier Preference**
```python
persona.preferred_model_tier  # 'fast', 'balanced', 'quality'
```

**Level 2: Task-Specific Overrides**
```python
persona.task_model_overrides = {
    'code_generation': 'deepseek-coder:33b',
    'rag_query': 'llama3.3:70b',
}
```

**Level 3: Tier Adjustment Rules**
```python
persona.tier_adjustment_rules = [
    {
        'condition': 'complexity < 3',
        'adjustment': 'downgrade',  # quality → balanced
    },
    {
        'condition': 'task == "code_generation"',
        'override_tier': 'balanced',
    },
]
```

### Routing Integration Example

```python
class PersonaAwareRouter:
    """Router that integrates persona preferences"""

    def route(
        self,
        query: str,
        persona: Optional[Persona],
        context: dict,
        available_models: list[str]
    ) -> RoutingDecision:
        """Route with persona awareness"""

        # Classify task and analyse complexity
        task_type = self.classifier.classify(query, context)
        complexity = self.complexity_analyser.analyse(query, context)

        # Check persona task override
        if persona and task_type in persona.task_model_overrides:
            explicit_model = persona.task_model_overrides[task_type]
            if explicit_model in available_models:
                return RoutingDecision(
                    model=explicit_model,
                    tier=self.registry[explicit_model].performance_tier,
                    task_type=task_type,
                    complexity=complexity.total,
                    reason='persona_task_override'
                )

        # Determine base tier from complexity
        base_tier = complexity.tier

        # Apply persona tier preference
        if persona:
            final_tier = self._apply_persona_tier(
                base_tier, complexity.total, task_type, persona
            )
        else:
            final_tier = base_tier

        # Build requirements
        requirements = {
            'tier': final_tier,
            'task_type': task_type,
            'capabilities': self._get_task_capabilities(task_type),
            'specialisations': self._get_task_specialisations(task_type),
            'min_context': context.get('min_context_window', 8192),
        }

        # Match to best model
        model = self.capability_matcher.find_best_match(
            requirements,
            available_models,
            self.hardware
        )

        # Generate fallbacks
        fallbacks = self._generate_fallbacks(requirements, available_models)

        return RoutingDecision(
            model=model,
            tier=final_tier,
            task_type=task_type,
            complexity=complexity.total,
            fallbacks=fallbacks,
            reason='persona_aware_routing'
        )

    def _apply_persona_tier(
        self,
        base_tier: str,
        complexity: float,
        task_type: str,
        persona: Persona
    ) -> str:
        """Apply persona tier preferences to base tier"""

        # Check tier adjustment rules
        for rule in persona.tier_adjustment_rules:
            if self._evaluate_rule(rule, complexity, task_type):
                if 'override_tier' in rule:
                    return rule['override_tier']
                elif rule.get('adjustment') == 'upgrade':
                    return self._upgrade_tier(base_tier)
                elif rule.get('adjustment') == 'downgrade':
                    return self._downgrade_tier(base_tier)

        # Apply default preference
        if persona.preferred_model_tier == 'quality':
            # Upgrade unless complexity very low
            if complexity > persona.tier_downgrade_threshold:
                return 'quality'
        elif persona.preferred_model_tier == 'fast':
            # Downgrade unless complexity very high
            if complexity < persona.tier_upgrade_threshold:
                return 'fast'

        return base_tier
```

---

## Fallback Handling

### Fallback Strategy

When primary model unavailable, system automatically falls back through a chain:

**Fallback Chain Example**:
```
Primary: llama3.3:70b (quality tier, reasoning task)
    ↓ (if unavailable)
Fallback 1: qwen2.5:32b (balanced tier, general)
    ↓ (if unavailable)
Fallback 2: llama3.1:30b (balanced tier, general)
    ↓ (if unavailable)
Fallback 3: llama3.2:8b (fast tier, general)
    ↓ (if unavailable)
Error: No models available
```

### Fallback Generation

```python
class FallbackGenerator:
    """Generate intelligent fallback chains"""

    def generate_fallbacks(
        self,
        primary_model: str,
        requirements: dict,
        available_models: list[str],
        max_fallbacks: int = 3
    ) -> list[str]:
        """
        Generate fallback chain for primary model

        Strategy:
        1. Same tier, different model
        2. One tier down, same specialisation
        3. One tier down, general purpose
        4. Two tiers down if necessary
        """

        primary_caps = self.registry.get(primary_model)
        if not primary_caps:
            return []

        fallbacks = []
        candidates = [m for m in available_models if m != primary_model]

        # Strategy 1: Same tier, different model
        same_tier = [
            m for m in candidates
            if self.registry[m].performance_tier == primary_caps.performance_tier
        ]
        if same_tier:
            # Prefer models with similar capabilities
            scored = self._score_similarity(same_tier, primary_caps)
            fallbacks.extend(scored[:min(2, max_fallbacks)])

        # Strategy 2: One tier down, preserve specialisation
        if len(fallbacks) < max_fallbacks:
            lower_tier = self._downgrade_tier(primary_caps.performance_tier)
            specialised_lower = [
                m for m in candidates
                if (self.registry[m].performance_tier == lower_tier and
                    any(s in self.registry[m].specialisations
                        for s in primary_caps.specialisations))
            ]
            if specialised_lower and specialised_lower[0] not in fallbacks:
                fallbacks.append(specialised_lower[0])

        # Strategy 3: One tier down, general
        if len(fallbacks) < max_fallbacks:
            lower_tier = self._downgrade_tier(primary_caps.performance_tier)
            general_lower = [
                m for m in candidates
                if self.registry[m].performance_tier == lower_tier
            ]
            for model in general_lower:
                if model not in fallbacks:
                    fallbacks.append(model)
                    if len(fallbacks) >= max_fallbacks:
                        break

        # Strategy 4: Two tiers down if desperate
        if len(fallbacks) < max_fallbacks and primary_caps.performance_tier == 'quality':
            fast_models = [
                m for m in candidates
                if self.registry[m].performance_tier == 'fast'
            ]
            for model in fast_models:
                if model not in fallbacks:
                    fallbacks.append(model)
                    break

        return fallbacks[:max_fallbacks]

    def _score_similarity(
        self,
        models: list[str],
        reference: ModelCapabilities
    ) -> list[str]:
        """Score models by similarity to reference"""
        scores = {}
        for model in models:
            caps = self.registry[model]
            score = 0

            # Capability overlap
            overlap = caps.capabilities & reference.capabilities
            score += len(overlap) * 2

            # Specialisation overlap
            spec_overlap = set(caps.specialisations) & set(reference.specialisations)
            score += len(spec_overlap) * 3

            # Context window similarity
            if caps.context_window >= reference.context_window * 0.5:
                score += 1

            scores[model] = score

        return [m for m, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]
```

### Error Handling

```python
class RoutingError(Exception):
    """Base exception for routing errors"""
    pass

class NoModelsAvailableError(RoutingError):
    """No models available for routing"""

    def __init__(self, requirements: dict):
        self.requirements = requirements
        super().__init__(f"No models available matching: {requirements}")

class ModelLoadError(RoutingError):
    """Failed to load selected model"""

    def __init__(self, model: str, reason: str):
        self.model = model
        self.reason = reason
        super().__init__(f"Failed to load {model}: {reason}")

class RouterWithFallback:
    """Router with automatic fallback handling"""

    def route_with_fallback(
        self,
        query: str,
        persona: Optional[Persona],
        context: dict,
        available_models: list[str]
    ) -> tuple[str, Optional[str]]:
        """
        Route with automatic fallback

        Returns:
            (selected_model, fallback_reason or None)
        """

        # Initial routing
        decision = self.route(query, persona, context, available_models)

        # Try primary model
        try:
            self._test_model_availability(decision.model)
            return decision.model, None
        except ModelLoadError as e:
            logger.warning(f"Primary model {decision.model} unavailable: {e.reason}")

        # Try fallbacks
        for i, fallback_model in enumerate(decision.fallbacks):
            try:
                self._test_model_availability(fallback_model)
                reason = f"Primary {decision.model} unavailable, using fallback #{i+1}"
                logger.info(f"Fallback to {fallback_model}: {reason}")
                return fallback_model, reason
            except ModelLoadError as e:
                logger.warning(f"Fallback {fallback_model} unavailable: {e.reason}")
                continue

        # All models failed
        raise NoModelsAvailableError(decision.requirements)
```

---

## Implementation Architecture

### Core Components

```python
# routing/core.py

@dataclass
class RoutingRequest:
    """Request for model routing"""
    query: str
    persona: Optional[Persona] = None
    context: dict = field(default_factory=dict)
    explicit_model: Optional[str] = None
    available_models: Optional[list[str]] = None

@dataclass
class RoutingDecision:
    """Routing decision with rationale"""
    model: str
    tier: str
    task_type: str
    complexity: float
    fallbacks: list[str] = field(default_factory=list)
    reason: str = 'auto_routing'
    metadata: dict = field(default_factory=dict)

class UnifiedModelRouter:
    """
    Unified router integrating all routing strategies

    Combines:
    - Task classification
    - Complexity analysis
    - Persona preferences
    - Capability matching
    - Fallback generation
    """

    def __init__(
        self,
        hardware: HardwareProfile,
        model_registry: dict[str, ModelCapabilities],
        config: Optional[dict] = None
    ):
        self.hardware = hardware
        self.model_registry = model_registry
        self.config = config or {}

        # Initialize components
        self.task_classifier = TaskClassifier()
        self.complexity_analyser = ComplexityAnalyserV2()
        self.capability_matcher = CapabilityMatcher(model_registry)
        self.fallback_generator = FallbackGenerator(model_registry)

        # Detect available models
        self.available_models = self._detect_available_models()

        logger.info(f"Router initialized with {len(self.available_models)} models")

    def route(self, request: RoutingRequest) -> RoutingDecision:
        """
        Main routing method

        5-stage pipeline:
        1. Check explicit override
        2. Check persona preferences
        3. Classify task
        4. Analyse complexity and determine tier
        5. Match capabilities and select model
        """

        available = request.available_models or self.available_models

        # Stage 1: Explicit override
        if request.explicit_model:
            if request.explicit_model in available:
                return RoutingDecision(
                    model=request.explicit_model,
                    tier=self.model_registry[request.explicit_model].performance_tier,
                    task_type='unknown',
                    complexity=0.0,
                    reason='explicit_override'
                )
            else:
                logger.warning(f"Explicit model {request.explicit_model} not available")

        # Stage 2 & 3: Classify task
        task_type = self.task_classifier.classify(request.query, request.context)

        # Check persona task override
        if request.persona and task_type in request.persona.task_model_overrides:
            explicit_model = request.persona.task_model_overrides[task_type]
            if explicit_model in available:
                fallbacks = self.fallback_generator.generate_fallbacks(
                    explicit_model, {}, available
                )
                return RoutingDecision(
                    model=explicit_model,
                    tier=self.model_registry[explicit_model].performance_tier,
                    task_type=task_type,
                    complexity=0.0,
                    fallbacks=fallbacks,
                    reason='persona_task_override'
                )

        # Stage 4: Analyse complexity
        complexity = self.complexity_analyser.analyse(request.query, request.context)
        base_tier = complexity.tier

        # Apply persona tier adjustments
        if request.persona:
            final_tier = self._apply_persona_tier_preference(
                base_tier, complexity.total, task_type, request.persona
            )
        else:
            final_tier = base_tier

        # Stage 5: Capability matching
        requirements = {
            'tier': final_tier,
            'task_type': task_type,
            'capabilities': self._get_task_capabilities(task_type),
            'specialisations': self._get_task_specialisations(task_type),
            'min_context': request.context.get('min_context_window', 8192),
        }

        model = self.capability_matcher.find_best_match(
            requirements, available, self.hardware
        )

        if not model:
            raise NoModelsAvailableError(requirements)

        # Generate fallbacks
        fallbacks = self.fallback_generator.generate_fallbacks(
            model, requirements, available
        )

        return RoutingDecision(
            model=model,
            tier=final_tier,
            task_type=task_type,
            complexity=complexity.total,
            fallbacks=fallbacks,
            reason='capability_matched',
            metadata={
                'complexity_breakdown': asdict(complexity),
                'requirements': requirements,
            }
        )

    def _detect_available_models(self) -> list[str]:
        """Detect which models are available via Ollama"""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                logger.error("Failed to list Ollama models")
                return []

            # Parse output (format: NAME ID SIZE MODIFIED)
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    name = line.split()[0]
                    # Match against registry
                    for registered_name in self.model_registry.keys():
                        if name.startswith(registered_name.split(':')[0]):
                            models.append(registered_name)
                            break

            return models
        except Exception as e:
            logger.error(f"Error detecting models: {e}")
            return []
```

### Integration Example

```python
# Example usage in main RAG pipeline

class RAGPipeline:
    """RAG pipeline with dynamic model selection"""

    def __init__(self, config: dict):
        # Detect hardware
        self.hardware = HardwareDetector.detect()

        # Initialize router
        self.router = UnifiedModelRouter(
            hardware=self.hardware,
            model_registry=MODEL_REGISTRY,
            config=config.get('routing', {})
        )

        # Load active persona
        self.persona = self._load_active_persona()

    def query(self, query_text: str, **kwargs) -> dict:
        """Process query with dynamic model selection"""

        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(query_text)

        # Build context
        context = {
            'retrieved_docs': retrieved_docs,
            'min_context_window': self._estimate_context_size(
                query_text, retrieved_docs
            ),
        }

        # Route to best model
        routing_request = RoutingRequest(
            query=query_text,
            persona=self.persona,
            context=context,
            explicit_model=kwargs.get('model')
        )

        decision = self.router.route(routing_request)

        logger.info(
            f"Routing: {decision.model} "
            f"(tier={decision.tier}, task={decision.task_type}, "
            f"complexity={decision.complexity:.1f}, reason={decision.reason})"
        )

        # Generate response with selected model
        try:
            response = self._generate_with_model(
                decision.model,
                query_text,
                retrieved_docs
            )
        except ModelLoadError:
            # Try fallback
            logger.warning(f"Failed to load {decision.model}, trying fallback")
            if decision.fallbacks:
                response = self._generate_with_model(
                    decision.fallbacks[0],
                    query_text,
                    retrieved_docs
                )
            else:
                raise

        return {
            'answer': response,
            'model_used': decision.model,
            'routing_decision': asdict(decision),
            'retrieved_docs': retrieved_docs,
        }
```

---

## Model Registry

### Complete Model Specifications

```python
# routing/models.py

MODEL_REGISTRY = {
    # Quality Tier - 70B+ models
    'llama3.3:70b': ModelCapabilities(
        name='llama3.3:70b',
        size_b=70,
        context_window=131072,
        capabilities={'general', 'reasoning', 'analysis', 'long_context'},
        performance_tier='quality',
        specialisations=['complex_reasoning', 'long_documents', 'analysis'],
        memory_gb=45.0,
        speed_tokens_sec=11.0,
    ),
    'deepseek-r1:70b': ModelCapabilities(
        name='deepseek-r1:70b',
        size_b=70,
        context_window=65536,
        capabilities={'reasoning', 'mathematics', 'analysis', 'chain_of_thought'},
        performance_tier='quality',
        specialisations=['chain_of_thought', 'mathematical_reasoning', 'step_by_step'],
        memory_gb=45.0,
        speed_tokens_sec=10.0,
    ),
    'qwen2.5:72b': ModelCapabilities(
        name='qwen2.5:72b',
        size_b=72,
        context_window=32768,
        capabilities={'general', 'reasoning', 'multilingual'},
        performance_tier='quality',
        specialisations=['multilingual', 'general_purpose'],
        memory_gb=48.0,
        speed_tokens_sec=10.5,
    ),

    # Balanced Tier - 13B-34B models
    'qwen2.5-coder:32b': ModelCapabilities(
        name='qwen2.5-coder:32b',
        size_b=32,
        context_window=32768,
        capabilities={'code', 'general'},
        performance_tier='balanced',
        specialisations=['code_generation', 'code_explanation', 'debugging', 'multiple_languages'],
        memory_gb=22.0,
        speed_tokens_sec=24.0,
    ),
    'deepseek-coder:33b': ModelCapabilities(
        name='deepseek-coder:33b',
        size_b=33,
        context_window=16384,
        capabilities={'code', 'general'},
        performance_tier='balanced',
        specialisations=['code_generation', 'code_completion', 'infilling'],
        memory_gb=23.0,
        speed_tokens_sec=23.0,
    ),
    'codellama:34b': ModelCapabilities(
        name='codellama:34b',
        size_b=34,
        context_window=16384,
        capabilities={'code'},
        performance_tier='balanced',
        specialisations=['code_generation', 'infilling', 'instruction_following'],
        memory_gb=24.0,
        speed_tokens_sec=22.0,
    ),
    'llama3.1:30b': ModelCapabilities(
        name='llama3.1:30b',
        size_b=30,
        context_window=131072,
        capabilities={'general', 'long_context'},
        performance_tier='balanced',
        specialisations=['long_documents', 'general_purpose'],
        memory_gb=20.0,
        speed_tokens_sec=26.0,
    ),
    'qwen2.5:32b': ModelCapabilities(
        name='qwen2.5:32b',
        size_b=32,
        context_window=32768,
        capabilities={'general', 'reasoning', 'multilingual'},
        performance_tier='balanced',
        specialisations=['multilingual', 'general_purpose'],
        memory_gb=22.0,
        speed_tokens_sec=24.0,
    ),
    'qwen2.5:14b': ModelCapabilities(
        name='qwen2.5:14b',
        size_b=14,
        context_window=32768,
        capabilities={'general', 'summarisation'},
        performance_tier='balanced',
        specialisations=['multilingual', 'summarisation', 'efficient'],
        memory_gb=10.0,
        speed_tokens_sec=35.0,
    ),
    'codellama:13b': ModelCapabilities(
        name='codellama:13b',
        size_b=13,
        context_window=16384,
        capabilities={'code'},
        performance_tier='balanced',
        specialisations=['code_generation', 'fast_inference'],
        memory_gb=9.0,
        speed_tokens_sec=40.0,
    ),

    # Fast Tier - 7B-8B models
    'llama3.2:8b': ModelCapabilities(
        name='llama3.2:8b',
        size_b=8,
        context_window=131072,
        capabilities={'general', 'long_context'},
        performance_tier='fast',
        specialisations=['general_purpose', 'long_context', 'efficient'],
        memory_gb=6.0,
        speed_tokens_sec=65.0,
    ),
    'mistral:7b': ModelCapabilities(
        name='mistral:7b',
        size_b=7,
        context_window=32768,
        capabilities={'general'},
        performance_tier='fast',
        specialisations=['general_purpose', 'efficient', 'fast_inference'],
        memory_gb=5.0,
        speed_tokens_sec=70.0,
    ),
    'deepseek-coder:6.7b': ModelCapabilities(
        name='deepseek-coder:6.7b',
        size_b=6.7,
        context_window=16384,
        capabilities={'code'},
        performance_tier='fast',
        specialisations=['code_generation', 'fast_inference'],
        memory_gb=5.0,
        speed_tokens_sec=72.0,
    ),
}

# Embedding models (separate registry)
EMBEDDING_REGISTRY = {
    'nomic-embed-text': {
        'dimensions': 768,
        'context_window': 8192,
        'memory_gb': 0.5,
        'speed': 'fast',
        'use_case': 'general_purpose',
    },
    'mxbai-embed-large': {
        'dimensions': 1024,
        'context_window': 512,
        'memory_gb': 0.7,
        'speed': 'medium',
        'use_case': 'high_quality',
    },
}
```

---

## Performance Benchmarks

### Mac Studio M4 Max Performance

Based on hardware optimisation research:

| Model | Tier | Speed (t/s) | Memory (GB) | Context Window | Use Case |
|-------|------|-------------|-------------|----------------|----------|
| **llama3.3:70b** | Quality | 10-12 | 45 | 128K | Complex reasoning, research |
| **deepseek-r1:70b** | Quality | 9-11 | 45 | 64K | Mathematical reasoning |
| **qwen2.5:72b** | Quality | 10-11 | 48 | 32K | Multilingual, general |
| **qwen2.5-coder:32b** | Balanced | 22-25 | 22 | 32K | Code generation |
| **deepseek-coder:33b** | Balanced | 22-24 | 23 | 16K | Code generation |
| **llama3.1:30b** | Balanced | 24-27 | 20 | 128K | Long documents |
| **qwen2.5:14b** | Balanced | 33-36 | 10 | 32K | Summarisation |
| **llama3.2:8b** | Fast | 63-68 | 6 | 128K | Quick QA |
| **mistral:7b** | Fast | 68-72 | 5 | 32K | Fast general purpose |

**Test configuration**: Mac Studio M4 Max 128GB, Q4_K_M quantisation, Metal acceleration

### Cross-Platform Comparison

| Hardware | Fast Tier | Balanced Tier | Quality Tier |
|----------|-----------|---------------|--------------|
| **Mac Studio M4 Max 128GB** | 65-70 t/s (8B) | 22-25 t/s (32B) | 10-12 t/s (70B) |
| **Mac mini M4 Pro 64GB** | 60-65 t/s (8B) | 20-23 t/s (32B) | N/A (insufficient RAM) |
| **MacBook Pro M4 Pro 48GB** | 55-60 t/s (8B) | 18-21 t/s (32B) | N/A (insufficient RAM) |
| **RTX 4090 24GB** | 70-80 t/s (8B) | 25-30 t/s (32B) | N/A (insufficient VRAM) |
| **RTX 5090 32GB** | 75-85 t/s (8B) | 30-35 t/s (32B) | 12-15 t/s (70B) |

**Note**: NVIDIA numbers are estimates based on comparable benchmarks.

---

## Configuration

### Router Configuration File

```yaml
# config/routing.yaml

routing:
  # Default tier when no persona active
  default_tier: "balanced"

  # Complexity thresholds for tier selection
  complexity_thresholds:
    fast_max: 3.5        # complexity < 3.5 → fast tier
    balanced_max: 7.0    # complexity < 7.0 → balanced tier
    quality_min: 7.0     # complexity >= 7.0 → quality tier

  # Task-specific routing overrides
  task_routing:
    code_generation:
      prefer_specialised: true
      min_tier: "balanced"
    reasoning:
      min_tier: "balanced"
    query_rewriting:
      max_tier: "fast"

  # Fallback configuration
  fallbacks:
    enabled: true
    max_fallbacks: 3
    strategy: "graceful_degradation"  # or "best_effort"

  # Model availability check
  model_check:
    enabled: true
    cache_duration_seconds: 300

  # Logging
  logging:
    log_decisions: true
    log_level: "INFO"
    log_file: "~/.ragged/logs/routing.log"

# Persona-specific routing overrides
personas:
  researcher:
    preferred_tier: "quality"
    tier_downgrade_threshold: 2
    task_overrides:
      code_generation: "balanced"

  developer:
    preferred_tier: "balanced"
    task_overrides:
      code_generation: "qwen2.5-coder:32b"

  casual:
    preferred_tier: "fast"
    tier_upgrade_threshold: 8
```

### CLI Flags

```bash
# Explicit model selection
ragged query "What is photosynthesis?" --model llama3.3:70b

# Force tier
ragged query "Explain quantum computing" --tier quality

# Override persona routing
ragged query "Write a sorting function" --model deepseek-coder:33b --ignore-persona

# Show routing decision
ragged query "Compare X and Y" --show-routing

# List available models with tiers
ragged models list --show-tiers
```

---

## Implementation Timeline

### v0.1 - MVP (Single Model)
**Duration**: 2-3 weeks
**Status**: Foundation

- ✅ Single model support (manual selection)
- ✅ Basic Ollama integration
- ✅ No routing (use default model)

**Deliverables**:
- Basic model interface
- Ollama client wrapper
- Manual model configuration

---

### v0.2 - Basic Routing
**Duration**: 3-4 weeks
**Status**: Planned

**Features**:
- Task classification (basic patterns)
- Hardware detection
- Tier recommendations (fast/balanced/quality)
- Simple task-based routing

**Deliverables**:
- `TaskClassifier` with regex patterns
- `HardwareDetector` integration
- `ModelSelector` with tier logic
- Configuration file support

**Example**:
```python
# Auto-select based on task
answer = ragged.query("Write a Python function...")
# → Automatically routes to code-specialised model
```

---

### v0.3 - Complexity Analysis
**Duration**: 2-3 weeks
**Status**: Planned

**Features**:
- Complexity scoring algorithm
- Tier selection based on complexity
- Capability matching
- Model registry with capabilities

**Deliverables**:
- `ComplexityAnalyser` with multi-dimensional scoring
- Expanded `MODEL_REGISTRY` with capabilities
- `CapabilityMatcher` for requirement matching

**Example**:
```python
# Simple query → fast tier
ragged.query("What is Paris?")  # → mistral:7b

# Complex query → quality tier
ragged.query("Analyse the architectural trade-offs...")  # → llama3.3:70b
```

---

### v0.4 - Persona Integration
**Duration**: 3-4 weeks
**Status**: Planned

**Features**:
- Persona-aware routing
- Persona model preferences
- Task overrides per persona
- Tier adjustment rules

**Deliverables**:
- `PersonaAwareRouter`
- Persona configuration schema
- Integration with persona system

**Example**:
```python
# Researcher persona prefers quality tier
ragged.set_persona("researcher")
ragged.query("Explain neural networks")  # → llama3.3:70b

# Developer persona uses code-specialised models
ragged.set_persona("developer")
ragged.query("Write a sorting function")  # → deepseek-coder:33b
```

---

### v0.5 - Advanced Routing
**Duration**: 2-3 weeks
**Status**: Planned

**Features**:
- Fallback chain generation
- Error handling and recovery
- Routing analytics and logging
- Performance monitoring

**Deliverables**:
- `FallbackGenerator`
- `RouterWithFallback`
- Routing decision logging
- Performance metrics collection

**Example**:
```python
# Automatic fallback if primary unavailable
ragged.query("Complex query")
# → Try llama3.3:70b
# → Fallback to qwen2.5:32b if unavailable
# → Fallback to llama3.2:8b if needed
```

---

### v1.0 - Production Routing
**Duration**: 3-4 weeks
**Status**: Future

**Features**:
- Cost optimisation (for cloud deployments)
- Latency optimisation
- A/B testing framework
- Learning-based routing (optional)
- Advanced monitoring and dashboards

**Deliverables**:
- Production-grade router
- Monitoring dashboards
- Cost tracking
- Performance analytics
- Optional: RouteLLM integration

---

## Testing Strategy

### Unit Tests

**Routing Components** (coverage target: 90%):
```python
# tests/routing/test_task_classifier.py
def test_classify_code_generation():
    classifier = TaskClassifier()
    assert classifier.classify("Write a Python function") == 'code_generation'
    assert classifier.classify("Debug this code") == 'code_generation'

def test_classify_reasoning():
    classifier = TaskClassifier()
    assert classifier.classify("Why does X happen?") == 'reasoning'
    assert classifier.classify("Compare A and B") == 'reasoning'

# tests/routing/test_complexity_analyser.py
def test_complexity_scoring():
    analyser = ComplexityAnalyserV2()

    # Simple query
    score = analyser.analyse("What is Paris?")
    assert score.total < 3.0
    assert score.tier == 'fast'

    # Complex query
    score = analyser.analyse("Analyse the architectural trade-offs between...")
    assert score.total > 7.0
    assert score.tier == 'quality'

# tests/routing/test_capability_matcher.py
def test_match_code_task():
    matcher = CapabilityMatcher(MODEL_REGISTRY)

    requirements = {
        'tier': 'balanced',
        'capabilities': {'code'},
        'specialisations': ['code_generation'],
    }

    model = matcher.find_best_match(
        requirements,
        available_models=['qwen2.5-coder:32b', 'llama3.2:8b'],
        hardware=mock_hardware_128gb
    )

    assert model == 'qwen2.5-coder:32b'
```

### Integration Tests

**End-to-End Routing** (coverage target: 80%):
```python
# tests/routing/test_integration.py
def test_routing_pipeline():
    router = UnifiedModelRouter(
        hardware=mock_hardware_128gb,
        model_registry=MODEL_REGISTRY
    )

    # Code generation routing
    request = RoutingRequest(
        query="Write a Python function to sort a list",
        available_models=['qwen2.5-coder:32b', 'llama3.2:8b']
    )
    decision = router.route(request)

    assert decision.task_type == 'code_generation'
    assert decision.model == 'qwen2.5-coder:32b'
    assert decision.tier == 'balanced'

def test_persona_routing():
    persona = Persona(
        name='researcher',
        preferred_model_tier='quality',
        task_model_overrides={}
    )

    request = RoutingRequest(
        query="Explain neural networks",
        persona=persona,
        available_models=['llama3.3:70b', 'llama3.2:8b']
    )

    decision = router.route(request)
    assert decision.tier == 'quality'
    assert decision.model == 'llama3.3:70b'
```

### Evaluation Tests

**Routing Quality Assessment**:
```python
# tests/routing/test_routing_quality.py
def test_routing_accuracy_on_golden_dataset():
    """Test routing decisions against golden dataset"""

    golden_dataset = load_golden_routing_examples()
    # Dataset contains: (query, expected_tier, expected_task_type)

    router = UnifiedModelRouter(...)
    correct = 0
    total = len(golden_dataset)

    for query, expected_tier, expected_task in golden_dataset:
        request = RoutingRequest(query=query)
        decision = router.route(request)

        if (decision.tier == expected_tier and
            decision.task_type == expected_task):
            correct += 1

    accuracy = correct / total
    assert accuracy >= 0.80, f"Routing accuracy {accuracy:.2%} below threshold"

def test_fallback_chain_quality():
    """Ensure fallback chains degrade gracefully"""

    generator = FallbackGenerator(MODEL_REGISTRY)

    # Quality tier primary
    fallbacks = generator.generate_fallbacks(
        primary_model='llama3.3:70b',
        requirements={'task_type': 'reasoning'},
        available_models=list(MODEL_REGISTRY.keys())
    )

    # Check fallbacks are progressively smaller
    primary_size = MODEL_REGISTRY['llama3.3:70b'].size_b
    for fallback in fallbacks:
        fallback_size = MODEL_REGISTRY[fallback].size_b
        assert fallback_size < primary_size
```

---

## Future Enhancements

### Phase 1: Learning-Based Routing (v1.1+)

**RouteLLM Integration**:
- Train lightweight router model on routing decisions
- 85% cost reduction while preserving 95% quality
- Requires dataset of (query, best_model, quality_score)

```python
# Future implementation
class LearnedRouter:
    """Router with learned preferences from usage data"""

    def train_from_history(self, routing_history: list[RoutingRecord]):
        """Train router from historical routing decisions and outcomes"""
        # RouteLLM or similar framework
        pass
```

### Phase 2: Multi-Model Ensemble (v1.2+)

**Use multiple models for single query**:
- Fast model for query rewriting
- Balanced model for initial answer
- Quality model for refinement/verification

```python
# Future implementation
class EnsembleRouter:
    """Route to multiple models in pipeline"""

    def route_ensemble(self, query: str) -> list[RoutingDecision]:
        return [
            RoutingDecision(model='mistral:7b', role='query_rewriter'),
            RoutingDecision(model='qwen2.5:32b', role='primary'),
            RoutingDecision(model='llama3.3:70b', role='verifier'),
        ]
```

### Phase 3: Cloud Integration (v2.0+)

**Hybrid local + cloud routing**:
- Use local models for fast/balanced tier
- Route complex queries to cloud (Claude, GPT-4)
- Cost-aware routing decisions

```python
# Future implementation
class HybridRouter:
    """Route between local and cloud models"""

    def route_hybrid(
        self,
        query: str,
        cost_limit: float,
        latency_limit: float
    ) -> RoutingDecision:
        # Balance cost, latency, quality
        pass
```

### Phase 4: Specialised Fine-Tuned Models (v2.1+)

**User-specific fine-tuning**:
- Fine-tune small models on user's documents
- Route domain-specific queries to fine-tuned models
- Continual learning from user feedback

---

## Summary

This document defines a comprehensive **dynamic model selection system** for ragged, enabling:

**Automatic Routing**: Intelligent model selection without user intervention
**Multi-Strategy**: Task-based, complexity-based, and persona-aware routing
**Hardware-Aware**: Respects memory and compute constraints
**Extensible**: Easy to add new models and routing strategies
**Production-Ready**: Robust fallback handling and error recovery

**Implementation spans v0.2-v1.0**, with progressive enhancement:
- v0.2: Basic task routing
- v0.3: Complexity analysis
- v0.4: Persona integration
- v0.5: Advanced fallbacks
- v1.0: Production monitoring

The system balances **performance, quality, and resource efficiency**, ensuring users get optimal results regardless of hardware tier or query complexity.

---

**Next Steps**:
1. Review and approve design
2. Create implementation tickets
3. Begin v0.2 development (basic routing)
4. Develop golden dataset for routing evaluation

---

**Document Status**: Design Complete
**Last Updated**: 2025-11-09
**Related Documents**:
- [Hardware Optimisation Strategy](./hardware-optimisation.md)
- [Personal Memory & Personas](./personal-memory-personas.md)
- [Testing Strategy](./testing-strategy.md) (pending)
