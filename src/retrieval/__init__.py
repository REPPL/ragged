"""
Retrieval system for semantic search and chunk retrieval.

Provides the Retriever class for querying the vector store and
retrieving relevant document chunks based on semantic similarity.
"""

from src.retrieval.retriever import RetrievedChunk, Retriever

__all__ = ["Retriever", "RetrievedChunk"]
