"""BM25 keyword-based retrieval for ragged v0.2."""

from typing import List, Tuple, Optional
from rank_bm25 import BM25Okapi
import logging

logger = logging.getLogger(__name__)


class BM25Retriever:
    """BM25 (Best Matching 25) keyword-based retriever.

    Uses the Okapi BM25 algorithm for keyword-based document retrieval.
    Complements vector-based semantic search in hybrid retrieval.
    """

    def __init__(self):
        """Initialize BM25 retriever."""
        self.index: Optional[BM25Okapi] = None
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.metadatas: List[dict] = []

    def index_documents(
        self,
        documents: List[str],
        doc_ids: List[str],
        metadatas: Optional[List[dict]] = None,
    ) -> None:
        """Index documents for BM25 search.

        Args:
            documents: List of document texts to index
            doc_ids: List of document IDs (must match documents length)
            metadatas: Optional list of metadata dicts
        """
        if len(documents) != len(doc_ids):
            raise ValueError("documents and doc_ids must have same length")

        if not documents:
            logger.warning("No documents to index")
            return

        # Tokenize documents (simple whitespace split)
        tokenized_corpus = [doc.lower().split() for doc in documents]

        # Create BM25 index
        self.index = BM25Okapi(tokenized_corpus)
        self.documents = documents
        self.doc_ids = doc_ids
        self.metadatas = metadatas or [{} for _ in documents]

        logger.info(f"Indexed {len(documents)} documents for BM25 search")

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Tuple[str, str, float, dict]]:
        """Search for documents using BM25.

        Args:
            query: Search query
            top_k: Number of top results to return

        Returns:
            List of (doc_id, document, score, metadata) tuples, sorted by score descending
        """
        if self.index is None:
            raise RuntimeError("No documents indexed. Call index_documents() first.")

        if not query.strip():
            return []

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores
        scores = self.index.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        # Build results
        results = [
            (
                self.doc_ids[i],
                self.documents[i],
                float(scores[i]),
                self.metadatas[i]
            )
            for i in top_indices
            if scores[i] > 0  # Only return docs with non-zero scores
        ]

        logger.debug(f"BM25 search for '{query}' returned {len(results)} results")

        return results

    def get_top_k_indices(self, query: str, top_k: int = 5) -> List[int]:
        """Get indices of top-k documents for a query.

        Useful for fusion algorithms that need document indices.

        Args:
            query: Search query
            top_k: Number of top results

        Returns:
            List of document indices, sorted by score descending
        """
        if self.index is None:
            raise RuntimeError("No documents indexed. Call index_documents() first.")

        tokenized_query = query.lower().split()
        scores = self.index.get_scores(tokenized_query)

        return sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

    def clear(self) -> None:
        """Clear the index and all stored documents."""
        self.index = None
        self.documents = []
        self.doc_ids = []
        self.metadatas = []
        logger.info("BM25 index cleared")

    def count(self) -> int:
        """Return number of indexed documents."""
        return len(self.documents)
