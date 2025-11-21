# VISION-003: Vision-Aware Retrieval System

**Feature:** Multi-Modal Query Processing and Vision Retrieval
**Category:** Retrieval Enhancement
**Estimated Effort:** 28-38 hours
**Dependencies:** VISION-001 (ColPali), VISION-002 (Dual Storage)
**Status:** Planned

---

## Overview

Transform ragged's retrieval system to leverage vision embeddings for multi-modal queries. This feature enables users to query documents using:
- **Text queries** (existing): Traditional semantic search
- **Image queries** (new): Upload screenshot/diagram to find similar visuals
- **Hybrid queries** (new): Combined text + image search
- **Visual reranking** (new): Boost results with relevant diagrams/tables

**Use Cases:**
1. "Find the architecture diagram that looks like this sketch"
2. "Search for 'database schema' with preference for results containing diagrams"
3. "Find pages similar to this screenshot from another document"

---

## Architecture

### Current State (v0.4.x)

```python
# Text-only retrieval
retriever = Retriever()
results = retriever.query("database schema")
# Returns: Text chunks ranked by semantic similarity
```

### Target State (v0.5.0)

```python
# Multi-modal retrieval
retriever = VisionRetriever()

# Text query with visual boost
results = retriever.query(
    text="database schema",
    boost_diagrams=True  # Prioritise results with diagrams
)

# Image query
results = retriever.query_image(
    image_path="sketch.png",
    n_results=10
)

# Hybrid text + image
results = retriever.query_hybrid(
    text="authentication flow",
    image_path="example_diagram.png",
    text_weight=0.6,
    vision_weight=0.4
)
```

### Retrieval Pipeline

```
User Query
    ↓
[Query Processor]
    ├─ Text Query → TextEmbedder → 384-dim embedding
    ├─ Image Query → ColPaliEmbedder → 768-dim embedding
    └─ Hybrid → Both embeddings
    ↓
[DualEmbeddingStore]
    ├─ Text-only search → Text embeddings
    ├─ Vision-only search → Vision embeddings
    └─ Hybrid search → Both, merged with RRF
    ↓
[Visual Reranker] (optional)
    ├─ Boost results with diagrams/tables
    ├─ Filter by layout complexity
    └─ Cross-modal relevance scoring
    ↓
Results (ranked by combined score)
```

---

## Implementation Plan

### Phase 1: Multi-Modal Query Processing (8-10 hours)

#### Session 1.1: Query Type Detection (3-4h)

**Task:** Implement query type classification and processing

**Implementation:**

