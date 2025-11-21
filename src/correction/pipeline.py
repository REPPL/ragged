"""PDF correction pipeline integration.

v0.3.5: Integrates PDF analysis and correction into document ingestion.
"""

from pathlib import Path

from src.correction.analyzer import PDFAnalyzer, AnalyzerConfig
from src.correction.corrector import PDFCorrector, CorrectorConfig
from src.correction.schemas import AnalysisResult, CorrectionResult
from src.correction.transformers import (
    RotationTransformer,
    DuplicateRemover,
    PageReorderTransformer,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CorrectionPipeline:
    """Coordinates PDF analysis and correction for document ingestion.

    Provides a high-level interface for analyzing and correcting PDFs
    with sensible defaults and automatic transformer registration.
    """

    def __init__(
        self,
        analyzer_config: AnalyzerConfig | None = None,
        corrector_config: CorrectorConfig | None = None,
    ):
        """Initialize correction pipeline.

        Args:
            analyzer_config: Optional analyzer configuration.
            corrector_config: Optional corrector configuration.
        """
        # Create analyzer with default config
        self.analyzer = PDFAnalyzer(analyzer_config or AnalyzerConfig())

        # Register detectors
        from src.correction.detectors import (
            RotationDetector,
            PageOrderDetector,
            DuplicateDetector,
            QualityDetector,
        )

        self.analyzer.register_detector("rotation", RotationDetector())
        self.analyzer.register_detector("ordering", PageOrderDetector())
        self.analyzer.register_detector("duplicate", DuplicateDetector())
        self.analyzer.register_detector("quality", QualityDetector())

        # Create corrector with default config
        self.corrector = PDFCorrector(corrector_config or CorrectorConfig())

        # Register transformers
        self.corrector.register_transformer("rotation", RotationTransformer())
        self.corrector.register_transformer("duplicates", DuplicateRemover())
        self.corrector.register_transformer("ordering", PageReorderTransformer())

        logger.debug("Correction pipeline initialized")

    async def analyze_and_correct(
        self,
        pdf_path: Path,
        output_path: Path | None = None,
    ) -> tuple[AnalysisResult, CorrectionResult | None]:
        """Analyze and optionally correct a PDF.

        Args:
            pdf_path: Path to PDF file to analyze.
            output_path: Optional path for corrected PDF. If None, no correction applied.

        Returns:
            Tuple of (AnalysisResult, CorrectionResult or None).
            CorrectionResult is None if no corrections were needed or output_path not provided.
        """
        logger.info(f"Analyzing PDF: {pdf_path}")

        # Run analysis
        analysis = await self.analyzer.analyze(pdf_path)

        logger.info(
            f"Analysis complete: {len(analysis.issues)} issues found, "
            f"quality={analysis.quality_grade.value}"
        )

        # Apply corrections if needed and output path provided
        correction_result = None
        if analysis.requires_correction and output_path:
            logger.info("Applying corrections...")
            correction_result = self.corrector.correct(pdf_path, analysis, output_path)
            logger.info(
                f"Corrections applied: {len([a for a in correction_result.actions if a.success])}"
                f"/{len(correction_result.actions)} successful"
            )

        return analysis, correction_result

    def format_analysis_summary(self, analysis: AnalysisResult) -> dict[str, str]:
        """Format analysis results for display.

        Args:
            analysis: Analysis results.

        Returns:
            Dictionary with formatted strings for display.
        """
        # Quality indicator
        quality_score = analysis.overall_quality_score
        quality_grade = analysis.quality_grade.value.capitalize()

        if quality_score >= 0.90:
            quality_icon = "✓"
            quality_color = "green"
        elif quality_score >= 0.70:
            quality_icon = "✓"
            quality_color = "yellow"
        else:
            quality_icon = "⚠"
            quality_color = "red"

        # Issue summary
        issue_summary = []
        issue_types = {}
        for issue in analysis.issues:
            issue_type = issue.issue_type.value
            if issue_type not in issue_types:
                issue_types[issue_type] = 0
            issue_types[issue_type] += 1

        if issue_types:
            for issue_type, count in sorted(issue_types.items()):
                issue_summary.append(f"{count} {issue_type}")

        return {
            "quality_icon": quality_icon,
            "quality_color": quality_color,
            "quality_score": f"{quality_score:.0%}",
            "quality_grade": quality_grade,
            "issue_count": str(len(analysis.issues)),
            "issue_summary": ", ".join(issue_summary) if issue_summary else "none",
            "requires_correction": str(analysis.requires_correction),
        }
