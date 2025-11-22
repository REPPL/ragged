"""Security tests for HIGH-1: Plugin manifest validation."""

import pytest
import tempfile
from pathlib import Path

from ragged.plugins.validation import (
    PluginValidator,
    ValidationSeverity,
    MAX_PERMISSIONS,
    MAX_DEPENDENCIES,
    MAX_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)


class TestManifestValidation:
    """Tests for plugin manifest validation (HIGH-1)."""

    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return PluginValidator()

    @pytest.fixture
    def valid_manifest(self, tmp_path):
        """Create a valid plugin manifest."""
        manifest_content = """
[plugin]
name = "test_plugin"
version = "1.0.0"
type = "embedder"
description = "A test plugin for validation"
author = "Test Author"

[permissions]
required = ["read:documents"]
optional = ["write:documents"]

[dependencies]
numpy = ">=1.20.0"
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)
        return manifest_path

    def test_valid_manifest_passes(self, validator, valid_manifest):
        """Test that a valid manifest passes validation."""
        result = validator.validate_manifest(valid_manifest)

        assert result.passed is True
        assert result.score > 0.8

    def test_missing_manifest_fails(self, validator, tmp_path):
        """Test that missing manifest file fails validation."""
        nonexistent = tmp_path / "nonexistent.toml"

        result = validator.validate_manifest(nonexistent)

        assert result.passed is False
        assert any(i.severity == ValidationSeverity.CRITICAL for i in result.issues)
        assert any("not found" in i.message.lower() for i in result.issues)

    def test_malformed_toml_fails(self, validator, tmp_path):
        """Test that malformed TOML fails validation."""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text("this is not valid TOML [[[")

        result = validator.validate_manifest(manifest_path)

        assert result.passed is False
        assert any(i.severity == ValidationSeverity.CRITICAL for i in result.issues)
        assert any("parse" in i.message.lower() for i in result.issues)

    def test_missing_plugin_section_fails(self, validator, tmp_path):
        """Test that missing [plugin] section fails."""
        manifest_content = """
[permissions]
required = []
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        assert result.passed is False
        assert any("[plugin]" in i.message for i in result.issues)

    def test_missing_permissions_section_fails(self, validator, tmp_path):
        """Test that missing [permissions] section fails."""
        manifest_content = """
[plugin]
name = "test"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        assert result.passed is False
        assert any("[permissions]" in i.message for i in result.issues)

    def test_missing_required_fields_fails(self, validator, tmp_path):
        """Test that missing required fields fail validation."""
        # Missing 'version' field
        manifest_content = """
[plugin]
name = "test"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = []
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        assert result.passed is False
        assert any("version" in i.message.lower() for i in result.issues)

    def test_invalid_plugin_name_characters(self, validator, tmp_path):
        """Test that invalid characters in plugin name are rejected."""
        manifest_content = """
[plugin]
name = "test plugin with spaces!"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = []
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        assert result.passed is False
        assert any("invalid characters" in i.message.lower() for i in result.issues)

    def test_plugin_name_too_long(self, validator, tmp_path):
        """Test that overly long plugin names are rejected."""
        long_name = "a" * (MAX_NAME_LENGTH + 10)
        manifest_content = f"""
