"""PDF analysis coordinator for detecting document issues.

v0.3.5: Orchestrates parallel detection of rotation, ordering, duplicates, and quality issues.
"""

import asyncio
import time
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from src.correction.schemas import AnalysisResult, IssueReport, QualityGrade
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DetectorProtocol(Protocol):
    """Protocol that all detectors must implement."""

    async def detect(self, pdf_path: Path) -> list[IssueReport]:
        """Detect issues in the PDF.

        Args:
            pdf_path: Path to the PDF file to analyse.

        Returns:
            List of detected issues.
        """
        ...


class AnalyzerConfig(BaseModel):
    """Configuration for PDFAnalyzer.

    Attributes:
        rotation_enabled: Whether to run rotation detection.
        ordering_enabled: Whether to run page ordering detection.
        duplicate_enabled: Whether to run duplicate detection.
        quality_enabled: Whether to run quality detection.
        parallel_execution: Whether to run detectors in parallel.
        timeout_seconds: Maximum time for analysis in seconds.
        confidence_thresholds: Confidence thresholds for each detector.
    """

    rotation_enabled: bool = Field(default=True, description="Enable rotation detection")
    ordering_enabled: bool = Field(default=True, description="Enable ordering detection")
    duplicate_enabled: bool = Field(default=True, description="Enable duplicate detection")
    quality_enabled: bool = Field(default=True, description="Enable quality detection")
    parallel_execution: bool = Field(default=True, description="Run detectors in parallel")
    timeout_seconds: float = Field(default=120.0, gt=0, description="Analysis timeout")
    confidence_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "rotation": 0.85,
            "ordering": 0.80,
            "duplicate": 0.95,
            "quality": 0.70,
        },
        description="Confidence thresholds per detector",
    )


