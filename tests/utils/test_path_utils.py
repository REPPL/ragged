"""Tests for path handling utilities."""

import pytest
from pathlib import Path
from src.utils.path_utils import (
    normalize_path,
    validate_path_exists,
    safe_join,
    validate_file_extension,
    ensure_directory,
    get_relative_path,
    validate_directory_not_empty,
    is_hidden_path,
    sanitize_filename,
    get_file_size_mb,
    get_directory_size_mb,
)
from src.exceptions import InvalidPathError, ResourceNotFoundError


@pytest.fixture
def temp_structure(tmp_path):
    """Create temporary directory structure for testing."""
    # Create files
    (tmp_path / "file.txt").write_text("test content")
    (tmp_path / "document.pdf").write_text("PDF content")
    (tmp_path / "README.md").write_text("# README")

    # Create directories
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("Guide")

    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "secret.txt").write_text("secret")

    (tmp_path / "empty_dir").mkdir()

    return tmp_path


class TestNormalizePath:
    """Tests for normalize_path."""

    def test_absolute_path(self, tmp_path):
        """Test normalizing absolute path."""
        result = normalize_path(tmp_path)
        assert result.is_absolute()
        assert result == tmp_path

    def test_relative_path(self):
        """Test normalizing relative path."""
        result = normalize_path(".")
        assert result.is_absolute()

    def test_str_to_path(self, tmp_path):
        """Test converting string to Path."""
        result = normalize_path(str(tmp_path))
        assert isinstance(result, Path)
        assert result == tmp_path

    def test_user_expansion(self, monkeypatch):
        """Test that ~ is expanded."""
        result = normalize_path("~/test")
        assert "~" not in str(result)


class TestValidatePathExists:
    """Tests for validate_path_exists."""

    def test_existing_file(self, temp_structure):
        """Test validating existing file."""
        file_path = temp_structure / "file.txt"
        result = validate_path_exists(file_path)
        assert result == file_path.resolve()

    def test_existing_directory(self, temp_structure):
        """Test validating existing directory."""
        dir_path = temp_structure / "docs"
        result = validate_path_exists(dir_path)
        assert result == dir_path.resolve()

    def test_nonexistent_path(self, tmp_path):
        """Test that nonexistent path raises error."""
        with pytest.raises(ResourceNotFoundError) as exc:
            validate_path_exists(tmp_path / "nonexistent.txt")
        assert "does not exist" in str(exc.value)

    def test_must_be_file_success(self, temp_structure):
        """Test must_be_file with actual file."""
        file_path = temp_structure / "file.txt"
        result = validate_path_exists(file_path, must_be_file=True)
        assert result.is_file()

    def test_must_be_file_failure(self, temp_structure):
        """Test must_be_file with directory."""
        dir_path = temp_structure / "docs"
        with pytest.raises(ResourceNotFoundError) as exc:
            validate_path_exists(dir_path, must_be_file=True)
        assert "not a file" in str(exc.value)

    def test_must_be_dir_success(self, temp_structure):
        """Test must_be_dir with actual directory."""
        dir_path = temp_structure / "docs"
        result = validate_path_exists(dir_path, must_be_dir=True)
        assert result.is_dir()

    def test_must_be_dir_failure(self, temp_structure):
        """Test must_be_dir with file."""
        file_path = temp_structure / "file.txt"
        with pytest.raises(ResourceNotFoundError) as exc:
            validate_path_exists(file_path, must_be_dir=True)
        assert "not a directory" in str(exc.value)

    def test_conflicting_requirements(self):
        """Test that both must_be_file and must_be_dir raises error."""
        with pytest.raises(InvalidPathError):
            validate_path_exists("/tmp", must_be_file=True, must_be_dir=True)


class TestSafeJoin:
    """Tests for safe_join."""

    def test_simple_join(self, tmp_path):
        """Test simple path joining."""
        result = safe_join(tmp_path, "subdir", "file.txt")
        expected = tmp_path / "subdir" / "file.txt"
        assert result == expected.resolve()

    def test_prevents_traversal_dotdot(self, tmp_path):
        """Test prevention of .. traversal."""
        with pytest.raises(InvalidPathError) as exc:
            safe_join(tmp_path, "..", "etc", "passwd")
        assert "traversal" in str(exc.value).lower()

    def test_prevents_absolute_path(self, tmp_path):
        """Test prevention of absolute path injection."""
        with pytest.raises(InvalidPathError):
            safe_join(tmp_path, "/etc/passwd")

    def test_allows_relative_within_base(self, tmp_path):
        """Test that relative paths within base are allowed."""
        result = safe_join(tmp_path, "a/../b/file.txt")
        expected = tmp_path / "b" / "file.txt"
        assert result == expected.resolve()