```python
# src/retrieval/query_processor.py

from enum import Enum
from pathlib import Path
from typing import Optional, Union, Tuple
from dataclasses import dataclass
import numpy as np
from PIL import Image
from loguru import logger

from ragged.embeddings.text_embedder import TextEmbedder
from ragged.embeddings.colpali_embedder import ColPaliEmbedder


class QueryType(str, Enum):
    """Query type enumeration."""
    TEXT_ONLY = "text_only"
    IMAGE_ONLY = "image_only"
    HYBRID = "hybrid"


@dataclass
class QueryEmbeddings:
    """
    Container for query embeddings.

    Attributes:
        query_type: Type of query
        text_embedding: 384-dim text embedding (None for image-only)
        vision_embedding: 768-dim vision embedding (None for text-only)
        text_query: Original text query string
        image_path: Path to query image file
    """
    query_type: QueryType
    text_embedding: Optional[np.ndarray] = None
    vision_embedding: Optional[np.ndarray] = None
    text_query: Optional[str] = None
    image_path: Optional[Path] = None

    def __post_init__(self):
        """Validate embedding presence based on query type."""
        if self.query_type == QueryType.TEXT_ONLY:
            if self.text_embedding is None:
                raise ValueError("Text-only query requires text embedding")

        elif self.query_type == QueryType.IMAGE_ONLY:
            if self.vision_embedding is None:
                raise ValueError("Image-only query requires vision embedding")

        elif self.query_type == QueryType.HYBRID:
            if self.text_embedding is None or self.vision_embedding is None:
                raise ValueError("Hybrid query requires both embeddings")


class MultiModalQueryProcessor:
    """
    Process multi-modal queries (text, image, or both).

    Handles:
    - Text query embedding generation
    - Image query embedding generation
    - Hybrid query processing
    - Query type detection
    """

    def __init__(
        self,
        text_embedder: Optional[TextEmbedder] = None,
        vision_embedder: Optional[ColPaliEmbedder] = None
    ):
        """
        Initialise multi-modal query processor.

        Args:
            text_embedder: Text embedding model
            vision_embedder: Vision embedding model
        """
        self.text_embedder = text_embedder or TextEmbedder()
        self.vision_embedder = vision_embedder

        logger.info(
            f"Initialised MultiModalQueryProcessor "
            f"(vision_enabled={vision_embedder is not None})"
        )

    def process_query(
        self,
        text: Optional[str] = None,
        image: Optional[Union[Path, Image.Image]] = None
    ) -> QueryEmbeddings:
        """
        Process query and generate embeddings.

        Args:
            text: Text query string
            image: Image query (file path or PIL Image)

        Returns:
            QueryEmbeddings container with generated embeddings

        Raises:
            ValueError: If both text and image are None
            RuntimeError: If image query requested but vision embedder not available
        """
        if text is None and image is None:
            raise ValueError("At least one of text or image must be provided")

        # Determine query type
        if text and image:
            query_type = QueryType.HYBRID
        elif text:
            query_type = QueryType.TEXT_ONLY
        else:
            query_type = QueryType.IMAGE_ONLY

        logger.debug(f"Processing {query_type} query")

        # Generate text embedding if needed
        text_embedding = None
        if text:
            text_embedding = self.text_embedder.embed(text)
            logger.debug(f"Generated text embedding: {text_embedding.shape}")

        # Generate vision embedding if needed
        vision_embedding = None
        image_path = None

        if image:
            if self.vision_embedder is None:
                raise RuntimeError(
                    "Image query requested but vision embedder not initialised. "
                    "Ensure ColPali is configured and GPU is available."
                )

            # Convert to PIL Image if path provided
            if isinstance(image, (str, Path)):
                image_path = Path(image)
                image = Image.open(image_path)

            # Generate vision embedding for single image
            vision_embedding = self.vision_embedder.embed_page(image)
            logger.debug(f"Generated vision embedding: {vision_embedding.shape}")

        return QueryEmbeddings(
            query_type=query_type,
            text_embedding=text_embedding,
            vision_embedding=vision_embedding,
            text_query=text,
            image_path=image_path
        )

    def process_text(self, text: str) -> QueryEmbeddings:
        """
        Process text-only query.

        Args:
            text: Query text

        Returns:
            QueryEmbeddings with text embedding
        """
        return self.process_query(text=text, image=None)

    def process_image(
        self,
        image: Union[Path, Image.Image]
    ) -> QueryEmbeddings:
        """
        Process image-only query.

        Args:
            image: Query image (path or PIL Image)

        Returns:
            QueryEmbeddings with vision embedding
        """
        return self.process_query(text=None, image=image)

    def process_hybrid(
        self,
        text: str,
        image: Union[Path, Image.Image]
    ) -> QueryEmbeddings:
        """
        Process hybrid text+image query.

        Args:
            text: Query text
            image: Query image (path or PIL Image)

        Returns:
            QueryEmbeddings with both embeddings
        """
        return self.process_query(text=text, image=image)
```

**Deliverables:**
- `src/retrieval/query_processor.py` (~200 lines)
- Type-safe query processing
- Support for text, image, and hybrid queries

**Time:** 3-4 hours

---

#### Session 1.2: Query Expansion for Vision (5-6h)

**Task:** Implement visual query expansion and augmentation

**Implementation:**

