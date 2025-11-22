"""
Prompt templates for chain-of-thought reasoning.

v0.3.7b: Structured prompts for transparent reasoning at multiple depth levels.
"""

from typing import List, Any
from src.generation.reasoning.types import ReasoningMode


# Base system instruction for all reasoning modes
REASONING_SYSTEM_INSTRUCTION = """You are a helpful AI assistant that provides transparent reasoning.
When answering questions, show your thinking process clearly and cite sources accurately.
Use [1], [2], [3] notation for citations corresponding to the provided sources."""


# Reasoning templates by mode
REASONING_TEMPLATES = {
    ReasoningMode.NONE: """
Based on the provided sources, please answer the following question:

{query}

Sources:
{context}

Provide a clear, concise answer with citations [1], [2], etc.
""",

    ReasoningMode.BASIC: """
Based on the provided sources, please answer the following question:

{query}

Sources:
{context}

Think step by step:
<reasoning>
1. What is being asked?
2. What relevant information do I have?
3. How do these pieces connect?
4. What is my conclusion?
</reasoning>

Then provide your answer:
<answer>
[Your answer with citations [1], [2], etc.]
</answer>
""",

    ReasoningMode.STRUCTURED: """
Based on the provided sources, please answer the following question:

{query}

Sources:
{context}

Work through this systematically using the following structure:

<reasoning>
<step number="1" action="understand">
Restate the question and identify key requirements.
</step>

<step number="2" action="retrieve">
Identify relevant information from the provided sources.
List which sources [1], [2], etc. are most relevant and why.
</step>

<step number="3" action="analyze" confidence="0.X">
Analyze the retrieved information:
- What does each source say?
- Are there any contradictions?
- Are there any gaps in information?
Rate your confidence (0.0-1.0) based on source quality and agreement.
</step>

<step number="4" action="synthesize" confidence="0.X">
Combine information from multiple sources to form a comprehensive answer.
Note any assumptions or limitations.
</step>

<step number="5" action="conclude" confidence="0.X">
State your final conclusion with overall confidence assessment.
</step>
</reasoning>

<answer>
[Your complete answer with [1], [2], [3] citations]
</answer>
""",

    ReasoningMode.CHAIN: """
Based on the provided sources, please answer the following question:

{query}

Sources:
{context}

Let me work through this systematically with full transparency.

<chain_of_thought>
## Understanding the Query
[Detailed analysis of what's being asked, breaking down any complex or multi-part questions]

## Evidence Gathering
From source [1]: [Key information and direct quotes]
From source [2]: [Key information and direct quotes]
From source [3]: [Key information and direct quotes]
...

## Reasoning Process
Given that [observation from evidence]...
This suggests [inference]...
However, [note any contradictions, uncertainties, or limitations]...
Cross-referencing sources [X] and [Y], we can see that [comparison]...
Therefore, [resolution or acknowledgment of limitation]...

## Confidence Assessment
- High confidence (>0.8): [What we're certain about based on strong agreement]
- Medium confidence (0.5-0.8): [What seems likely but has some uncertainty]
- Low confidence (<0.5): [What we're uncertain about or cannot verify]

## Validation Check
☑ Information consistency across sources: [Status and explanation]
☑ Citation accuracy and relevance: [Status and explanation]
☑ Logical coherence of reasoning: [Status and explanation]
☑ Identified gaps or assumptions: [List any limitations]

## Overall Confidence: [0.X]
[Brief justification for overall confidence score]
</chain_of_thought>

<answer>
[Your final, well-structured answer with [1], [2], [3] citations integrated naturally]
</answer>
"""
}


def build_reasoning_prompt(
    query: str,
    chunks: List[Any],
    mode: ReasoningMode = ReasoningMode.BASIC
) -> str:
    """
    Build a reasoning prompt for the specified mode.

    Args:
        query: User's question
        chunks: Retrieved document chunks with metadata
        mode: Reasoning depth level

    Returns:
        Formatted prompt string ready for LLM

    Example:
        >>> chunks = [
        ...     Chunk(content="ML is...", metadata={"source": "paper.pdf", "page": 1}),
        ...     Chunk(content="Neural networks...", metadata={"source": "book.pdf", "page": 42})
        ... ]
        >>> prompt = build_reasoning_prompt(
        ...     "What is machine learning?",
        ...     chunks,
        ...     ReasoningMode.BASIC
        ... )
    """
    # Format sources with citation numbers
    context = _format_sources(chunks)

    # Get template for mode
    template = REASONING_TEMPLATES.get(mode, REASONING_TEMPLATES[ReasoningMode.BASIC])

    # Fill in template
    prompt = template.format(query=query, context=context)

    return prompt


