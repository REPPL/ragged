"""Tests for verbosity control."""

from unittest.mock import patch, MagicMock
import logging
import pytest

from src.cli.verbosity import (
    set_verbosity,
    get_effective_level,
    is_verbose,
    is_quiet,
)


class TestSetVerbosity:
    """Test set_verbosity function."""

    def test_set_verbose_mode(self):
        """Test setting verbose mode."""
        set_verbosity(verbose=True, quiet=False)

        assert is_verbose() is True
        assert is_quiet() is False
        assert get_effective_level() == logging.DEBUG

    def test_set_quiet_mode(self):
        """Test setting quiet mode."""
        set_verbosity(verbose=False, quiet=True)

        assert is_verbose() is False
        assert is_quiet() is True
        assert get_effective_level() == logging.WARNING

    def test_set_normal_mode(self):
        """Test normal mode (neither verbose nor quiet)."""
        set_verbosity(verbose=False, quiet=False)

        assert is_verbose() is False
        assert is_quiet() is False
        assert get_effective_level() == logging.INFO

    def test_verbose_and_quiet_conflict(self):
        """Test that verbose takes precedence over quiet."""
        set_verbosity(verbose=True, quiet=True)

        # Verbose should take precedence
        assert get_effective_level() == logging.DEBUG


class TestGetEffectiveLevel:
    """Test get_effective_level function."""

    def test_default_level(self):
        """Test default logging level."""
        set_verbosity(verbose=False, quiet=False)
        level = get_effective_level()

        assert level == logging.INFO

    def test_debug_level_when_verbose(self):
        """Test DEBUG level in verbose mode."""
        set_verbosity(verbose=True, quiet=False)
        level = get_effective_level()

        assert level == logging.DEBUG

    def test_warning_level_when_quiet(self):
        """Test WARNING level in quiet mode."""
        set_verbosity(verbose=False, quiet=True)
        level = get_effective_level()

        assert level == logging.WARNING


class TestIsVerbose:
    """Test is_verbose function."""

    def test_is_verbose_true(self):
        """Test is_verbose returns True in verbose mode."""
        set_verbosity(verbose=True, quiet=False)
        assert is_verbose() is True

    def test_is_verbose_false(self):
        """Test is_verbose returns False in normal mode."""
        set_verbosity(verbose=False, quiet=False)
        assert is_verbose() is False


class TestIsQuiet:
    """Test is_quiet function."""

    def test_is_quiet_true(self):
        """Test is_quiet returns True in quiet mode."""
        set_verbosity(verbose=False, quiet=True)
        assert is_quiet() is True

    def test_is_quiet_false(self):
        """Test is_quiet returns False in normal mode."""
        set_verbosity(verbose=False, quiet=False)
        assert is_quiet() is False


class TestLoggingIntegration:
    """Test integration with logging system."""

    @patch("src.cli.verbosity.get_logger")
    def test_verbose_mode_affects_logger(self, mock_get_logger):
        """Test that verbose mode affects logger level."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        set_verbosity(verbose=True, quiet=False)

        # Should set DEBUG level somewhere in the system
        assert get_effective_level() == logging.DEBUG

    @patch("src.cli.verbosity.get_logger")
    def test_quiet_mode_affects_logger(self, mock_get_logger):
        """Test that quiet mode affects logger level."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        set_verbosity(verbose=False, quiet=True)

        # Should set WARNING level somewhere in the system
        assert get_effective_level() == logging.WARNING
