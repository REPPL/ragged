"""
Metadata filtering and faceted search for retrieval.

v0.3.7d: Rich metadata queries with filter parsing and faceted search.

SECURITY FIX (HIGH-4): Safe query construction to prevent NoSQL injection
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.utils.logging import get_logger

logger = get_logger(__name__)

# SECURITY FIX (HIGH-4): Whitelisted metadata field names to prevent injection
ALLOWED_METADATA_FIELDS: set[str] = {
    "tag", "tags",
    "author", "authors",
    "file_type", "filetype",
    "date", "created_at", "updated_at",
    "confidence", "score",
    "source", "category",
    "title", "description",
    "language", "lang",
    "version", "status",
    "page", "page_number",
    "chunk_id", "chunk_index",
    "embedding_model", "model",
}

# SECURITY FIX (HIGH-4): Whitelisted operators
ALLOWED_OPERATORS: set[str] = {
    "==", "!=", ">", "<", ">=", "<=",
    "in", "not_in", "contains",
}

# SECURITY FIX (HIGH-4): MongoDB operators that should never appear in field names
FORBIDDEN_FIELD_PREFIXES: set[str] = {
    "$where", "$regex", "$gt", "$lt", "$gte", "$lte",
    "$eq", "$ne", "$in", "$nin", "$and", "$or", "$not",
    "$exists", "$type", "$mod", "$text", "$search",
}


class MetadataFilterSecurityError(Exception):
    """Raised when metadata filter contains malicious input."""

    pass


def validate_field_name(field: str) -> str:
    """Validate metadata field name to prevent injection.

    SECURITY FIX (HIGH-4): Validates field names against whitelist and forbidden patterns.

    Args:
        field: Field name to validate

    Returns:
        Validated field name

    Raises:
        MetadataFilterSecurityError: If field name is malicious
    """
    if not field or not isinstance(field, str):
        raise MetadataFilterSecurityError("Field name must be a non-empty string")

    # Check for forbidden MongoDB operators
    field_lower = field.lower()
    for forbidden in FORBIDDEN_FIELD_PREFIXES:
        if field_lower.startswith(forbidden):
            raise MetadataFilterSecurityError(
                f"Field name '{field}' contains forbidden operator '{forbidden}'"
            )

    # Validate against whitelist (case-insensitive)
    if field_lower not in ALLOWED_METADATA_FIELDS:
        raise MetadataFilterSecurityError(
            f"Field name '{field}' not in allowed fields. "
            f"Allowed: {sorted(ALLOWED_METADATA_FIELDS)}"
        )

    # Additional checks: only alphanumeric and underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', field):
        raise MetadataFilterSecurityError(
            f"Field name '{field}' contains invalid characters. "
            "Only alphanumeric and underscore allowed."
        )

    return field_lower  # Normalize to lowercase


def validate_operator(operator: str) -> str:
    """Validate filter operator.

    SECURITY FIX (HIGH-4): Validates operators against whitelist.

    Args:
        operator: Operator to validate

    Returns:
        Validated operator

    Raises:
        MetadataFilterSecurityError: If operator is not allowed
    """
    if operator not in ALLOWED_OPERATORS:
        raise MetadataFilterSecurityError(
            f"Operator '{operator}' not allowed. "
            f"Allowed: {sorted(ALLOWED_OPERATORS)}"
        )

    return operator


def sanitize_value(value: Any, field: str) -> Any:
    """Sanitize filter value to prevent injection.

    SECURITY FIX (HIGH-4): Validates and sanitizes values.

    Args:
        value: Value to sanitize
        field: Field name (for type hints)

    Returns:
        Sanitized value

    Raises:
        MetadataFilterSecurityError: If value is malicious
    """
    # Check for dict-based injection attempts (MongoDB operators in values)
    if isinstance(value, dict):
        # Dicts are not allowed in values (prevent operator injection)
        raise MetadataFilterSecurityError(
            "Dictionary values not allowed (potential operator injection)"
        )

    # Check for list values (should only be used with 'in' operator)
    if isinstance(value, list):
        # Validate each item in list
        if len(value) > 1000:
            raise MetadataFilterSecurityError("List values limited to 1000 items")

        sanitized = []
        for item in value:
            if isinstance(item, (str, int, float, bool)):
                sanitized.append(item)
            else:
                raise MetadataFilterSecurityError(
                    f"List items must be primitive types, got {type(item).__name__}"
                )
        return sanitized

    # Primitives are safe
    if isinstance(value, (str, int, float, bool, type(None))):
        # Additional string validation
        if isinstance(value, str):
            # Prevent extremely long strings (DoS)
            if len(value) > 10000:
                raise MetadataFilterSecurityError("String values limited to 10000 characters")

            # Check for null bytes
            if '\x00' in value:
                raise MetadataFilterSecurityError("Null bytes not allowed in values")

        return value

    # Unsupported types
    raise MetadataFilterSecurityError(
        f"Value type '{type(value).__name__}' not allowed. "
        "Only str, int, float, bool, None, or list of primitives allowed."
    )


@dataclass
class FilterCondition:
    """A single filter condition.

    SECURITY FIX (HIGH-4): Validates field, operator, and value to prevent NoSQL injection.
    """

    field: str  # Metadata field name
    operator: str  # "==", "!=", ">", "<", ">=", "<=", "in", "not_in", "contains"
    value: Any  # Filter value

    def __post_init__(self):
        """Validate filter condition components.

        SECURITY FIX (HIGH-4): Validates all components to prevent injection.
        """
        # Validate and normalize field name
        self.field = validate_field_name(self.field)

        # Validate operator
        self.operator = validate_operator(self.operator)

        # Sanitize value
        self.value = sanitize_value(self.value, self.field)

    def __str__(self) -> str:
        """String representation."""
        if self.operator == "in":
            return f"{self.field} in {self.value}"
        elif self.operator == "not_in":
            return f"{self.field} not in {self.value}"
        elif self.operator == "contains":
            return f"{self.field} contains '{self.value}'"
        return f"{self.field} {self.operator} {self.value}"


@dataclass
class MetadataFilter:
    """Complex metadata filter with AND/OR logic.

    SECURITY FIX (HIGH-4): All conditions are validated via FilterCondition.__post_init__.
    """

    conditions: list[FilterCondition] = field(default_factory=list)
    logic: str = "AND"  # "AND" or "OR"

    def add_condition(self, field: str, operator: str, value: Any) -> None:
        """Add a filter condition.

        SECURITY FIX (HIGH-4): FilterCondition validates all inputs to prevent injection.

        Args:
            field: Metadata field name (validated against whitelist)
            operator: Comparison operator (validated against allowed operators)
            value: Filter value (sanitized to prevent operator injection)

        Raises:
            MetadataFilterSecurityError: If field, operator, or value is malicious
        """
        self.conditions.append(FilterCondition(field, operator, value))

    def to_dict(self) -> dict[str, Any]:
        """
        Convert filter to vector store where clause.

        Returns:
            Dictionary suitable for ChromaDB where clause

        Example:
            >>> filter = MetadataFilter()
            >>> filter.add_condition("tag", "==", "python")
            >>> filter.add_condition("confidence", ">", 0.9)
            >>> filter.to_dict()
            {"$and": [{"tag": "python"}, {"confidence": {"$gt": 0.9}}]}
        """
        if not self.conditions:
            return {}

        # Map operators to ChromaDB operators
        operator_map = {
            "==": "$eq",
            "!=": "$ne",
            ">": "$gt",
            "<": "$lt",
            ">=": "$gte",
            "<=": "$lte",
            "in": "$in",
            "not_in": "$nin",
            "contains": "$contains",
        }

        # Build individual conditions
        clauses = []
        for condition in self.conditions:
            op = operator_map.get(condition.operator, "$eq")

            if condition.operator in ("==", "in", "not_in"):
                # Simple equality or membership
                if condition.operator == "==":
                    clauses.append({condition.field: condition.value})
                else:
                    clauses.append({condition.field: {op: condition.value}})
            elif condition.operator == "contains":
                # String contains (case-insensitive)
                clauses.append({condition.field: {op: condition.value}})
            else:
                # Comparison operators
                clauses.append({condition.field: {op: condition.value}})

        # Combine with logic
        if len(clauses) == 1:
            return clauses[0]
        elif self.logic == "AND":
            return {"$and": clauses}
        else:  # OR
            return {"$or": clauses}

    def __str__(self) -> str:
        """String representation."""
        if not self.conditions:
            return "No filters"
        separator = f" {self.logic} "
        return separator.join(str(c) for c in self.conditions)


class FilterParser:
    """
    Parse user-friendly filter syntax into MetadataFilter.

    Supports:
    - Equality: tag=python
    - Comparison: confidence>0.9, date>=2023-01-01
    - Multiple values (OR): tag=python,java
    - Multiple filters (AND): tag=python confidence>0.9
    - Negation: tag!=python
    """

    # Regex for parsing filter expressions
    FILTER_PATTERN = re.compile(r'(\w+)(==|!=|>=|<=|>|<|=)(.+)')

    @classmethod
    def parse(cls, filter_string: str) -> MetadataFilter:
        """
        Parse filter string into MetadataFilter.

        SECURITY FIX (HIGH-4): Validates all filter components via FilterCondition.

        Args:
            filter_string: Filter expression (e.g., "tag=python confidence>0.9")

        Returns:
            MetadataFilter object

        Raises:
            MetadataFilterSecurityError: If any filter component is malicious

        Examples:
            >>> parser = FilterParser()
            >>> filter = parser.parse("tag=python")
            >>> filter = parser.parse("tag=python,java confidence>0.9")
            >>> filter = parser.parse("date>=2023-01-01 author=Smith")
        """
        metadata_filter = MetadataFilter()

        if not filter_string or not filter_string.strip():
            return metadata_filter

        # Split by whitespace (each part is a filter condition)
        parts = filter_string.strip().split()

        for part in parts:
            match = cls.FILTER_PATTERN.match(part)
            if not match:
                logger.warning(f"Invalid filter expression: {part}")
                continue

            field, operator, value_str = match.groups()

            # Normalize operator (= becomes ==)
            if operator == "=":
                operator = "=="

            try:
                # Parse value
                value = cls._parse_value(value_str, field)

                # Check for multiple values (OR within field)
                if isinstance(value, str) and "," in value:
                    values = [cls._parse_value(v.strip(), field) for v in value.split(",")]
                    metadata_filter.add_condition(field, "in", values)
                else:
                    metadata_filter.add_condition(field, operator, value)

            except MetadataFilterSecurityError as e:
                # Log and skip malicious filter
                logger.warning(f"Rejected malicious filter '{part}': {e}")
                continue

        return metadata_filter

    @classmethod
    def parse_cli_filters(
        cls,
        tag: str | None = None,
        author: str | None = None,
        file_type: str | None = None,
        date_after: str | None = None,
        date_before: str | None = None,
        confidence: str | None = None,
        **kwargs: Any,
    ) -> MetadataFilter:
        """
        Parse CLI-style filter arguments.

        SECURITY FIX (HIGH-4): All filter values validated via FilterCondition.

        Args:
            tag: Tag filter (comma-separated for OR)
            author: Author name filter
            file_type: File type filter (pdf, txt, md, etc.)
            date_after: Date range start (YYYY-MM-DD)
            date_before: Date range end (YYYY-MM-DD)
            confidence: Confidence threshold (e.g., ">0.9", ">=0.95")
            **kwargs: Additional custom filters

        Returns:
            MetadataFilter object

        Raises:
            MetadataFilterSecurityError: If any filter component is malicious

        Example:
            >>> parser = FilterParser()
            >>> filter = parser.parse_cli_filters(
            ...     tag="python,java",
            ...     author="Smith",
            ...     confidence=">0.9"
            ... )
        """
        metadata_filter = MetadataFilter()

        # Tag filter (OR for multiple tags)
        if tag:
            tags = [t.strip() for t in tag.split(",")]
            if len(tags) == 1:
                metadata_filter.add_condition("tag", "==", tags[0])
            else:
                metadata_filter.add_condition("tag", "in", tags)

        # Author filter
        if author:
            metadata_filter.add_condition("author", "==", author)

        # File type filter
        if file_type:
            # Normalize file type (remove leading dot)
            ft = file_type.lstrip(".")
            metadata_filter.add_condition("file_type", "==", ft)

        # Date filters
        if date_after:
            try:
                date = datetime.strptime(date_after, "%Y-%m-%d").isoformat()
                metadata_filter.add_condition("date", ">=", date)
            except ValueError:
                logger.warning(f"Invalid date format: {date_after} (use YYYY-MM-DD)")

        if date_before:
            try:
                date = datetime.strptime(date_before, "%Y-%m-%d").isoformat()
                metadata_filter.add_condition("date", "<=", date)
            except ValueError:
                logger.warning(f"Invalid date format: {date_before} (use YYYY-MM-DD)")

        # Confidence filter (supports comparisons like ">0.9")
        if confidence is not None:
            # Convert to string if numeric
            confidence_str = str(confidence) if isinstance(confidence, (int, float)) else confidence

            if confidence_str.startswith((">=", "<=", ">", "<", "==", "!=")):
                # Extract operator and value
                for op in [">=", "<=", "==", "!=", ">", "<"]:
                    if confidence_str.startswith(op):
                        value = float(confidence_str[len(op):].strip())
                        metadata_filter.add_condition("confidence", op, value)
                        break
            else:
                # Assume equality
                metadata_filter.add_condition("confidence", "==", float(confidence_str))

        # Additional custom filters
        for key, value in kwargs.items():
            if value is not None:
                metadata_filter.add_condition(key, "==", value)

        return metadata_filter

    @classmethod
    def _parse_value(cls, value_str: str, field: str) -> Any:
        """
        Parse value string to appropriate type.

        Args:
            value_str: String value
            field: Field name (hint for type inference)

        Returns:
            Typed value
        """
        value_str = value_str.strip()

        # Try to infer type
        # Boolean
        if value_str.lower() in ("true", "false"):
            return value_str.lower() == "true"

        # Float (for confidence, score, etc.)
        if field in ("confidence", "score") or "." in value_str:
            try:
                return float(value_str)
            except ValueError:
                pass

        # Integer
        try:
            return int(value_str)
        except ValueError:
            pass

        # Date (YYYY-MM-DD format)
        if re.match(r'\d{4}-\d{2}-\d{2}', value_str):
            try:
                return datetime.strptime(value_str, "%Y-%m-%d").isoformat()
            except ValueError:
                pass

        # Default: string (remove quotes if present)
        return value_str.strip('"\'')


class FacetedSearch:
    """
    Faceted search interface for exploring available filter values.

    Provides statistics on metadata fields to help users discover
    what filters are available.
    """

    @staticmethod
    def get_facets(
        vector_store: Any,
        fields: list[str] | None = None,
    ) -> dict[str, list[Any]]:
        """
        Get available values for metadata fields (facets).

        Args:
            vector_store: Vector store instance
            fields: Specific fields to get facets for (None = all fields)

        Returns:
            Dictionary mapping field names to lists of unique values

        Example:
            >>> facets = FacetedSearch.get_facets(vector_store, fields=["tag", "author"])
            >>> print(f"Available tags: {facets['tag']}")
            >>> print(f"Available authors: {facets['author']}")

        TODO: Implement facet extraction from vector store metadata
        """
        # Placeholder for v0.3.7d
        # Will need vector store API to extract unique metadata values
        facets: dict[str, list[Any]] = {}

        # Common facets (placeholders)
        if fields is None or "tag" in fields:
            facets["tag"] = []
        if fields is None or "author" in fields:
            facets["author"] = []
        if fields is None or "file_type" in fields:
            facets["file_type"] = []

        return facets

    @staticmethod
    def count_facet_values(
        vector_store: Any,
        field: str,
    ) -> dict[Any, int]:
        """
        Count occurrences of each value in a metadata field.

        Args:
            vector_store: Vector store instance
            field: Metadata field to count

        Returns:
            Dictionary mapping values to counts

        Example:
            >>> counts = FacetedSearch.count_facet_values(vector_store, "tag")
            >>> for tag, count in counts.items():
            ...     print(f"{tag}: {count} documents")

        TODO: Implement facet counting from vector store metadata
        """
        # Placeholder for v0.3.7d
        return {}


# Convenience function for quick filter creation
def create_filter(**kwargs: Any) -> MetadataFilter:
    """
    Create a metadata filter from keyword arguments.

    Args:
        **kwargs: Field=value pairs

    Returns:
        MetadataFilter object

    Example:
        >>> filter = create_filter(tag="python", confidence=0.9)
        >>> filter = create_filter(author="Smith", date_after="2023-01-01")
    """
    return FilterParser.parse_cli_filters(**kwargs)
