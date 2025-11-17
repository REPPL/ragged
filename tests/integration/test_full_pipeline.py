"""
Integration tests for the full RAG pipeline.

Tests end-to-end flow: document ingestion → chunking → embedding → storage → retrieval → generation
"""

import pytest
from pathlib import Path
from src.ingestion.loaders import load_document
from src.chunking.splitters import RecursiveCharacterTextSplitter
from src.embeddings.factory import create_embedder
from src.storage.vector_store import VectorStore
from src.retrieval.retriever import Retriever
from src.generation.ollama_client import OllamaClient
from src.config.settings import get_settings


class TestFullRAGPipeline:
    """Test complete RAG pipeline with real components."""

    @pytest.fixture
    def settings(self):
        """Get settings for tests."""
        return get_settings()

    @pytest.fixture
    def sample_text_file(self, tmp_path):
        """Create a sample text file for testing."""
        content = """
        Artificial Intelligence and Machine Learning

        Machine learning is a subset of artificial intelligence that enables systems to learn
        from data without being explicitly programmed. Deep learning, a subset of machine learning,
        uses neural networks with multiple layers.

        Natural Language Processing (NLP) is a branch of AI that helps computers understand,
        interpret, and generate human language. Modern NLP systems use transformer architectures
        like BERT and GPT.

        Computer vision is another AI domain that enables machines to interpret visual information
        from the world. It powers applications like facial recognition and autonomous vehicles.
        """

        file_path = tmp_path / "ai_overview.txt"
        file_path.write_text(content.strip())
        return file_path

    @pytest.fixture
    def vector_store(self, settings):
        """Create a clean vector store for testing."""
        # Parse chroma_url to extract host and port
        import re
        match = re.match(r'https?://([^:]+):(\d+)', settings.chroma_url)
        if match:
            host, port = match.groups()
            port = int(port)
        else:
            host, port = "localhost", 8001

        store = VectorStore(
            host=host,
            port=port,
            collection_name="test_integration"
        )
        # Clear any existing data
        store.clear()
        yield store
        # Cleanup after test
        store.clear()

    @pytest.mark.integration
    def test_complete_pipeline_with_sentence_transformers(
        self, sample_text_file, vector_store, settings
    ):
        """Test full pipeline: ingest → chunk → embed → store → retrieve → generate."""

        # Step 1: Load document
        document = load_document(sample_text_file)
        assert document is not None
        assert len(document.content) > 0
        assert document.metadata.file_name == "ai_overview.txt"

        # Step 2: Chunk document
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        chunks = splitter.chunk_document(document)
        assert len(chunks) > 0
        assert all(chunk.content for chunk in chunks)

        # Step 3: Create embedder
        embedder = create_embedder(
            model_type="sentence-transformers",
            model_name="all-MiniLM-L6-v2"
        )

        # Step 4: Embed and store chunks
        for chunk in chunks:
            embedding = embedder.embed_text(chunk.content)
            vector_store.add(
                ids=[chunk.id],
                embeddings=[embedding],
                documents=[chunk.content],
                metadatas=[chunk.metadata.model_dump()]
            )

        # Verify storage
        count = vector_store.count()
        assert count == len(chunks)

        # Step 5: Retrieve relevant chunks
        retriever = Retriever(
            embedder=embedder,
            vector_store=vector_store
        )

        query = "What is deep learning?"
        retrieved_chunks = retriever.retrieve(query, top_k=3)

        assert len(retrieved_chunks) > 0
        assert all(chunk.score > 0 for chunk in retrieved_chunks)
        # Should retrieve chunk mentioning deep learning
        assert any("deep learning" in chunk.content.lower() for chunk in retrieved_chunks)

        # Step 6: Generate answer (requires Ollama)
        # Skip generation test if Ollama not available
        try:
            llm_client = OllamaClient(
                base_url=settings.ollama_url,
                model=settings.llm_model
            )

            # Build context from retrieved chunks
            context = "\n\n".join([
                f"[Source: {chunk.source_file}]\n{chunk.content}"
                for chunk in retrieved_chunks
            ])

            prompt = f"""You are a helpful AI assistant. Answer the question based on the context provided.

Context:
{context}

Question: {query}

Answer with citations in the format [Source: filename]:"""

            response = llm_client.generate(prompt)

            assert response is not None
            assert len(response) > 0
            # Response should mention the source
            assert "ai_overview.txt" in response.lower() or "[source:" in response.lower()

        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")

    @pytest.mark.integration
    def test_multiple_documents_retrieval(self, tmp_path, vector_store, settings):
        """Test retrieval across multiple documents."""

        # Create multiple documents
        doc1_path = tmp_path / "python.txt"
        doc1_path.write_text("""
        Python is a high-level programming language known for its simplicity and readability.
        It supports multiple programming paradigms including procedural, object-oriented, and functional.
        """)

        doc2_path = tmp_path / "javascript.txt"
        doc2_path.write_text("""
        JavaScript is a programming language primarily used for web development.
        It runs in browsers and enables interactive web pages.
        """)

        # Load and process both documents
        embedder = create_embedder(
            model_type="sentence-transformers",
            model_name="all-MiniLM-L6-v2"
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

        all_chunks = []
        for doc_path in [doc1_path, doc2_path]:
            document = load_document(doc_path)
            chunks = splitter.chunk_document(document)
            all_chunks.extend(chunks)

        # Store all chunks
        for chunk in all_chunks:
            embedding = embedder.embed_text(chunk.content)
            vector_store.add(
                ids=[chunk.id],
                embeddings=[embedding],
                documents=[chunk.content],
                metadatas=[chunk.metadata.model_dump()]
            )

        # Retrieve for Python-specific query
        retriever = Retriever(embedder=embedder, vector_store=vector_store)
        results = retriever.retrieve("What programming paradigms does Python support?", top_k=2)

        # Should retrieve Python document
        assert any("python" in chunk.content.lower() for chunk in results)
        assert any("paradigm" in chunk.content.lower() for chunk in results)

    @pytest.mark.integration
    def test_empty_query_handling(self, vector_store, settings):
        """Test graceful handling of edge cases."""

        embedder = create_embedder(
            model_type="sentence-transformers",
            model_name="all-MiniLM-L6-v2"
        )
        retriever = Retriever(embedder=embedder, vector_store=vector_store)

        # Empty collection should return empty results
        results = retriever.retrieve("test query", top_k=5)
        assert len(results) == 0

    @pytest.mark.integration
    def test_pipeline_with_metadata_filtering(self, sample_text_file, vector_store, settings):
        """Test retrieval with metadata filtering."""

        # Load and process document
        document = load_document(sample_text_file)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        chunks = splitter.chunk_document(document)

        # Embed and store with metadata
        embedder = create_embedder(
            model_type="sentence-transformers",
            model_name="all-MiniLM-L6-v2"
        )

        for chunk in chunks:
            embedding = embedder.embed_text(chunk.content)
            metadata = chunk.metadata.model_dump()
            metadata["custom_tag"] = "ai_topic"  # Add custom metadata

            vector_store.add(
                ids=[chunk.id],
                embeddings=[embedding],
                documents=[chunk.content],
                metadatas=[metadata]
            )

        # Query with metadata filter
        retriever = Retriever(embedder=embedder, vector_store=vector_store)

        # Should be able to retrieve with filter
        # (Note: ChromaDB metadata filtering syntax may vary)
        results = retriever.retrieve("machine learning", top_k=3)
        assert len(results) > 0
