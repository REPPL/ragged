"""Few-shot prompt formatting."""


from src.generation.few_shot.models import FewShotExample


def format_few_shot_prompt(
    query: str,
    context: str,
    examples: list[FewShotExample],
    max_examples: int = 3
) -> str:
    """Format a prompt with few-shot examples.

    Args:
        query: Current query
        context: Retrieved context for current query
        examples: Few-shot examples to include
        max_examples: Maximum number of examples to include

    Returns:
        Formatted prompt with examples
    """
    if not examples:
        # No examples - return basic prompt
        return f"""Context:
{context}

Question: {query}

Answer:"""

    # Include examples
    example_text = "\n\n".join(
        ex.to_prompt_format() for ex in examples[:max_examples]
    )

    prompt = f"""You are a helpful AI assistant. Answer questions based on the provided context.

Here are some examples of good answers:

{example_text}

Now answer this question:

Context:
{context}

Question: {query}

Answer:"""

    return prompt
