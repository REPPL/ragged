"""User persona management for context switching.

v0.4.5: Persona Manager

Provides user persona system enabling:
- Multiple user contexts (researcher, student, developer, etc.)
- Focus areas and preferences per persona
- Usage statistics tracking
- Active project management
- Seamless context switching

Privacy: All persona data stored locally in ~/.ragged/memory/profiles/
"""
from __future__ import annotations


import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ragged.config.settings import get_settings
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


class PersonaConfig(BaseModel):
    """Persona configuration model."""

    model_config = ConfigDict(validate_assignment=True)

    name: str = Field(..., min_length=1, max_length=50, description="Persona name")
    description: str = Field(default="", max_length=500, description="Persona description")
    focus_areas: list[str] = Field(
        default_factory=list, max_length=20, description="Focus areas/topics"
    )
    preferences: dict[str, Any] = Field(
        default_factory=dict, description="User preferences"
    )
    active_projects: list[str] = Field(
        default_factory=list, max_length=10, description="Active projects"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: datetime = Field(default_factory=datetime.now)
    usage_count: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate persona name."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Persona name must be alphanumeric (- and _ allowed)")
        return v

    @field_validator("focus_areas")
    @classmethod
    def validate_focus_areas(cls, v: list[str]) -> list[str]:
        """Validate focus areas."""
        return [area.strip() for area in v if area.strip()]

    model_config = {"validate_assignment": True}


