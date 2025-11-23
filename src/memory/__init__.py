"""Personal memory system for ragged.

v0.4.5: Memory Foundation - Personas & Tracking

This module implements a privacy-first personal memory system that enables ragged to:
- Remember user context and preferences
- Track interaction history
- Build knowledge graphs of user interests
- Support multiple user personas for context switching

All data is stored locally with encryption and full user control.

Components:
- Persona: User persona management for context switching
- Interactions: Interaction history tracking with SQLite
- Graph: Knowledge graph for relationships (Kuzu)
- Manager: Orchestrates memory components

Privacy Guarantees:
- 100% local storage (no cloud dependencies)
- Encryption at rest for all sensitive data
- Full user control (view, edit, delete, export)
- Persona isolation (no cross-contamination)
- GDPR compliant (Articles 15, 17, 20)

Example:
    >>> from ragged.memory import PersonaManager, InteractionTracker
    >>> personas = PersonaManager()
    >>> personas.create("researcher", description="ML researcher", focus=["RAG", "NLP"])
    >>> personas.switch("researcher")
    >>> tracker = InteractionTracker(persona="researcher")
    >>> tracker.record_interaction(query="What is RAG?", response="...")
"""

from ragged.memory.persona import Persona, PersonaManager
from ragged.memory.interactions import Interaction, InteractionTracker

__all__ = [
    "Persona",
    "PersonaManager",
    "Interaction",
    "InteractionTracker",
]

__version__ = "0.4.5"
