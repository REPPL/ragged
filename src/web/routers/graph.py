"""Knowledge Graph API router.

Provides endpoints for knowledge graph operations:
- Get graph data (nodes and edges)
- Manage user interests
- Track document access
- Query topic-document relationships
- Export graph data

v0.9.0: Initial implementation
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ragged.memory.graph import KnowledgeGraph
from ragged.utils.logging import get_logger
from ragged.web.schemas.graph import (
    AccessedDocument,
    AccessedDocumentsResponse,
    AddInterestRequest,
    GraphDataResponse,
    GraphEdge,
    GraphExportResponse,
    GraphNode,
    InterestsResponse,
    LinkTopicRequest,
    NeighborsResponse,
    RecordAccessRequest,
    RelatedDocument,
    RelatedDocumentsResponse,
    SuccessResponse,
    TopicInterest,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/graph", tags=["graph"])


# Global graph instance (will be initialised on first use)
_knowledge_graph: KnowledgeGraph | None = None


def get_knowledge_graph() -> KnowledgeGraph:
    """Dependency to get the knowledge graph instance.

    Returns:
        KnowledgeGraph: The initialised knowledge graph

    Note:
        Creates the graph on first access (lazy initialisation)
    """
    global _knowledge_graph
    if _knowledge_graph is None:
        try:
            _knowledge_graph = KnowledgeGraph()
            logger.info("Knowledge graph initialised")
        except Exception as e:
            logger.error(f"Failed to initialise knowledge graph: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Knowledge graph unavailable: {str(e)}"
            ) from e
    return _knowledge_graph


@router.get("/data", response_model=GraphDataResponse)
async def get_graph_data(
    persona: str = Query(default="default", description="Persona to get graph data for"),
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> GraphDataResponse:
    """Get full graph data (nodes and edges) for visualisation.

    Args:
        persona: Persona to get graph data for
        graph: Injected knowledge graph dependency

    Returns:
        GraphDataResponse with nodes and edges
    """
    try:
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        edge_id = 0

        # Get user node
        nodes.append(GraphNode(
            id=f"user_{persona}",
            type="user",
            label=persona,
            properties={"name": persona}
        ))

        # Get interests (topics and relationships)
        interests = graph.get_user_interests(persona)
        for interest in interests:
            topic_id = f"topic_{interest['topic']}"
            nodes.append(GraphNode(
                id=topic_id,
                type="topic",
                label=interest["topic"],
                properties={
                    "interest_level": interest["interest_level"],
                    "frequency": interest["frequency"],
                }
            ))
            edges.append(GraphEdge(
                id=f"edge_{edge_id}",
                source=f"user_{persona}",
                target=topic_id,
                type="INTERESTED_IN",
                properties={
                    "frequency": interest["frequency"],
                    "last_accessed": interest["last_accessed"].isoformat()
                    if interest["last_accessed"]
                    else None,
                }
            ))
            edge_id += 1

        # Get accessed documents
        documents = graph.get_accessed_documents(persona, limit=100)
        for doc in documents:
            doc_id = f"doc_{doc['doc_id']}"
            nodes.append(GraphNode(
                id=doc_id,
                type="document",
                label=doc["title"] or doc["doc_id"],
                properties={
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "access_count": doc["access_count"],
                }
            ))
            edges.append(GraphEdge(
                id=f"edge_{edge_id}",
                source=f"user_{persona}",
                target=doc_id,
                type="ACCESSED",
                properties={
                    "access_count": doc["access_count"],
                    "last_accessed": doc["last_accessed"].isoformat()
                    if doc["last_accessed"]
                    else None,
                }
            ))
            edge_id += 1

        # Get topic-document relationships
        for interest in interests:
            topic = interest["topic"]
            related_docs = graph.get_related_documents(topic, limit=50)
            for doc in related_docs:
                topic_id = f"topic_{topic}"
                doc_id = f"doc_{doc['doc_id']}"
                edges.append(GraphEdge(
                    id=f"edge_{edge_id}",
                    source=topic_id,
                    target=doc_id,
                    type="RELATED_TO",
                    properties={"relevance": doc["relevance"]}
                ))
                edge_id += 1

        # Deduplicate nodes
        seen_ids = set()
        unique_nodes = []
        for node in nodes:
            if node.id not in seen_ids:
                seen_ids.add(node.id)
                unique_nodes.append(node)

        return GraphDataResponse(
            nodes=unique_nodes,
            edges=edges,
            node_count=len(unique_nodes),
            edge_count=len(edges)
        )

    except Exception as e:
        logger.exception("Error getting graph data")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting graph data: {str(e)}"
        ) from e


@router.get("/interests/{persona}", response_model=InterestsResponse)
async def get_interests(
    persona: str,
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> InterestsResponse:
    """Get topic interests for a persona.

    Args:
        persona: Persona name
        graph: Injected knowledge graph dependency

    Returns:
        InterestsResponse with topic interests
    """
    try:
        interests_data = graph.get_user_interests(persona)

        interests = [
            TopicInterest(
                topic=i["topic"],
                interest_level=i["interest_level"] or 0.0,
                frequency=i["frequency"] or 0,
                last_accessed=i["last_accessed"]
            )
            for i in interests_data
        ]

        return InterestsResponse(
            persona=persona,
            interests=interests,
            count=len(interests)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error getting interests")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting interests: {str(e)}"
        ) from e


@router.get("/documents/{persona}", response_model=AccessedDocumentsResponse)
async def get_accessed_documents(
    persona: str,
    limit: int = Query(default=50, ge=1, le=500, description="Maximum documents"),
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> AccessedDocumentsResponse:
    """Get accessed documents for a persona.

    Args:
        persona: Persona name
        limit: Maximum number of documents
        graph: Injected knowledge graph dependency

    Returns:
        AccessedDocumentsResponse with documents
    """
    try:
        docs_data = graph.get_accessed_documents(persona, limit=limit)

        documents = [
            AccessedDocument(
                doc_id=d["doc_id"],
                title=d["title"] or "",
                access_count=d["access_count"] or 0,
                last_accessed=d["last_accessed"]
            )
            for d in docs_data
        ]

        return AccessedDocumentsResponse(
            persona=persona,
            documents=documents,
            count=len(documents)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error getting accessed documents")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting accessed documents: {str(e)}"
        ) from e


@router.get("/related/{topic}", response_model=RelatedDocumentsResponse)
async def get_related_documents(
    topic: str,
    limit: int = Query(default=50, ge=1, le=500, description="Maximum documents"),
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> RelatedDocumentsResponse:
    """Get documents related to a topic.

    Args:
        topic: Topic name
        limit: Maximum number of documents
        graph: Injected knowledge graph dependency

    Returns:
        RelatedDocumentsResponse with documents
    """
    try:
        docs_data = graph.get_related_documents(topic, limit=limit)

        documents = [
            RelatedDocument(
                doc_id=d["doc_id"],
                title=d["title"] or "",
                relevance=d["relevance"] or 0.0
            )
            for d in docs_data
        ]

        return RelatedDocumentsResponse(
            topic=topic,
            documents=documents,
            count=len(documents)
        )

    except Exception as e:
        logger.exception("Error getting related documents")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting related documents: {str(e)}"
        ) from e


@router.post("/interests", response_model=SuccessResponse)
async def add_interest(
    request: AddInterestRequest,
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> SuccessResponse:
    """Add or update a topic interest for a persona.

    Args:
        request: Interest details
        graph: Injected knowledge graph dependency

    Returns:
        SuccessResponse indicating success
    """
    try:
        graph.add_topic_interest(
            topic=request.topic,
            interest_level=request.interest_level,
            persona=request.persona
        )

        return SuccessResponse(
            success=True,
            message=f"Added interest in '{request.topic}' for persona '{request.persona}'"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error adding interest")
        raise HTTPException(
            status_code=500,
            detail=f"Error adding interest: {str(e)}"
        ) from e


@router.post("/access", response_model=SuccessResponse)
async def record_access(
    request: RecordAccessRequest,
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> SuccessResponse:
    """Record document access for a persona.

    Args:
        request: Access details
        graph: Injected knowledge graph dependency

    Returns:
        SuccessResponse indicating success
    """
    try:
        graph.record_document_access(
            doc_id=request.doc_id,
            title=request.title,
            persona=request.persona
        )

        return SuccessResponse(
            success=True,
            message=f"Recorded access to document '{request.doc_id}' for persona '{request.persona}'"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error recording access")
        raise HTTPException(
            status_code=500,
            detail=f"Error recording access: {str(e)}"
        ) from e


@router.post("/link", response_model=SuccessResponse)
async def link_topic_to_document(
    request: LinkTopicRequest,
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> SuccessResponse:
    """Link a topic to a document.

    Args:
        request: Link details
        graph: Injected knowledge graph dependency

    Returns:
        SuccessResponse indicating success
    """
    try:
        graph.link_topic_to_document(
            topic=request.topic,
            doc_id=request.doc_id,
            relevance=request.relevance
        )

        return SuccessResponse(
            success=True,
            message=f"Linked topic '{request.topic}' to document '{request.doc_id}'"
        )

    except Exception as e:
        logger.exception("Error linking topic to document")
        raise HTTPException(
            status_code=500,
            detail=f"Error linking topic to document: {str(e)}"
        ) from e


@router.get("/export", response_model=GraphExportResponse)
async def export_graph(
    persona: str = Query(..., description="Persona to export"),
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> GraphExportResponse:
    """Export graph data for a persona.

    Args:
        persona: Persona to export
        graph: Injected knowledge graph dependency

    Returns:
        GraphExportResponse with exported data
    """
    try:
        export_data = graph.export_graph(persona)

        return GraphExportResponse(
            persona=export_data["persona"],
            export_timestamp=datetime.fromisoformat(export_data["export_timestamp"]),
            interests=export_data["interests"],
            documents=export_data["documents"],
            topic_document_links=export_data["topic_document_links"]
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error exporting graph")
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting graph: {str(e)}"
        ) from e


@router.get("/neighbors/{node_type}/{node_id}", response_model=NeighborsResponse)
async def get_neighbors(
    node_type: str,
    node_id: str,
    graph: KnowledgeGraph = Depends(get_knowledge_graph),
) -> NeighborsResponse:
    """Get neighbors of a node.

    Args:
        node_type: Type of node (user, topic, document)
        node_id: Node identifier
        graph: Injected knowledge graph dependency

    Returns:
        NeighborsResponse with connected nodes
    """
    try:
        neighbors: list[GraphNode] = []
        edges: list[GraphEdge] = []
        edge_id = 0

        if node_type == "user":
            # Get interests (outgoing INTERESTED_IN)
            interests = graph.get_user_interests(node_id)
            for i in interests:
                topic_id = f"topic_{i['topic']}"
                neighbors.append(GraphNode(
                    id=topic_id,
                    type="topic",
                    label=i["topic"],
                    properties={"interest_level": i["interest_level"]}
                ))
                edges.append(GraphEdge(
                    id=f"edge_{edge_id}",
                    source=f"user_{node_id}",
                    target=topic_id,
                    type="INTERESTED_IN",
                    properties={"frequency": i["frequency"]}
                ))
                edge_id += 1

            # Get documents (outgoing ACCESSED)
            docs = graph.get_accessed_documents(node_id, limit=100)
            for d in docs:
                doc_id = f"doc_{d['doc_id']}"
                neighbors.append(GraphNode(
                    id=doc_id,
                    type="document",
                    label=d["title"] or d["doc_id"],
                    properties={"access_count": d["access_count"]}
                ))
                edges.append(GraphEdge(
                    id=f"edge_{edge_id}",
                    source=f"user_{node_id}",
                    target=doc_id,
                    type="ACCESSED",
                    properties={"access_count": d["access_count"]}
                ))
                edge_id += 1

        elif node_type == "topic":
            # Get related documents
            docs = graph.get_related_documents(node_id, limit=100)
            for d in docs:
                doc_id = f"doc_{d['doc_id']}"
                neighbors.append(GraphNode(
                    id=doc_id,
                    type="document",
                    label=d["title"] or d["doc_id"],
                    properties={"relevance": d["relevance"]}
                ))
                edges.append(GraphEdge(
                    id=f"edge_{edge_id}",
                    source=f"topic_{node_id}",
                    target=doc_id,
                    type="RELATED_TO",
                    properties={"relevance": d["relevance"]}
                ))
                edge_id += 1

        elif node_type == "document":
            # Documents don't have outgoing relationships in our schema
            pass

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid node type: {node_type}. Must be user, topic, or document"
            )

        return NeighborsResponse(
            node_id=node_id,
            node_type=node_type,
            neighbors=neighbors,
            edges=edges,
            count=len(neighbors)
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error getting neighbors")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting neighbors: {str(e)}"
        ) from e
