"""Security tests to prevent pickle usage and ensure safe serialization.

v0.2.10 FEAT-SEC-001: Automated detection of unsafe serialization patterns.

This test suite ensures:
1. No pickle imports in production code (except migration utilities)
2. No pickle.load() or pickle.dump() calls in production code
3. No .pkl files in cache/checkpoint directories
4. Safe JSON serialization works correctly
5. Migration from legacy pickle files works

Security Context:
- CRITICAL-001: Pickle arbitrary code execution vulnerability
- CVSS 9.8: Remote code execution through crafted pickle files
"""

import re
from pathlib import Path
from typing import List, Set

import pytest
import numpy as np

from src.utils.serialization import (
    save_json,
    load_json,
    save_bm25_index,
    load_bm25_index,
    numpy_array_to_list,
    list_to_numpy_array,
)


# Test Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
ALLOWED_PICKLE_FILES = {
    # Migration utilities are allowed to import pickle temporarily
    "src/utils/serialization.py",  # Contains migrate_pickle_to_json()
    # Legacy files during migration (remove after migration complete)
    "src/retrieval/incremental_index.py",  # Temporary for legacy .pkl migration
    "src/utils/multi_tier_cache.py",  # Temporary for legacy .pkl migration
}


class TestPickleBan:
    """Test suite for pickle usage detection."""

    def test_no_pickle_imports_in_production_code(self) -> None:
        """Ensure no production code imports pickle (except allowed migration files).

        Security: Prevents reintroduction of CRITICAL-001 vulnerability.
        """
        violations: List[str] = []

        # Scan all Python files
        for py_file in SRC_DIR.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            # Check if file is allowed to use pickle
            relative_path = str(py_file.relative_to(PROJECT_ROOT))
            if relative_path in ALLOWED_PICKLE_FILES:
                continue

            # Read file content
            content = py_file.read_text(encoding="utf-8")

            # Check for pickle imports (various forms)
            patterns = [
                r"^\s*import\s+pickle\s*$",  # import pickle
                r"^\s*from\s+pickle\s+import",  # from pickle import ...
                r"^\s*import\s+pickle\s+as",  # import pickle as ...
            ]

            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE):
                    violations.append(
                        f"{relative_path}: Contains pickle import (pattern: {pattern})"
                    )

        # Assert no violations found
        if violations:
            violation_msg = "\n".join(violations)
            pytest.fail(
                f"Pickle imports found in production code:\n{violation_msg}\n\n"
                f"Only these files are allowed to import pickle for migration:\n"
                f"{ALLOWED_PICKLE_FILES}\n\n"
                f"If you need to add a new migration utility, update ALLOWED_PICKLE_FILES."
            )

    def test_no_pickle_calls_in_production_code(self) -> None:
        """Ensure no production code calls pickle.load() or pickle.dump().

        Security: Even with allowed imports, verify pickle is only used in controlled migration contexts.
        """
        violations: List[str] = []

        for py_file in SRC_DIR.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text(encoding="utf-8")
            relative_path = str(py_file.relative_to(PROJECT_ROOT))

            # Check for pickle.load() or pickle.dump() calls
            patterns = [
                (r"pickle\.load\(", "pickle.load()"),
                (r"pickle\.dump\(", "pickle.dump()"),
                (r"pickle\.loads\(", "pickle.loads()"),
                (r"pickle\.dumps\(", "pickle.dumps()"),
            ]

            for pattern, description in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Check if it's in a migration context (has noqa: S301 comment)
                    line_start = content.rfind("\n", 0, match.start()) + 1
                    line_end = content.find("\n", match.end())
                    line = content[line_start:line_end] if line_end != -1 else content[line_start:]

                    # Allow if it has security exception comment
                    if "noqa: S301" in line or "migration only" in line.lower():
                        continue

                    # Get line number
                    line_num = content[:match.start()].count("\n") + 1

                    violations.append(
                        f"{relative_path}:{line_num}: Contains {description} "
                        f"(missing noqa: S301 migration marker)"
                    )

        if violations:
            violation_msg = "\n".join(violations)
            pytest.fail(
                f"Unsafe pickle calls found (not marked as migration):\n{violation_msg}\n\n"
                f"If this is a migration utility, add '# noqa: S301 (migration only)' comment."
            )

    def test_no_legacy_pickle_cache_files(self, tmp_path: Path) -> None:
        """Ensure no .pkl cache files exist in test environment.

        This verifies that migration from pickle to JSON is complete.
        """
        # Check various cache directories
        cache_dirs = [
            PROJECT_ROOT / ".ragged" / "checkpoints",
            PROJECT_ROOT / ".ragged" / "cache",
            tmp_path / "checkpoints",
            tmp_path / "cache",
        ]

        pkl_files: List[str] = []

        for cache_dir in cache_dirs:
            if not cache_dir.exists():
                continue

            for pkl_file in cache_dir.rglob("*.pkl"):
                pkl_files.append(str(pkl_file.relative_to(PROJECT_ROOT)))

        if pkl_files:
            files_msg = "\n".join(pkl_files)
            pytest.fail(
                f"Legacy .pkl files found:\n{files_msg}\n\n"
                f"These should be migrated to .json format for security.\n"
                f"Run migration utility or delete legacy files."
            )

    def test_no_banned_functions(self) -> None:
        """Ensure no code uses other dangerous functions (eval, exec, __import__).

        Security: Prevents arbitrary code execution through other vectors.
        """
        violations: List[str] = []

        banned_patterns = [
            (r"\beval\(", "eval()"),
            (r"\bexec\(", "exec()"),
            (r"\b__import__\(", "__import__()"),
            (r"\bcompile\(", "compile()"),  # Can lead to code execution
        ]

        for py_file in SRC_DIR.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text(encoding="utf-8")
            relative_path = str(py_file.relative_to(PROJECT_ROOT))

            for pattern, description in banned_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    # Check if it's in a comment or string
                    line_start = content.rfind("\n", 0, match.start()) + 1
                    line_end = content.find("\n", match.end())
                    line = content[line_start:line_end] if line_end != -1 else content[line_start:]

                    # Skip if in comment
                    if "#" in line and line.index("#") < match.start() - line_start:
                        continue

                    line_num = content[:match.start()].count("\n") + 1
                    violations.append(f"{relative_path}:{line_num}: Uses {description}")

        if violations:
            violation_msg = "\n".join(violations)
            pytest.fail(
                f"Banned functions found:\n{violation_msg}\n\n"
                f"These functions can lead to arbitrary code execution.\n"
                f"Use safer alternatives or add security exception if absolutely necessary."
            )


