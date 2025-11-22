"""ChromaDB implementation of VectorStore interface."""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import numpy as np

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

from ragged.vectorstore.interface import VectorStore, VectorStoreDocument, VectorStoreQueryResult
from ragged.vectorstore.exceptions import VectorStoreConnectionError, VectorStoreNotFoundError

logger = logging.getLogger(__name__)


class ChromaDBStore(VectorStore):
    """ChromaDB implementation of VectorStore."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialise ChromaDB store.

        Args:
            config: Configuration dictionary with 'persist_directory' and other settings
        """
        if chromadb is None:
            raise ImportError("chromadb not installed. Install with: pip install chromadb")

        self.config = config or {}
        persist_dir = self.config.get("persist_directory", str(Path.home() / ".ragged" / "data" / "chroma"))

        try:
            self.client = chromadb.PersistentClient(path=persist_dir)
            logger.info(f"Initialised ChromaDB at {persist_dir}")
        except Exception as e:
            raise VectorStoreConnectionError(f"Failed to connect to ChromaDB: {e}")

    def health_check(self) -> bool:
        """Check ChromaDB health."""
        try:
            self.client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False

    def add(
        self,
        ids: List[str],
        embeddings: np.ndarray,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        collection_name: str = "default",
    ) -> None:
        """Add documents to ChromaDB."""
        collection = self.client.get_or_create_collection(name=collection_name)
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.debug(f"Added {len(ids)} documents to collection '{collection_name}'")

    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        collection_name: str = "default",
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> VectorStoreQueryResult:
        """Search ChromaDB for similar documents."""
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            raise VectorStoreNotFoundError(f"Collection '{collection_name}' not found")

        results = collection.query(
            query_embeddings=[query_embedding.tolist()] if isinstance(query_embedding, np.ndarray) else [query_embedding],
            n_results=n_results,
            where=filter_dict,
        )

        # Convert to VectorStoreQueryResult
        documents = []
        for i, doc_id in enumerate(results["ids"][0]):
            doc = VectorStoreDocument(
                id=doc_id,
                content=results["documents"][0][i] if results.get("documents") else "",
                metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
            )
            documents.append(doc)

        return VectorStoreQueryResult(
            documents=documents,
            distances=results["distances"][0] if results.get("distances") else [],
            ids=results["ids"][0],
        )

    def delete(self, document_ids: List[str], collection_name: str = "default") -> int:
        """Delete documents from ChromaDB."""
        try:
            collection = self.client.get_collection(name=collection_name)
            collection.delete(ids=document_ids)
            return len(document_ids)
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return 0

    def update(
        self,
        ids: List[str],
        embeddings: Optional[np.ndarray] = None,
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        collection_name: str = "default",
    ) -> int:
        """Update documents in ChromaDB."""
        try:
            collection = self.client.get_collection(name=collection_name)
            update_kwargs = {"ids": ids}
            if embeddings is not None:
                update_kwargs["embeddings"] = embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings
            if documents is not None:
                update_kwargs["documents"] = documents
            if metadatas is not None:
                update_kwargs["metadatas"] = metadatas

            collection.update(**update_kwargs)
            return len(ids)
        except Exception as e:
            logger.error(f"Failed to update documents: {e}")
            return 0

    def get(self, document_ids: List[str], collection_name: str = "default") -> List[VectorStoreDocument]:
        """Get documents by ID from ChromaDB."""
        try:
            collection = self.client.get_collection(name=collection_name)
            results = collection.get(ids=document_ids)

            documents = []
            for i, doc_id in enumerate(results["ids"]):
                doc = VectorStoreDocument(
                    id=doc_id,
                    content=results["documents"][i] if results.get("documents") else "",
                    metadata=results["metadatas"][i] if results.get("metadatas") else {},
                )
                documents.append(doc)

            return documents
        except Exception as e:
            logger.error(f"Failed to get documents: {e}")
            return []

    def count(self, collection_name: str = "default") -> int:
        """Count documents in collection."""
        try:
            collection = self.client.get_collection(name=collection_name)
            return collection.count()
        except Exception:
            return 0

    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def create_collection(self, name: str, metadata: Optional[Dict] = None) -> None:
        """Create a new collection."""
        self.client.create_collection(name=name, metadata=metadata or {})
        logger.info(f"Created collection '{name}'")

    def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(name=name)
            logger.info(f"Deleted collection '{name}'")
        except Exception as e:
            logger.error(f"Failed to delete collection '{name}': {e}")

    def close(self) -> None:
        """Close ChromaDB connection."""
        # ChromaDB doesn't require explicit closing
        logger.debug("Closed ChromaDB connection")
