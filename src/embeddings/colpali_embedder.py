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

from ragged.embeddings.base import BaseEmbedder

logger = logging.getLogger(__name__)


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

    Attributes:
        model_name (str): HuggingFace model identifier
        device (str): Computation device ('cuda', 'mps', or 'cpu')
        batch_size (int): Number of pages to process simultaneously
        cache_dir (Optional[Path]): Model cache directory
        model: Loaded ColPali model
        processor: Image preprocessing pipeline

    Example:
        >>> embedder = ColPaliEmbedder()
        >>> image = Image.open("document_page.png")
        >>> embedding = embedder.embed_page(image)
        >>> embedding.shape
        (128,)
        >>> embedder.get_device_info()
        {'device': 'cuda', 'name': 'NVIDIA RTX 4090', 'vram_free_gb': 18.5}
    """

    def __init__(
        self,
        model_name: str = "vidore/colpali-v1.3-hf",
        device: Optional[str] = None,
        batch_size: int = 4,
        cache_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialise ColPali vision embedder.

        Args:
            model_name: HuggingFace model identifier for ColPali
                       Default: "vidore/colpali-v1.3-hf" (native transformers support)
            device: Computation device ('cuda', 'mps', 'cpu', or None for auto-detect)
                   Priority: CUDA > MPS > CPU
            batch_size: Number of pages to process in parallel
                       Guidelines: 4GB VRAM=1-2, 8GB=4-6, 16GB=8-12, 24GB+=16-32
            cache_dir: Directory for model cache (None = HuggingFace default ~/.cache)

        Raises:
            RuntimeError: If model fails to load
            ValueError: If specified device is unavailable

        Example:
            >>> # Auto-detect best device
            >>> embedder = ColPaliEmbedder()
            >>> # Force specific device
            >>> embedder = ColPaliEmbedder(device="cuda", batch_size=8)
            >>> # Custom cache location
            >>> embedder = ColPaliEmbedder(cache_dir=Path("/mnt/models"))
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.cache_dir = cache_dir

        # Detect optimal device
        self.device = self._detect_device(device)

        logger.info(f"Initialising ColPali embedder on device: {self.device}")

        # Load model and processor
        self._load_model()

        logger.info("ColPali embedder initialised successfully")

    def _detect_device(self, device: Optional[str]) -> str:
        """
        Detect optimal computation device (GPU/CPU).

        Device selection priority: CUDA > MPS (Apple Silicon) > CPU

        Args:
            device: User-specified device or None for auto-detect

        Returns:
            Device string ('cuda', 'mps', or 'cpu')

        Raises:
            ValueError: If specified device is unavailable

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder._detect_device(None)  # Auto-detect
            'cuda'  # On NVIDIA system
            >>> embedder._detect_device("mps")  # Force MPS
            'mps'  # On Apple Silicon
        """
        if device:
            # Validate user-specified device
            if device == "cuda" and not torch.cuda.is_available():
                raise ValueError(
                    "CUDA device requested but not available. "
                    "Ensure NVIDIA GPU is present and CUDA toolkit is installed. "
                    "See docs/tutorials/installation.md for setup instructions."
                )
            if device == "mps" and not torch.backends.mps.is_available():
                raise ValueError(
                    "MPS device requested but not available. "
                    "Ensure you're on Apple Silicon (M1/M2/M3) with macOS 12.3+. "
                    "See docs/tutorials/installation.md for setup instructions."
                )
            logger.info(f"Using user-specified device: {device}")
            return device

        # Auto-detect optimal device
        if torch.cuda.is_available():
            cuda_device = torch.cuda.current_device()
            cuda_name = torch.cuda.get_device_name(cuda_device)
            vram_gb = torch.cuda.get_device_properties(cuda_device).total_memory / 1e9
            logger.info(f"CUDA available: {cuda_name} ({vram_gb:.1f}GB VRAM)")
            return "cuda"

        if torch.backends.mps.is_available():
            logger.info("MPS (Apple Silicon GPU) available")
            return "mps"

        logger.warning(
            "No GPU available, using CPU. "
            "Vision embedding will be 10x+ slower. "
            "Consider adding GPU support for production use. "
            "See docs/tutorials/installation.md for GPU setup."
        )
        return "cpu"

    def _load_model(self) -> None:
        """
        Load ColPali model and processor from HuggingFace.

        Downloads model on first use (~1.2GB, cached locally).
        Uses bfloat16 precision on CUDA for efficiency, float32 on MPS/CPU.

        Raises:
            RuntimeError: If model loading fails
            ImportError: If transformers library is not installed

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> # Model automatically loaded during initialization
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
            # Determine optimal dtype
            dtype = torch.bfloat16 if self.device == "cuda" else torch.float32

            logger.info(f"Loading ColPali model: {self.model_name}")
            logger.info(f"Using dtype: {dtype}, device: {self.device}")

            # Load model with HuggingFace transformers
            self.model = AutoModel.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                cache_dir=str(self.cache_dir) if self.cache_dir else None,
                device_map=self.device if self.device != "cpu" else None,
            )

            # Move to device if not using device_map
            if self.device == "cpu":
                self.model = self.model.to(self.device)

            self.model.eval()  # Set to inference mode (disable dropout, etc.)

            logger.info("Model loaded successfully")

            # Load processor (handles image preprocessing)
            logger.info("Loading ColPali processor")
            self.processor = AutoProcessor.from_pretrained(
                self.model_name, cache_dir=str(self.cache_dir) if self.cache_dir else None
            )

            logger.info("Processor loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load ColPali model: {e}")
            raise RuntimeError(
                f"ColPali model loading failed: {e}. "
                f"Ensure model '{self.model_name}' exists on HuggingFace and "
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
    def model_name_property(self) -> str:
        """
        Get the name of the embedding model (BaseEmbedder property).

        Returns:
            Model name string

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.model_name_property
            'vidore/colpali-v1.3-hf'
        """
        return self.model_name

    def get_device_info(self) -> dict[str, str | float]:
        """
        Get information about computation device.

        Returns:
            Dictionary with device type, name, and available memory (if GPU)

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.get_device_info()
            {'device': 'cuda', 'name': 'NVIDIA RTX 4090', 'vram_total_gb': 24.0, 'vram_free_gb': 18.5}
        """
        info: dict[str, str | float] = {"device": self.device}

        if self.device == "cuda":
            device_props = torch.cuda.get_device_properties(0)
            info["name"] = torch.cuda.get_device_name(0)
            info["vram_total_gb"] = device_props.total_memory / 1e9
            info["vram_free_gb"] = (
                device_props.total_memory - torch.cuda.memory_allocated(0)
            ) / 1e9
        elif self.device == "mps":
            info["name"] = "Apple Silicon GPU"
        else:
            info["name"] = "CPU"

        return info

    def estimate_batch_size_for_vram(self, available_vram_gb: float) -> int:
        """
        Estimate optimal batch size based on available VRAM.

        Rule of thumb for ColPali: 2GB base + 0.5GB per page in batch

        Args:
            available_vram_gb: Available VRAM in GB

        Returns:
            Recommended batch size (capped at 32)

        Example:
            >>> embedder = ColPaliEmbedder()
            >>> embedder.estimate_batch_size_for_vram(8.0)
            12  # (8GB - 2GB base) / 0.5GB per page = 12
            >>> embedder.estimate_batch_size_for_vram(4.0)
            4   # (4GB - 2GB base) / 0.5GB per page = 4
        """
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
        Generate vision embedding for a single document page.

        Processes the image through ColPali model and returns mean-pooled
        128-dimensional embedding vector.

        Args:
            image: PIL Image of document page (any size, will be resized by processor)

        Returns:
            128-dimensional vision embedding as numpy array

        Raises:
            ValueError: If image is invalid or wrong type
            RuntimeError: If embedding generation fails

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
        Generate vision embeddings for multiple pages (batched for efficiency).

        Processes images in batches determined by self.batch_size for optimal
        GPU memory usage and throughput.

        Args:
            images: List of PIL Images (document pages)

        Returns:
            Array of shape (n_images, 128) containing embeddings

        Raises:
            ValueError: If images list is empty
            RuntimeError: If batch processing fails

        Example:
            >>> from PIL import Image
            >>> embedder = ColPaliEmbedder(batch_size=4)
            >>> pages = [Image.open(f"page{i}.png") for i in range(10)]
            >>> embeddings = embedder.embed_batch_images(pages)
            >>> embeddings.shape
            (10, 128)
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

        embeddings_list = []

        # Process in batches for efficiency
        for i in range(0, len(images), self.batch_size):
            batch = images[i : i + self.batch_size]

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

                logger.debug(f"Processed batch {i // self.batch_size + 1} ({len(batch)} images)")

            except Exception as e:
                logger.error(f"Batch {i // self.batch_size} failed: {e}")
                raise RuntimeError(f"Batch embedding failed at index {i}: {e}") from e

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

        Attempts to generate embedding on configured device (GPU),
        and automatically retries on CPU if GPU runs out of memory.

        Args:
            image: Document page image (PIL Image)
            retry_on_cpu: If GPU fails with OOM, retry on CPU

        Returns:
            Vision embedding (128-dim numpy array)

        Raises:
            RuntimeError: If both GPU and CPU attempts fail

        Example:
            >>> embedder = ColPaliEmbedder(device="cuda")
            >>> image = Image.open("large_diagram.png")
            >>> embedding = embedder.embed_with_fallback(image)
            # If GPU OOM occurs, automatically retries on CPU
            >>> embedding.shape
            (128,)
        """
        try:
            return self.embed_page(image)

        except RuntimeError as e:
            error_msg = str(e).lower()

            # Check if error is GPU out-of-memory
            is_oom = any(
                keyword in error_msg
                for keyword in ["out of memory", "oom", "cuda error", "mps error"]
            )

            if is_oom and retry_on_cpu and self.device != "cpu":
                logger.warning(
                    f"GPU out of memory on {self.device}, retrying on CPU. "
                    f"Consider reducing batch size or using lower resolution images."
                )

                # Temporarily switch to CPU
                original_device = self.device
                self.device = "cpu"
                self.model = self.model.to("cpu")

                try:
                    result = self.embed_page(image)

                    # Restore original device
                    self.device = original_device
                    self.model = self.model.to(original_device)

                    logger.info(f"CPU fallback successful, restored to {original_device}")
                    return result

                except Exception as cpu_error:
                    logger.error(f"CPU fallback also failed: {cpu_error}")
                    raise RuntimeError(
                        f"Embedding failed on both {original_device} and CPU: {cpu_error}"
                    ) from cpu_error
            else:
                # Not an OOM error, or CPU fallback disabled, or already on CPU
                raise