class TestSafeJSONSerialization:
    """Test suite for safe JSON serialization utilities."""

    def test_save_and_load_json(self, tmp_path: Path) -> None:
        """Test basic JSON save/load functionality."""
        test_file = tmp_path / "test.json"
        test_data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        # Save and load
        save_json(test_data, test_file)
        loaded_data = load_json(test_file)

        assert loaded_data == test_data
        assert test_file.exists()
        assert test_file.suffix == ".json"

    def test_numpy_array_conversion(self) -> None:
        """Test numpy array to list conversion for JSON serialization."""
        # Test various numpy array types
        test_cases = [
            np.array([1, 2, 3], dtype=np.int32),
            np.array([1.0, 2.0, 3.0], dtype=np.float32),
            np.array([[1, 2], [3, 4]], dtype=np.int64),
            np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]], dtype=np.float64),
        ]

        for arr in test_cases:
            # Convert to list
            list_repr = numpy_array_to_list(arr)
            assert isinstance(list_repr, list)

            # Convert back to numpy array
            restored_arr = list_to_numpy_array(list_repr, dtype=arr.dtype)
            assert isinstance(restored_arr, np.ndarray)
            assert restored_arr.dtype == arr.dtype
            assert restored_arr.shape == arr.shape
            np.testing.assert_array_equal(restored_arr, arr)

    def test_bm25_index_serialization(self, tmp_path: Path) -> None:
        """Test BM25 index save/load without pickle."""
        checkpoint_file = tmp_path / "bm25_checkpoint.json"

        # Create test BM25 data
        corpus_processed = [
            ["hello", "world"],
            ["foo", "bar", "baz"],
            ["test", "document"],
        ]
        idf = {"hello": 1.5, "world": 1.2, "foo": 2.0, "bar": 1.8, "baz": 1.1}
        doc_len = [2, 3, 2]
        avgdl = 2.33

        # Save BM25 index
        save_bm25_index(corpus_processed, idf, doc_len, avgdl, checkpoint_file)
        assert checkpoint_file.exists()
        assert checkpoint_file.suffix == ".json"

        # Load BM25 index
        loaded_corpus, loaded_idf, loaded_doc_len, loaded_avgdl = load_bm25_index(
            checkpoint_file
        )

        # Verify data matches
        assert loaded_corpus == corpus_processed
        assert loaded_idf == idf
        assert loaded_doc_len == doc_len
        assert loaded_avgdl == avgdl

    def test_json_files_not_executable(self, tmp_path: Path) -> None:
        """Verify that JSON files cannot execute arbitrary code when loaded.

        This is the key security advantage over pickle.
        """
        malicious_json = tmp_path / "malicious.json"

        # Create JSON with Python-like code (should be treated as string data, not code)
        malicious_content = '''
        {
            "code": "__import__('os').system('echo hacked')",
            "eval": "eval('1+1')",
            "import": "import pickle"
        }
        '''
        malicious_json.write_text(malicious_content)

        # Load the "malicious" JSON
        data = load_json(malicious_json)

        # Verify it's just string data, not executed code
        assert isinstance(data, dict)
        assert "__import__" in data["code"]
        assert "eval" in data["eval"]
        assert "import" in data["import"]
        # If pickle was used, this would have executed arbitrary code!