def _format_sources(chunks: List[Any]) -> str:
    """
    Format chunks as numbered sources for the prompt.

    Args:
        chunks: Retrieved document chunks

    Returns:
        Formatted source list with citation numbers

    Example:
        [1] Source: paper.pdf (Page 42)
        "Machine learning is a subset of artificial intelligence..."

        [2] Source: book.pdf (Page 15)
        "Neural networks are computational models..."
    """
    sources = []

    for i, chunk in enumerate(chunks, start=1):
        # Extract metadata
        metadata = getattr(chunk, 'metadata', {})
        source = metadata.get('source', 'Unknown')
        page = metadata.get('page')

        # Get content
        content = getattr(chunk, 'content', str(chunk))
        if hasattr(chunk, 'page_content'):
            content = chunk.page_content

        # Format source
        source_text = f"[{i}] Source: {source}"
        if page is not None:
            source_text += f" (Page {page})"

        source_text += f"\n\"{content}\"\n"
        sources.append(source_text)

    return "\n".join(sources)


def build_confidence_prompt(reasoning_steps: List[str], answer: str) -> str:
    """
    Build a follow-up prompt to assess confidence (if needed).

    This can be used to get a confidence score when the LLM doesn't
    provide one in the initial response.

    Args:
        reasoning_steps: List of reasoning steps from initial response
        answer: The answer provided

    Returns:
        Prompt asking for confidence assessment

    Example:
        >>> prompt = build_confidence_prompt(
        ...     ["Step 1: Understanding...", "Step 2: Retrieved..."],
        ...     "Machine learning is..."
        ... )
    """
    prompt = f"""
Given the following reasoning process and answer, provide a confidence score (0.0-1.0).

Reasoning:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(reasoning_steps))}

Answer:
{answer}

Consider:
- Agreement between sources
- Completeness of information
- Logical consistency
- Any contradictions or gaps

Provide only a confidence score between 0.0 and 1.0.
"""
    return prompt.strip()


def build_validation_prompt(reasoning_text: str, answer: str) -> str:
    """
    Build a prompt to validate reasoning for contradictions.

    This can be used as a second pass to validate the reasoning process.

    Args:
        reasoning_text: Raw reasoning from LLM
        answer: Final answer provided

    Returns:
        Prompt asking for validation check

    Example:
        >>> prompt = build_validation_prompt(
        ...     "<reasoning>...</reasoning>",
        ...     "Machine learning is..."
        ... )
    """
    prompt = f"""
Please validate the following reasoning for logical consistency:

Reasoning:
{reasoning_text}

Answer:
{answer}

Check for:
1. Internal contradictions
2. Unsupported claims
3. Logical fallacies
4. Gaps in reasoning

List any issues found, or respond "No issues detected" if the reasoning is sound.
"""
    return prompt.strip()


# Confidence interpretation guidance
CONFIDENCE_INTERPRETATION = {
    "very_high": (0.9, 1.0, "Very confident - strong agreement between high-quality sources"),
    "high": (0.7, 0.9, "Confident - sources generally agree with minor uncertainties"),
    "medium": (0.5, 0.7, "Moderate confidence - some contradictions or gaps in sources"),
    "low": (0.3, 0.5, "Low confidence - significant uncertainties or limited information"),
    "very_low": (0.0, 0.3, "Very low confidence - contradictory sources or insufficient evidence"),
}


def interpret_confidence(score: float) -> str:
    """
    Get human-readable interpretation of confidence score.

    Args:
        score: Confidence value (0.0-1.0)

    Returns:
        Interpretation string

    Example:
        >>> interpret_confidence(0.85)
        'Confident - sources generally agree with minor uncertainties'
    """
    for level, (low, high, description) in CONFIDENCE_INTERPRETATION.items():
        if low <= score < high:
            return description
    return "Unknown confidence level"
