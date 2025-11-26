"""
Configuration Recovery.

REFINE-002: Recovery strategies for configuration issues.
"""

import logging
import secrets
import string
from pathlib import Path
from typing import Any

import yaml

from ragged.install.recovery.framework import (
    RecoveryAction,
    RecoveryResult,
    RecoveryStatus,
    RecoveryStrategy,
)


logger = logging.getLogger(__name__)


class RepairConfigStrategy(RecoveryStrategy):
    """Repair corrupted configuration files."""

    @property
    def name(self) -> str:
        return "repair_config"

    @property
    def action(self) -> RecoveryAction:
        return RecoveryAction.REPAIR

    def can_recover(self, context: dict[str, Any]) -> bool:
        """Check if config needs repair."""
        ragged_home = context.get("ragged_home")
        if ragged_home:
            config_path = ragged_home / "config.yaml"
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        yaml.safe_load(f)
                except yaml.YAMLError:
                    return True  # Config is invalid YAML

        return False

    def recover(self, context: dict[str, Any]) -> RecoveryResult:
        """Repair configuration."""
        ragged_home = context.get("ragged_home")
        config_path = ragged_home / "config.yaml"

        try:
            # Backup current config
            backup_path = context.get("backups", {}).get("config")
            if not backup_path:
                from datetime import datetime
                backup_path = ragged_home / f"config.yaml.corrupted.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                config_path.rename(backup_path)

            # Generate default config
            from ragged.install.config_manager import ConfigManager

            manager = ConfigManager(ragged_home)
            config = manager.generate_config()
            manager.save_config(config)

            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.SUCCESS,
                message="Configuration repaired with defaults",
                details={"backup": str(backup_path)},
            )

        except Exception as e:
            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.FAILED,
                message=f"Failed to repair config: {e}",
            )


class RegenerateSecretsStrategy(RecoveryStrategy):
    """Regenerate missing or exposed secrets."""

    @property
    def name(self) -> str:
        return "regenerate_secrets"

    @property
    def action(self) -> RecoveryAction:
        return RecoveryAction.REGENERATE

    def can_recover(self, context: dict[str, Any]) -> bool:
        """Check if secrets need regeneration."""
        ragged_home = context.get("ragged_home")
        if ragged_home:
            env_path = ragged_home / ".env"

            # Check if .env is missing
            if not env_path.exists():
                return True

            # Check if JWT secret is missing or weak
            try:
                content = env_path.read_text()
                if "RAGGED_JWT_SECRET" not in content:
                    return True

                # Check if secret is too short
                for line in content.split("\n"):
                    if line.startswith("RAGGED_JWT_SECRET="):
                        secret = line.split("=", 1)[1].strip()
                        if len(secret) < 32:
                            return True
            except Exception:
                return True

        return False

    def recover(self, context: dict[str, Any]) -> RecoveryResult:
        """Regenerate secrets."""
        ragged_home = context.get("ragged_home")
        env_path = ragged_home / ".env"

        try:
            # Generate new secret
            alphabet = string.ascii_letters + string.digits
            new_secret = "".join(secrets.choice(alphabet) for _ in range(64))

            # Read existing .env if present
            existing_vars = {}
            if env_path.exists():
                for line in env_path.read_text().split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        if key != "RAGGED_JWT_SECRET":
                            existing_vars[key] = value

            # Write new .env
            lines = [
                "# ragged environment variables",
                "# IMPORTANT: Never commit this file to version control",
                "",
                "# JWT Secret (regenerated)",
                f"RAGGED_JWT_SECRET={new_secret}",
                "",
            ]

            # Preserve other variables
            for key, value in existing_vars.items():
                lines.append(f"{key}={value}")

            env_path.write_text("\n".join(lines))
            env_path.chmod(0o600)

            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.SUCCESS,
                message="Regenerated JWT secret",
            )

        except Exception as e:
            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.FAILED,
                message=f"Failed to regenerate secrets: {e}",
            )


class ValidateConfigStrategy(RecoveryStrategy):
    """Validate and fix config keys."""

    @property
    def name(self) -> str:
        return "validate_config"

    @property
    def action(self) -> RecoveryAction:
        return RecoveryAction.REPAIR

    def can_recover(self, context: dict[str, Any]) -> bool:
        """Check if config needs validation."""
        ragged_home = context.get("ragged_home")
        if ragged_home:
            config_path = ragged_home / "config.yaml"
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = yaml.safe_load(f)

                    # Check for missing required sections
                    required = ["server", "database", "llm"]
                    return any(key not in config for key in required)
                except Exception:
                    pass

        return False

    def recover(self, context: dict[str, Any]) -> RecoveryResult:
        """Validate and fix config."""
        ragged_home = context.get("ragged_home")
        config_path = ragged_home / "config.yaml"

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}

            # Load default config
            from ragged.install.config_manager import ConfigManager

            manager = ConfigManager(ragged_home)
            default_config = manager.generate_config()
            default_dict = default_config.to_dict()

            # Merge missing keys
            merged = self._merge_configs(default_dict, config)

            # Save merged config
            with open(config_path, "w") as f:
                yaml.dump(merged, f, default_flow_style=False)

            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.SUCCESS,
                message="Config validated and missing keys added",
            )

        except Exception as e:
            return RecoveryResult(
                action=self.action,
                status=RecoveryStatus.FAILED,
                message=f"Failed to validate config: {e}",
            )

    def _merge_configs(self, default: dict, current: dict) -> dict:
        """Merge configs, preferring current values."""
        result = default.copy()

        for key, value in current.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result


class ConfigurationRecovery:
    """Utility class for configuration recovery."""

    @staticmethod
    def backup_config(ragged_home: Path) -> Path | None:
        """Create backup of configuration."""
        config_path = ragged_home / "config.yaml"
        if not config_path.exists():
            return None

        from datetime import datetime
        import shutil

        backup_path = ragged_home / f"config.yaml.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy2(config_path, backup_path)
        return backup_path

    @staticmethod
    def restore_config(backup_path: Path, ragged_home: Path) -> bool:
        """Restore configuration from backup."""
        if not backup_path.exists():
            return False

        import shutil

        config_path = ragged_home / "config.yaml"
        shutil.copy2(backup_path, config_path)
        return True


def repair_config(
    ragged_home: Path | None = None,
) -> bool:
    """
    Repair configuration file.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        True if repair successful.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    strategy = RepairConfigStrategy()
    context = {"ragged_home": ragged_home}

    if strategy.can_recover(context):
        result = strategy.recover(context)
        return result.status == RecoveryStatus.SUCCESS

    return True  # Nothing to repair


def regenerate_secrets(
    ragged_home: Path | None = None,
) -> bool:
    """
    Regenerate secrets.

    Args:
        ragged_home: Path to ragged home.

    Returns:
        True if regeneration successful.
    """
    import os

    if ragged_home is None:
        ragged_home = Path(os.environ.get("RAGGED_HOME", Path.home() / ".ragged"))

    strategy = RegenerateSecretsStrategy()
    context = {"ragged_home": ragged_home}

    result = strategy.recover(context)
    return result.status == RecoveryStatus.SUCCESS
