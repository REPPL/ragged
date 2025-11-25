"""
Image validation for security (v0.5.7 HIGH-4).

Prevents DoS attacks via oversized images by validating:
- File size (bytes)
- Image dimensions (width x height pixels)
- Memory footprint (width * height * bytes_per_pixel)

Security: Validates images before GPU processing to prevent:
- Memory exhaustion (OOM)
- Slow processing (DoS)
- Resource abuse
"""
from __future__ import annotations


import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

logger = logging.getLogger(__name__)


class ImageSizeError(ValueError):
    """Raised when image exceeds size or dimension limits.

    v0.5.7 HIGH-4: Image size validation
    Used to reject oversized images before processing.
    """

    pass


class ImageValidator:
    """
    Validate image sizes and dimensions for security.

    v0.5.7 HIGH-4: Prevents DoS attacks via oversized images

    Default Limits (configurable):
    - Max file size: 50 MB
    - Max dimensions: 10000 x 10000 pixels
    - Max memory footprint: 500 MB (width * height * 4 bytes/pixel for RGBA)

    Example:
        >>> validator = ImageValidator(max_file_size_mb=20, max_dimension=5000)
        >>> from PIL import Image
        >>> image = Image.open("document.png")
        >>> validator.validate(image)  # Raises ImageSizeError if too large
    """

    def __init__(
        self,
        max_file_size_mb: float = 50.0,
        max_dimension: int = 10000,
        max_memory_mb: float = 500.0,
    ) -> None:
        """
        Initialise image validator with size limits.

        Args:
            max_file_size_mb: Maximum file size in megabytes (default: 50 MB)
            max_dimension: Maximum width or height in pixels (default: 10000)
            max_memory_mb: Maximum memory footprint in MB (default: 500 MB)

        Security (v0.5.7 HIGH-4):
        - Prevents memory exhaustion from oversized images
        - Limits apply before GPU processing
        - Configurable for different deployment environments

        Example:
            >>> # Default limits (suitable for most deployments)
            >>> validator = ImageValidator()
            >>> # Strict limits for resource-constrained environments
            >>> validator = ImageValidator(max_file_size_mb=10, max_dimension=5000)
            >>> # Relaxed limits for high-memory systems
            >>> validator = ImageValidator(max_file_size_mb=100, max_dimension=20000)
        """
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.max_dimension = max_dimension
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)

        logger.info(
            f"ImageValidator initialised: "
            f"max_file_size={max_file_size_mb}MB, "
            f"max_dimension={max_dimension}px, "
            f"max_memory={max_memory_mb}MB"
        )

    def validate(self, image: "Image.Image", file_path: Path | None = None) -> None:
        """
        Validate image size and dimensions.

        Args:
            image: PIL Image to validate
            file_path: Optional file path (for file size validation)

        Raises:
            ImageSizeError: If image exceeds any limit
            TypeError: If image is not a PIL Image

        Security (v0.5.7 HIGH-4):
        - Checks file size (if path provided)
        - Checks dimensions (width, height)
        - Checks memory footprint (width * height * bytes_per_pixel)

        Example:
            >>> validator = ImageValidator()
            >>> from PIL import Image
            >>> image = Image.open("scan.png")
            >>> try:
            ...     validator.validate(image, Path("scan.png"))
            ... except ImageSizeError as e:
            ...     print(f"Image rejected: {e}")
        """
        try:
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "Pillow (PIL) required for image validation. "
                "Install with: pip install Pillow>=10.0.0"
            ) from e

        # Type check
        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL Image, got {type(image)}")

        # Validate file size (if path provided)
        if file_path is not None and file_path.exists():
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size_bytes:
                raise ImageSizeError(
                    f"Image file too large: {file_size / 1024 / 1024:.1f}MB "
                    f"(max: {self.max_file_size_bytes / 1024 / 1024:.1f}MB). "
                    f"File: {file_path}"
                )

        # Validate dimensions
        width, height = image.size

        if width > self.max_dimension:
            raise ImageSizeError(
                f"Image width too large: {width}px (max: {self.max_dimension}px)"
            )

        if height > self.max_dimension:
            raise ImageSizeError(
                f"Image height too large: {height}px (max: {self.max_dimension}px)"
            )

        # Validate memory footprint
        # Assume 4 bytes per pixel (RGBA) for worst-case estimation
        bytes_per_pixel = 4
        memory_footprint = width * height * bytes_per_pixel

        if memory_footprint > self.max_memory_bytes:
            raise ImageSizeError(
                f"Image memory footprint too large: "
                f"{memory_footprint / 1024 / 1024:.1f}MB "
                f"(max: {self.max_memory_bytes / 1024 / 1024:.1f}MB). "
                f"Dimensions: {width}x{height}px"
            )

        logger.debug(
            f"Image validated: {width}x{height}px, "
            f"memory: {memory_footprint / 1024 / 1024:.1f}MB"
        )

    def validate_batch(
        self, images: list["Image.Image"], file_paths: list[Path] | None = None
    ) -> None:
        """
        Validate a batch of images.

        Args:
            images: List of PIL Images to validate
            file_paths: Optional list of file paths (for file size validation)

        Raises:
            ImageSizeError: If any image exceeds limits
            ValueError: If lists have mismatched lengths

        Security (v0.5.7 HIGH-4):
        - Validates all images before processing begins
        - Prevents batch processing of oversized images

        Example:
            >>> validator = ImageValidator()
            >>> images = [Image.open(f"page{i}.png") for i in range(10)]
            >>> validator.validate_batch(images)
        """
        if file_paths is not None and len(images) != len(file_paths):
            raise ValueError(
                f"Mismatched lengths: {len(images)} images, {len(file_paths)} paths"
            )

        for i, image in enumerate(images):
            file_path = file_paths[i] if file_paths else None
            try:
                self.validate(image, file_path)
            except ImageSizeError as e:
                raise ImageSizeError(
                    f"Image {i} in batch failed validation: {e}"
                ) from e


