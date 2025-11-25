"""RAG tools for agent framework.

Phase 2 Infrastructure: Core RAG operations wrapped as agent tools.

Design Principles:
- Wrap existing RAG services with tool interface
- Provide clear parameter schemas for LLM tool calling
- Handle errors gracefully with informative messages
"""

import logging
from pathlib import Path
from typing import Any

from ragged.agents.base import (
    ExecutionContext,
    Tool,
    ToolCategory,
    ToolExecutionError,
    ToolSpec,
)

logger = logging.getLogger(__name__)


class VectorSearchTool(Tool):
    """Search documents using vector similarity.

    Wraps the Retriever to provide semantic search over
    indexed documents.

    Example:
        >>> tool = VectorSearchTool()
        >>> results = await tool.execute(
        ...     context,
        ...     query="authentication best practices",
        ...     k=5,
        ... )
    """

    @property
    def spec(self) -> ToolSpec:
        """Get tool specification."""
        return ToolSpec(
            name="search",
            description=(
                "Search documents using semantic similarity. "
                "Returns the most relevant document chunks for a query."
            ),
            category=ToolCategory.RAG,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query in natural language",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5,
                    },
                    "min_score": {
                        "type": "number",
                        "description": "Minimum similarity score threshold (optional)",
                    },
                    "filter": {
                        "type": "object",
                        "description": "Metadata filter (optional)",
                    },
                },
                "required": ["query"],
            },
            returns="List of relevant document chunks with scores and metadata",
            examples=[
                "search(query='how to implement authentication')",
                "search(query='API endpoints', k=10)",
                "search(query='security', filter={'type': 'pdf'})",
            ],
        )

    async def execute(self, context: ExecutionContext, **kwargs) -> Any:
        """Execute vector search.

        Args:
            context: Execution context
            **kwargs: Search parameters (query, k, min_score, filter)

        Returns:
            List of search results with text, score, and metadata
        """
        query = kwargs.get("query", "")
        k = kwargs.get("k", 5)
        min_score = kwargs.get("min_score")
        filter_metadata = kwargs.get("filter")

        if not query:
            raise ToolExecutionError("search", "Query cannot be empty")

        logger.debug(f"VectorSearchTool: searching for '{query[:50]}...' (k={k})")

        try:
            # Import here to avoid circular dependencies
            from ragged.retrieval import Retriever

            retriever = Retriever()
            chunks = retriever.retrieve(
                query=query,
                k=k,
                filter_metadata=filter_metadata,
                min_score=min_score,
            )

            # Convert to serialisable format
            results = [
                {
                    "text": chunk.text,
                    "score": chunk.score,
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "document_path": chunk.document_path,
                    "metadata": chunk.metadata,
                }
                for chunk in chunks
            ]

            logger.info(f"VectorSearchTool: found {len(results)} results")
            return results

        except Exception as e:
            logger.exception(f"VectorSearchTool failed: {e}")
            raise ToolExecutionError("search", str(e), cause=e)


class IngestTool(Tool):
    """Ingest documents into the knowledge base.

    Wraps the document ingestion pipeline to add documents
    for future retrieval.

    Example:
        >>> tool = IngestTool()
        >>> result = await tool.execute(
        ...     context,
        ...     path="/path/to/document.pdf",
        ... )
    """

    @property
    def spec(self) -> ToolSpec:
        """Get tool specification."""
        return ToolSpec(
            name="ingest",
            description=(
                "Add a document to the knowledge base. "
                "Supports PDF, TXT, MD, and HTML files."
            ),
            category=ToolCategory.RAG,
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to document file",
                    },
                    "format": {
                        "type": "string",
                        "description": "Document format (pdf, txt, md, html). Auto-detected if not specified.",
                        "enum": ["pdf", "txt", "md", "html"],
                    },
                    "chunking": {
                        "type": "string",
                        "description": "Chunking strategy (fixed, semantic, hierarchical)",
                        "enum": ["fixed", "semantic", "hierarchical"],
                        "default": "fixed",
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata to attach to document",
                    },
                },
                "required": ["path"],
            },
            returns="Ingestion result with document ID and chunk count",
            examples=[
                "ingest(path='/docs/guide.pdf')",
                "ingest(path='/docs/readme.md', chunking='semantic')",
            ],
            requires_confirmation=True,  # Modifies data
        )

    async def execute(self, context: ExecutionContext, **kwargs) -> Any:
        """Execute document ingestion.

        Args:
            context: Execution context
            **kwargs: Ingestion parameters (path, format, chunking, metadata)

        Returns:
            Dictionary with document_id, chunk_count, and status
        """
        path_str = kwargs.get("path", "")
        format_hint = kwargs.get("format")
        chunking = kwargs.get("chunking", "fixed")
        extra_metadata = kwargs.get("metadata", {})

        if not path_str:
            raise ToolExecutionError("ingest", "Path cannot be empty")

        path = Path(path_str)

        if not path.exists():
            raise ToolExecutionError("ingest", f"File not found: {path}")

        logger.debug(f"IngestTool: ingesting '{path}' with {chunking} chunking")

        try:
            # Import here to avoid circular dependencies
            from ragged.ingestion.loaders import load_document
            from ragged.chunking import chunk_document
            from ragged.storage.vector_store import VectorStore
            from ragged.embeddings.factory import get_embedder

            # Load document
            document = load_document(path, format=format_hint)

            # Add extra metadata
            if extra_metadata:
                document.metadata.update(extra_metadata)

            # Chunk document
            chunks = chunk_document(document, strategy=chunking)

            # Embed and store chunks
            embedder = get_embedder()
            vector_store = VectorStore()

            chunk_ids = []
            for chunk in chunks:
                embedding = embedder.embed_text(chunk.text)
                chunk_id = vector_store.add(
                    id=chunk.chunk_id,
                    embedding=embedding,
                    document=chunk.text,
                    metadata={
                        **chunk.metadata,
                        "document_id": document.document_id,
                        "document_path": str(path),
                        "chunk_position": chunk.position,
                    },
                )
                chunk_ids.append(chunk_id)

            result = {
                "document_id": document.document_id,
                "path": str(path),
                "chunk_count": len(chunk_ids),
                "status": "success",
            }

            logger.info(
                f"IngestTool: ingested {result['chunk_count']} chunks "
                f"from {path.name}"
            )
            return result

        except Exception as e:
            logger.exception(f"IngestTool failed: {e}")
            raise ToolExecutionError("ingest", str(e), cause=e)


