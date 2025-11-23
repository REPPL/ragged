"""Tests for Persona Manager.

v0.4.5: Test coverage for user persona system
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from ragged.memory.persona import Persona, PersonaManager, PersonaConfig


class TestPersonaConfig:
    """Test Persona configuration validation."""

    def test_valid_persona_config(self):
        """Test creating valid persona config."""
        config = PersonaConfig(
            name="researcher",
            description="ML researcher",
            focus_areas=["RAG", "NLP"],
        )
        assert config.name == "researcher"
        assert "RAG" in config.focus_areas

    def test_persona_name_validation(self):
        """Test persona name validation."""
        # Valid names
        PersonaConfig(name="researcher")
        PersonaConfig(name="ml-engineer")
        PersonaConfig(name="student_2024")

        # Invalid names
        with pytest.raises(ValueError, match="alphanumeric"):
            PersonaConfig(name="invalid name!")

        with pytest.raises(ValueError, match="alphanumeric"):
            PersonaConfig(name="test@user")

    def test_focus_areas_cleaned(self):
        """Test focus areas are cleaned."""
        config = PersonaConfig(
            name="test",
            focus_areas=["RAG", "  NLP  ", "", "privacy"],
        )
        assert config.focus_areas == ["RAG", "NLP", "privacy"]


class TestPersona:
    """Test Persona dataclass."""

    def test_persona_creation(self):
        """Test creating persona."""
        persona = Persona(
            name="researcher",
            description="ML researcher",
            focus_areas=["RAG", "NLP"],
        )
        assert persona.name == "researcher"
        assert persona.usage_count == 0

    def test_persona_to_dict(self):
        """Test persona serialization."""
        persona = Persona(
            name="researcher",
            description="ML researcher",
            focus_areas=["RAG"],
            preferences={"theme": "dark"},
        )
        data = persona.to_dict()

        assert data["name"] == "researcher"
        assert data["description"] == "ML researcher"
        assert data["focus_areas"] == ["RAG"]
        assert data["preferences"]["theme"] == "dark"
        assert "created_at" in data
        assert "usage_count" in data

    def test_persona_from_dict(self):
        """Test persona deserialization."""
        data = {
            "name": "researcher",
            "description": "ML researcher",
            "focus_areas": ["RAG", "NLP"],
            "preferences": {"theme": "dark"},
            "active_projects": ["thesis"],
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "usage_count": 5,
        }
        persona = Persona.from_dict(data)

        assert persona.name == "researcher"
        assert persona.usage_count == 5
        assert persona.active_projects == ["thesis"]

    def test_persona_mark_used(self):
        """Test marking persona as used."""
        persona = Persona(name="test")
        initial_count = persona.usage_count
        initial_time = persona.last_used

        persona.mark_used()

        assert persona.usage_count == initial_count + 1
        assert persona.last_used > initial_time


class TestPersonaManager:
    """Test PersonaManager."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def manager(self, temp_storage):
        """Create PersonaManager with temp storage."""
        return PersonaManager(storage_dir=temp_storage)

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert len(manager.personas) == 0
        assert manager.active_persona is None
        assert manager.storage_dir.exists()

    def test_create_persona(self, manager):
        """Test creating persona."""
        persona = manager.create(
            name="researcher",
            description="ML researcher",
            focus=["RAG", "NLP"],
        )

        assert persona.name == "researcher"
        assert persona.description == "ML researcher"
        assert "RAG" in persona.focus_areas
        assert persona.name in manager.personas

    def test_create_duplicate_persona(self, manager):
        """Test creating duplicate persona fails."""
        manager.create("researcher")

        with pytest.raises(ValueError, match="already exists"):
            manager.create("researcher")

    def test_get_persona(self, manager):
        """Test getting persona by name."""
        manager.create("researcher")
        persona = manager.get("researcher")

        assert persona.name == "researcher"

    def test_get_nonexistent_persona(self, manager):
        """Test getting nonexistent persona fails."""
        with pytest.raises(KeyError, match="not found"):
            manager.get("nonexistent")

    def test_switch_persona(self, manager):
        """Test switching persona."""
        manager.create("researcher")
        manager.create("student")

        persona = manager.switch("researcher")
        assert manager.active_persona == "researcher"
        assert persona.usage_count == 1

        persona = manager.switch("student")
        assert manager.active_persona == "student"
        assert persona.usage_count == 1

    def test_list_personas(self, manager):
        """Test listing personas."""
        assert manager.list() == []

        manager.create("researcher")
        manager.create("student")
        manager.create("developer")

        personas = manager.list()
        assert personas == ["developer", "researcher", "student"]  # Sorted

    def test_delete_persona(self, manager):
        """Test deleting persona."""
        manager.create("researcher")
        assert "researcher" in manager.personas

        manager.delete("researcher", confirm=True)
        assert "researcher" not in manager.personas

    def test_delete_without_confirmation(self, manager):
        """Test delete requires confirmation."""
        manager.create("researcher")

        with pytest.raises(ValueError, match="confirm=True"):
            manager.delete("researcher")

    def test_delete_active_persona(self, manager):
        """Test deleting active persona clears active."""
        manager.create("researcher")
        manager.switch("researcher")

        assert manager.active_persona == "researcher"

        manager.delete("researcher", confirm=True)
        assert manager.active_persona is None

    def test_get_active_persona(self, manager):
        """Test getting active persona."""
        assert manager.get_active() is None

        manager.create("researcher")
        manager.switch("researcher")

        active = manager.get_active()
        assert active is not None
        assert active.name == "researcher"

    def test_persona_persistence(self, temp_storage):
        """Test persona data persists across manager instances."""
        # Create persona with first manager
        manager1 = PersonaManager(storage_dir=temp_storage)
        manager1.create(
            "researcher",
            description="ML researcher",
            focus=["RAG", "NLP"],
        )
        manager1.switch("researcher")

        # Load with second manager
        manager2 = PersonaManager(storage_dir=temp_storage)

        assert "researcher" in manager2.personas
        assert manager2.active_persona == "researcher"

        persona = manager2.get("researcher")
        assert persona.description == "ML researcher"
        assert "RAG" in persona.focus_areas
        assert persona.usage_count == 1

    def test_persona_usage_tracking(self, manager):
        """Test persona usage tracking."""
        manager.create("researcher")

        persona = manager.get("researcher")
        assert persona.usage_count == 0

        manager.switch("researcher")
        assert persona.usage_count == 1

        manager.switch("researcher")
        assert persona.usage_count == 2

    def test_persona_with_preferences(self, manager):
        """Test persona with custom preferences."""
        manager.create(
            "researcher",
            preferences={
                "theme": "dark",
                "model": "llama3",
                "top_k": 5,
            },
        )

        persona = manager.get("researcher")
        assert persona.preferences["theme"] == "dark"
        assert persona.preferences["model"] == "llama3"
        assert persona.preferences["top_k"] == 5

    def test_persona_with_active_projects(self, manager):
        """Test persona with active projects."""
        manager.create(
            "researcher",
            active_projects=["thesis", "paper-review", "grant-proposal"],
        )

        persona = manager.get("researcher")
        assert len(persona.active_projects) == 3
        assert "thesis" in persona.active_projects