```python
# src/retrieval/query_expansion.py

from typing import List, Dict, Optional
import numpy as np
from PIL import Image
from loguru import logger

from ragged.retrieval.query_processor import QueryEmbeddings, QueryType


class VisualQueryExpander:
    """
    Expand visual queries with synthetic variations.

    Techniques:
    - Text query expansion: Synonyms, related terms
    - Image query augmentation: Rotations, crops, colour adjustments
    - Cross-modal expansion: Generate text descriptions from images
    """

    def __init__(
        self,
        enable_image_augmentation: bool = True,
        enable_text_expansion: bool = True
    ):
        """
        Initialise visual query expander.

        Args:
            enable_image_augmentation: Whether to augment image queries
            enable_text_expansion: Whether to expand text queries
        """
        self.enable_image_augmentation = enable_image_augmentation
        self.enable_text_expansion = enable_text_expansion

        logger.info(
            f"Initialised VisualQueryExpander "
            f"(image_aug={enable_image_augmentation}, "
            f"text_exp={enable_text_expansion})"
        )

    def expand_text_query(self, text: str) -> List[str]:
        """
        Expand text query with visual-relevant terms.

        For queries that suggest visual content, add:
        - "diagram", "chart", "figure", "illustration"
        - "table", "graph", "schematic", "flowchart"

        Args:
            text: Original query text

        Returns:
            List of expanded query variants
        """
        if not self.enable_text_expansion:
            return [text]

        # Keywords suggesting visual content
        visual_keywords = [
            "architecture", "diagram", "flow", "chart",
            "schema", "structure", "design", "layout"
        ]

        # Check if query contains visual keywords
        text_lower = text.lower()
        has_visual_intent = any(kw in text_lower for kw in visual_keywords)

        if not has_visual_intent:
            return [text]

        # Add visual content qualifiers
        expanded = [
            text,
            f"{text} diagram",
            f"{text} illustration",
            f"{text} visual"
        ]

        logger.debug(f"Expanded query to {len(expanded)} variants")
        return expanded

    def augment_image_query(
        self,
        image: Image.Image,
        num_augmentations: int = 3
    ) -> List[Image.Image]:
        """
        Create augmented variants of query image.

        Augmentations:
        - Slight rotations (-5° to +5°)
        - Random crops (90-100% of original)
        - Brightness adjustments (0.9x to 1.1x)

        Args:
            image: Original query image
            num_augmentations: Number of augmented variants to create

        Returns:
            List including original + augmented images
        """
        if not self.enable_image_augmentation:
            return [image]

        augmented = [image]  # Include original

        for i in range(num_augmentations):
            # Simple augmentation: slight rotation
            angle = np.random.uniform(-5, 5)
            rotated = image.rotate(angle, expand=True)
            augmented.append(rotated)

        logger.debug(f"Created {len(augmented)} image variants")
        return augmented

    def expand_query_embeddings(
        self,
        query: QueryEmbeddings,
        processor: 'MultiModalQueryProcessor'
    ) -> List[QueryEmbeddings]:
        """
        Generate expanded query embeddings.

        Args:
            query: Original query
            processor: Query processor for generating embeddings

        Returns:
            List of QueryEmbeddings (original + expansions)
        """
        expansions = [query]

        # Expand text queries
        if query.text_query and self.enable_text_expansion:
            expanded_texts = self.expand_text_query(query.text_query)

            for text in expanded_texts[1:]:  # Skip original
                expanded_query = processor.process_text(text)
                expansions.append(expanded_query)

        # Augment image queries (future enhancement)
        # Currently: Image augmentation requires re-embedding each variant
        # This is computationally expensive for real-time queries
        # Consider: Pre-compute augmented embeddings or use on-demand

        logger.info(f"Expanded query to {len(expansions)} variants")
        return expansions
```

**Deliverables:**
- `src/retrieval/query_expansion.py` (~150 lines)
- Text query expansion with visual keywords
- Image augmentation framework (basic implementation)

**Time:** 5-6 hours

---

### Phase 2: Vision-Aware Retriever (10-14 hours)

#### Session 2.1: VisionRetriever Class (6-8h)

**Task:** Implement multi-modal retrieval engine

**Implementation:**