class QueryTool(Tool):
    """Execute RAG query with retrieval and generation.

    Combines retrieval and LLM generation to answer questions
    using the knowledge base.

    Example:
        >>> tool = QueryTool()
        >>> response = await tool.execute(
        ...     context,
        ...     question="What are the security best practices?",
        ... )
    """

    @property
    def spec(self) -> ToolSpec:
        """Get tool specification."""
        return ToolSpec(
            name="query",
            description=(
                "Answer a question using RAG (Retrieval-Augmented Generation). "
                "Retrieves relevant documents and generates an answer."
            ),
            category=ToolCategory.RAG,
            parameters={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to answer",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of chunks to retrieve for context (default: 5)",
                        "default": 5,
                    },
                    "model": {
                        "type": "string",
                        "description": "LLM model to use for generation (optional)",
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Generation temperature (0.0-1.0, default: 0.7)",
                        "default": 0.7,
                    },
                },
                "required": ["question"],
            },
            returns="Generated answer with source citations",
            examples=[
                "query(question='How do I configure authentication?')",
                "query(question='Summarise the API docs', k=10)",
            ],
        )

    async def execute(self, context: ExecutionContext, **kwargs) -> Any:
        """Execute RAG query.

        Args:
            context: Execution context
            **kwargs: Query parameters (question, k, model, temperature)

        Returns:
            Dictionary with answer, sources, and metadata
        """
        question = kwargs.get("question", "")
        k = kwargs.get("k", 5)
        model = kwargs.get("model")
        temperature = kwargs.get("temperature", 0.7)

        if not question:
            raise ToolExecutionError("query", "Question cannot be empty")

        logger.debug(f"QueryTool: answering '{question[:50]}...'")

        try:
            # Import here to avoid circular dependencies
            from ragged.retrieval import Retriever
            from ragged.generation import OllamaClient, build_rag_prompt, parse_response

            # Retrieve relevant chunks
            retriever = Retriever()
            chunks = retriever.retrieve(query=question, k=k)

            if not chunks:
                return {
                    "answer": "No relevant documents found to answer this question.",
                    "sources": [],
                    "chunk_count": 0,
                }

            # Build context from chunks
            context_texts = [
                f"[{i+1}] {chunk.text}"
                for i, chunk in enumerate(chunks)
            ]
            context_str = "\n\n".join(context_texts)

            # Generate answer
            client = OllamaClient(model=model) if model else OllamaClient()
            prompt = build_rag_prompt(question, context_str)
            raw_response = client.generate(prompt, temperature=temperature)

            # Parse response
            parsed = parse_response(raw_response)

            # Build source citations
            sources = [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_path": chunk.document_path,
                    "score": chunk.score,
                    "preview": chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text,
                }
                for chunk in chunks
            ]

            result = {
                "answer": parsed.answer if hasattr(parsed, 'answer') else raw_response,
                "sources": sources,
                "chunk_count": len(chunks),
                "model": client.model if hasattr(client, 'model') else model,
            }

            logger.info(f"QueryTool: generated answer using {len(chunks)} sources")
            return result

        except Exception as e:
            logger.exception(f"QueryTool failed: {e}")
            raise ToolExecutionError("query", str(e), cause=e)
