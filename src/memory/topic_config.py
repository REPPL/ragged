"""Topic extraction configuration (v0.4.7).

Configuration management for topic extraction and behaviour learning.

Privacy: All configuration stored locally, no external dependencies.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Set

import yaml

from ragged.memory.topics import DEFAULT_STOP_WORDS
from ragged.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TopicExtractionConfig:
    """Configuration for topic extraction.

    Attributes:
        min_topic_length: Minimum characters for valid topic (default: 3)
        max_topics_per_query: Maximum topics to extract per query (default: 10)
        confidence_threshold: Minimum confidence to keep topic (default: 0.3)
        stop_words: Set of words to filter out (default: DEFAULT_STOP_WORDS)
        enable_phrases: Enable multi-word phrase detection (default: True)
    """

    min_topic_length: int = 3
    max_topics_per_query: int = 10
    confidence_threshold: float = 0.3
    stop_words: Set[str] = field(default_factory=lambda: DEFAULT_STOP_WORDS.copy())
    enable_phrases: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.min_topic_length < 1:
            raise ValueError(f"min_topic_length must be >= 1, got {self.min_topic_length}")
        if self.max_topics_per_query < 1:
            raise ValueError(f"max_topics_per_query must be >= 1, got {self.max_topics_per_query}")
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(f"confidence_threshold must be 0.0-1.0, got {self.confidence_threshold}")

    @classmethod
    def from_dict(cls, config_dict: dict) -> "TopicExtractionConfig":
        """Create configuration from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            TopicExtractionConfig instance

        Example:
            >>> config = TopicExtractionConfig.from_dict({
            ...     "min_topic_length": 3,
            ...     "confidence_threshold": 0.3,
            ...     "stop_words": ["the", "a", "an"]
            ... })
        """
        # Handle stop_words specially
        stop_words_config = config_dict.get("stop_words", "default")

        if stop_words_config == "default":
            stop_words = DEFAULT_STOP_WORDS.copy()
        elif isinstance(stop_words_config, list):
            stop_words = set(stop_words_config)
        elif isinstance(stop_words_config, set):
            stop_words = stop_words_config.copy()
        else:
            raise ValueError(f"stop_words must be 'default', list, or set, got {type(stop_words_config)}")

        return cls(
            min_topic_length=config_dict.get("min_topic_length", 3),
            max_topics_per_query=config_dict.get("max_topics_per_query", 10),
            confidence_threshold=config_dict.get("confidence_threshold", 0.3),
            stop_words=stop_words,
            enable_phrases=config_dict.get("enable_phrases", True),
        )

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            Dictionary representation of configuration

        Example:
            >>> config = TopicExtractionConfig()
            >>> config_dict = config.to_dict()
            >>> config_dict["min_topic_length"]
            3
        """
        return {
            "min_topic_length": self.min_topic_length,
            "max_topics_per_query": self.max_topics_per_query,
            "confidence_threshold": self.confidence_threshold,
            "stop_words": list(self.stop_words) if self.stop_words != DEFAULT_STOP_WORDS else "default",
            "enable_phrases": self.enable_phrases,
        }

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "TopicExtractionConfig":
        """Load configuration from YAML file.

        Args:
            yaml_path: Path to YAML configuration file

        Returns:
            TopicExtractionConfig instance

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is invalid

        Example:
            >>> config = TopicExtractionConfig.from_yaml(Path("config.yaml"))
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        with open(yaml_path, "r") as f:
            config_dict = yaml.safe_load(f)

        # Handle nested structure (behaviour_learning.topic_extraction)
        if "behaviour_learning" in config_dict:
            config_dict = config_dict["behaviour_learning"].get("topic_extraction", {})
        elif "topic_extraction" in config_dict:
            config_dict = config_dict["topic_extraction"]

        logger.info(f"Loaded topic extraction config from {yaml_path}")
        return cls.from_dict(config_dict)

    def to_yaml(self, yaml_path: Path) -> None:
        """Save configuration to YAML file.

        Args:
            yaml_path: Path to save YAML configuration file

        Example:
            >>> config = TopicExtractionConfig()
            >>> config.to_yaml(Path("config.yaml"))
        """
        yaml_path.parent.mkdir(parents=True, exist_ok=True)

        config_dict = {
            "behaviour_learning": {
                "topic_extraction": self.to_dict()
            }
        }

        with open(yaml_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved topic extraction config to {yaml_path}")

    def load_custom_stop_words(self, stop_words_path: Path) -> None:
        """Load custom stop words from file.

        Args:
            stop_words_path: Path to text file with one stop word per line

        Raises:
            FileNotFoundError: If stop words file doesn't exist

        Example:
            >>> config = TopicExtractionConfig()
            >>> config.load_custom_stop_words(Path("my_stop_words.txt"))
        """
        if not stop_words_path.exists():
            raise FileNotFoundError(f"Stop words file not found: {stop_words_path}")

        with open(stop_words_path, "r") as f:
            custom_stop_words = {line.strip().lower() for line in f if line.strip()}

        self.stop_words = custom_stop_words
        logger.info(f"Loaded {len(custom_stop_words)} custom stop words from {stop_words_path}")

    def add_stop_words(self, words: Set[str] | list[str]) -> None:
        """Add additional stop words to existing set.

        Args:
            words: Set or list of words to add

        Example:
            >>> config = TopicExtractionConfig()
            >>> config.add_stop_words(["foo", "bar", "baz"])
            >>> "foo" in config.stop_words
            True
        """
        if isinstance(words, list):
            words = set(words)

        self.stop_words.update(w.lower() for w in words)
        logger.debug(f"Added {len(words)} stop words (total: {len(self.stop_words)})")

    def remove_stop_words(self, words: Set[str] | list[str]) -> None:
        """Remove stop words from existing set.

        Args:
            words: Set or list of words to remove

        Example:
            >>> config = TopicExtractionConfig()
            >>> config.remove_stop_words(["python", "machine"])
            >>> "python" in config.stop_words
            False
        """
        if isinstance(words, list):
            words = set(words)

        self.stop_words -= {w.lower() for w in words}
        logger.debug(f"Removed {len(words)} stop words (total: {len(self.stop_words)})")


def create_default_config() -> TopicExtractionConfig:
    """Create default topic extraction configuration.

    Returns:
        TopicExtractionConfig with default settings

    Example:
        >>> config = create_default_config()
        >>> config.confidence_threshold
        0.3
    """
    return TopicExtractionConfig()