```python
# src/retrieval/vision_retriever.py

from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import numpy as np
from PIL import Image
from loguru import logger

from ragged.storage.dual_store import DualEmbeddingStore
from ragged.retrieval.query_processor import (
    MultiModalQueryProcessor,
    QueryEmbeddings,
    QueryType
)
from ragged.retrieval.query_expansion import VisualQueryExpander


@dataclass
class RetrievalResult:
    """
    Single retrieval result.

    Attributes:
        document_id: Parent document UUID
        embedding_id: Unique embedding identifier
        score: Relevance score (higher = more relevant)
        embedding_type: "text" or "vision"
        metadata: Full metadata dictionary
        rank: Position in results (1-indexed)
    """
    document_id: str
    embedding_id: str
    score: float
    embedding_type: str
    metadata: Dict
    rank: int


@dataclass
class RetrievalResponse:
    """
    Complete retrieval response.

    Attributes:
        results: List of retrieval results (ranked)
        query_type: Type of query executed
        total_results: Total number of results
        execution_time_ms: Query execution time in milliseconds
    """
    results: List[RetrievalResult]
    query_type: QueryType
    total_results: int
    execution_time_ms: float


class VisionRetriever:
    """
    Multi-modal retrieval engine for text and vision queries.

    Supports:
    - Text-only queries (traditional semantic search)
    - Image-only queries (visual similarity search)
    - Hybrid text+image queries (multi-modal fusion)
    - Visual content filtering (diagrams, tables)
    """

    def __init__(
        self,
        store: Optional[DualEmbeddingStore] = None,
        query_processor: Optional[MultiModalQueryProcessor] = None,
        query_expander: Optional[VisualQueryExpander] = None,
        default_text_weight: float = 0.5,
        default_vision_weight: float = 0.5
    ):
        """
        Initialise vision-aware retriever.

        Args:
            store: Dual embedding storage
            query_processor: Multi-modal query processor
            query_expander: Query expansion utilities
            default_text_weight: Default weight for text scores (0-1)
            default_vision_weight: Default weight for vision scores (0-1)
        """
        self.store = store or DualEmbeddingStore()
        self.query_processor = query_processor or MultiModalQueryProcessor()
        self.query_expander = query_expander or VisualQueryExpander()

        self.default_text_weight = default_text_weight
        self.default_vision_weight = default_vision_weight

        logger.info(
            f"Initialised VisionRetriever "
            f"(text_weight={default_text_weight}, "
            f"vision_weight={default_vision_weight})"
        )

    def query(
        self,
        text: Optional[str] = None,
        image: Optional[Union[Path, Image.Image]] = None,
        n_results: int = 10,
        text_weight: Optional[float] = None,
        vision_weight: Optional[float] = None,
        boost_diagrams: bool = False,
        boost_tables: bool = False,
        filter_metadata: Optional[Dict] = None
    ) -> RetrievalResponse:
        """
        Execute multi-modal query.

        Args:
            text: Text query string
            image: Image query (path or PIL Image)
            n_results: Number of results to return
            text_weight: Weight for text scores (None = use default)
            vision_weight: Weight for vision scores (None = use default)
            boost_diagrams: Boost results containing diagrams
            boost_tables: Boost results containing tables
            filter_metadata: Additional metadata filters

        Returns:
            RetrievalResponse with ranked results

        Raises:
            ValueError: If both text and image are None
        """
        import time
        start_time = time.time()

        # Process query
        query_embeddings = self.query_processor.process_query(
            text=text, image=image
        )

        # Use default weights if not specified
        if text_weight is None:
            text_weight = self.default_text_weight
        if vision_weight is None:
            vision_weight = self.default_vision_weight

        logger.info(
            f"Executing {query_embeddings.query_type} query "
            f"(n={n_results}, text_w={text_weight}, vision_w={vision_weight})"
        )

        # Execute appropriate retrieval strategy
        if query_embeddings.query_type == QueryType.TEXT_ONLY:
            raw_results = self._query_text_only(
                query_embeddings, n_results, filter_metadata
            )

        elif query_embeddings.query_type == QueryType.IMAGE_ONLY:
            raw_results = self._query_image_only(
                query_embeddings, n_results, filter_metadata
            )

        else:  # HYBRID
            raw_results = self._query_hybrid(
                query_embeddings, n_results,
                text_weight, vision_weight,
                filter_metadata
            )

        # Apply visual content boosting if requested
        if boost_diagrams or boost_tables:
            raw_results = self._apply_visual_boost(
                raw_results, boost_diagrams, boost_tables
            )

        # Convert to RetrievalResult objects
        results = []
        for i, (embedding_id, score, metadata) in enumerate(raw_results):
            results.append(RetrievalResult(
                document_id=metadata["document_id"],
                embedding_id=embedding_id,
                score=score,
                embedding_type=metadata["embedding_type"],
                metadata=metadata,
                rank=i + 1
            ))

        execution_time = (time.time() - start_time) * 1000  # ms

        logger.info(
            f"Retrieved {len(results)} results in {execution_time:.2f}ms"
        )

        return RetrievalResponse(
            results=results,
            query_type=query_embeddings.query_type,
            total_results=len(results),
            execution_time_ms=execution_time
        )

    def _query_text_only(
        self,
        query: QueryEmbeddings,
        n_results: int,
        filter_metadata: Optional[Dict]
    ) -> List[Tuple[str, float, Dict]]:
        """Execute text-only query."""
        results = self.store.query_text(
            query_embedding=query.text_embedding,
            n_results=n_results,
            where_filter=filter_metadata
        )

        return self._format_raw_results(results)

    def _query_image_only(
        self,
        query: QueryEmbeddings,
        n_results: int,
        filter_metadata: Optional[Dict]
    ) -> List[Tuple[str, float, Dict]]:
        """Execute image-only query."""
        results = self.store.query_vision(
            query_embedding=query.vision_embedding,
            n_results=n_results,
            where_filter=filter_metadata
        )

        return self._format_raw_results(results)

    def _query_hybrid(
        self,
        query: QueryEmbeddings,
        n_results: int,
        text_weight: float,
        vision_weight: float,
        filter_metadata: Optional[Dict]
    ) -> List[Tuple[str, float, Dict]]:
        """Execute hybrid text+vision query."""
        results = self.store.query_hybrid(
            text_embedding=query.text_embedding,
            vision_embedding=query.vision_embedding,
            n_results=n_results,
            text_weight=text_weight,
            vision_weight=vision_weight,
            where_filter=filter_metadata
        )

        return self._format_raw_results(results)

    def _format_raw_results(
        self,
        raw_results: Dict
    ) -> List[Tuple[str, float, Dict]]:
        """Convert ChromaDB results to (id, score, metadata) tuples."""
        formatted = []

        ids = raw_results["ids"][0]
        distances = raw_results.get("distances", [[]])[0]
        scores = raw_results.get("scores", [[]])[0]
        metadatas = raw_results["metadatas"][0]

        # Convert distances to scores if needed (lower distance = higher score)
        if distances and not scores:
            max_distance = max(distances) if distances else 1.0
            scores = [1.0 - (d / max_distance) for d in distances]

        for i, embedding_id in enumerate(ids):
            score = scores[i] if i < len(scores) else 0.0
            metadata = metadatas[i] if i < len(metadatas) else {}

            formatted.append((embedding_id, score, metadata))

        return formatted

    def _apply_visual_boost(
        self,
        results: List[Tuple[str, float, Dict]],
        boost_diagrams: bool,
        boost_tables: bool
    ) -> List[Tuple[str, float, Dict]]:
        """
        Boost scores for results with visual content.

        Args:
            results: Raw results (id, score, metadata)
            boost_diagrams: Boost results with diagrams
            boost_tables: Boost results with tables

        Returns:
            Re-ranked results with boosted scores
        """
        boosted = []
        diagram_boost = 1.2  # 20% score increase
        table_boost = 1.15   # 15% score increase

        for embedding_id, score, metadata in results:
            boosted_score = score

            if boost_diagrams and metadata.get("has_diagrams", False):
                boosted_score *= diagram_boost
                logger.debug(f"Boosted {embedding_id} for diagrams")

            if boost_tables and metadata.get("has_tables", False):
                boosted_score *= table_boost
                logger.debug(f"Boosted {embedding_id} for tables")

            boosted.append((embedding_id, boosted_score, metadata))

        # Re-sort by boosted scores
        boosted.sort(key=lambda x: x[1], reverse=True)

        return boosted
```

