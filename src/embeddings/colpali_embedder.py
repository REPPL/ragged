"""
ColPali vision embedder for document understanding.

This module provides vision-based embeddings for PDF documents,
capturing layout, diagrams, tables, and visual content using the
ColPali model from VidOre.

The ColPali model generates multi-vector embeddings (128-dim per patch)
from document page images, enabling retrieval based on visual similarity
without requiring OCR or layout detection pipelines.

References:
    - VidOre ColPali: https://huggingface.co/vidore/colpali-v1.3-hf
    - Paper: https://arxiv.org/abs/2407.01449

Example:
    >>> from PIL import Image
    >>> embedder = ColPaliEmbedder()
    >>> image = Image.open("document_page.png")
    >>> embedding = embedder.embed_page(image)
    >>> embedding.shape
    (128,)
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from ragged.config.settings import get_settings
from ragged.embeddings.base import BaseEmbedder
from ragged.gpu.batch_sizer import AdaptiveBatchSizer, BatchSizeConfig
from ragged.gpu.device_manager import DeviceInfo, DeviceManager, DeviceType
from ragged.gpu.memory_monitor import MemoryMonitor
from ragged.gpu.oom_handler import OOMHandler
from ragged.validation.image_validator import ImageValidator

logger = logging.getLogger(__name__)

# v0.5.8 MEDIUM-5: Pin ColPali model to specific revision for security
# Prevents automatic updates that could introduce vulnerabilities
# Revision: 7d3c8ab1c1908b32d701308fb1dfb2968d150c67 (vidore/colpali-v1.3-hf)
# Verified: 2025-11-23
COLPALI_MODEL_REVISION = "7d3c8ab1c1908b32d701308fb1dfb2968d150c67"


class ColPaliEmbedder(BaseEmbedder):
    """
    ColPali vision embedder for multi-modal document understanding.

    Generates 128-dimensional vision embeddings (mean-pooled from multi-vector output)
    that capture:
    - Document layout and structure
    - Diagrams, charts, and visual content
    - Tables and formatted data
    - Handwriting and annotations
    - Mathematical equations and notation

    GPU acceleration is used when available, with automatic fallback to CPU.
    Supports CUDA (NVIDIA), MPS (Apple Silicon), and CPU devices.

    Features (v0.5.2):
    - Automatic device detection (CUDA > MPS > CPU priority)
    - Adaptive batch sizing based on available GPU memory
    - Memory monitoring with threshold callbacks
    - Automatic OOM recovery (cache clearing → batch reduction → CPU fallback)

    Attributes:
        model_name (str): HuggingFace model identifier
        device_info (DeviceInfo): Computation device information
        batch_size (int): Current batch size (adaptive if enabled)
        cache_dir (Optional[Path]): Model cache directory
        model: Loaded ColPali model
        processor: Image preprocessing pipeline
        device_manager (DeviceManager): GPU/CPU device manager
        memory_monitor (Optional[MemoryMonitor]): GPU memory monitor
        batch_sizer (Optional[AdaptiveBatchSizer]): Adaptive batch sizer
        oom_handler (Optional[OOMHandler]): OOM recovery handler

    Example:
        >>> # Automatic device selection and adaptive batching
        >>> embedder = ColPaliEmbedder()
        >>> image = Image.open("document_page.png")
        >>> embedding = embedder.embed_page(image)
        >>> embedding.shape
        (128,)
        >>> # With custom configuration
        >>> embedder = ColPaliEmbedder(
        ...     device="cuda",
        ...     enable_adaptive_batching=True,
        ...     enable_memory_monitoring=True
        ... )
        >>> embedder.get_device_info()
        {'device': 'cuda', 'name': 'NVIDIA RTX 4090', 'total_memory_gb': 24.0, 'free_memory_gb': 18.5}
    """

    def __init__(
        self,
        model_name: str = "vidore/colpali-v1.3-hf",
        device: Optional[str] = None,
        batch_size: Optional[int] = None,
        cache_dir: Optional[Path] = None,
        enable_adaptive_batching: bool = True,
        enable_memory_monitoring: bool = True,
        enable_oom_recovery: bool = True,
        batch_size_config: Optional[BatchSizeConfig] = None,
    ) -> None:
        """
        Initialise ColPali vision embedder with GPU resource management.

        Args:
            model_name: HuggingFace model identifier for ColPali
                       Default: "vidore/colpali-v1.3-hf" (native transformers support)
            device: Computation device ('cuda', 'mps', 'cpu', or None for auto-detect)
                   Priority: CUDA > MPS > CPU
            batch_size: Fixed batch size (None = adaptive based on GPU memory)
                       Guidelines if fixed: 4GB VRAM=1-2, 8GB=4-6, 16GB=8-12, 24GB+=16-32
            cache_dir: Directory for model cache (None = HuggingFace default ~/.cache)
            enable_adaptive_batching: Automatically adjust batch size based on GPU memory
            enable_memory_monitoring: Monitor GPU memory usage with threshold callbacks
            enable_oom_recovery: Automatic OOM recovery (cache → batch reduction → CPU)
            batch_size_config: Custom batch size configuration (overrides defaults)

        Raises:
            RuntimeError: If model fails to load or device unavailable
            ValueError: If configuration is invalid

        Example:
            >>> # Auto-detect device with adaptive batching
            >>> embedder = ColPaliEmbedder()
            >>> # Force specific device with fixed batch size
            >>> embedder = ColPaliEmbedder(device="cuda", batch_size=8)
            >>> # Custom batch size configuration
            >>> config = BatchSizeConfig(min_batch_size=2, max_batch_size=16)
            >>> embedder = ColPaliEmbedder(batch_size_config=config)
            >>> # Disable adaptive features for deterministic behavior
            >>> embedder = ColPaliEmbedder(
            ...     enable_adaptive_batching=False,
            ...     enable_memory_monitoring=False,
            ...     batch_size=4
            ... )
        """
        self._model_name = model_name
        self.cache_dir = cache_dir

        # Initialise GPU device manager
        logger.info("Initialising GPU device manager")
        self.device_manager = DeviceManager()
        self.device_info = self.device_manager.get_optimal_device(
            device_hint=device, min_memory_gb=4.0  # ColPali requires ~4GB minimum
        )

        logger.info(f"Selected device: {self.device_info}")

        # Initialise memory monitoring (GPU only)
        self.memory_monitor: Optional[MemoryMonitor] = None
        if enable_memory_monitoring and self.device_info.device_type != DeviceType.CPU:
            logger.info("Enabling GPU memory monitoring")
            self.memory_monitor = MemoryMonitor(
                device=self.device_info,
                device_manager=self.device_manager,
                warning_threshold_pct=85.0,
                critical_threshold_pct=95.0,
            )

        # Initialise adaptive batch sizer
        self.batch_sizer: Optional[AdaptiveBatchSizer] = None
        if enable_adaptive_batching:
            logger.info("Enabling adaptive batch sizing")
            self.batch_sizer = AdaptiveBatchSizer(
                device=self.device_info,
                memory_monitor=self.memory_monitor,
                config=batch_size_config or BatchSizeConfig(),
            )

        # Determine batch size
        if batch_size is not None:
            # User-specified fixed batch size
            self.batch_size = batch_size
            logger.info(f"Using fixed batch size: {batch_size}")
        elif self.batch_sizer:
            # Adaptive batch sizing
            # ColPali: 768-dim embeddings (internal), 1024 sequence length
            self.batch_size = self.batch_sizer.calculate_batch_size(
                embedding_dim=768, sequence_length=1024, bytes_per_element=4
            )
            logger.info(f"Calculated adaptive batch size: {self.batch_size}")
        else:
            # Fallback default
            self.batch_size = 4
            logger.info(f"Using default batch size: {self.batch_size}")

        # Initialise OOM handler
        self.oom_handler: Optional[OOMHandler] = None
        if enable_oom_recovery:
            logger.info("Enabling OOM recovery")
            self.oom_handler = OOMHandler(
                device_manager=self.device_manager,
                enable_cache_clearing=True,
                enable_batch_reduction=True,
                enable_cpu_fallback=True,
            )

        # Store device string for backward compatibility
        self.device = self.device_info.device_type.value

        logger.info(f"Initialising ColPali embedder on device: {self.device}")

        # Initialise image validator (v0.5.7 HIGH-4)
        settings = get_settings()
        self.image_validator = ImageValidator(
            max_file_size_mb=settings.max_image_file_size_mb,
            max_dimension=settings.max_image_dimension,
            max_memory_mb=settings.max_image_memory_mb,
        )
        logger.info("Image size validation enabled (v0.5.7 HIGH-4)")

        # Load model and processor
        self._load_model()

        logger.info("ColPali embedder initialised successfully")


    def _load_model(self) -> None:
        """
        Load ColPali model and processor from HuggingFace with progress indication.

        Downloads model on first use (~5GB, cached locally).
        Uses bfloat16 precision on CUDA for efficiency, float32 on MPS/CPU.
        Shows download progress with estimated time remaining.

        Raises:
            RuntimeError: If model loading fails
            ImportError: If transformers library is not installed

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> # Model automatically loaded during initialisation
            >>> # Shows: "Downloading model: vidore/colpali-v1.3-hf (5.2GB)"
            >>> # Progress: ████████████████░░░░░░░░░░░░ 50% | 2.6GB/5.2GB | ETA: 5min 30s
            >>> embedder.model  # Access loaded model
        """
        try:
            from transformers import AutoModel, AutoProcessor
        except ImportError as e:
            raise ImportError(
                "transformers library required for ColPali. "
                "Install with: pip install transformers>=4.35.0"
            ) from e

        try:
            import os

            # Enable HuggingFace download progress bars
            # Remove HF_HUB_DISABLE_PROGRESS_BARS if set
            if 'HF_HUB_DISABLE_PROGRESS_BARS' in os.environ:
                del os.environ['HF_HUB_DISABLE_PROGRESS_BARS']

            # Determine optimal dtype
            dtype = torch.bfloat16 if self.device == "cuda" else torch.float32

            logger.info(f"Loading ColPali model: {self._model_name}")
            logger.info(f"Using dtype: {dtype}, device: {self.device}")
            logger.info("First-time download may take 10-30 minutes (~5GB model)")
            logger.info("Progress will be displayed below:")

            # Load model with HuggingFace transformers
            # transformers library automatically shows progress bars during download
            # v0.5.8 MEDIUM-5: Pin to specific revision for security
            self.model = AutoModel.from_pretrained(
                self._model_name,
                revision=COLPALI_MODEL_REVISION,
                torch_dtype=dtype,
                cache_dir=str(self.cache_dir) if self.cache_dir else None,
                device_map=self.device if self.device != "cpu" else None,
                # force_download=False ensures we use cache if available
                local_files_only=False,  # Allow downloads
            )

            # Move to device if not using device_map
            if self.device == "cpu":
                self.model = self.model.to(self.device)

            self.model.eval()  # Set to inference mode (disable dropout, etc.)

            logger.info("Model loaded successfully")

            # Load processor (handles image preprocessing)
            logger.info("Loading ColPali processor")
            # v0.5.8 MEDIUM-5: Pin to specific revision for security
            self.processor = AutoProcessor.from_pretrained(
                self._model_name,
                revision=COLPALI_MODEL_REVISION,
                cache_dir=str(self.cache_dir) if self.cache_dir else None,
                local_files_only=False,
            )

            logger.info("Processor loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load ColPali model: {e}")
            raise RuntimeError(
                f"ColPali model loading failed: {e}. "
                f"Ensure model '{self._model_name}' exists on HuggingFace and "
                f"you have internet connection for first download."
            ) from e

    def get_embedding_dimension(self) -> int:
        """
        Get dimension of vision embeddings.

        ColPali produces multi-vector embeddings (N patches × 128 dimensions).
        This implementation returns mean-pooled single vector of 128 dimensions
        for compatibility with standard vector databases.

        Returns:
            Embedding dimension (128 for ColPali mean-pooled)

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.get_embedding_dimension()
            128
        """
        return 128

    @property
    def dimensions(self) -> int:
        """
        Get embedding dimensionality (BaseEmbedder property).

        Returns:
            Number of dimensions in output embeddings (128)

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.dimensions
            128
        """
        return self.get_embedding_dimension()

    @property
    def model_name(self) -> str:
        """
        Get the name of the embedding model (BaseEmbedder property).

        Returns:
            Model name string

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.model_name
            'vidore/colpali-v1.3-hf'
        """
        return self._model_name

    def get_device_info(self) -> dict[str, str | float]:
        """
        Get information about computation device and memory status.

        Returns:
            Dictionary with device type, name, memory info, and monitoring status

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.get_device_info()
            {
                'device': 'cuda',
                'device_id': 0,
                'name': 'NVIDIA RTX 4090',
                'total_memory_gb': 24.0,
                'free_memory_gb': 18.5,
                'allocated_memory_gb': 5.5,
                'memory_utilisation_pct': 22.9,
                'batch_size': 8,
                'adaptive_batching_enabled': True,
                'memory_monitoring_enabled': True
            }
        """
        info: dict[str, str | float] = {
            "device": self.device_info.device_type.value,
            "device_id": self.device_info.device_id,
            "name": self.device_info.name or "Unknown",
            "batch_size": self.batch_size,
            "adaptive_batching_enabled": self.batch_sizer is not None,
            "memory_monitoring_enabled": self.memory_monitor is not None,
        }

        # Add memory information if GPU
        if self.device_info.device_type != DeviceType.CPU:
            try:
                memory_info = self.device_manager.get_device_memory_info(self.device_info)
                info["total_memory_gb"] = memory_info["total"] / 1e9
                info["allocated_memory_gb"] = memory_info["allocated"] / 1e9
                info["reserved_memory_gb"] = memory_info["reserved"] / 1e9
                info["free_memory_gb"] = memory_info["free"] / 1e9

                # Add utilisation percentage
                if memory_info["total"] > 0:
                    utilisation_pct = (memory_info["allocated"] / memory_info["total"]) * 100
                    info["memory_utilisation_pct"] = round(utilisation_pct, 1)

            except (ValueError, Exception) as e:
                logger.debug(f"Could not retrieve memory info: {e}")

        return info

    def estimate_batch_size_for_vram(self, available_vram_gb: float) -> int:
        """
        Estimate optimal batch size based on available VRAM.

        Uses AdaptiveBatchSizer if enabled, otherwise falls back to rule of thumb.

        Args:
            available_vram_gb: Available VRAM in GB

        Returns:
            Recommended batch size (capped at configured max)

        Note:
            Deprecated in v0.5.2 in favor of automatic adaptive batching.
            Consider using enable_adaptive_batching=True in __init__ instead.

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.estimate_batch_size_for_vram(8.0)
            12
            >>> embedder.estimate_batch_size_for_vram(4.0)
            4
        """
        if self.batch_sizer:
            # Use adaptive batch sizer with specified memory
            # Convert GB to bytes and use as total memory
            temp_device = DeviceInfo(
                device_type=self.device_info.device_type,
                total_memory=int(available_vram_gb * 1e9),
            )
            temp_sizer = AdaptiveBatchSizer(
                device=temp_device, config=self.batch_sizer.config
            )
            return temp_sizer.calculate_batch_size(
                embedding_dim=768, sequence_length=1024, bytes_per_element=4
            )

        # Fallback to rule of thumb for backward compatibility
        base_memory_gb = 2.0  # Model + overhead
        memory_per_page_gb = 0.5  # Per page in batch

        available_for_batch = max(0, available_vram_gb - base_memory_gb)
        optimal_batch_size = int(available_for_batch / memory_per_page_gb)

        # Cap at 32 to avoid excessive memory usage
        return max(1, min(optimal_batch_size, 32))

    # Placeholder methods to satisfy BaseEmbedder interface
    # These will be implemented in Session 2.2

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string (not applicable for vision embedder).

        Note: ColPali is a vision-based embedder. Use embed_page() for images.

        Args:
            text: Text to embed (not used)

        Raises:
            NotImplementedError: Vision embedder does not support text-only embedding

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.embed_text("sample text")
            NotImplementedError: Use embed_page() for vision-based embedding
        """
        raise NotImplementedError(
            "ColPaliEmbedder is vision-based. Use embed_page() to embed document images."
        )

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """
        Embed multiple text strings (not applicable for vision embedder).

        Note: ColPali is a vision-based embedder. Use embed_batch_images() for images.

        Args:
            texts: List of texts to embed (not used)

        Raises:
            NotImplementedError: Vision embedder does not support text-only embedding

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.embed_batch(["text1", "text2"])
            NotImplementedError: Use embed_batch_images() for vision-based embedding
        """
        raise NotImplementedError(
            "ColPaliEmbedder is vision-based. "
            "Use embed_batch_images() to embed document images in batch."
        )

    # Vision-specific embedding methods

    def embed_page(self, image) -> np.ndarray:
        """
        Generate vision embedding for a single document page with OOM recovery.

        Processes the image through ColPali model and returns mean-pooled
        128-dimensional embedding vector. Automatically handles OOM errors through:
        1. Cache clearing and retry
        2. CPU fallback

        Args:
            image: PIL Image of document page (any size, will be resized by processor)

        Returns:
            128-dimensional vision embedding as numpy array

        Raises:
            ValueError: If image is invalid or wrong type
            RuntimeError: If embedding generation fails after all recovery attempts

        Example:
            >>> from PIL import Image
            >>> embedder = ColPaliEmbedder()
            >>> page = Image.open("report_page1.png")
            >>> embedding = embedder.embed_page(page)
            >>> embedding.shape
            (128,)
        """
        try:
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "Pillow (PIL) library required for image processing. "
                "Install with: pip install Pillow>=10.0.0"
            ) from e

        if not isinstance(image, Image.Image):
            raise ValueError(f"Expected PIL Image, got {type(image)}")

        # Use OOM handler if enabled
        if self.oom_handler and self.device_info.device_type != DeviceType.CPU:
            return self.oom_handler.handle_oom(
                self._embed_page_impl, image=image, device=self.device_info
            )
        else:
            # No OOM handling
            return self._embed_page_impl(image=image)

    def _embed_page_impl(self, image) -> np.ndarray:
        """
        Internal implementation of single page embedding.

        Args:
            image: PIL Image

        Returns:
            128-dimensional embedding vector
        """
        # SECURITY FIX (v0.5.7 HIGH-4): Validate image size before processing
        self.image_validator.validate(image)

        try:
            with torch.no_grad():
                # Preprocess image
                inputs = self.processor(images=image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Generate multi-vector embedding
                outputs = self.model(**inputs)

                # Extract patch embeddings from model output
                # ColPali outputs multi-vector (N_patches × 128)
                # We mean-pool to get single 128-dim vector for storage compatibility
                if hasattr(outputs, "last_hidden_state"):
                    patch_embeddings = outputs.last_hidden_state
                else:
                    # Direct output is embeddings
                    patch_embeddings = outputs

                # Mean pool across patches: (1, N_patches, 128) -> (128,)
                embedding = patch_embeddings.mean(dim=1).squeeze().cpu().numpy()

            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise RuntimeError(f"Failed to generate vision embedding: {e}") from e

    def embed_batch_images(self, images: list) -> np.ndarray:
        """
        Generate vision embeddings for multiple pages with automatic OOM recovery.

        Processes images in batches determined by self.batch_size for optimal
        GPU memory usage and throughput. Automatically handles OOM errors through:
        1. Cache clearing and retry
        2. Batch size reduction and retry
        3. CPU fallback

        Args:
            images: List of PIL Images (document pages)

        Returns:
            Array of shape (n_images, 128) containing embeddings

        Raises:
            ValueError: If images list is empty
            RuntimeError: If batch processing fails after all recovery attempts

        Example:
            >>> from PIL import Image
            >>> embedder = ColPaliEmbedder(batch_size=4)
            >>> pages = [Image.open(f"page{i}.png") for i in range(10)]
            >>> embeddings = embedder.embed_batch_images(pages)
            >>> embeddings.shape
            (10, 128)
            >>> # Automatically handles OOM by reducing batch size or falling back to CPU
        """
        if not images:
            raise ValueError("Cannot embed empty image list")

        try:
            from PIL import Image
        except ImportError as e:
            raise ImportError(
                "Pillow (PIL) library required for image processing. "
                "Install with: pip install Pillow>=10.0.0"
            ) from e

        # Validate all inputs are PIL Images
        for i, img in enumerate(images):
            if not isinstance(img, Image.Image):
                raise ValueError(f"Image at index {i} is not a PIL Image, got {type(img)}")

        # Use OOM handler if enabled
        if self.oom_handler and self.device_info.device_type != DeviceType.CPU:
            return self.oom_handler.handle_oom(
                self._embed_batch_images_impl,
                images=images,
                device=self.device_info,
                batch_size=self.batch_size,
            )
        else:
            # No OOM handling
            return self._embed_batch_images_impl(images=images)

    def _embed_batch_images_impl(self, images: list, batch_size: Optional[int] = None) -> np.ndarray:
        """
        Internal implementation of batch image embedding.

        Args:
            images: List of PIL Images
            batch_size: Batch size to use (overrides self.batch_size if provided)

        Returns:
            Array of embeddings
        """
        # SECURITY FIX (v0.5.7 HIGH-4): Validate all images before processing
        self.image_validator.validate_batch(images)

        current_batch_size = batch_size if batch_size is not None else self.batch_size
        embeddings_list = []

        # Take memory snapshot before processing (if monitoring enabled)
        if self.memory_monitor:
            snapshot = self.memory_monitor.take_snapshot()
            logger.debug(
                f"Memory before batch processing: {snapshot.utilisation_pct:.1f}% utilisation"
            )

        # Process in batches for efficiency
        for i in range(0, len(images), current_batch_size):
            batch = images[i : i + current_batch_size]

            try:
                with torch.no_grad():
                    # Preprocess batch
                    inputs = self.processor(images=batch, return_tensors="pt", padding=True)
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}

                    # Generate embeddings
                    outputs = self.model(**inputs)

                    # Extract patch embeddings
                    if hasattr(outputs, "last_hidden_state"):
                        patch_embeddings = outputs.last_hidden_state
                    else:
                        patch_embeddings = outputs

                    # Mean pool across patches: (batch_size, N_patches, 128) -> (batch_size, 128)
                    batch_embeddings = patch_embeddings.mean(dim=1).cpu().numpy()

                    embeddings_list.append(batch_embeddings)

                logger.debug(
                    f"Processed batch {i // current_batch_size + 1} ({len(batch)} images)"
                )

            except Exception as e:
                logger.error(f"Batch {i // current_batch_size} failed: {e}")
                raise RuntimeError(f"Batch embedding failed at index {i}: {e}") from e

        # Take memory snapshot after processing (if monitoring enabled)
        if self.memory_monitor:
            snapshot = self.memory_monitor.take_snapshot()
            logger.debug(
                f"Memory after batch processing: {snapshot.utilisation_pct:.1f}% utilisation"
            )

            # Adjust batch size based on observed memory usage
            if self.batch_sizer:
                recommended_batch_size = self.batch_sizer.adjust_batch_size(
                    current_batch_size
                )
                if recommended_batch_size != current_batch_size:
                    self.batch_size = recommended_batch_size

        # Concatenate all batches
        return np.vstack(embeddings_list)

    def _extract_pages_as_images(
        self,
        pdf_path: Path,
        dpi: int = 150,
        first_page: Optional[int] = None,
        last_page: Optional[int] = None,
    ) -> list:
        """
        Extract specific pages from PDF as images.

        Uses pdf2image library to convert PDF pages to PIL Images.
        Requires poppler-utils system dependency.

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for image conversion (150 recommended for ColPali)
            first_page: First page to extract (1-indexed, None = all)
            last_page: Last page to extract (1-indexed, None = all)

        Returns:
            List of PIL Images

        Raises:
            FileNotFoundError: If PDF doesn't exist
            RuntimeError: If PDF conversion fails (check poppler installation)

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> images = embedder._extract_pages_as_images(
            ...     Path("report.pdf"), dpi=150, first_page=1, last_page=5
            ... )
            >>> len(images)
            5
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            from pdf2image import convert_from_path
        except ImportError as e:
            raise ImportError(
                "pdf2image library required for PDF processing. "
                "Install with: pip install pdf2image>=1.16.3\n"
                "Also requires poppler-utils system dependency. "
                "See docs/tutorials/installation.md for setup instructions."
            ) from e

        try:
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page,
                thread_count=4,  # Parallel PDF rendering
            )
            logger.debug(f"Extracted {len(images)} pages from {pdf_path.name}")

            # SECURITY FIX (v0.5.7 HIGH-4): Validate extracted images
            self.image_validator.validate_batch(images)

            return images

        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            raise RuntimeError(
                f"Cannot extract pages from PDF: {e}\n"
                f"Ensure poppler-utils is installed. "
                f"See docs/tutorials/installation.md for setup instructions."
            ) from e

    def embed_document(self, pdf_path: Path, dpi: int = 150) -> tuple[np.ndarray, list[int]]:
        """
        Generate vision embeddings for all pages in a PDF document.

        Converts each page to an image and generates vision embeddings
        using batch processing for efficiency.

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for PDF rendering (150 recommended, higher = slower but better quality)

        Returns:
            Tuple of (embeddings array, page numbers list)
            - embeddings: shape (n_pages, 128)
            - page_numbers: list of page indices (0-indexed)

        Raises:
            FileNotFoundError: If PDF doesn't exist
            RuntimeError: If PDF conversion or embedding fails

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embeddings, pages = embedder.embed_document(Path("report.pdf"))
            >>> embeddings.shape
            (25, 128)
            >>> len(pages)
            25
            >>> pages
            [0, 1, 2, ..., 24]
        """
        if not isinstance(pdf_path, Path):
            pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            # Convert PDF to images
            logger.info(f"Converting PDF to images: {pdf_path.name}")
            images = self._extract_pages_as_images(pdf_path, dpi=dpi)

            if not images:
                raise RuntimeError(f"No pages extracted from PDF: {pdf_path}")

            # Generate embeddings for all pages
            logger.info(f"Generating embeddings for {len(images)} pages")
            embeddings = self.embed_batch_images(images)
            page_numbers = list(range(len(images)))

            logger.info(f"Embedded {len(images)} pages successfully")
            return embeddings, page_numbers

        except Exception as e:
            logger.error(f"Document embedding failed for {pdf_path}: {e}")
            raise RuntimeError(f"Failed to embed document: {e}") from e

    def embed_with_fallback(self, image, retry_on_cpu: bool = True) -> np.ndarray:
        """
        Generate embedding with automatic CPU fallback on GPU OOM.

        Note:
            Deprecated in v0.5.2. OOM handling is now automatic when
            enable_oom_recovery=True (default). This method now simply
            calls embed_page() which has built-in OOM recovery.

        Args:
            image: Document page image (PIL Image)
            retry_on_cpu: Ignored (kept for backward compatibility)

        Returns:
            Vision embedding (128-dim numpy array)

        Raises:
            RuntimeError: If embedding fails after all recovery attempts

        Example:
            >>> embedder = ColPaliEmbedder(device="cuda")
            >>> image = Image.open("large_diagram.png")
            >>> embedding = embedder.embed_with_fallback(image)
            >>> embedding.shape
            (128,)
        """
        # OOM handling is now automatic via OOMHandler
        # This method is kept for backward compatibility
        logger.debug(
            "embed_with_fallback() is deprecated. Use embed_page() instead "
            "(OOM recovery is now automatic)"
        )
        return self.embed_page(image)
