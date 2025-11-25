"""Terminology expansion and normalization for domain-specific retrieval.

Handles abbreviations, synonyms, and domain-specific terminology to improve
query matching and retrieval accuracy.

v0.6.3 OPTIMISE-003 Phase 2: Terminology Management
"""

import json
import logging
import re
from pathlib import Path

from ragged.optimisation.domain_adapter import Domain

logger = logging.getLogger(__name__)


class TerminologyManager:
    """Manages domain-specific terminology expansion and normalization."""

    def __init__(self, dictionaries_dir: Path | None = None):
        """Initialize terminology manager with domain dictionaries.

        Args:
            dictionaries_dir: Path to domain dictionaries directory.
                             Defaults to src/optimisation/dictionaries/
        """
        if dictionaries_dir is None:
            # Default to dictionaries/ subdirectory in same module
            dictionaries_dir = Path(__file__).parent / "dictionaries"

        self.dictionaries_dir = dictionaries_dir
        self.dictionaries = self._load_dictionaries()

    def _load_dictionaries(self) -> dict[Domain, dict]:
        """Load all domain dictionaries from JSON files.

        Returns:
            Dictionary mapping Domain to loaded dictionary data
        """
        dictionaries = {}

        domain_files = {
            Domain.TECHNICAL: "technical.json",
            Domain.MEDICAL: "medical.json",
            Domain.LEGAL: "legal.json",
            Domain.ACADEMIC: "academic.json",
        }

        for domain, filename in domain_files.items():
            filepath = self.dictionaries_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, "r") as f:
                        dictionaries[domain] = json.load(f)
                    logger.debug(f"Loaded {domain.value} dictionary from {filepath}")
                except Exception as e:
                    logger.warning(f"Failed to load {domain.value} dictionary: {e}")
                    dictionaries[domain] = {}
            else:
                logger.warning(f"Dictionary file not found: {filepath}")
                dictionaries[domain] = {}

        return dictionaries

    def expand_abbreviations(self, text: str, domain: Domain) -> str:
        """Expand abbreviations in text for the given domain.

        Args:
            text: Text containing abbreviations
            domain: Domain for terminology context

        Returns:
            Text with abbreviations expanded (non-recursive)
        """
        if domain not in self.dictionaries or domain == Domain.GENERAL:
            return text

        abbreviations = self.dictionaries[domain].get("abbreviations", {})
        if not abbreviations:
            return text

        # Find all abbreviations in original text first (to avoid recursive expansion)
        # Sort abbreviations by length (longest first) to handle overlapping matches
        sorted_abbrs = sorted(abbreviations.keys(), key=len, reverse=True)

        matches_to_expand = []
        matched_ranges = set()

        for abbr in sorted_abbrs:
            # For abbreviations with periods, use lookahead/lookbehind instead of \b
            # Match if preceded by space/start and followed by space/end/punctuation
            escaped_abbr = re.escape(abbr)
            pattern = r"(?<![a-zA-Z])" + escaped_abbr + r"(?![a-zA-Z])"
            for match in re.finditer(pattern, text):
                start, end = match.start(), match.end()
                # Check if this range overlaps with already matched ranges
                if not any(start < me and end > ms for ms, me in matched_ranges):
                    matches_to_expand.append((start, end, abbr))
                    matched_ranges.add((start, end))

        # Sort by position (reverse order to preserve indices during replacement)
        matches_to_expand.sort(reverse=True)

        # Expand matches from end to start (to preserve indices)
        expanded = text
        for start, end, abbr in matches_to_expand:
            expansion = abbreviations[abbr]
            replacement = f"{abbr} ({expansion})"
            expanded = expanded[:start] + replacement + expanded[end:]

        return expanded

    def get_synonyms(self, term: str, domain: Domain) -> list[str]:
        """Get synonyms for a term in the given domain.

        Args:
            term: Term to find synonyms for
            domain: Domain for terminology context

        Returns:
            List of synonyms (empty if none found)
        """
        if domain not in self.dictionaries or domain == Domain.GENERAL:
            return []

        synonyms = self.dictionaries[domain].get("synonyms", {})

        # Check for exact match (case-insensitive)
        term_lower = term.lower()
        for key, syn_list in synonyms.items():
            if key.lower() == term_lower:
                return syn_list

        # Check if term is in any synonym list
        for key, syn_list in synonyms.items():
            if term_lower in [s.lower() for s in syn_list]:
                # Return the key and other synonyms
                result = [key] + [s for s in syn_list if s.lower() != term_lower]
                return result

        return []

    def expand_query_with_synonyms(self, query: str, domain: Domain, max_synonyms: int = 2) -> str:
        """Expand query with domain-specific synonyms.

        Args:
            query: Original query text
            domain: Domain for terminology context
            max_synonyms: Maximum number of synonyms to add per term

        Returns:
            Expanded query with synonyms
        """
        if domain not in self.dictionaries or domain == Domain.GENERAL:
            return query

        synonyms = self.dictionaries[domain].get("synonyms", {})
        if not synonyms:
            return query

        # Extract meaningful terms (skip common words)
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        words = re.findall(r"\b\w+\b", query.lower())

        # Build expanded query
        expansions = []
        for word in words:
            if word in stop_words or len(word) < 3:
                continue

            # Check if word has synonyms
            word_synonyms = self.get_synonyms(word, domain)
            if word_synonyms:
                # Add original word and limited synonyms
                added = [word] + word_synonyms[:max_synonyms]
                expansions.append(" OR ".join(added))

        # If we found expansions, append them to original query
        if expansions:
            return f"{query} ({' '.join(expansions)})"

        return query

    def normalize_term(self, term: str, domain: Domain) -> str:
        """Normalize a term using domain-specific rules.

        Args:
            term: Term to normalize
            domain: Domain for normalization context

        Returns:
            Normalized term
        """
        if domain not in self.dictionaries or domain == Domain.GENERAL:
            return term.lower().strip()

        # Get abbreviations for expansion
        abbreviations = self.dictionaries[domain].get("abbreviations", {})

        # Check if term is an abbreviation
        term_stripped = term.strip()
        if term_stripped in abbreviations:
            return abbreviations[term_stripped].lower()

        # Otherwise, return lowercase normalized
        return term.lower().strip()

    def expand_query(self, query: str, domain: Domain) -> str:
        """Comprehensive query expansion for domain.

        Combines abbreviation expansion and synonym expansion.

        Args:
            query: Original query
            domain: Domain for context

        Returns:
            Expanded query
        """
        if domain == Domain.GENERAL:
            return query

        # Step 1: Expand abbreviations
        expanded = self.expand_abbreviations(query, domain)

        # Step 2: Add synonyms (commented out for now - can be expensive)
        # expanded = self.expand_query_with_synonyms(expanded, domain)

        return expanded

    def get_expansions(self, term: str, domain: Domain) -> list[str]:
        """Get expansion terms for a given term.

        Args:
            term: Term to expand
            domain: Domain for context

        Returns:
            List of expansion terms
        """
        if domain not in self.dictionaries or domain == Domain.GENERAL:
            return []

        expansions_dict = self.dictionaries[domain].get("expansions", {})

        # Check for exact match (case-insensitive)
        term_lower = term.lower()
        for key, exp_list in expansions_dict.items():
            if key.lower() == term_lower:
                return exp_list

        return []

    def get_domain_phrases(self, domain: Domain) -> dict[str, list[str]]:
        """Get common phrases for a domain.

        Args:
            domain: Domain to get phrases for

        Returns:
            Dictionary of phrase -> synonyms/expansions
        """
        if domain not in self.dictionaries or domain == Domain.GENERAL:
            return {}

        return self.dictionaries[domain].get("common_phrases", {})

    def enrich_query_context(self, query: str, domain: Domain) -> dict[str, list[str]]:
        """Enrich query with contextual information from domain.

        Returns abbreviations, synonyms, and expansions found in query.

        Args:
            query: Query text
            domain: Domain for context

        Returns:
            Dictionary with 'abbreviations', 'synonyms', 'expansions'
        """
        if domain == Domain.GENERAL:
            return {
                "abbreviations": [],
                "synonyms": [],
                "expansions": [],
            }

        result = {
            "abbreviations": [],
            "synonyms": [],
            "expansions": [],
        }

        if domain not in self.dictionaries:
            return result

        domain_dict = self.dictionaries[domain]

        # Find abbreviations in query
        abbreviations = domain_dict.get("abbreviations", {})
        for abbr, expansion in abbreviations.items():
            if re.search(r"\b" + re.escape(abbr) + r"\b", query, re.IGNORECASE):
                result["abbreviations"].append({"abbr": abbr, "expansion": expansion})

        # Find terms with synonyms
        words = re.findall(r"\b\w+\b", query.lower())
        for word in set(words):
            if len(word) >= 3:  # Skip very short words
                syns = self.get_synonyms(word, domain)
                if syns:
                    result["synonyms"].append({"term": word, "synonyms": syns})

                exps = self.get_expansions(word, domain)
                if exps:
                    result["expansions"].append({"term": word, "expansions": exps})

        return result


# Global instance for convenience
_terminology_manager = None


def get_terminology_manager() -> TerminologyManager:
    """Get global TerminologyManager instance (singleton pattern)."""
    global _terminology_manager
    if _terminology_manager is None:
        _terminology_manager = TerminologyManager()
    return _terminology_manager
