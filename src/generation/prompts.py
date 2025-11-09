"""
Prompt templates for RAG generation.

Provides prompt engineering templates for answer generation with citations.
"""

from typing import List

from src.retrieval.retriever import RetrievedChunk


RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on provided context.

Your responsibilities:
1. Answer the question using ONLY information from the provided context
2. If the context doesn't contain enough information, say "I don't have enough information to answer that question based on the provided context"
3. Include citations in your answer using [Source: filename] format
4. Be concise and accurate
5. Do not make up information or use knowledge outside the provided context

Format your citations like this:
- "According to the documentation [Source: install.md], you need Python 3.10 or higher."
- "The system supports PDF, TXT, MD, and HTML formats [Source: user-guide.md]."
"""


def build_rag_prompt(query: str, chunks: List[RetrievedChunk]) -> str:
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


def build_few_shot_prompt(query: str, chunks: List[RetrievedChunk]) -> str:
    """
    Build a RAG prompt with few-shot examples.

    Includes example Q&A pairs to improve citation format.

    Args:
        query: User's question
        chunks: Retrieved chunks

    Returns:
        Prompt with few-shot examples

    TODO: Implement few-shot prompting (v0.2 feature):
          1. Add example Q&A pairs showing good citations
          2. Then add actual context and query
          3. Improves consistency of citation format
    """
    # For v0.1, just use regular RAG prompt
    return build_rag_prompt(query, chunks)
