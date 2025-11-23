"""
Retrieval system for semantic search and chunk retrieval.

Provides the Retriever class for querying the vector store and
retrieving relevant document chunks based on semantic similarity.

v0.4.8: Personalised retrieval using interest profiles.
"""

from ragged.retrieval.personalised_retriever import PersonalisedRetriever
from ragged.retrieval.retriever import RetrievedChunk, Retriever

__all__ = ["Retriever", "RetrievedChunk", "PersonalisedRetriever"]