@dataclass
class Persona:
    """User persona for context switching.

    Attributes:
        name: Unique persona identifier
        description: Human-readable description
        focus_areas: List of focus topics/areas
        preferences: Dict of user preferences
        active_projects: List of active project names
        created_at: Creation timestamp
        last_used: Last usage timestamp
        usage_count: Number of times persona was used
    """

    name: str
    description: str = ""
    focus_areas: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    active_projects: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    usage_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert persona to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "focus_areas": self.focus_areas,
            "preferences": self.preferences,
            "active_projects": self.active_projects,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Persona":
        """Create persona from dictionary."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            focus_areas=data.get("focus_areas", []),
            preferences=data.get("preferences", {}),
            active_projects=data.get("active_projects", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_used=datetime.fromisoformat(data["last_used"]),
            usage_count=data.get("usage_count", 0),
        )

    def mark_used(self) -> None:
        """Mark persona as recently used."""
        self.last_used = datetime.now()
        self.usage_count += 1


class PersonaManager:
    """Manages user personas for context switching.

    Provides CRUD operations for personas with local storage.

    Storage: ~/.ragged/memory/profiles/personas.yaml

    Example:
        >>> manager = PersonaManager()
        >>> manager.create("researcher", description="ML researcher", focus=["RAG", "NLP"])
        >>> manager.switch("researcher")
        >>> manager.list()
        ['researcher']
    """

    def __init__(self, storage_dir: Path | None = None):
        """Initialise persona manager.

        Args:
            storage_dir: Custom storage directory (default: ~/.ragged/memory/profiles)
        """
        settings = get_settings()
        data_dir = Path(settings.data_dir)

        self.storage_dir = storage_dir or (data_dir / "memory" / "profiles")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.personas_file = self.storage_dir / "personas.yaml"
        self.active_persona_file = self.storage_dir / "active_persona.txt"

        self.personas: dict[str, Persona] = {}
        self.active_persona: str | None = None

        self._load_personas()
        self._load_active_persona()

        logger.info(
            f"PersonaManager initialised with {len(self.personas)} personas "
            f"(active: {self.active_persona})"
        )

    def create(
        self,
        name: str,
        description: str = "",
        focus: list[str] | None = None,
        preferences: dict[str, Any] | None = None,
        active_projects: list[str] | None = None,
    ) -> Persona:
        """Create a new persona.

        Args:
            name: Persona name (alphanumeric, - and _ allowed)
            description: Human-readable description
            focus: List of focus areas/topics
            preferences: Dict of user preferences
            active_projects: List of active project names

        Returns:
            Created Persona object

        Raises:
            ValueError: If persona already exists or name is invalid
        """
        # Validate through Pydantic model
        config = PersonaConfig(
            name=name,
            description=description,
            focus_areas=focus or [],
            preferences=preferences or {},
            active_projects=active_projects or [],
        )

        if config.name in self.personas:
            raise ValueError(f"Persona '{config.name}' already exists")

        persona = Persona(
            name=config.name,
            description=config.description,
            focus_areas=config.focus_areas,
            preferences=config.preferences,
            active_projects=config.active_projects,
        )

        self.personas[persona.name] = persona
        self._save_personas()

        logger.info(f"Created persona: {persona.name}")
        return persona

    def get(self, name: str) -> Persona:
        """Get persona by name.

        Args:
            name: Persona name

        Returns:
            Persona object

        Raises:
            KeyError: If persona not found
        """
        if name not in self.personas:
            raise KeyError(f"Persona '{name}' not found")
        return self.personas[name]

    def switch(self, name: str) -> Persona:
        """Switch to a different persona.

        Args:
            name: Persona name to switch to

        Returns:
            Switched-to Persona object

        Raises:
            KeyError: If persona not found
        """
        persona = self.get(name)
        persona.mark_used()

        self.active_persona = name
        self._save_active_persona()
        self._save_personas()  # Save updated usage stats

        logger.info(f"Switched to persona: {name}")
        return persona

    def list(self) -> list[str]:
        """List all persona names.

        Returns:
            List of persona names sorted alphabetically
        """
        return sorted(self.personas.keys())

    def delete(self, name: str, confirm: bool = False) -> None:
        """Delete a persona.

        Args:
            name: Persona name to delete
            confirm: Confirmation flag (required for safety)

        Raises:
            KeyError: If persona not found
            ValueError: If confirmation not provided
        """
        if not confirm:
            raise ValueError("Must set confirm=True to delete persona")

        if name not in self.personas:
            raise KeyError(f"Persona '{name}' not found")

        del self.personas[name]

        # Clear active persona if it was deleted
        if self.active_persona == name:
            self.active_persona = None
            self._save_active_persona()

        self._save_personas()
        logger.info(f"Deleted persona: {name}")

    def get_active(self) -> Persona | None:
        """Get currently active persona.

        Returns:
            Active Persona object or None if no active persona
        """
        if self.active_persona:
            return self.personas.get(self.active_persona)
        return None

    def export_persona(self, name: str, output_path: Path | None = None) -> Path:
        """Export persona data to JSON file (GDPR Article 20: Data Portability).

        Args:
            name: Persona name to export
            output_path: Optional custom output path

        Returns:
            Path to exported JSON file

        Raises:
            ValueError: If persona not found
        """
        if name not in self.personas:
            raise ValueError(f"Persona '{name}' not found")

        persona = self.personas[name]
        export_data = {
            "export_type": "persona",
            "export_timestamp": datetime.now().isoformat(),
            "persona": persona.to_dict(),
        }

        if output_path is None:
            export_dir = self.storage_dir / "exports"
            export_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = export_dir / f"persona_{name}_{timestamp}.json"

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        logger.info(f"Exported persona '{name}' to {output_path}")
        return output_path

    def _load_personas(self) -> None:
        """Load personas from YAML file."""
        if not self.personas_file.exists():
            return

        try:
            with open(self.personas_file) as f:
                data = yaml.safe_load(f) or {}

            self.personas = {
                name: Persona.from_dict(persona_data)
                for name, persona_data in data.items()
            }
            logger.debug(f"Loaded {len(self.personas)} personas")

        except Exception as e:
            logger.error(f"Failed to load personas: {e}", exc_info=True)
            self.personas = {}

    def _save_personas(self) -> None:
        """Save personas to YAML file."""
        try:
            data = {name: persona.to_dict() for name, persona in self.personas.items()}

            with open(self.personas_file, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

            logger.debug(f"Saved {len(self.personas)} personas")

        except Exception as e:
            logger.error(f"Failed to save personas: {e}", exc_info=True)

    def _load_active_persona(self) -> None:
        """Load active persona name from file."""
        if not self.active_persona_file.exists():
            return

        try:
            with open(self.active_persona_file) as f:
                self.active_persona = f.read().strip() or None
            logger.debug(f"Loaded active persona: {self.active_persona}")

        except Exception as e:
            logger.error(f"Failed to load active persona: {e}", exc_info=True)
            self.active_persona = None

    def _save_active_persona(self) -> None:
        """Save active persona name to file."""
        try:
            with open(self.active_persona_file, "w") as f:
                f.write(self.active_persona or "")
            logger.debug(f"Saved active persona: {self.active_persona}")

        except Exception as e:
            logger.error(f"Failed to save active persona: {e}", exc_info=True)
