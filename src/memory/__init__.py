"""Personal memory system for ragged.

v0.4.8: Personalised Retrieval & Ranking

This module implements a privacy-first personal memory system that enables ragged to:
- Remember user context and preferences
- Track interaction history
- Build knowledge graphs of user interests
- Support multiple user personas for context switching
- Learn from behaviour patterns (v0.4.7)
- Personalise retrieval ranking (v0.4.8)

All data is stored locally with encryption and full user control.

Components:
- Persona: User persona management for context switching
- Interactions: Interaction history tracking with SQLite
- Graph: Knowledge graph for relationships (Kuzu)
- Topics: Topic extraction from queries (v0.4.7)
- Profile: Interest profile management (v0.4.7)
- Behaviour: Behaviour learning system (v0.4.7)
- Personalisation: Personalised ranking (v0.4.8)

Privacy Guarantees:
- 100% local storage (no cloud dependencies)
- Encryption at rest for all sensitive data
- Full user control (view, edit, delete, export)
- Persona isolation (no cross-contamination)
- GDPR compliant (Articles 15, 17, 20)

Example:
    >>> from ragged.memory import PersonaManager, InteractionTracker
    >>> from ragged.memory import PersonalisedRanker, BehaviourLearner
    >>> personas = PersonaManager()
    >>> personas.create("researcher", description="ML researcher", focus=["RAG", "NLP"])
    >>> personas.switch("researcher")
    >>> tracker = InteractionTracker(persona="researcher")
    >>> tracker.record_interaction(query="What is RAG?", response="...")
    >>> # Personalised ranking
    >>> ranker = PersonalisedRanker(profile_manager, topic_extractor)
    >>> personalised_results = ranker.rerank(results, query, persona="researcher", k=10)
"""

from ragged.memory.behaviour import BehaviourLearner
from ragged.memory.confidence import ConfidenceCalculator
from ragged.memory.graph import KnowledgeGraph
from ragged.memory.interactions import Interaction, InteractionTracker
from ragged.memory.persona import Persona, PersonaManager
from ragged.memory.personalisation import PersonalisationConfig, PersonalisedRanker
from ragged.memory.profile import InterestProfile, ProfileManager, TopicInterest
from ragged.memory.topics import Topic, TopicExtractor

__all__ = [
    "Persona",
    "PersonaManager",
    "Interaction",
    "InteractionTracker",
    "KnowledgeGraph",
    "Topic",
    "TopicExtractor",
    "TopicInterest",
    "InterestProfile",
    "ProfileManager",
    "ConfidenceCalculator",
    "BehaviourLearner",
    "PersonalisedRanker",
    "PersonalisationConfig",
]

__version__ = "0.4.8"
