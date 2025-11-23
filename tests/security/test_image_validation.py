"""
Tests for image size validation (v0.5.7 HIGH-4).

Security Feature: DoS protection via image size validation
Reference: docs/development/roadmap/version/v0.5.7/README.md
"""
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from ragged.validation.image_validator import (
    ImageSizeError,
    ImageValidator,
    validate_image,
    validate_image_batch,
)


@pytest.fixture
def validator():
    """Create validator with default limits."""
    return ImageValidator(
        max_file_size_mb=50.0, max_dimension=10000, max_memory_mb=500.0
    )


@pytest.fixture
def strict_validator():
    """Create validator with strict limits."""
    return ImageValidator(max_file_size_mb=1.0, max_dimension=1000, max_memory_mb=10.0)


class TestImageValidator:
    """Test image size and dimension validation."""

    def test_validator_initialization(self, validator):
        """Test that validator initializes with correct limits."""
        assert validator.max_file_size_bytes == 50 * 1024 * 1024
        assert validator.max_dimension == 10000
        assert validator.max_memory_bytes == 500 * 1024 * 1024

    def test_validate_small_image_passes(self, validator):
        """Test that small image passes validation."""
        # Create small test image (100x100 px)
        image = Image.new("RGB", (100, 100), color="white")

        # Should not raise
        validator.validate(image)

    def test_validate_large_dimension_fails(self, strict_validator):
        """Test that oversized dimensions are rejected."""
        # Create image larger than max dimension (2000x2000 > 1000)
        image = Image.new("RGB", (2000, 2000), color="white")

        # Should raise ImageSizeError
        with pytest.raises(ImageSizeError) as exc_info:
            strict_validator.validate(image)

        assert "width too large" in str(exc_info.value).lower() or "height too large" in str(
            exc_info.value
        ).lower()

    def test_validate_excessive_memory_footprint_fails(self, strict_validator):
        """Test that images with large memory footprint are rejected."""
        # Create image that exceeds memory limit
        # 900x900 pixels * 4 bytes/pixel = 3.24 MB > 10 MB limit is fine
        # But 5000x5000 * 4 bytes/pixel = 100 MB > 10 MB limit
        image = Image.new("RGB", (3000, 3000), color="white")

        with pytest.raises(ImageSizeError) as exc_info:
            strict_validator.validate(image)

        assert "memory footprint" in str(exc_info.value).lower() or "too large" in str(
            exc_info.value
        ).lower()

    def test_validate_file_size_with_path(self, strict_validator):
        """Test file size validation when path is provided."""
        # Create image and save to temp file
        image = Image.new("RGB", (500, 500), color="red")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Save as PNG (typically compressed)
            image.save(tmp_path, format="PNG")

        try:
            # Check actual file size
            file_size_mb = tmp_path.stat().st_size / (1024 * 1024)
            print(f"Temp file size: {file_size_mb:.2f} MB")

            # Should pass if file size < 1 MB
            if file_size_mb < 1.0:
                strict_validator.validate(image, tmp_path)
            else:
                # If file happens to be larger, expect rejection
                with pytest.raises(ImageSizeError):
                    strict_validator.validate(image, tmp_path)

        finally:
            tmp_path.unlink()

    def test_validate_non_pil_image_raises_type_error(self, validator):
        """Test that non-PIL Image types are rejected."""
        import numpy as np

        # Create numpy array (not a PIL Image)
        fake_image = np.zeros((100, 100, 3))

        with pytest.raises(TypeError) as exc_info:
            validator.validate(fake_image)

        assert "expected pil image" in str(exc_info.value).lower()

    def test_validate_batch_all_pass(self, validator):
        """Test batch validation when all images pass."""
        # Create batch of small images
        images = [Image.new("RGB", (200, 200), color="blue") for _ in range(5)]

        # Should not raise
        validator.validate_batch(images)

    def test_validate_batch_one_fails(self, strict_validator):
        """Test batch validation fails if any image fails."""
        # Create batch with one oversized image
        images = [
            Image.new("RGB", (500, 500), color="green"),
            Image.new("RGB", (500, 500), color="yellow"),
            Image.new("RGB", (2000, 2000), color="red"),  # Too large
        ]

        with pytest.raises(ImageSizeError) as exc_info:
            strict_validator.validate_batch(images)

        assert "image 2" in str(exc_info.value).lower() or "batch" in str(exc_info.value).lower()

    def test_validate_batch_with_paths(self, validator):
        """Test batch validation with file paths."""
        images = []
        paths = []

        # Create temporary images
        for i in range(3):
            image = Image.new("RGB", (300, 300), color="cyan")
            images.append(image)

            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp_path = Path(tmp.name)
            image.save(tmp_path, format="PNG")
            paths.append(tmp_path)
            tmp.close()

        try:
            # Should validate successfully
            validator.validate_batch(images, paths)

        finally:
            # Cleanup
            for path in paths:
                path.unlink()

    def test_validate_batch_mismatched_lengths_raises_error(self, validator):
        """Test that mismatched image/path lists raise ValueError."""
        images = [Image.new("RGB", (100, 100)) for _ in range(3)]
        paths = [Path("dummy1.png"), Path("dummy2.png")]  # Only 2 paths for 3 images

        with pytest.raises(ValueError) as exc_info:
            validator.validate_batch(images, paths)

        assert "mismatched" in str(exc_info.value).lower()

    def test_edge_case_exactly_at_limit(self, validator):
        """Test image exactly at dimension limit."""
        # Create image exactly at max dimension (10000x10000)
        image = Image.new("RGB", (10000, 10000), color="black")

        # Should NOT raise (10000 == 10000 is allowed)
        validator.validate(image)

    def test_edge_case_one_pixel_over_limit(self, validator):
        """Test image one pixel over dimension limit."""
        # Create image one pixel over max dimension (10001x10000)
        image = Image.new("RGB", (10001, 10000), color="black")

        # Should raise
        with pytest.raises(ImageSizeError):
            validator.validate(image)


