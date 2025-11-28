"""API routers for ragged web interface.

This module provides modular API routers organised by feature domain.
"""

from ragged.web.routers.documents import router as documents_router
from ragged.web.routers.graph import router as graph_router
from ragged.web.routers.workflows import router as workflows_router

__all__ = ["documents_router", "graph_router", "workflows_router"]