class TestValidateFileExtension:
    """Tests for validate_file_extension."""

    def test_valid_extension(self, temp_structure):
        """Test file with valid extension."""
        file_path = temp_structure / "document.pdf"
        result = validate_file_extension(file_path, [".pdf", ".txt"])
        assert result == file_path.resolve()

    def test_invalid_extension(self, temp_structure):
        """Test file with invalid extension."""
        file_path = temp_structure / "document.pdf"
        with pytest.raises(InvalidPathError) as exc:
            validate_file_extension(file_path, [".txt", ".md"])
        assert "not allowed" in str(exc.value)
        assert ".pdf" in str(exc.value)

    def test_case_insensitive(self, temp_structure):
        """Test that extension check is case-insensitive."""
        file_path = temp_structure / "README.MD"  # uppercase
        file_path.write_text("test")
        result = validate_file_extension(file_path, [".md"])
        assert result == file_path.resolve()

    def test_extensions_without_dot(self, temp_structure):
        """Test extensions specified without leading dot."""
        file_path = temp_structure / "file.txt"
        result = validate_file_extension(file_path, ["txt", "md"])
        assert result == file_path.resolve()


class TestEnsureDirectory:
    """Tests for ensure_directory."""

    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "newdir"
        result = ensure_directory(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_existing_directory(self, temp_structure):
        """Test with existing directory."""
        existing = temp_structure / "docs"
        result = ensure_directory(existing)
        assert result == existing.resolve()

    def test_create_nested_directories(self, tmp_path):
        """Test creating nested directories with parents=True."""
        nested = tmp_path / "a" / "b" / "c"
        result = ensure_directory(nested, parents=True)
        assert result.exists()
        assert result.is_dir()

    def test_fails_without_parents(self, tmp_path):
        """Test that creation fails without parents=True."""
        nested = tmp_path / "a" / "b" / "c"
        with pytest.raises(InvalidPathError):
            ensure_directory(nested, parents=False)

    def test_path_exists_as_file(self, temp_structure):
        """Test error when path exists as file."""
        file_path = temp_structure / "file.txt"
        with pytest.raises(InvalidPathError) as exc:
            ensure_directory(file_path)
        assert "not a directory" in str(exc.value)


class TestGetRelativePath:
    """Tests for get_relative_path."""

    def test_simple_relative_path(self, tmp_path):
        """Test getting simple relative path."""
        base = tmp_path
        target = tmp_path / "subdir" / "file.txt"
        result = get_relative_path(target, base)
        assert result == Path("subdir/file.txt")

    def test_same_path(self, tmp_path):
        """Test relative path to same location."""
        result = get_relative_path(tmp_path, tmp_path)
        assert result == Path(".")

    def test_not_relative_raises_error(self, tmp_path):
        """Test error when paths are not relative."""
        base = tmp_path / "dir1"
        target = tmp_path.parent / "dir2" / "file.txt"

        with pytest.raises(InvalidPathError) as exc:
            get_relative_path(target, base)
        assert "not relative" in str(exc.value).lower()


class TestValidateDirectoryNotEmpty:
    """Tests for validate_directory_not_empty."""

    def test_non_empty_directory(self, temp_structure):
        """Test non-empty directory passes."""
        docs_dir = temp_structure / "docs"
        result = validate_directory_not_empty(docs_dir)
        assert result == docs_dir.resolve()

    def test_empty_directory(self, temp_structure):
        """Test empty directory raises error."""
        empty_dir = temp_structure / "empty_dir"
        with pytest.raises(ResourceNotFoundError) as exc:
            validate_directory_not_empty(empty_dir)
        assert "empty" in str(exc.value).lower()

    def test_nonexistent_directory(self, tmp_path):
        """Test nonexistent directory raises error."""
        with pytest.raises(ResourceNotFoundError):
            validate_directory_not_empty(tmp_path / "nonexistent")


class TestIsHiddenPath:
    """Tests for is_hidden_path."""

    def test_hidden_file(self, temp_structure):
        """Test hidden file detection."""
        hidden_file = temp_structure / ".hidden" / "secret.txt"
        assert is_hidden_path(hidden_file) is True

    def test_hidden_directory(self, temp_structure):
        """Test hidden directory detection."""
        hidden_dir = temp_structure / ".hidden"
        assert is_hidden_path(hidden_dir) is True

    def test_file_in_hidden_directory(self, temp_structure):
        """Test file in hidden directory."""
        file_in_hidden = temp_structure / ".hidden" / "secret.txt"
        assert is_hidden_path(file_in_hidden) is True

    def test_normal_file(self, temp_structure):
        """Test normal file is not hidden."""
        normal_file = temp_structure / "file.txt"
        assert is_hidden_path(normal_file) is False

    def test_normal_directory(self, temp_structure):
        """Test normal directory is not hidden."""
        normal_dir = temp_structure / "docs"
        assert is_hidden_path(normal_dir) is False

    def test_current_directory_not_hidden(self):
        """Test that . and .. are not considered hidden."""
        assert is_hidden_path(Path(".")) is False
        assert is_hidden_path(Path("..")) is False


class TestSanitizeFilename:
    """Tests for sanitize_filename."""

    def test_remove_invalid_characters(self):
        """Test removal of invalid characters."""
        dirty = "my/file:name*?.txt"
        clean = sanitize_filename(dirty)
        assert "/" not in clean
        assert ":" not in clean
        assert "*" not in clean
        assert "?" not in clean
        assert clean == "my_file_name__.txt"

    def test_custom_replacement(self):
        """Test custom replacement character."""
        dirty = "file/name.txt"
        clean = sanitize_filename(dirty, replacement="-")
        assert clean == "file-name.txt"

    def test_strip_dots_and_spaces(self):
        """Test stripping leading/trailing dots and spaces."""
        assert sanitize_filename("  file.txt  ") == "file.txt"
        assert sanitize_filename("...file.txt...") == "file.txt"

    def test_empty_name(self):
        """Test that empty name becomes 'unnamed'."""
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"
        assert sanitize_filename("...") == "unnamed"

    def test_preserves_valid_names(self):
        """Test that valid names are preserved."""
        valid = "my-file_name.txt"
        assert sanitize_filename(valid) == valid


class TestGetFileSize:
    """Tests for get_file_size_mb."""

    def test_small_file(self, tmp_path):
        """Test file size calculation for small file."""
        file_path = tmp_path / "small.txt"
        file_path.write_bytes(b"x" * 1024)  # 1KB
        size = get_file_size_mb(file_path)
        assert 0 < size < 0.01  # Less than 0.01 MB

    def test_large_file(self, tmp_path):
        """Test file size calculation for larger file."""
        file_path = tmp_path / "large.txt"
        file_path.write_bytes(b"x" * (1024 * 1024 * 2))  # 2MB
        size = get_file_size_mb(file_path)
        assert 1.9 < size < 2.1  # Approximately 2MB

    def test_nonexistent_file(self, tmp_path):
        """Test error for nonexistent file."""
        with pytest.raises(ResourceNotFoundError):
            get_file_size_mb(tmp_path / "nonexistent.txt")

    def test_directory_raises_error(self, tmp_path):
        """Test error when passing directory instead of file."""
        (tmp_path / "dir").mkdir()
        with pytest.raises(ResourceNotFoundError):
            get_file_size_mb(tmp_path / "dir")


class TestGetDirectorySize:
    """Tests for get_directory_size_mb."""

    def test_directory_with_files(self, tmp_path):
        """Test directory size calculation."""
        dir_path = tmp_path / "test_dir"
        dir_path.mkdir()

        # Create files
        (dir_path / "file1.txt").write_bytes(b"x" * (1024 * 1024))  # 1MB
        (dir_path / "file2.txt").write_bytes(b"x" * (1024 * 1024))  # 1MB

        size = get_directory_size_mb(dir_path)
        assert 1.9 < size < 2.1  # Approximately 2MB

    def test_empty_directory(self, tmp_path):
        """Test empty directory has zero size."""
        dir_path = tmp_path / "empty"
        dir_path.mkdir()
        size = get_directory_size_mb(dir_path)
        assert size == 0

    def test_nested_directories(self, tmp_path):
        """Test size calculation includes nested directories."""
        dir_path = tmp_path / "parent"
        dir_path.mkdir()
        (dir_path / "child").mkdir()

        (dir_path / "file1.txt").write_bytes(b"x" * (1024 * 1024))  # 1MB
        (dir_path / "child" / "file2.txt").write_bytes(b"x" * (1024 * 1024))  # 1MB

        size = get_directory_size_mb(dir_path)
        assert 1.9 < size < 2.1  # Approximately 2MB total

    def test_nonexistent_directory(self, tmp_path):
        """Test error for nonexistent directory."""
        with pytest.raises(ResourceNotFoundError):
            get_directory_size_mb(tmp_path / "nonexistent")

    def test_file_raises_error(self, tmp_path):
        """Test error when passing file instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        with pytest.raises(ResourceNotFoundError):
            get_directory_size_mb(file_path)