**Deliverables:**
- `src/retrieval/vision_retriever.py` (~400 lines)
- Unified interface for all query types
- Visual content boosting
- Type-safe result formatting

**Time:** 6-8 hours

---

#### Session 2.2: Reranking with Visual Signals (4-6h)

**Task:** Implement vision-aware reranking strategies

**Implementation:**

```python
# src/retrieval/reranker.py

from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np
from loguru import logger

from ragged.retrieval.vision_retriever import RetrievalResult


@dataclass
class RerankerConfig:
    """Configuration for visual reranker."""
    diagram_weight: float = 0.3
    table_weight: float = 0.2
    layout_complexity_weight: float = 0.1
    use_cross_modal_alignment: bool = False


class VisualReranker:
    """
    Rerank retrieval results using visual signals.

    Reranking strategies:
    1. Visual content boosting (diagrams, tables)
    2. Layout complexity matching
    3. Cross-modal alignment (text-vision consistency)
    """

    def __init__(self, config: Optional[RerankerConfig] = None):
        """
        Initialise visual reranker.

        Args:
            config: Reranker configuration
        """
        self.config = config or RerankerConfig()
        logger.info(f"Initialised VisualReranker: {self.config}")

    def rerank(
        self,
        results: List[RetrievalResult],
        query_text: Optional[str] = None,
        prefer_diagrams: bool = False,
        prefer_tables: bool = False,
        max_layout_complexity: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Rerank results using visual signals.

        Args:
            results: Initial retrieval results
            query_text: Original query text (for cross-modal alignment)
            prefer_diagrams: Boost results with diagrams
            prefer_tables: Boost results with tables
            max_layout_complexity: Filter by complexity ("simple"|"moderate"|"complex")

        Returns:
            Reranked results (new scores, updated ranks)
        """
        logger.info(f"Reranking {len(results)} results")

        reranked = []

        for result in results:
            # Start with original score
            new_score = result.score

            # Apply visual content boosting
            if prefer_diagrams and result.metadata.get("has_diagrams", False):
                new_score += self.config.diagram_weight
                logger.debug(f"Boosted {result.embedding_id} for diagrams")

            if prefer_tables and result.metadata.get("has_tables", False):
                new_score += self.config.table_weight
                logger.debug(f"Boosted {result.embedding_id} for tables")

            # Apply layout complexity filtering
            if max_layout_complexity:
                complexity = result.metadata.get("layout_complexity", "simple")
                complexity_order = {"simple": 0, "moderate": 1, "complex": 2}

                if complexity_order.get(complexity, 0) > \
                   complexity_order.get(max_layout_complexity, 2):
                    new_score *= 0.5  # Penalise overly complex layouts

            # Create reranked result
            reranked_result = RetrievalResult(
                document_id=result.document_id,
                embedding_id=result.embedding_id,
                score=new_score,
                embedding_type=result.embedding_type,
                metadata=result.metadata,
                rank=result.rank  # Will update after sorting
            )

            reranked.append(reranked_result)

        # Sort by new scores
        reranked.sort(key=lambda r: r.score, reverse=True)

        # Update ranks
        for i, result in enumerate(reranked):
            result.rank = i + 1

        logger.info(f"Reranking complete: {len(reranked)} results")
        return reranked
```

