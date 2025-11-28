"""Pydantic schemas for Knowledge Graph API.

Provides request/response models for graph endpoints:
- Graph data (nodes and edges)
- User interests and document access
- Topic-document relationships
- Graph export

v0.9.0: Initial implementation
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Base model for a graph node."""

    id: str = Field(..., description="Node identifier")
    type: Literal["user", "topic", "document"] = Field(..., description="Node type")
    label: str = Field(..., description="Display label")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Node properties"
    )


class GraphEdge(BaseModel):
    """Model for a graph edge (relationship)."""

    id: str = Field(..., description="Edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: Literal["INTERESTED_IN", "ACCESSED", "RELATED_TO"] = Field(
        ..., description="Relationship type"
    )
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Edge properties"
    )


class GraphDataResponse(BaseModel):
    """Response model for full graph data."""

    nodes: list[GraphNode] = Field(default_factory=list, description="Graph nodes")
    edges: list[GraphEdge] = Field(default_factory=list, description="Graph edges")
    node_count: int = Field(..., ge=0, description="Total nodes")
    edge_count: int = Field(..., ge=0, description="Total edges")


class TopicInterest(BaseModel):
    """Model for a topic interest."""

    topic: str = Field(..., description="Topic name")
    interest_level: float = Field(
        ..., ge=0.0, le=1.0, description="Interest level (0-1)"
    )
    frequency: int = Field(..., ge=0, description="Query frequency")
    last_accessed: datetime | None = Field(None, description="Last access time")


class InterestsResponse(BaseModel):
    """Response model for user interests."""

    persona: str = Field(..., description="Persona name")
    interests: list[TopicInterest] = Field(
        default_factory=list, description="Topic interests"
    )
    count: int = Field(..., ge=0, description="Number of interests")


class AccessedDocument(BaseModel):
    """Model for an accessed document."""

    doc_id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Document title")
    access_count: int = Field(..., ge=0, description="Number of accesses")
    last_accessed: datetime | None = Field(None, description="Last access time")


class AccessedDocumentsResponse(BaseModel):
    """Response model for accessed documents."""

    persona: str = Field(..., description="Persona name")
    documents: list[AccessedDocument] = Field(
        default_factory=list, description="Accessed documents"
    )
    count: int = Field(..., ge=0, description="Number of documents")


class RelatedDocument(BaseModel):
    """Model for a topic-related document."""

    doc_id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Document title")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance score")


class RelatedDocumentsResponse(BaseModel):
    """Response model for related documents."""

    topic: str = Field(..., description="Topic name")
    documents: list[RelatedDocument] = Field(
        default_factory=list, description="Related documents"
    )
    count: int = Field(..., ge=0, description="Number of documents")


class AddInterestRequest(BaseModel):
    """Request model for adding a topic interest."""

    topic: str = Field(..., min_length=1, description="Topic name")
    interest_level: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Interest level (0-1)"
    )
    persona: str = Field(..., min_length=1, description="Persona name")


class RecordAccessRequest(BaseModel):
    """Request model for recording document access."""

    doc_id: str = Field(..., min_length=1, description="Document identifier")
    title: str = Field(default="", description="Document title")
    persona: str = Field(..., min_length=1, description="Persona name")


class LinkTopicRequest(BaseModel):
    """Request model for linking topic to document."""

    topic: str = Field(..., min_length=1, description="Topic name")
    doc_id: str = Field(..., min_length=1, description="Document identifier")
    relevance: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Relevance score"
    )


class GraphExportResponse(BaseModel):
    """Response model for graph export."""

    persona: str = Field(..., description="Persona name")
    export_timestamp: datetime = Field(..., description="Export timestamp")
    interests: list[dict[str, Any]] = Field(
        default_factory=list, description="Topic interests"
    )
    documents: list[dict[str, Any]] = Field(
        default_factory=list, description="Accessed documents"
    )
    topic_document_links: list[dict[str, Any]] = Field(
        default_factory=list, description="Topic-document relationships"
    )


class NeighborsResponse(BaseModel):
    """Response model for node neighbors."""

    node_id: str = Field(..., description="Source node ID")
    node_type: str = Field(..., description="Source node type")
    neighbors: list[GraphNode] = Field(
        default_factory=list, description="Connected nodes"
    )
    edges: list[GraphEdge] = Field(
        default_factory=list, description="Connecting edges"
    )
    count: int = Field(..., ge=0, description="Number of neighbors")


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = Field(True, description="Operation success")
    message: str = Field(..., description="Success message")
