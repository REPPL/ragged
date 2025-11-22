"""
Prompt templates for RAG generation.

Provides prompt engineering templates for answer generation with citations.
"""


from src.generation.few_shot import FewShotExampleStore, format_few_shot_prompt
from src.retrieval.retriever import RetrievedChunk

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided context.

Your responsibilities:
1. Answer the question using ONLY information from the provided context
2. If the context doesn't contain enough information, say "I don't have enough information to answer that question based on the provided context"
3. Include numbered citations in your answer using [1], [2], [3] format
4. Be concise and accurate
5. Do not make up information or use knowledge outside the provided context

Important citation rules:
- Use ONLY the numbers [1], [2], [3], etc. that correspond to the context sources provided
- Place citations immediately after the relevant statement
- You may cite the same source multiple times if needed
- Do not invent citation numbers that weren't provided in the context

Format your citations like this:
- "According to the documentation [1], you need Python 3.10 or higher."
- "The system supports PDF, TXT, MD, and HTML formats [2]."
- "Machine learning models require training data [1] and can be used for various tasks [3]."
"""


def build_rag_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    """
    Build a RAG prompt from query and retrieved chunks.

    Args:
        query: User's question
        chunks: Retrieved relevant chunks

    Returns:
        Formatted prompt for LLM

    Example output:
        Context:
        [1] (from document.pdf): "Machine learning is..."
        [2] (from guide.md): "RAG systems combine..."

        Question: What is machine learning?

        Instructions: Answer using only the context above...
    """
    # Format context from chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        # Extract filename from path
        from pathlib import Path
        source = Path(chunk.document_path).name if chunk.document_path else "unknown"
        context_parts.append(f"[{i}] (from {source}): {chunk.text}")

    context = "\n\n".join(context_parts)

    # Build final prompt
    prompt = f"""Context:
{context}

Question: {query}

Instructions: Answer the question using only the context above. Include citations using [Source: filename] format.

Answer:"""

    return prompt


def build_few_shot_prompt(
    query: str,
    chunks: list[RetrievedChunk],
    example_store: FewShotExampleStore | None = None,
    num_examples: int = 3
) -> str:
    """Build a RAG prompt with few-shot examples.

    Includes relevant example Q&A pairs to improve answer quality.

    Args:
        query: User's question
        chunks: Retrieved chunks
        example_store: Optional example store (creates default if None)
        num_examples: Number of few-shot examples to include

    Returns:
        Prompt with few-shot examples
    """
    # Format context from chunks
    from pathlib import Path
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = Path(chunk.document_path).name if chunk.document_path else "unknown"
        # Use original_content if available, otherwise text
        text = getattr(chunk, 'original_content', chunk.text)
        context_parts.append(f"[Source {i}: {source}]\n{text}")

    context = "\n\n---\n\n".join(context_parts)

    # Get few-shot examples if store provided
    if example_store and len(example_store.get_all_examples()) > 0:
        similar_examples = example_store.search_similar(query, top_k=num_examples)
        return format_few_shot_prompt(query, context, similar_examples, num_examples)
    else:
        # Fallback to basic prompt without examples
        prompt = f"""Context:
{context}

Question: {query}

Instructions: Answer the question using only the context above. Include citations using [Source: filename] format.

Answer:"""
        return prompt


def build_contextual_prompt(
    query: str,
    chunks: list[RetrievedChunk],
    use_compression: bool = False
) -> str:
    """Build a RAG prompt with contextual chunks.

    Uses enriched chunks with document/section context headers.

    Args:
        query: User's question
        chunks: Contextual chunks (with headers)
        use_compression: Whether to compress context

    Returns:
        Prompt with contextual information
    """
    from src.chunking.contextual import ContextCompressor

    if use_compression:
        compressor = ContextCompressor(max_tokens=2000)
        context = compressor.compress(chunks, query)  # type: ignore[arg-type]
    else:
        # Use enriched text from contextual chunks
        context = build_rag_prompt(query, chunks).split("Question:")[0].strip()

    prompt = f"""{context}

Question: {query}

Instructions: Answer based on the context above. Use the document and section information to provide a well-sourced answer with citations [Source: filename].

Answer:"""

    return prompt
