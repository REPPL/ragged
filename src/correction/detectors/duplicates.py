"""Duplicate page detection using layered hashing approach.

v0.3.5: Detects duplicate pages using quick hash, perceptual hash, and text similarity.
"""

import hashlib
from collections import defaultdict
from pathlib import Path

import pymupdf
from PIL import Image

from src.correction.schemas import IssueReport, IssueType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DuplicateDetector:
    """Detects duplicate pages in PDFs.

    Uses layered approach:
    - Layer 1: Quick hash (MD5 of rendered page at low resolution)
    - Layer 2: Perceptual hash (difference hash for near-duplicates)
    - Layer 3: Content comparison (text similarity for validation)

    Confidence threshold: 0.95 (95% similarity required for duplicate detection)
    """

    def __init__(self, confidence_threshold: float = 0.95, similarity_threshold: float = 0.95):
        """Initialize duplicate detector.

        Args:
            confidence_threshold: Minimum confidence to report duplicate (0.0-1.0).
            similarity_threshold: Minimum similarity score to consider pages duplicates (0.0-1.0).
        """
        self.confidence_threshold = confidence_threshold
        self.similarity_threshold = similarity_threshold

    async def detect(self, pdf_path: Path) -> list[IssueReport]:
        """Detect duplicate pages in PDF.

        Args:
            pdf_path: Path to the PDF file to analyse.

        Returns:
            List of IssueReports for detected duplicates.
        """
        issues = []

        try:
            doc = pymupdf.open(pdf_path)

            # Layer 1: Quick hash - find exact duplicates
            quick_hash_groups = self._find_exact_duplicates(doc)

            # Layer 2 & 3: Perceptual hash and text similarity for near-duplicates
            perceptual_groups = self._find_near_duplicates(doc)

            # Merge duplicate groups
            all_duplicate_groups = self._merge_duplicate_groups(
                quick_hash_groups, perceptual_groups
            )

            # Create issues for each duplicate group
            for group in all_duplicate_groups:
                if len(group) > 1:
                    # Calculate confidence based on detection method
                    # Exact duplicates = 1.0, near-duplicates = similarity score
                    if group in quick_hash_groups:
                        confidence = 1.0
                    else:
                        # Use average perceptual hash similarity
                        confidence = self.similarity_threshold

                    # First page in group is original, rest are duplicates
                    original_page = min(group)
                    duplicate_pages = [p for p in group if p != original_page]

                    issues.append(
                        IssueReport(
                            issue_type=IssueType.DUPLICATE,
                            page_numbers=duplicate_pages,
                            confidence=confidence,
                            severity="high" if len(duplicate_pages) > 2 else "medium",
                            details=(
                                f"Pages {', '.join(map(str, duplicate_pages))} are duplicates "
                                f"of page {original_page}"
                            ),
                            suggested_correction=f"Remove duplicate pages: {', '.join(map(str, duplicate_pages))}",
                            metadata={
                                "original_page": original_page,
                                "duplicate_count": len(duplicate_pages),
                                "all_pages_in_group": sorted(group),
                            },
                        )
                    )

            doc.close()

        except Exception as e:
            logger.error(f"Duplicate detection failed for {pdf_path}: {e}", exc_info=True)
            return []

        logger.debug(f"Duplicate detection: {len(issues)} duplicate groups found")
        return issues

    def _find_exact_duplicates(self, doc: pymupdf.Document) -> list[set[int]]:
        """Find exact duplicate pages using quick hash.

        Args:
            doc: PyMuPDF document object.

        Returns:
            List of sets, each containing page numbers of exact duplicates.
        """
        hash_to_pages = defaultdict(set)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render page at low resolution for quick hashing
            pix = page.get_pixmap(matrix=pymupdf.Matrix(0.5, 0.5))  # 50% scale
            img_bytes = pix.tobytes()

            # Quick hash (MD5)
            quick_hash = hashlib.md5(img_bytes).hexdigest()
            hash_to_pages[quick_hash].add(page_num + 1)  # 1-indexed

        # Return groups with more than one page
        return [pages for pages in hash_to_pages.values() if len(pages) > 1]

    def _find_near_duplicates(self, doc: pymupdf.Document) -> list[set[int]]:
        """Find near-duplicate pages using perceptual hashing and text similarity.

        Args:
            doc: PyMuPDF document object.

        Returns:
            List of sets, each containing page numbers of near-duplicates.
        """
        # Store page hashes and text
        page_data = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Compute perceptual hash (difference hash)
            dhash = self._compute_dhash(page)

            # Extract text for content comparison
            text = page.get_text()

            page_data.append({
                "page_num": page_num + 1,  # 1-indexed
                "dhash": dhash,
                "text": text,
            })

        # Find similar pages
        duplicate_groups = []
        processed = set()

        for i, page_i in enumerate(page_data):
            if page_i["page_num"] in processed:
                continue

            similar_pages = {page_i["page_num"]}

            for j, page_j in enumerate(page_data[i + 1 :], start=i + 1):
                if page_j["page_num"] in processed:
                    continue

                # Compare hashes
                hash_similarity = self._compare_hashes(
                    page_i["dhash"], page_j["dhash"]
                )

                # Compare text
                text_similarity = self._compare_text(page_i["text"], page_j["text"])

                # Consider pages near-duplicates if both hash and text similarity are high
                if (
                    hash_similarity >= self.similarity_threshold
                    and text_similarity >= self.similarity_threshold
                ):
                    similar_pages.add(page_j["page_num"])
                    processed.add(page_j["page_num"])

            if len(similar_pages) > 1:
                duplicate_groups.append(similar_pages)
                processed.update(similar_pages)

        return duplicate_groups

    def _compute_dhash(self, page: pymupdf.Page, hash_size: int = 8) -> str:
        """Compute difference hash (dHash) for a page.

        Args:
            page: PyMuPDF page object.
            hash_size: Size of hash (8 = 64-bit hash).

        Returns:
            Hexadecimal string representation of hash.
        """
        # Render page to image at low resolution
        pix = page.get_pixmap(matrix=pymupdf.Matrix(0.3, 0.3))  # 30% scale

        # Convert to PIL Image
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Resize to hash_size + 1 x hash_size
        img = img.convert("L")  # Grayscale
        img = img.resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)

        # Compute differences
        pixels = list(img.getdata())
        difference = []

        for row in range(hash_size):
            for col in range(hash_size):
                pixel_left = pixels[row * (hash_size + 1) + col]
                pixel_right = pixels[row * (hash_size + 1) + col + 1]
                difference.append(pixel_left > pixel_right)

        # Convert to hexadecimal
        decimal_value = 0
        for bit in difference:
            decimal_value = (decimal_value << 1) | bit

        return format(decimal_value, '016x')

    def _compare_hashes(self, hash1: str, hash2: str) -> float:
        """Compare two perceptual hashes using Hamming distance.

        Args:
            hash1: First hash.
            hash2: Second hash.

        Returns:
            Similarity score (0.0-1.0), where 1.0 is identical.
        """
        if hash1 == hash2:
            return 1.0

        # Convert to binary and compute Hamming distance
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        xor = int1 ^ int2

        # Count number of different bits
        hamming_distance = bin(xor).count('1')

        # Convert to similarity (max distance = 64 for 8x8 hash)
        max_distance = 64
        similarity = 1.0 - (hamming_distance / max_distance)

        return similarity

    def _compare_text(self, text1: str, text2: str) -> float:
        """Compare two text strings using simple similarity metric.

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Similarity score (0.0-1.0), where 1.0 is identical.
        """
        if not text1 and not text2:
            return 1.0

        if not text1 or not text2:
            return 0.0

        # Normalize text
        text1_norm = text1.lower().strip()
        text2_norm = text2.lower().strip()

        if text1_norm == text2_norm:
            return 1.0

        # Simple character-level similarity (Jaccard index on character sets)
        set1 = set(text1_norm)
        set2 = set(text2_norm)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def _merge_duplicate_groups(
        self, quick_groups: list[set[int]], perceptual_groups: list[set[int]]
    ) -> list[set[int]]:
        """Merge duplicate groups from different detection methods.

        Args:
            quick_groups: Duplicate groups from quick hash.
            perceptual_groups: Duplicate groups from perceptual hash.

        Returns:
            Merged list of duplicate groups.
        """
        # Use quick groups as base (they have higher confidence)
        all_groups = list(quick_groups)

        # Add perceptual groups that don't overlap with quick groups
        for perceptual_group in perceptual_groups:
            # Check if this group overlaps with any existing group
            overlaps = False
            for quick_group in quick_groups:
                if perceptual_group & quick_group:  # Intersection not empty
                    overlaps = True
                    break

            if not overlaps:
                all_groups.append(perceptual_group)

        return all_groups