**Deliverables:**
- `src/retrieval/reranker.py` (~150 lines)
- Visual content-aware reranking
- Layout complexity filtering

**Time:** 4-6 hours

---

### Phase 3: Integration & Configuration (6-8 hours)

#### Session 3.1: CLI Integration (3-4h)

**Task:** Add vision retrieval commands to CLI

**Implementation:**

```python
# src/cli.py (additions)

@click.group()
def query():
    """Query documents with multi-modal search."""
    pass


@query.command("text")
@click.argument("query_text")
@click.option("-n", "--num-results", default=10, help="Number of results")
@click.option("--boost-diagrams", is_flag=True, help="Prefer results with diagrams")
@click.option("--boost-tables", is_flag=True, help="Prefer results with tables")
def query_text(query_text: str, num_results: int, boost_diagrams: bool, boost_tables: bool):
    """Search documents by text query."""
    from ragged.retrieval.vision_retriever import VisionRetriever

    retriever = VisionRetriever()
    response = retriever.query(
        text=query_text,
        n_results=num_results,
        boost_diagrams=boost_diagrams,
        boost_tables=boost_tables
    )

    click.echo(f"Found {response.total_results} results in {response.execution_time_ms:.2f}ms\n")

    for result in response.results:
        click.echo(f"{result.rank}. {result.document_id} (score: {result.score:.4f})")
        click.echo(f"   Type: {result.embedding_type}")
        click.echo()


@query.command("image")
@click.argument("image_path", type=click.Path(exists=True))
@click.option("-n", "--num-results", default=10, help="Number of results")
def query_image(image_path: str, num_results: int):
    """Search documents by image similarity."""
    from ragged.retrieval.vision_retriever import VisionRetriever
    from pathlib import Path

    retriever = VisionRetriever()
    response = retriever.query(
        image=Path(image_path),
        n_results=num_results
    )

    click.echo(f"Found {response.total_results} results in {response.execution_time_ms:.2f}ms\n")

    for result in response.results:
        click.echo(f"{result.rank}. {result.document_id} (score: {result.score:.4f})")
        click.echo(f"   Page: {result.metadata.get('page_number', 'N/A')}")
        click.echo()


@query.command("hybrid")
@click.argument("query_text")
@click.argument("image_path", type=click.Path(exists=True))
@click.option("-n", "--num-results", default=10, help="Number of results")
@click.option("--text-weight", default=0.5, help="Weight for text score (0-1)")
@click.option("--vision-weight", default=0.5, help="Weight for vision score (0-1)")
def query_hybrid(
    query_text: str,
    image_path: str,
    num_results: int,
    text_weight: float,
    vision_weight: float
):
    """Search documents with both text and image."""
    from ragged.retrieval.vision_retriever import VisionRetriever
    from pathlib import Path

    retriever = VisionRetriever()
    response = retriever.query(
        text=query_text,
        image=Path(image_path),
        n_results=num_results,
        text_weight=text_weight,
        vision_weight=vision_weight
    )

    click.echo(
        f"Found {response.total_results} results in {response.execution_time_ms:.2f}ms\n"
    )

    for result in response.results:
        click.echo(f"{result.rank}. {result.document_id} (score: {result.score:.4f})")
        click.echo(f"   Type: {result.embedding_type}")
        click.echo()
```

