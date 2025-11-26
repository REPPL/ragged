"""
Configuration Manager.

PREREQ-004: Manages installation-time configuration generation,
validation, and secrets management.
"""

import os
import secrets
import string
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class ConfigProfile(Enum):
    """Pre-defined configuration profiles."""

    DEFAULT = "default"  # Local development, all services on localhost
    PRODUCTION = "production"  # Secure defaults, authentication enabled
    DOCKER = "docker"  # All services in containers
    MINIMAL = "minimal"  # Minimum viable configuration


@dataclass
class ServerConfig:
    """Server configuration."""

    host: str = "localhost"
    port: int = 8000
    workers: int = 1
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])


@dataclass
class DatabaseConfig:
    """Database configuration."""

    chromadb_host: str = "localhost"
    chromadb_port: int = 8001
    collection_name: str = "ragged_documents"
    persist_directory: str = "~/.ragged/chromadb"


@dataclass
class LLMConfig:
    """LLM configuration."""

    ollama_host: str = "http://localhost:11434"
    default_model: str = "llama3.2:3b"
    embedding_model: str = "nomic-embed-text"
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class StorageConfig:
    """Storage configuration."""

    documents_path: str = "~/.ragged/documents"
    cache_path: str = "~/.ragged/cache"
    logs_path: str = "~/.ragged/logs"


@dataclass
class SecurityConfig:
    """Security configuration."""

    authentication_enabled: bool = False
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    session_timeout_minutes: int = 60


@dataclass
class WebUIConfig:
    """WebUI configuration."""

    enabled: bool = True
    port: int = 5173
    theme: str = "system"


