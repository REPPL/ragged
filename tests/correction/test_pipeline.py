"""Tests for PDF correction pipeline.

v0.3.5: Tests for CorrectionPipeline integration.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.correction.pipeline import CorrectionPipeline
from src.correction.schemas import (
    AnalysisResult,
    CorrectionAction,
    CorrectionResult,
    IssueReport,
    IssueType,
    QualityGrade,
)


@pytest.fixture
def mock_pdf_path(tmp_path):
    """Create a mock PDF file."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\nMock PDF content")
    return pdf_file


@pytest.fixture
def mock_analysis_clean():
    """Create a clean analysis result (no issues)."""
    return AnalysisResult(
        document_path=Path("test.pdf"),
        total_pages=10,
        overall_quality_score=0.95,
        quality_grade=QualityGrade.EXCELLENT,
        requires_correction=False,
        analysis_duration=1.5,
        issues=[],
        metadata={},
    )


@pytest.fixture
def mock_analysis_with_issues():
    """Create an analysis result with issues."""
    return AnalysisResult(
        document_path=Path("test.pdf"),
        total_pages=10,
        overall_quality_score=0.65,
        quality_grade=QualityGrade.FAIR,
        requires_correction=True,
        analysis_duration=2.3,
        issues=[
            IssueReport(
                issue_type=IssueType.ROTATION,
                page_numbers=[1, 2],
                confidence=0.95,
                severity="high",
                details="Pages rotated 90 degrees",
                suggested_correction="Rotate pages counter-clockwise",
            ),
            IssueReport(
                issue_type=IssueType.DUPLICATE,
                page_numbers=[5, 6],
                confidence=0.90,
                severity="medium",
                details="Duplicate pages detected",
                suggested_correction="Remove duplicate pages",
            ),
        ],
        metadata={},
    )


@pytest.fixture
def mock_correction_result():
    """Create a mock correction result."""
    return CorrectionResult(
        original_path=Path("test.pdf"),
        corrected_path=Path("corrected.pdf"),
        quality_before=0.65,
        quality_after=0.90,
        improvement=0.25,
        total_duration=5.2,
        actions=[
            CorrectionAction(
                action_type="rotation",
                pages_affected=[1, 2],
                success=True,
                issue=IssueReport(
                    issue_type=IssueType.ROTATION,
                    page_numbers=[1, 2],
                    confidence=0.95,
                    severity="high",
                    details="Pages rotated 90 degrees",
                    suggested_correction="Rotate pages counter-clockwise",
                ),
            ),
        ],
    )


