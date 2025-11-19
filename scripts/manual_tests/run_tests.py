#!/usr/bin/env python3
"""
Manual test runner with filtering capabilities.

Provides a convenient interface for running manual tests with various filters:
- By version (v0.2.9, v0.2.8, etc.)
- By test type (smoke, regression, workflow, performance)
- By feature (cli, formatting, ingestion, etc.)
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


VERSIONS = [
    "v0.2.4",
    "v0.2.5",
    "v0.2.7",
    "v0.2.8",
    "v0.2.9",
    "v0.2.10",
    "v0.2.11",
]

TEST_TYPES = [
    "smoke",
    "regression",
    "workflow",
    "performance",
    "interactive",
]

FEATURES = [
    "cli",
    "formatting",
    "completion",
    "validation",
    "monitoring",
    "folder_ingestion",
    "html_processing",
    "modular_cli",
    "settings_refactor",
    "error_handling",
    "type_safety",
    "web_ui",
    "hybrid_retrieval",
    "gradio",
    "fastapi",
    "performance",
    "chunking",
    "test_coverage",
    "cold_start",
]


def build_pytest_command(
    version: Optional[str] = None,
    test_type: Optional[str] = None,
    feature: Optional[str] = None,
    path: Optional[str] = None,
    verbose: bool = False,
    html_report: Optional[str] = None,
    markers: Optional[str] = None,
) -> List[str]:
    """
    Build pytest command with appropriate filters.

    Args:
        version: Version to test (e.g., "v0.2.9")
        test_type: Test type (smoke, regression, workflow, performance)
        feature: Feature to test (cli, formatting, etc.)
        path: Specific path to test
        verbose: Verbose output
        html_report: Path to HTML report output
        markers: Additional pytest markers

    Returns:
        List of command arguments for subprocess
    """
    cmd = ["pytest"]

    # Determine path
    if path:
        cmd.append(path)
    elif version:
        cmd.append(f"scripts/manual_tests/version/{version}/")
    elif test_type == "regression":
        cmd.append("scripts/manual_tests/regression/")
    elif test_type == "workflow":
        cmd.append("scripts/manual_tests/workflows/")
    elif test_type == "performance":
        cmd.append("scripts/manual_tests/performance/benchmarks/")
    else:
        cmd.append("scripts/manual_tests/")

    # Build marker expression
    marker_expressions = []

    if test_type and test_type in TEST_TYPES:
        marker_expressions.append(test_type)

    if feature:
        marker_expressions.append(f'feature("{feature}")')

    if version:
        marker_expressions.append(f'version("{version}")')

    if markers:
        marker_expressions.append(markers)

    if marker_expressions:
        marker_expr = " and ".join(marker_expressions)
        cmd.extend(["-m", marker_expr])

    # Additional options
    if verbose:
        cmd.append("-v")

    if html_report:
        cmd.append(f"--html={html_report}")
        cmd.append("--self-contained-html")

    return cmd


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Run manual tests with filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all smoke tests
  python run_tests.py --type smoke

  # Run tests for specific version
  python run_tests.py --version v0.2.9

  # Run smoke tests for specific version
  python run_tests.py --version v0.2.9 --type smoke

  # Run tests for specific feature across all versions
  python run_tests.py --feature cli

  # Run regression tests
  python run_tests.py --type regression

  # Run performance benchmarks
  python run_tests.py --type performance

  # Generate HTML report
  python run_tests.py --type smoke --html reports/smoke_tests.html

  # Run specific test file
  python run_tests.py --path version/v0.2.9/smoke_test.py
        """
    )

    parser.add_argument(
        "--version",
        choices=VERSIONS,
        help="Version to test"
    )

    parser.add_argument(
        "--type",
        choices=TEST_TYPES,
        help="Test type to run"
    )

    parser.add_argument(
        "--feature",
        choices=FEATURES,
        help="Feature to test"
    )

    parser.add_argument(
        "--path",
        help="Specific test path"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--html",
        help="Generate HTML report at specified path"
    )

    parser.add_argument(
        "--markers",
        help="Additional pytest markers (e.g., 'not slow')"
    )

    parser.add_argument(
        "--list-versions",
        action="store_true",
        help="List available versions"
    )

    parser.add_argument(
        "--list-features",
        action="store_true",
        help="List available features"
    )

    parser.add_argument(
        "--list-types",
        action="store_true",
        help="List available test types"
    )

    args = parser.parse_args()

    # Handle list commands
    if args.list_versions:
        print("Available versions:")
        for version in VERSIONS:
            print(f"  - {version}")
        return 0

    if args.list_features:
        print("Available features:")
        for feature in FEATURES:
            print(f"  - {feature}")
        return 0

    if args.list_types:
        print("Available test types:")
        for test_type in TEST_TYPES:
            print(f"  - {test_type}")
        return 0

    # Build and run pytest command
    cmd = build_pytest_command(
        version=args.version,
        test_type=args.type,
        feature=args.feature,
        path=args.path,
        verbose=args.verbose,
        html_report=args.html,
        markers=args.markers,
    )

    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
