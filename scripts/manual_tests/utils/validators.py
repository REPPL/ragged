"""
Result validation functions for manual tests.

Provides validation logic for test assertions and result verification.
"""

from typing import Any, Dict, List, Optional, Tuple, Union


# ============================================================================
# Schema Validation
# ============================================================================

def validate_schema(
    data: Dict,
    schema: Dict[str, type],
    strict: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate data against a schema.

    Args:
        data: Data to validate
        schema: Expected schema (field_name: type)
        strict: If True, data must have exactly the fields in schema

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        response = {"answer": "...", "sources": []}
        is_valid, errors = validate_schema(
            response,
            {"answer": str, "sources": list}
        )
    """
    errors = []

    # Check required fields
    for field, expected_type in schema.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(
                f"Field '{field}' has wrong type: "
                f"expected {expected_type.__name__}, got {type(data[field]).__name__}"
            )

    # Check for extra fields in strict mode
    if strict:
        for field in data:
            if field not in schema:
                errors.append(f"Unexpected field: {field}")

    return len(errors) == 0, errors


# ============================================================================
# Query Result Validation
# ============================================================================

def validate_query_results(
    results: Dict,
    min_sources: Optional[int] = None,
    max_sources: Optional[int] = None,
    required_fields: Optional[List[str]] = None,
    validate_sources: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate query results structure and content.

    Args:
        results: Query results dictionary
        min_sources: Minimum number of sources required
        max_sources: Maximum number of sources allowed
        required_fields: List of required fields in results
        validate_sources: Whether to validate source structure

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        is_valid, errors = validate_query_results(
            results,
            min_sources=3,
            required_fields=["answer", "sources", "metadata"]
        )
    """
    errors = []

    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in results:
                errors.append(f"Missing required field: {field}")

    # Check sources
    if "sources" in results:
        sources = results["sources"]

        if not isinstance(sources, list):
            errors.append(f"Sources must be a list, got {type(sources).__name__}")
        else:
            num_sources = len(sources)

            if min_sources is not None and num_sources < min_sources:
                errors.append(f"Too few sources: {num_sources} < {min_sources}")

            if max_sources is not None and num_sources > max_sources:
                errors.append(f"Too many sources: {num_sources} > {max_sources}")

            # Validate source structure
            if validate_sources:
                for i, source in enumerate(sources):
                    if not isinstance(source, dict):
                        errors.append(f"Source {i} must be a dict")
                    elif "content" not in source:
                        errors.append(f"Source {i} missing 'content' field")

    # Check answer
    if "answer" in results:
        answer = results["answer"]
        if not isinstance(answer, str):
            errors.append(f"Answer must be a string, got {type(answer).__name__}")
        elif len(answer.strip()) == 0:
            errors.append("Answer is empty")

    return len(errors) == 0, errors


# ============================================================================
# Document Ingestion Validation
# ============================================================================

def validate_document_ingestion(
    document_id: str,
    expected_chunks: Optional[int] = None,
    expected_metadata: Optional[Dict] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that a document was ingested correctly.

    Args:
        document_id: ID of ingested document
        expected_chunks: Expected number of chunks
        expected_metadata: Expected metadata fields

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        is_valid, errors = validate_document_ingestion(
            "doc_123",
            expected_chunks=5,
            expected_metadata={"title": "Test Doc"}
        )
    """
    errors = []

    # Note: This would need to query the actual ragged instance
    # to verify the document was ingested correctly.
    # Placeholder implementation:

    if not document_id:
        errors.append("Document ID is empty")

    # TODO: Implement actual validation when ragged API is available
    # - Check document exists in vector store
    # - Verify chunk count
    # - Validate metadata

    return len(errors) == 0, errors


# ============================================================================
# Metadata Validation
# ============================================================================

def validate_metadata(
    metadata: Dict,
    required_fields: Optional[List[str]] = None,
    field_types: Optional[Dict[str, type]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate document metadata.

    Args:
        metadata: Metadata dictionary
        required_fields: List of required fields
        field_types: Expected types for fields

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        is_valid, errors = validate_metadata(
            metadata,
            required_fields=["title", "author"],
            field_types={"title": str, "page_count": int}
        )
    """
    errors = []

    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Missing required metadata field: {field}")

    # Check field types
    if field_types:
        for field, expected_type in field_types.items():
            if field in metadata and not isinstance(metadata[field], expected_type):
                errors.append(
                    f"Metadata field '{field}' has wrong type: "
                    f"expected {expected_type.__name__}, got {type(metadata[field]).__name__}"
                )

    return len(errors) == 0, errors


# ============================================================================
# Performance Validation
# ============================================================================

def validate_performance(
    metric: str,
    value: float,
    baseline: float,
    tolerance: float = 0.1
) -> bool:
    """
    Validate performance against baseline with tolerance.

    Args:
        metric: Metric name (for error messages)
        value: Current value
        baseline: Baseline value to compare against
        tolerance: Acceptable deviation (0.1 = 10%)

    Returns:
        True if within tolerance, False otherwise

    Example:
        assert validate_performance(
            "query_latency_ms",
            value=220,
            baseline=200,
            tolerance=0.2  # 20% tolerance
        )
    """
    max_value = baseline * (1 + tolerance)
    return value <= max_value


def detect_regression(
    current: Dict[str, float],
    baseline: Dict[str, float],
    tolerance: float = 0.1
) -> Optional[Dict[str, Dict[str, float]]]:
    """
    Detect performance regressions by comparing current vs baseline metrics.

    Args:
        current: Current performance metrics
        baseline: Baseline performance metrics
        tolerance: Acceptable deviation (0.1 = 10%)

    Returns:
        Dictionary of regressions (metric -> details) or None if no regressions

    Example:
        regression = detect_regression(
            current={"latency_ms": 250},
            baseline={"latency_ms": 200},
            tolerance=0.1
        )
        if regression:
            print(f"Regressions found: {regression}")
    """
    regressions = {}

    for metric, baseline_value in baseline.items():
        if metric not in current:
            continue

        current_value = current[metric]
        max_value = baseline_value * (1 + tolerance)

        if current_value > max_value:
            change_percent = ((current_value - baseline_value) / baseline_value) * 100
            regressions[metric] = {
                "baseline": baseline_value,
                "current": current_value,
                "change_percent": change_percent,
                "threshold": max_value,
            }

    return regressions if regressions else None


# ============================================================================
# Error Message Validation
# ============================================================================

def validate_error_message(
    error_message: str,
    expected_keywords: Optional[List[str]] = None,
    min_length: int = 10,
    max_length: int = 500
) -> Tuple[bool, List[str]]:
    """
    Validate error message quality.

    Args:
        error_message: Error message to validate
        expected_keywords: Keywords that should appear in message
        min_length: Minimum message length
        max_length: Maximum message length

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        is_valid, errors = validate_error_message(
            error,
            expected_keywords=["service", "unavailable"],
            min_length=20
        )
    """
    errors = []

    # Check length
    if len(error_message) < min_length:
        errors.append(f"Error message too short: {len(error_message)} < {min_length}")

    if len(error_message) > max_length:
        errors.append(f"Error message too long: {len(error_message)} > {max_length}")

    # Check keywords
    if expected_keywords:
        for keyword in expected_keywords:
            if keyword.lower() not in error_message.lower():
                errors.append(f"Error message missing keyword: '{keyword}'")

    return len(errors) == 0, errors


# ============================================================================
# API Response Validation
# ============================================================================

def validate_api_response(
    response: Dict,
    expected_status: int = 200,
    required_fields: Optional[List[str]] = None,
    error_on_extra_fields: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate API response structure.

    Args:
        response: API response dictionary
        expected_status: Expected HTTP status code
        required_fields: List of required fields
        error_on_extra_fields: Error if response has unexpected fields

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        is_valid, errors = validate_api_response(
            response,
            expected_status=200,
            required_fields=["status", "data"]
        )
    """
    errors = []

    # Check status code
    if "status_code" in response:
        if response["status_code"] != expected_status:
            errors.append(
                f"Wrong status code: {response['status_code']} != {expected_status}"
            )

    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in response:
                errors.append(f"Missing required field: {field}")

    # Check for extra fields
    if error_on_extra_fields and required_fields:
        for field in response:
            if field not in required_fields and field != "status_code":
                errors.append(f"Unexpected field: {field}")

    return len(errors) == 0, errors


# ============================================================================
# Result Comparison
# ============================================================================

def compare_results(
    actual: Any,
    expected: Any,
    tolerance: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Compare actual vs expected results with optional tolerance for floats.

    Args:
        actual: Actual result
        expected: Expected result
        tolerance: Tolerance for float comparison (absolute difference)

    Returns:
        Tuple of (matches, difference_description)

    Example:
        matches, diff = compare_results(
            actual=0.95,
            expected=1.0,
            tolerance=0.1
        )
        assert matches, diff
    """
    if type(actual) != type(expected):
        return False, f"Type mismatch: {type(actual).__name__} != {type(expected).__name__}"

    if isinstance(actual, float) and isinstance(expected, float):
        if tolerance is not None:
            diff = abs(actual - expected)
            if diff <= tolerance:
                return True, ""
            else:
                return False, f"Float difference {diff} > tolerance {tolerance}"

    if actual == expected:
        return True, ""
    else:
        return False, f"Values don't match: {actual} != {expected}"