**Deliverables:**
- CLI commands: `query text`, `query image`, `query hybrid`
- Result formatting and display
- Configuration via command-line flags

**Time:** 3-4 hours

---

#### Session 3.2: Configuration Updates (3-4h)

**Task:** Add vision retrieval settings to configuration

**Implementation:**

```python
# src/config/settings.py (additions)

class RetrievalConfig(BaseSettings):
    """Retrieval configuration."""

    # Text retrieval (existing)
    default_num_results: int = 10

    # Multi-modal retrieval (new)
    enable_vision_retrieval: bool = False
    default_text_weight: float = 0.5
    default_vision_weight: float = 0.5

    # Query expansion
    enable_query_expansion: bool = True
    enable_image_augmentation: bool = False  # Computationally expensive

    # Visual boosting
    diagram_boost_factor: float = 1.2
    table_boost_factor: float = 1.15

    # Reranking
    enable_visual_reranking: bool = True
    diagram_rerank_weight: float = 0.3
    table_rerank_weight: float = 0.2
```

**Deliverables:**
- Configuration schema for vision retrieval
- Default values for weights and boosting factors
- Toggle flags for experimental features

**Time:** 3-4 hours

---

### Phase 4: Testing (4-6 hours)

#### Session 4.1: Unit Tests (2-3h)