[plugin]
name = "{long_name}"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = []
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        assert result.passed is False
        assert any("exceeds maximum length" in i.message for i in result.issues)

    def test_invalid_version_format(self, validator, tmp_path):
        """Test that invalid semantic version format is rejected."""
        invalid_versions = ["1.0", "v1.0.0", "1.0.0.0", "latest", "1.0.x"]

        for invalid_version in invalid_versions:
            manifest_content = f"""
[plugin]
name = "test"
version = "{invalid_version}"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = []
"""
            manifest_path = tmp_path / f"plugin_{invalid_version.replace('.', '_')}.toml"
            manifest_path.write_text(manifest_content)

            result = validator.validate_manifest(manifest_path)

            assert result.passed is False, f"Version {invalid_version} should fail"
            assert any("semantic versioning" in i.message.lower() for i in result.issues)

    def test_valid_semantic_versions(self, validator, tmp_path):
        """Test that valid semantic versions are accepted."""
        valid_versions = ["1.0.0", "0.1.0", "2.5.3", "1.0.0-beta", "1.0.0-alpha1"]

        for valid_version in valid_versions:
            manifest_content = f"""
[plugin]
name = "test"
version = "{valid_version}"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = []
"""
            manifest_path = tmp_path / f"plugin_v{valid_version.replace('.', '_').replace('-', '_')}.toml"
            manifest_path.write_text(manifest_content)

            result = validator.validate_manifest(manifest_path)

            # Should not have version-related errors
            version_errors = [i for i in result.issues if "version" in i.message.lower()
                            and "semantic" in i.message.lower()]
            assert len(version_errors) == 0, f"Version {valid_version} should be valid"

    def test_description_too_long_warning(self, validator, tmp_path):
        """Test that overly long descriptions generate warnings."""
        long_description = "x" * (MAX_DESCRIPTION_LENGTH + 100)
        manifest_content = f"""
[plugin]
name = "test"
version = "1.0.0"
type = "embedder"
description = "{long_description}"
author = "Author"

[permissions]
required = []
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        # Should have warning (not error)
        description_warnings = [i for i in result.issues
                              if "description" in i.message.lower()
                              and i.severity == ValidationSeverity.WARNING]
        assert len(description_warnings) > 0

    def test_invalid_plugin_type(self, validator, tmp_path):
        """Test that invalid plugin types are rejected."""
        manifest_content = """
[plugin]
name = "test"
version = "1.0.0"
type = "invalid_type"
description = "Test"
author = "Author"

[permissions]
required = []
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        assert result.passed is False
        assert any("invalid plugin type" in i.message.lower() for i in result.issues)

    def test_valid_plugin_types(self, validator, tmp_path):
        """Test that all valid plugin types are accepted."""
        valid_types = ["embedder", "retriever", "processor", "command"]

        for plugin_type in valid_types:
            manifest_content = f"""
[plugin]
name = "test"
version = "1.0.0"
type = "{plugin_type}"
description = "Test"
author = "Author"

[permissions]
required = []
"""
            manifest_path = tmp_path / f"plugin_{plugin_type}.toml"
            manifest_path.write_text(manifest_content)

            result = validator.validate_manifest(manifest_path)

            # Should not have type-related errors
            type_errors = [i for i in result.issues if "type" in i.message.lower()]
            assert len(type_errors) == 0, f"Plugin type {plugin_type} should be valid"

    def test_excessive_permissions_rejected(self, validator, tmp_path):
        """Test that requesting too many permissions is rejected."""
        # Request more than MAX_PERMISSIONS
        excessive_perms = [f"perm{i}:test" for i in range(MAX_PERMISSIONS + 2)]
        perms_str = '", "'.join(excessive_perms)

        manifest_content = f"""
[plugin]
name = "test"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = ["{perms_str}"]
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        assert result.passed is False
        assert any("exceeding maximum" in i.message for i in result.issues)
        assert any(str(MAX_PERMISSIONS) in i.message for i in result.issues)

    def test_permission_format_validation(self, validator, tmp_path):
        """Test that permission format is validated."""
        invalid_permissions = [
            "INVALID",  # Not lowercase
            "read_documents",  # Underscore instead of colon
            "read:",  # Missing permission part
            ":documents",  # Missing category part
            "read:Documents",  # Not lowercase
            "read documents",  # Space instead of colon
        ]

        for invalid_perm in invalid_permissions:
            manifest_content = f"""
[plugin]
name = "test"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = ["{invalid_perm}"]
"""
            manifest_path = tmp_path / "plugin_perm.toml"
            manifest_path.write_text(manifest_content)

            result = validator.validate_manifest(manifest_path)

            assert result.passed is False, f"Permission '{invalid_perm}' should be invalid"
            assert any("invalid permission format" in i.message.lower() for i in result.issues)

    def test_valid_permission_formats(self, validator, tmp_path):
        """Test that valid permission formats are accepted."""
        valid_permissions = [
            "read:documents",
            "write:config",
            "network:api",
            "system:vectorstore",
        ]

        perms_str = '", "'.join(valid_permissions)
        manifest_content = f"""