class PDFAnalyzer:
    """Coordinates PDF analysis using multiple parallel detectors.

    The analyzer runs detectors for rotation, page ordering, duplicates,
    and quality issues. Results are aggregated into a comprehensive
    AnalysisResult that guides the correction pipeline.

    Example:
        >>> analyzer = PDFAnalyzer()
        >>> result = await analyzer.analyze(Path("messy.pdf"))
        >>> if result.requires_correction:
        ...     print(f"Found {len(result.issues)} issues")
    """

    def __init__(self, config: AnalyzerConfig | None = None):
        """Initialize the PDF analyzer.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or AnalyzerConfig()
        self._detectors: dict[str, DetectorProtocol] = {}

    def register_detector(self, name: str, detector: DetectorProtocol) -> None:
        """Register a detector for use in analysis.

        Args:
            name: Detector name (e.g., "rotation", "ordering").
            detector: Detector instance implementing DetectorProtocol.
        """
        self._detectors[name] = detector
        logger.debug(f"Registered detector: {name}")

    async def analyze(self, pdf_path: Path) -> AnalysisResult:
        """Analyze a PDF document for issues.

        Runs all enabled detectors (optionally in parallel) and aggregates
        results into a comprehensive AnalysisResult.

        Args:
            pdf_path: Path to the PDF file to analyse.

        Returns:
            AnalysisResult containing detected issues and quality assessment.

        Raises:
            FileNotFoundError: If PDF file does not exist.
            TimeoutError: If analysis exceeds timeout threshold.
            ValueError: If PDF is invalid or cannot be analysed.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.suffix.lower() == ".pdf":
            raise ValueError(f"File is not a PDF: {pdf_path}")

        logger.info(f"Starting PDF analysis: {pdf_path}")
        start_time = time.time()

        try:
            # Run detectors
            if self.config.parallel_execution:
                issues = await self._run_parallel(pdf_path)
            else:
                issues = await self._run_sequential(pdf_path)

            # Compute analysis results
            analysis_duration = time.time() - start_time
            result = self._create_analysis_result(
                pdf_path=pdf_path,
                issues=issues,
                analysis_duration=analysis_duration,
            )

            logger.info(
                f"Analysis complete: {len(issues)} issues, "
                f"quality={result.quality_grade.value}, "
                f"duration={analysis_duration:.2f}s"
            )

            return result

        except TimeoutError as e:
            duration = time.time() - start_time
            logger.error(f"Analysis timeout after {duration:.2f}s: {pdf_path}")
            raise TimeoutError(
                f"PDF analysis exceeded timeout of {self.config.timeout_seconds}s"
            ) from e

    async def _run_parallel(self, pdf_path: Path) -> list[IssueReport]:
        """Run all enabled detectors in parallel.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Aggregated list of issues from all detectors.
        """
        tasks = []

        # Create tasks for each enabled detector
        detector_map = {
            "rotation": self.config.rotation_enabled,
            "ordering": self.config.ordering_enabled,
            "duplicate": self.config.duplicate_enabled,
            "quality": self.config.quality_enabled,
        }

        for detector_name, enabled in detector_map.items():
            if enabled and detector_name in self._detectors:
                detector = self._detectors[detector_name]
                task = asyncio.create_task(
                    self._run_detector_safe(detector_name, detector, pdf_path)
                )
                tasks.append(task)

        # Wait for all tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.timeout_seconds,
            )
        except TimeoutError:
            # Cancel all running tasks
            for task in tasks:
                task.cancel()
            raise

        # Flatten results (filter out exceptions)
        issues = []
        for result in results:
            if isinstance(result, list):
                issues.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Detector raised exception: {result}")

        return issues

    async def _run_sequential(self, pdf_path: Path) -> list[IssueReport]:
        """Run all enabled detectors sequentially.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            Aggregated list of issues from all detectors.
        """
        issues = []

        detector_map = {
            "rotation": self.config.rotation_enabled,
            "ordering": self.config.ordering_enabled,
            "duplicate": self.config.duplicate_enabled,
            "quality": self.config.quality_enabled,
        }

        for detector_name, enabled in detector_map.items():
            if enabled and detector_name in self._detectors:
                detector = self._detectors[detector_name]
                try:
                    detector_issues = await self._run_detector_safe(
                        detector_name, detector, pdf_path
                    )
                    issues.extend(detector_issues)
                except Exception as e:
                    logger.warning(f"Detector {detector_name} failed: {e}")

        return issues

    async def _run_detector_safe(
        self, name: str, detector: DetectorProtocol, pdf_path: Path
    ) -> list[IssueReport]:
        """Run a detector with error handling and confidence filtering.

        Args:
            name: Detector name.
            detector: Detector instance.
            pdf_path: Path to the PDF file.

        Returns:
            List of issues that meet confidence threshold.
        """
        try:
            logger.debug(f"Running detector: {name}")
            issues = await detector.detect(pdf_path)

            # Filter by confidence threshold
            threshold = self.config.confidence_thresholds.get(name, 0.0)
            filtered_issues = [
                issue for issue in issues if issue.confidence >= threshold
            ]

            logger.debug(
                f"Detector {name}: {len(filtered_issues)}/{len(issues)} "
                f"issues above threshold {threshold}"
            )

            return filtered_issues

        except Exception as e:
            logger.error(f"Detector {name} failed: {e}", exc_info=True)
            return []

    def _create_analysis_result(
        self,
        pdf_path: Path,
        issues: list[IssueReport],
        analysis_duration: float,
    ) -> AnalysisResult:
        """Create an AnalysisResult from detected issues.

        Args:
            pdf_path: Path to analysed PDF.
            issues: List of detected issues.
            analysis_duration: Time taken for analysis in seconds.

        Returns:
            Comprehensive AnalysisResult.
        """
        # Estimate total pages (will be properly detected by detectors)
        # For now, use metadata from issues or default to 1
        total_pages = 1
        if issues:
            all_pages = set()
            for issue in issues:
                all_pages.update(issue.page_numbers)
            if all_pages:
                total_pages = max(all_pages)

        # Compute overall quality score from quality detector issues
        # or default to 1.0 if no quality issues detected
        quality_issues = [
            issue for issue in issues if issue.issue_type.value == "quality"
        ]

        if quality_issues:
            # Average confidence of quality issues (inverted - low confidence = problem)
            avg_confidence = sum(issue.confidence for issue in quality_issues) / len(
                quality_issues
            )
            overall_quality_score = avg_confidence
        else:
            # No quality issues detected = high quality
            overall_quality_score = 0.95

        # Determine if correction is required
        requires_correction = len(issues) > 0

        # Estimate correction time (very rough heuristic)
        estimated_correction_time = None
        if requires_correction:
            # Base time + per-issue time + per-page time
            base_time = 5.0  # seconds
            per_issue_time = 2.0
            per_page_time = 0.5
            affected_pages = set()
            for issue in issues:
                affected_pages.update(issue.page_numbers)

            estimated_correction_time = (
                base_time
                + len(issues) * per_issue_time
                + len(affected_pages) * per_page_time
            )

        return AnalysisResult(
            document_path=pdf_path,
            total_pages=total_pages,
            issues=issues,
            requires_correction=requires_correction,
            overall_quality_score=overall_quality_score,
            quality_grade=QualityGrade.EXCELLENT,  # Will be computed by validator
            estimated_correction_time=estimated_correction_time,
            analysis_duration=analysis_duration,
            metadata={
                "detectors_run": list(self._detectors.keys()),
                "parallel_execution": self.config.parallel_execution,
            },
        )