class TestConvenienceFunctions:
    """Test convenience functions for image validation."""

    def test_validate_image_convenience_function(self):
        """Test validate_image convenience function."""
        image = Image.new("RGB", (500, 500), color="orange")

        # Should not raise
        validate_image(image)

    def test_validate_image_batch_convenience_function(self):
        """Test validate_image_batch convenience function."""
        images = [Image.new("RGB", (400, 400), color="purple") for _ in range(5)]

        # Should not raise
        validate_image_batch(images)

    def test_validate_image_oversized_raises(self):
        """Test convenience function raises on oversized image."""
        # Create extremely large image (20000x20000 > 10000 default limit)
        image = Image.new("RGB", (20000, 20000), color="white")

        with pytest.raises(ImageSizeError):
            validate_image(image)


class TestSecurityCompliance:
    """Test DoS protection features."""

    def test_prevents_memory_exhaustion_attack(self, validator):
        """Test that validator prevents memory exhaustion attacks.

        Security (v0.5.7 HIGH-4): Prevents DoS via oversized images.
        """
        # Attempt to create image that would consume excessive memory
        # 15000x15000 * 4 bytes = 900 MB > 500 MB limit
        oversized_image = Image.new("RGB", (15000, 15000), color="black")

        # Should be rejected before GPU processing
        with pytest.raises(ImageSizeError) as exc_info:
            validator.validate(oversized_image)

        assert "memory footprint" in str(exc_info.value).lower()

    def test_prevents_dimension_based_dos(self, strict_validator):
        """Test that validator prevents dimension-based DoS attacks."""
        # Attempt to create extremely tall/wide image
        # Even if memory footprint is acceptable, extreme dimensions can cause issues
        extreme_image = Image.new("RGB", (5000, 5000), color="white")

        # Should be rejected
        with pytest.raises(ImageSizeError):
            strict_validator.validate(extreme_image)

    def test_batch_validation_early_rejection(self, strict_validator):
        """Test that batch validation rejects before processing begins."""
        # Create batch where first image is oversized
        images = [
            Image.new("RGB", (5000, 5000), color="red"),  # Too large - should fail fast
            Image.new("RGB", (500, 500), color="green"),
            Image.new("RGB", (500, 500), color="blue"),
        ]

        # Should raise on first image
        with pytest.raises(ImageSizeError) as exc_info:
            strict_validator.validate_batch(images)

        # Error should mention image 0
        assert "image 0" in str(exc_info.value).lower()


class TestConfigurability:
    """Test validator configurability."""

    def test_custom_limits(self):
        """Test validator with custom limits."""
        custom_validator = ImageValidator(
            max_file_size_mb=10.0, max_dimension=2000, max_memory_mb=50.0
        )

        # Image within custom limits should pass
        image = Image.new("RGB", (1500, 1500), color="gray")
        custom_validator.validate(image)

        # Image exceeding custom limits should fail
        large_image = Image.new("RGB", (2500, 2500), color="gray")
        with pytest.raises(ImageSizeError):
            custom_validator.validate(large_image)

    def test_relaxed_limits_for_high_memory_systems(self):
        """Test validator with relaxed limits for powerful systems."""
        relaxed_validator = ImageValidator(
            max_file_size_mb=200.0, max_dimension=20000, max_memory_mb=2000.0
        )

        # Large image should pass with relaxed limits
        large_image = Image.new("RGB", (15000, 10000), color="white")
        relaxed_validator.validate(large_image)