@dataclass
class RaggedConfig:
    """Complete ragged configuration."""

    server: ServerConfig = field(default_factory=ServerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    webui: WebUIConfig = field(default_factory=WebUIConfig)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "workers": self.server.workers,
                "cors_origins": self.server.cors_origins,
            },
            "database": {
                "chromadb_host": self.database.chromadb_host,
                "chromadb_port": self.database.chromadb_port,
                "collection_name": self.database.collection_name,
                "persist_directory": self.database.persist_directory,
            },
            "llm": {
                "ollama_host": self.llm.ollama_host,
                "default_model": self.llm.default_model,
                "embedding_model": self.llm.embedding_model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
            },
            "storage": {
                "documents_path": self.storage.documents_path,
                "cache_path": self.storage.cache_path,
                "logs_path": self.storage.logs_path,
            },
            "security": {
                "authentication_enabled": self.security.authentication_enabled,
                "jwt_algorithm": self.security.jwt_algorithm,
                "jwt_expiry_hours": self.security.jwt_expiry_hours,
                "session_timeout_minutes": self.security.session_timeout_minutes,
                # Note: jwt_secret is stored in .env, not config.yaml
            },
            "webui": {
                "enabled": self.webui.enabled,
                "port": self.webui.port,
                "theme": self.webui.theme,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RaggedConfig":
        """Create configuration from dictionary."""
        config = cls()

        if "server" in data:
            server = data["server"]
            config.server = ServerConfig(
                host=server.get("host", config.server.host),
                port=server.get("port", config.server.port),
                workers=server.get("workers", config.server.workers),
                cors_origins=server.get("cors_origins", config.server.cors_origins),
            )

        if "database" in data:
            db = data["database"]
            config.database = DatabaseConfig(
                chromadb_host=db.get("chromadb_host", config.database.chromadb_host),
                chromadb_port=db.get("chromadb_port", config.database.chromadb_port),
                collection_name=db.get("collection_name", config.database.collection_name),
                persist_directory=db.get("persist_directory", config.database.persist_directory),
            )

        if "llm" in data:
            llm = data["llm"]
            config.llm = LLMConfig(
                ollama_host=llm.get("ollama_host", config.llm.ollama_host),
                default_model=llm.get("default_model", config.llm.default_model),
                embedding_model=llm.get("embedding_model", config.llm.embedding_model),
                temperature=llm.get("temperature", config.llm.temperature),
                max_tokens=llm.get("max_tokens", config.llm.max_tokens),
            )

        if "storage" in data:
            storage = data["storage"]
            config.storage = StorageConfig(
                documents_path=storage.get("documents_path", config.storage.documents_path),
                cache_path=storage.get("cache_path", config.storage.cache_path),
                logs_path=storage.get("logs_path", config.storage.logs_path),
            )

        if "security" in data:
            security = data["security"]
            config.security = SecurityConfig(
                authentication_enabled=security.get(
                    "authentication_enabled", config.security.authentication_enabled
                ),
                jwt_algorithm=security.get("jwt_algorithm", config.security.jwt_algorithm),
                jwt_expiry_hours=security.get("jwt_expiry_hours", config.security.jwt_expiry_hours),
                session_timeout_minutes=security.get(
                    "session_timeout_minutes", config.security.session_timeout_minutes
                ),
            )

        if "webui" in data:
            webui = data["webui"]
            config.webui = WebUIConfig(
                enabled=webui.get("enabled", config.webui.enabled),
                port=webui.get("port", config.webui.port),
                theme=webui.get("theme", config.webui.theme),
            )

        return config


class ConfigManager:
    """
    Manager for ragged configuration.

    Handles configuration generation, loading, saving, and validation.
    """

    def __init__(self, ragged_home: Path | None = None) -> None:
        """
        Initialise configuration manager.

        Args:
            ragged_home: Path to ragged home directory.
        """
        self._ragged_home = ragged_home or Path(
            os.environ.get("RAGGED_HOME", Path.home() / ".ragged")
        )
        self._config_path = self._ragged_home / "config.yaml"
        self._env_path = self._ragged_home / ".env"

    @property
    def config_path(self) -> Path:
        """Get path to config file."""
        return self._config_path

    @property
    def env_path(self) -> Path:
        """Get path to .env file."""
        return self._env_path

    def generate_config(
        self,
        profile: ConfigProfile = ConfigProfile.DEFAULT,
        overrides: dict[str, Any] | None = None,
    ) -> RaggedConfig:
        """
        Generate configuration for specified profile.

        Args:
            profile: Configuration profile.
            overrides: Optional overrides to apply.

        Returns:
            Generated configuration.
        """
        # Start with default config
        config = RaggedConfig()

        # Apply profile-specific settings
        if profile == ConfigProfile.PRODUCTION:
            config.security.authentication_enabled = True
            config.server.workers = 4

        elif profile == ConfigProfile.DOCKER:
            config.server.host = "0.0.0.0"
            config.database.chromadb_host = "chromadb"
            config.llm.ollama_host = "http://ollama:11434"
            config.database.persist_directory = "/data/chromadb"
            config.storage.documents_path = "/data/documents"
            config.storage.cache_path = "/data/cache"
            config.storage.logs_path = "/data/logs"

        elif profile == ConfigProfile.MINIMAL:
            config.webui.enabled = False
            config.security.authentication_enabled = False

        # Apply overrides
        if overrides:
            config = self._apply_overrides(config, overrides)

        return config

    def _apply_overrides(
        self,
        config: RaggedConfig,
        overrides: dict[str, Any],
    ) -> RaggedConfig:
        """Apply overrides to configuration."""
        config_dict = config.to_dict()

        for key, value in overrides.items():
            parts = key.split(".")
            target = config_dict
            for part in parts[:-1]:
                if part in target:
                    target = target[part]
            if parts[-1] in target:
                target[parts[-1]] = value

        return RaggedConfig.from_dict(config_dict)

    def save_config(self, config: RaggedConfig) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save.
        """
        # Ensure directory exists
        self._ragged_home.mkdir(parents=True, exist_ok=True)

        # Generate YAML with comments
        yaml_content = self._generate_yaml_with_comments(config)

        with open(self._config_path, "w") as f:
            f.write(yaml_content)

    def _generate_yaml_with_comments(self, config: RaggedConfig) -> str:
        """Generate YAML content with helpful comments."""
        lines = [
            "# ragged configuration",
            "# Generated during installation",
            "# See documentation for all options: https://ragged.ai/docs/config",
            "",
        ]

        config_dict = config.to_dict()

        # Server section
        lines.extend([
            "# Server settings",
            "server:",
            f"  host: {config_dict['server']['host']}  # Bind address",
            f"  port: {config_dict['server']['port']}  # API port",
            f"  workers: {config_dict['server']['workers']}  # Number of worker processes",
            f"  cors_origins:",
        ])
        for origin in config_dict["server"]["cors_origins"]:
            lines.append(f"    - {origin}")
        lines.append("")

        # Database section
        lines.extend([
            "# Database settings",
            "database:",
            f"  chromadb_host: {config_dict['database']['chromadb_host']}",
            f"  chromadb_port: {config_dict['database']['chromadb_port']}",
            f"  collection_name: {config_dict['database']['collection_name']}",
            f"  persist_directory: {config_dict['database']['persist_directory']}",
            "",
        ])

        # LLM section
        lines.extend([
            "# LLM settings",
            "llm:",
            f"  ollama_host: {config_dict['llm']['ollama_host']}",
            f"  default_model: {config_dict['llm']['default_model']}  # Default chat model",
            f"  embedding_model: {config_dict['llm']['embedding_model']}  # Embedding model",
            f"  temperature: {config_dict['llm']['temperature']}",
            f"  max_tokens: {config_dict['llm']['max_tokens']}",
            "",
        ])

        # Storage section
        lines.extend([
            "# Storage paths",
            "storage:",
            f"  documents_path: {config_dict['storage']['documents_path']}",
            f"  cache_path: {config_dict['storage']['cache_path']}",
            f"  logs_path: {config_dict['storage']['logs_path']}",
            "",
        ])

        # Security section
        lines.extend([
            "# Security settings",
            "security:",
            f"  authentication_enabled: {str(config_dict['security']['authentication_enabled']).lower()}",
            f"  jwt_algorithm: {config_dict['security']['jwt_algorithm']}",
            f"  jwt_expiry_hours: {config_dict['security']['jwt_expiry_hours']}",
            f"  session_timeout_minutes: {config_dict['security']['session_timeout_minutes']}",
            "  # Note: JWT secret is stored in .env file for security",
            "",
        ])

        # WebUI section
        lines.extend([
            "# WebUI settings",
            "webui:",
            f"  enabled: {str(config_dict['webui']['enabled']).lower()}",
            f"  port: {config_dict['webui']['port']}",
            f"  theme: {config_dict['webui']['theme']}  # system, light, or dark",
            "",
        ])

        return "\n".join(lines)

    def load_config(self) -> RaggedConfig:
        """
        Load configuration from file.

        Returns:
            Loaded configuration.

        Raises:
            FileNotFoundError: If config file doesn't exist.
        """
        if not self._config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self._config_path}")

        with open(self._config_path) as f:
            data = yaml.safe_load(f)

        return RaggedConfig.from_dict(data)

    def generate_env_file(self, jwt_secret: str | None = None) -> str:
        """
        Generate .env file content with secrets.

        Args:
            jwt_secret: JWT secret. If None, generates secure random secret.

        Returns:
            .env file content.
        """
        if jwt_secret is None:
            jwt_secret = self.generate_jwt_secret()

        lines = [
            "# ragged environment variables",
            "# IMPORTANT: Never commit this file to version control",
            "",
            "# JWT Secret (used for authentication)",
            f"RAGGED_JWT_SECRET={jwt_secret}",
            "",
            "# Optional: Override config file settings",
            "# RAGGED_SERVER_PORT=8000",
            "# RAGGED_CHROMADB_HOST=localhost",
            "# RAGGED_OLLAMA_HOST=http://localhost:11434",
            "",
        ]

        return "\n".join(lines)

    def save_env_file(self, jwt_secret: str | None = None) -> None:
        """
        Save .env file.

        Args:
            jwt_secret: JWT secret. If None, generates secure random secret.
        """
        self._ragged_home.mkdir(parents=True, exist_ok=True)

        content = self.generate_env_file(jwt_secret)

        with open(self._env_path, "w") as f:
            f.write(content)

        # Set restrictive permissions (owner read/write only)
        self._env_path.chmod(0o600)

    def generate_jwt_secret(self, length: int = 64) -> str:
        """
        Generate cryptographically secure JWT secret.

        Args:
            length: Length of the secret.

        Returns:
            Secure random string.
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def validate_config(self, config: RaggedConfig) -> list[str]:
        """
        Validate configuration.

        Args:
            config: Configuration to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        # Validate server settings
        if config.server.port < 1 or config.server.port > 65535:
            errors.append(f"Invalid server port: {config.server.port}")

        if config.server.workers < 1:
            errors.append(f"Invalid worker count: {config.server.workers}")

        # Validate database settings
        if config.database.chromadb_port < 1 or config.database.chromadb_port > 65535:
            errors.append(f"Invalid ChromaDB port: {config.database.chromadb_port}")

        # Validate LLM settings
        if not config.llm.ollama_host.startswith(("http://", "https://")):
            errors.append(f"Invalid Ollama host URL: {config.llm.ollama_host}")

        if config.llm.temperature < 0 or config.llm.temperature > 2:
            errors.append(f"Invalid temperature: {config.llm.temperature}")

        if config.llm.max_tokens < 1:
            errors.append(f"Invalid max_tokens: {config.llm.max_tokens}")

        # Validate security settings
        if config.security.authentication_enabled:
            if config.security.jwt_expiry_hours < 1:
                errors.append(f"Invalid JWT expiry: {config.security.jwt_expiry_hours}")

        # Validate WebUI settings
        if config.webui.enabled:
            if config.webui.port < 1 or config.webui.port > 65535:
                errors.append(f"Invalid WebUI port: {config.webui.port}")

            if config.webui.theme not in ("system", "light", "dark"):
                errors.append(f"Invalid theme: {config.webui.theme}")

        return errors

    def config_exists(self) -> bool:
        """Check if configuration file exists."""
        return self._config_path.exists()

    def backup_config(self) -> Path | None:
        """
        Create backup of existing configuration.

        Returns:
            Path to backup file or None if no existing config.
        """
        if not self._config_path.exists():
            return None

        import shutil
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self._ragged_home / f"config.yaml.backup.{timestamp}"

        shutil.copy2(self._config_path, backup_path)

        return backup_path