class TestCorrectionPipeline:
    """Tests for CorrectionPipeline."""

    def test_pipeline_initialization(self):
        """Test pipeline initializes with default config."""
        pipeline = CorrectionPipeline()

        assert pipeline.analyzer is not None
        assert pipeline.corrector is not None

        # Verify detectors registered
        assert "rotation" in pipeline.analyzer._detectors
        assert "ordering" in pipeline.analyzer._detectors
        assert "duplicate" in pipeline.analyzer._detectors
        assert "quality" in pipeline.analyzer._detectors

        # Verify transformers registered
        assert "rotation" in pipeline.corrector._transformers
        assert "duplicates" in pipeline.corrector._transformers
        assert "ordering" in pipeline.corrector._transformers

    def test_pipeline_with_custom_config(self):
        """Test pipeline accepts custom configurations."""
        from src.correction.analyzer import AnalyzerConfig
        from src.correction.corrector import CorrectorConfig

        analyzer_config = AnalyzerConfig(parallel_execution=False, timeout_seconds=60.0)
        corrector_config = CorrectorConfig(keep_checkpoints=True, max_attempts=5)

        pipeline = CorrectionPipeline(
            analyzer_config=analyzer_config,
            corrector_config=corrector_config,
        )

        assert pipeline.analyzer.config.parallel_execution is False
        assert pipeline.analyzer.config.timeout_seconds == 60.0
        assert pipeline.corrector.config.keep_checkpoints is True
        assert pipeline.corrector.config.max_attempts == 5

    @pytest.mark.asyncio
    async def test_analyze_and_correct_clean_pdf(
        self, mock_pdf_path, mock_analysis_clean
    ):
        """Test pipeline with clean PDF (no corrections needed)."""
        pipeline = CorrectionPipeline()

        with patch.object(
            pipeline.analyzer, "analyze", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = mock_analysis_clean

            analysis, correction = await pipeline.analyze_and_correct(
                mock_pdf_path, mock_pdf_path.parent / "output.pdf"
            )

            assert analysis == mock_analysis_clean
            assert correction is None  # No correction needed
            mock_analyze.assert_called_once_with(mock_pdf_path)

    @pytest.mark.asyncio
    async def test_analyze_and_correct_with_issues(
        self, mock_pdf_path, mock_analysis_with_issues, mock_correction_result
    ):
        """Test pipeline with PDF requiring corrections."""
        pipeline = CorrectionPipeline()
        output_path = mock_pdf_path.parent / "corrected.pdf"

        with patch.object(
            pipeline.analyzer, "analyze", new_callable=AsyncMock
        ) as mock_analyze, patch.object(
            pipeline.corrector, "correct"
        ) as mock_correct:
            mock_analyze.return_value = mock_analysis_with_issues
            mock_correct.return_value = mock_correction_result

            analysis, correction = await pipeline.analyze_and_correct(
                mock_pdf_path, output_path
            )

            assert analysis == mock_analysis_with_issues
            assert correction == mock_correction_result

            mock_analyze.assert_called_once_with(mock_pdf_path)
            mock_correct.assert_called_once_with(
                mock_pdf_path, mock_analysis_with_issues, output_path
            )

    @pytest.mark.asyncio
    async def test_analyze_only_no_output_path(
        self, mock_pdf_path, mock_analysis_with_issues
    ):
        """Test analyze-only mode (no output path provided)."""
        pipeline = CorrectionPipeline()

        with patch.object(
            pipeline.analyzer, "analyze", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = mock_analysis_with_issues

            analysis, correction = await pipeline.analyze_and_correct(
                mock_pdf_path, None
            )

            assert analysis == mock_analysis_with_issues
            assert correction is None  # No correction when output_path is None

    def test_format_analysis_summary_excellent(self, mock_analysis_clean):
        """Test formatting for excellent quality PDF."""
        pipeline = CorrectionPipeline()
        summary = pipeline.format_analysis_summary(mock_analysis_clean)

        assert summary["quality_icon"] == "✓"
        assert summary["quality_color"] == "green"
        assert summary["quality_score"] == "95%"
        assert summary["quality_grade"] == "Excellent"
        assert summary["issue_count"] == "0"
        assert summary["issue_summary"] == "none"
        assert summary["requires_correction"] == "False"

    def test_format_analysis_summary_fair(self, mock_analysis_with_issues):
        """Test formatting for fair quality PDF with issues."""
        pipeline = CorrectionPipeline()
        summary = pipeline.format_analysis_summary(mock_analysis_with_issues)

        assert summary["quality_icon"] == "⚠"
        assert summary["quality_color"] == "red"
        assert summary["quality_score"] == "65%"
        assert summary["quality_grade"] == "Fair"
        assert summary["issue_count"] == "2"
        assert "duplicate" in summary["issue_summary"]
        assert "rotation" in summary["issue_summary"]
        assert summary["requires_correction"] == "True"

    def test_format_analysis_summary_good(self):
        """Test formatting for good quality PDF (70-90%)."""
        analysis = AnalysisResult(
            document_path=Path("test.pdf"),
            total_pages=10,
            overall_quality_score=0.85,
            quality_grade=QualityGrade.GOOD,
            requires_correction=False,
            analysis_duration=1.0,
            issues=[
                IssueReport(
                    issue_type=IssueType.QUALITY,
                    page_numbers=[3],
                    confidence=0.70,
                    severity="low",
                    details="Minor quality issue",
                    suggested_correction="Review page",
                )
            ],
            metadata={},
        )

        pipeline = CorrectionPipeline()
        summary = pipeline.format_analysis_summary(analysis)

        assert summary["quality_icon"] == "✓"
        assert summary["quality_color"] == "yellow"
        assert summary["quality_score"] == "85%"
        assert summary["quality_grade"] == "Good"

    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, mock_pdf_path):
        """Test pipeline handles errors gracefully."""
        pipeline = CorrectionPipeline()

        with patch.object(
            pipeline.analyzer, "analyze", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis failed")

            with pytest.raises(Exception, match="Analysis failed"):
                await pipeline.analyze_and_correct(mock_pdf_path)

    def test_format_analysis_summary_multiple_same_type_issues(self):
        """Test formatting with multiple issues of the same type."""
        analysis = AnalysisResult(
            document_path=Path("test.pdf"),
            total_pages=10,
            overall_quality_score=0.60,
            quality_grade=QualityGrade.FAIR,
            requires_correction=True,
            analysis_duration=2.5,
            issues=[
                IssueReport(
                    issue_type=IssueType.ROTATION,
                    page_numbers=[1],
                    confidence=0.95,
                    severity="high",
                    details="Page 1 rotated",
                    suggested_correction="Rotate",
                ),
                IssueReport(
                    issue_type=IssueType.ROTATION,
                    page_numbers=[2],
                    confidence=0.95,
                    severity="high",
                    details="Page 2 rotated",
                    suggested_correction="Rotate",
                ),
                IssueReport(
                    issue_type=IssueType.DUPLICATE,
                    page_numbers=[5, 6],
                    confidence=0.90,
                    severity="medium",
                    details="Duplicates",
                    suggested_correction="Remove",
                ),
            ],
            metadata={},
        )

        pipeline = CorrectionPipeline()
        summary = pipeline.format_analysis_summary(analysis)

        assert summary["issue_count"] == "3"
        # Should count 2 rotation issues and 1 duplicate
        assert "2 rotation" in summary["issue_summary"]
        assert "1 duplicate" in summary["issue_summary"]