[plugin]
name = "test"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = ["{perms_str}"]
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        # Should not have permission format errors
        format_errors = [i for i in result.issues
                        if "permission format" in i.message.lower()]
        assert len(format_errors) == 0

    def test_excessive_dependencies_warning(self, validator, tmp_path):
        """Test that too many dependencies generates warning."""
        # Create more than MAX_DEPENDENCIES
        deps = "\n".join([f'dep{i} = "1.0.0"' for i in range(MAX_DEPENDENCIES + 2)])

        manifest_content = f"""
[plugin]
name = "test"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = []

[dependencies]
{deps}
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        # Should have warning about dependencies
        dep_warnings = [i for i in result.issues
                       if "dependencies" in i.message.lower()
                       and i.severity == ValidationSeverity.WARNING]
        assert len(dep_warnings) > 0

    def test_unpinned_dependencies_warning(self, validator, tmp_path):
        """Test that unpinned dependencies generate warnings."""
        manifest_content = """
[plugin]
name = "test"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = []

[dependencies]
numpy = "*"
pandas = ""
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        # Should have warnings about unpinned dependencies
        pin_warnings = [i for i in result.issues
                       if "version-pinned" in i.message.lower()]
        assert len(pin_warnings) >= 2  # At least warnings for numpy and pandas

    def test_pinned_dependencies_accepted(self, validator, tmp_path):
        """Test that properly pinned dependencies don't generate warnings."""
        manifest_content = """
[plugin]
name = "test"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = []

[dependencies]
numpy = ">=1.20.0"
pandas = "==1.3.0"
scipy = "~=1.7.0"
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        # Should not have unpinned warnings
        pin_warnings = [i for i in result.issues
                       if "version-pinned" in i.message.lower()]
        assert len(pin_warnings) == 0


class TestManifestSecurityConstraints:
    """Tests for security constraint enforcement."""

    @pytest.fixture
    def validator(self):
        return PluginValidator()

    def test_name_alphanumeric_only(self, validator, tmp_path):
        """Test that only safe characters are allowed in names."""
        # Test various injection attempts
        malicious_names = [
            "test'; DROP TABLE plugins--",
            "test<script>alert('xss')</script>",
            "../../etc/passwd",
            "test\x00null",
            "test\ninjection",
        ]

        for malicious_name in malicious_names:
            manifest_content = f"""
[plugin]
name = "{malicious_name}"
version = "1.0.0"
type = "embedder"
description = "Test"
author = "Author"

[permissions]
required = []
"""
            manifest_path = tmp_path / "plugin_mal.toml"
            manifest_path.write_text(manifest_content)

            result = validator.validate_manifest(manifest_path)

            assert result.passed is False, f"Malicious name '{malicious_name}' should be blocked"

    def test_permission_privilege_escalation_prevented(self, validator, tmp_path):
        """Test that plugins can't request unlimited permissions."""
        # This is already tested in test_excessive_permissions_rejected
        # but worth documenting the security implication

        # A malicious plugin trying to request all possible permissions
        all_perms = [
            "read:documents", "write:documents",
            "read:config", "write:config",
            "network:api", "network:download",
            "system:embedding", "system:vectorstore"
        ]

        perms_str = '", "'.join(all_perms)
        manifest_content = f"""
[plugin]
name = "malicious"
version = "1.0.0"
type = "embedder"
description = "Requests too many permissions"
author = "Attacker"

[permissions]
required = ["{perms_str}"]
"""
        manifest_path = tmp_path / "plugin.toml"
        manifest_path.write_text(manifest_content)

        result = validator.validate_manifest(manifest_path)

        # Should be rejected for exceeding permission limit
        assert result.passed is False
        assert any("exceeding maximum" in i.message for i in result.issues)