class TestLegacyPickleMigration:
    """Test suite for legacy pickle file migration."""

    @pytest.mark.skip(reason="Migration function uses pickle - only for trusted legacy files")
    def test_pickle_migration_warning(self) -> None:
        """Document that pickle migration should only be used on trusted files.

        This test serves as documentation and can be enabled if manual migration is needed.
        """
        # This is a documentation test - the actual migrate_pickle_to_json()
        # function should only be run manually on trusted legacy ragged files
        assert True, (
            "migrate_pickle_to_json() should only be used on trusted legacy files. "
            "Never use it on pickle files from untrusted sources."
        )


class TestSecurityRegression:
    """Test suite to prevent security regressions."""

    def test_no_new_serialization_modules(self) -> None:
        """Ensure no new unsafe serialization modules are introduced.

        Checks for: marshal, shelve, dill, cloudpickle (all unsafe like pickle).
        """
        unsafe_modules = ["marshal", "shelve", "dill", "cloudpickle"]
        violations: List[str] = []

        for py_file in SRC_DIR.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text(encoding="utf-8")
            relative_path = str(py_file.relative_to(PROJECT_ROOT))

            for module in unsafe_modules:
                pattern = rf"^\s*import\s+{module}\s*$"
                if re.search(pattern, content, re.MULTILINE):
                    violations.append(f"{relative_path}: Imports unsafe module '{module}'")

        if violations:
            violation_msg = "\n".join(violations)
            pytest.fail(
                f"Unsafe serialization modules found:\n{violation_msg}\n\n"
                f"Use JSON serialization instead (src/utils/serialization.py)."
            )

    def test_json_serialization_preferred(self) -> None:
        """Verify that new code uses safe JSON serialization utilities.

        Ensures imports from src.utils.serialization, not pickle/marshal.
        """
        # Check that serialization utilities are used in key modules
        modules_requiring_serialization = [
            SRC_DIR / "retrieval" / "incremental_index.py",
            SRC_DIR / "utils" / "multi_tier_cache.py",
        ]

        for module_file in modules_requiring_serialization:
            if not module_file.exists():
                continue

            content = module_file.read_text(encoding="utf-8")

            # Verify it imports from src.utils.serialization
            assert (
                "from src.utils.serialization import" in content
            ), f"{module_file.name} should use src.utils.serialization for safe serialization"


# Mark all tests as security tests
pytestmark = pytest.mark.security