# Global singleton
_image_validator: ImageValidator | None = None


def get_image_validator(
    max_file_size_mb: float = 50.0,
    max_dimension: int = 10000,
    max_memory_mb: float = 500.0,
) -> ImageValidator:
    """
    Get global image validator instance (singleton).

    v0.5.7 HIGH-4: Image size validation

    Args:
        max_file_size_mb: Maximum file size in MB
        max_dimension: Maximum width/height in pixels
        max_memory_mb: Maximum memory footprint in MB

    Returns:
        ImageValidator singleton

    Example:
        >>> validator = get_image_validator(max_file_size_mb=20)
        >>> validator.validate(image)
    """
    global _image_validator
    if _image_validator is None:
        _image_validator = ImageValidator(
            max_file_size_mb=max_file_size_mb,
            max_dimension=max_dimension,
            max_memory_mb=max_memory_mb,
        )
    return _image_validator


# Convenience functions
def validate_image(
    image: "Image.Image", file_path: Path | None = None
) -> None:
    """
    Validate image size and dimensions (convenience function).

    v0.5.7 HIGH-4: Image size validation

    Args:
        image: PIL Image to validate
        file_path: Optional file path for file size check

    Raises:
        ImageSizeError: If image exceeds limits

    Example:
        >>> from ragged.validation import validate_image
        >>> from PIL import Image
        >>> img = Image.open("large_scan.png")
        >>> try:
        ...     validate_image(img, Path("large_scan.png"))
        ... except ImageSizeError:
        ...     print("Image too large, rejecting upload")
    """
    validator = get_image_validator()
    validator.validate(image, file_path)


def validate_image_batch(
    images: list["Image.Image"], file_paths: list[Path] | None = None
) -> None:
    """
    Validate batch of images (convenience function).

    v0.5.7 HIGH-4: Image size validation

    Args:
        images: List of PIL Images
        file_paths: Optional list of file paths

    Raises:
        ImageSizeError: If any image exceeds limits

    Example:
        >>> from ragged.validation import validate_image_batch
        >>> images = [Image.open(f"page{i}.png") for i in range(10)]
        >>> validate_image_batch(images)
    """
    validator = get_image_validator()
    validator.validate_batch(images, file_paths)
