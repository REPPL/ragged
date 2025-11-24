"""
Retrieval system for semantic search and chunk retrieval.

Provides the Retriever class for querying the vector store and
retrieving relevant document chunks based on semantic similarity.

v0.4.8: Personalised retrieval using interest profiles.
"""

from ragged.retrieval.retriever import RetrievedChunk, Retriever

__all__ = ["Retriever", "RetrievedChunk", "PersonalisedRetriever"]


def __getattr__(name: str):
    """Lazy import to avoid circular dependency with memory.personalisation."""
    if name == "PersonalisedRetriever":
        from ragged.retrieval.personalised_retriever import PersonalisedRetriever
        return PersonalisedRetriever
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