**Test Coverage:**
1. Query type detection (text, image, hybrid)
2. Query embedding generation
3. Visual content boosting
4. Reranking logic
5. Result formatting

**Example Tests:**

```python
# tests/retrieval/test_vision_retriever.py

import pytest
import numpy as np
from PIL import Image

from ragged.retrieval.vision_retriever import VisionRetriever, RetrievalResult
from ragged.retrieval.query_processor import MultiModalQueryProcessor, QueryType


class TestVisionRetriever:
    """Test vision-aware retrieval."""

    @pytest.fixture
    def mock_retriever(self):
        """Create mock retriever for testing."""
        return VisionRetriever()

    def test_text_query(self, mock_retriever):
        """Test text-only query execution."""
        response = mock_retriever.query(
            text="database schema",
            n_results=5
        )

        assert response.query_type == QueryType.TEXT_ONLY
        assert len(response.results) <= 5

    def test_visual_boosting(self, mock_retriever):
        """Test diagram/table boosting."""
        response_no_boost = mock_retriever.query(
            text="architecture",
            n_results=10,
            boost_diagrams=False
        )

        response_with_boost = mock_retriever.query(
            text="architecture",
            n_results=10,
            boost_diagrams=True
        )

        # Results with diagrams should rank higher when boosted
        # (Test logic depends on mock data setup)

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires GPU")
    def test_image_query(self, mock_retriever, sample_image):
        """Test image-only query execution."""
        response = mock_retriever.query(
            image=sample_image,
            n_results=5
        )

        assert response.query_type == QueryType.IMAGE_ONLY
        assert len(response.results) <= 5
        assert all(r.embedding_type == "vision" for r in response.results)
```

**Time:** 2-3 hours

---

#### Session 4.2: Integration Tests (2-3h)

**Test Coverage:**
1. End-to-end query processing pipeline
2. Hybrid retrieval with score fusion
3. CLI command execution
4. Performance benchmarks

**Time:** 2-3 hours

---

## Success Criteria

**Functional Requirements:**
- [ ] Text-only queries return results ranked by text similarity
- [ ] Image-only queries return results ranked by visual similarity
- [ ] Hybrid queries merge text + vision scores using RRF
- [ ] `boost_diagrams` and `boost_tables` flags increase scores for matching results
- [ ] Visual reranker adjusts scores based on metadata
- [ ] CLI commands: `query text`, `query image`, `query hybrid`
- [ ] Query expansion generates visual-relevant keyword variants

**Quality Requirements:**
- [ ] 85%+ test coverage for retrieval module
- [ ] Type hints on all public methods
- [ ] British English docstrings
- [ ] All tests pass on CPU (vision tests require GPU)

**Performance Requirements:**
- [ ] Text query: <200ms latency
- [ ] Image query: <500ms latency (including embedding generation)
- [ ] Hybrid query: <600ms latency
- [ ] Reranking overhead: <50ms for 100 results

---

## Dependencies

**Required:**
- VISION-001: ColPaliEmbedder for image query processing
- VISION-002: DualEmbeddingStore for multi-modal storage/retrieval
- click >= 8.0 (CLI framework)
- PIL/Pillow >= 9.0 (image loading)

---

## Known Limitations

1. **Image Query Latency:** Vision embedding generation adds 200-400ms overhead per query image
2. **Cross-Modal Alignment:** No learned alignment between text and vision spaces (future enhancement)
3. **Query Expansion:** Text expansion is heuristic-based, not learned
4. **Image Augmentation:** Disabled by default due to computational cost

---

## Future Enhancements (Post-v0.5)

1. **Learned Fusion Weights:** Train optimal text/vision weights from user feedback
2. **Cross-Modal Transformers:** Learn shared text-vision embedding space
3. **Visual Query-by-Example:** Sketch-based diagram search
4. **Contextual Reranking:** Use surrounding text/images for better relevance

---

**Status:** Planned
**Estimated Total Effort:** 28-38 hours
