"""Tests for theme system.

v0.3.12: Test colour themes and accessibility.
"""

import pytest

from src.cli.themes import (
    ThemeManager,
    ThemeColors,
    create_theme_manager,
    get_current_theme,
)


class TestThemeManager:
    """Test ThemeManager class."""

    def test_init_default_theme(self):
        """Test default theme initialisation."""
        manager = ThemeManager()
        assert manager.theme_name == "dark"
        assert isinstance(manager.theme, ThemeColors)

    def test_init_specific_theme(self):
        """Test initialisation with specific theme."""
        manager = ThemeManager(theme_name="light")
        assert manager.theme_name == "light"

    def test_init_invalid_theme_fallback(self):
        """Test fallback to dark for invalid theme."""
        manager = ThemeManager(theme_name="invalid")  # type: ignore
        assert manager.theme_name == "dark"

    def test_all_themes_available(self):
        """Test all defined themes can be initialised."""
        for theme_name in ["dark", "light", "high-contrast", "colourblind-safe", "monochrome"]:
            manager = ThemeManager(theme_name=theme_name)  # type: ignore
            assert manager.theme_name == theme_name
            assert isinstance(manager.theme, ThemeColors)

    def test_get_color(self):
        """Test getting colour by type."""
        manager = ThemeManager(theme_name="dark")
        assert manager.get_color("success") == "green"
        assert manager.get_color("error") == "red"
        assert manager.get_color("warning") == "yellow"

    def test_get_color_invalid_type(self):
        """Test getting colour for invalid type returns primary."""
        manager = ThemeManager(theme_name="dark")
        assert manager.get_color("invalid_type") == manager.theme.primary

    def test_get_style(self):
        """Test getting style string."""
        manager = ThemeManager(theme_name="dark")
        style = manager.get_style("success")
        assert style == "green"

    def test_list_themes(self):
        """Test listing available themes."""
        themes = ThemeManager.list_themes()
        assert isinstance(themes, dict)
        assert "dark" in themes
        assert "light" in themes
        assert "high-contrast" in themes
        assert "colourblind-safe" in themes
        assert "monochrome" in themes

    def test_list_themes_has_descriptions(self):
        """Test theme list includes descriptions."""
        themes = ThemeManager.list_themes()
        for theme_name, description in themes.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_get_theme_colors(self):
        """Test getting theme colours."""
        colors = ThemeManager.get_theme_colors("dark")
        assert isinstance(colors, ThemeColors)
        assert hasattr(colors, "success")
        assert hasattr(colors, "error")

    def test_get_theme_colors_invalid(self):
        """Test getting colours for invalid theme."""
        colors = ThemeManager.get_theme_colors("invalid")  # type: ignore
        assert colors is None

    def test_apply_to_console(self):
        """Test applying theme to console."""
        manager = ThemeManager(theme_name="dark")
        mapping = manager.apply_to_console()
        assert isinstance(mapping, dict)
        assert "success" in mapping
        assert "error" in mapping
        assert mapping["success"] == manager.theme.success

    def test_validate_contrast_high_contrast(self):
        """Test contrast validation for high-contrast theme."""
        manager = ThemeManager(theme_name="high-contrast")
        assert manager.validate_contrast() is True

    def test_validate_contrast_monochrome(self):
        """Test contrast validation for monochrome theme."""
        manager = ThemeManager(theme_name="monochrome")
        assert manager.validate_contrast() is True

    def test_validate_contrast_other_themes(self):
        """Test contrast validation for other themes."""
        for theme_name in ["dark", "light", "colourblind-safe"]:
            manager = ThemeManager(theme_name=theme_name)  # type: ignore
            # Should return True (assumes okay for now)
            assert manager.validate_contrast() is True


class TestThemeColors:
    """Test ThemeColors dataclass."""

    def test_dark_theme_colors(self):
        """Test dark theme colour definitions."""
        colors = ThemeManager.get_theme_colors("dark")
        assert colors is not None
        assert colors.success == "green"
        assert colors.error == "red"
        assert colors.warning == "yellow"
        assert colors.info == "cyan"
        assert colors.highlight == "magenta"

    def test_light_theme_colors(self):
        """Test light theme colour definitions."""
        colors = ThemeManager.get_theme_colors("light")
        assert colors is not None
        assert colors.success == "green"
        assert colors.info == "blue"  # Different from dark
        assert colors.muted == "black"  # Different from dark

    def test_high_contrast_colors(self):
        """Test high-contrast theme uses bright colours."""
        colors = ThemeManager.get_theme_colors("high-contrast")
        assert colors is not None
        assert "bright" in colors.success
        assert "bright" in colors.error
        assert "bright" in colors.warning

    def test_colourblind_safe_colors(self):
        """Test colourblind-safe theme uses safe palette."""
        colors = ThemeManager.get_theme_colors("colourblind-safe")
        assert colors is not None
        # Orange-blue palette
        assert colors.success == "blue"
        assert "orange" in colors.error

    def test_monochrome_colors(self):
        """Test monochrome theme uses only white/black."""
        colors = ThemeManager.get_theme_colors("monochrome")
        assert colors is not None
        assert colors.success == "white"
        assert colors.error == "white"
        assert colors.warning == "white"
        assert colors.info == "white"


class TestHelperFunctions:
    """Test helper functions."""

    def test_create_theme_manager(self):
        """Test factory function."""
        manager = create_theme_manager()
        assert isinstance(manager, ThemeManager)
        assert manager.theme_name == "dark"

    def test_create_theme_manager_specific(self):
        """Test factory with specific theme."""
        manager = create_theme_manager(theme_name="light")
        assert manager.theme_name == "light"

    def test_get_current_theme(self):
        """Test getting current theme."""
        theme = get_current_theme()
        assert theme in ["dark", "light", "high-contrast", "colourblind-safe", "monochrome"]
