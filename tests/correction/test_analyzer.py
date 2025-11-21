"""Unit tests for PDFAnalyzer.

Tests the PDF analysis coordinator that orchestrates all detectors.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import asyncio

from src.correction.analyzer import PDFAnalyzer, AnalyzerConfig
from src.correction.schemas import IssueReport, IssueType, QualityGrade


class TestAnalyzerConfig:
    """Tests for AnalyzerConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AnalyzerConfig()

        assert config.rotation_enabled is True
        assert config.ordering_enabled is True
        assert config.duplicate_enabled is True
        assert config.quality_enabled is True
        assert config.parallel_execution is True
        assert config.timeout_seconds == 120.0
        assert "rotation" in config.confidence_thresholds
        assert config.confidence_thresholds["rotation"] == 0.85

    def test_custom_config(self):
        """Test custom configuration."""
        config = AnalyzerConfig(
            rotation_enabled=False,
            timeout_seconds=60.0,
            confidence_thresholds={"rotation": 0.90}
        )

        assert config.rotation_enabled is False
        assert config.timeout_seconds == 60.0
        assert config.confidence_thresholds["rotation"] == 0.90


class TestPDFAnalyzer:
    """Tests for PDFAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create a PDFAnalyzer instance."""
        return PDFAnalyzer()

    @pytest.fixture
    def mock_detector(self):
        """Create a mock detector."""
        detector = AsyncMock()
        detector.detect = AsyncMock(return_value=[])
        return detector

    def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.config is not None
        assert isinstance(analyzer.config, AnalyzerConfig)
        assert analyzer._detectors == {}

    def test_register_detector(self, analyzer, mock_detector):
        """Test detector registration."""
        analyzer.register_detector("test_detector", mock_detector)

        assert "test_detector" in analyzer._detectors
        assert analyzer._detectors["test_detector"] == mock_detector

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self, analyzer, tmp_path):
        """Test analysis raises FileNotFoundError for missing file."""
        non_existent = tmp_path / "missing.pdf"

        with pytest.raises(FileNotFoundError):
            await analyzer.analyze(non_existent)

    @pytest.mark.asyncio
    async def test_analyze_invalid_file_type(self, analyzer, tmp_path):
        """Test analysis raises ValueError for non-PDF file."""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("Not a PDF")

        with pytest.raises(ValueError, match="not a PDF"):
            await analyzer.analyze(invalid_file)

    @pytest.mark.asyncio
    async def test_analyze_no_issues(self, analyzer, tmp_path):
        """Test analysis with no detected issues."""
        # Create test PDF
        test_file = tmp_path / "clean.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        # Register mock detector that finds no issues
        mock_detector = AsyncMock()
        mock_detector.detect = AsyncMock(return_value=[])
        analyzer.register_detector("quality", mock_detector)

        # Mock pymupdf
        with patch('pymupdf.open') as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_open.return_value = mock_doc

            result = await analyzer.analyze(test_file)

        assert result.document_path == test_file
        assert len(result.issues) == 0
        assert result.requires_correction is False
        assert result.quality_grade in [QualityGrade.EXCELLENT, QualityGrade.GOOD]

    @pytest.mark.asyncio
    async def test_analyze_with_issues(self, analyzer, tmp_path):
        """Test analysis with detected issues."""
        test_file = tmp_path / "messy.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        # Create mock issue
        mock_issue = IssueReport(
            issue_type=IssueType.ROTATION,
            page_numbers=[1],
            confidence=0.90,
            severity="high",
            details="Page 1 needs rotation"
        )

        # Register mock detector that finds issues
        mock_detector = AsyncMock()
        mock_detector.detect = AsyncMock(return_value=[mock_issue])
        analyzer.register_detector("rotation", mock_detector)

        # Mock pymupdf
        with patch('pymupdf.open') as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_open.return_value = mock_doc

            result = await analyzer.analyze(test_file)

        assert len(result.issues) == 1
        assert result.requires_correction is True
        assert result.issues[0].issue_type == IssueType.ROTATION

    @pytest.mark.asyncio
    async def test_run_parallel_execution(self, analyzer, tmp_path):
        """Test parallel detector execution."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        # Register multiple mock detectors
        for detector_name in ["rotation", "ordering", "duplicate"]:
            mock_detector = AsyncMock()
            mock_detector.detect = AsyncMock(return_value=[])
            analyzer.register_detector(detector_name, mock_detector)

        # Mock pymupdf
        with patch('pymupdf.open') as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_open.return_value = mock_doc

            result = await analyzer.analyze(test_file)

        # All detectors should have been called
        for detector in analyzer._detectors.values():
            detector.detect.assert_called_once()

    @pytest.mark.asyncio
    async def test_confidence_filtering(self, analyzer, tmp_path):
        """Test that issues below confidence threshold are filtered."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        # Create issues with different confidence levels
        high_confidence_issue = IssueReport(
            issue_type=IssueType.ROTATION,
            page_numbers=[1],
            confidence=0.95,
            severity="high",
            details="High confidence"
        )

        low_confidence_issue = IssueReport(
            issue_type=IssueType.ROTATION,
            page_numbers=[2],
            confidence=0.60,
            severity="low",
            details="Low confidence"
        )

        mock_detector = AsyncMock()
        mock_detector.detect = AsyncMock(
            return_value=[high_confidence_issue, low_confidence_issue]
        )
        analyzer.register_detector("rotation", mock_detector)

        # Set threshold to 0.85 (should filter out low confidence issue)
        analyzer.config.confidence_thresholds["rotation"] = 0.85

        # Mock pymupdf
        with patch('pymupdf.open') as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 2
            mock_open.return_value = mock_doc

            result = await analyzer.analyze(test_file)

        # Only high confidence issue should remain
        assert len(result.issues) == 1
        assert result.issues[0].confidence == 0.95

    @pytest.mark.asyncio
    async def test_timeout_handling(self, analyzer, tmp_path):
        """Test that analysis respects timeout (skipped if not implemented)."""
        pytest.skip("Timeout handling not yet fully implemented - will add in Phase 3")

        # Future implementation test:
        # test_file = tmp_path / "test.pdf"
        # test_file.write_bytes(b"%PDF-1.4\n")
        #
        # async def slow_detect(pdf_path):
        #     await asyncio.sleep(5.0)
        #     return []
        #
        # mock_detector = AsyncMock()
        # mock_detector.detect = slow_detect
        # analyzer.register_detector("slow", mock_detector)
        # analyzer.config.timeout_seconds = 0.05
        #
        # with pytest.raises(TimeoutError):
        #     await analyzer.analyze(test_file)

    @pytest.mark.asyncio
    async def test_detector_error_handling(self, analyzer, tmp_path):
        """Test that detector errors don't crash analysis."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        # Create detector that raises exception
        mock_detector = AsyncMock()
        mock_detector.detect = AsyncMock(side_effect=Exception("Detector error"))
        analyzer.register_detector("faulty", mock_detector)

        # Mock pymupdf
        with patch('pymupdf.open') as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 1
            mock_open.return_value = mock_doc

            # Should not raise exception
            result = await analyzer.analyze(test_file)

        # Analysis should complete with empty results
        assert result.issues == []

    def test_create_analysis_result(self, analyzer, tmp_path):
        """Test creation of AnalysisResult."""
        test_file = tmp_path / "test.pdf"

        # Create mock issues
        issues = [
            IssueReport(
                issue_type=IssueType.ROTATION,
                page_numbers=[1, 2],
                confidence=0.90,
                severity="high",
                details="Rotation issue"
            )
        ]

        result = analyzer._create_analysis_result(
            pdf_path=test_file,
            issues=issues,
            analysis_duration=5.0
        )

        assert result.document_path == test_file
        assert len(result.issues) == 1
        assert result.requires_correction is True
        assert result.analysis_duration == 5.0
        assert result.estimated_correction_time is not None


class TestPDFAnalyzerIntegration:
    """Integration tests for PDFAnalyzer."""

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self, tmp_path):
        """Test complete analysis pipeline with multiple detectors."""
        analyzer = PDFAnalyzer(AnalyzerConfig(parallel_execution=True))

        # Create test PDF
        test_file = tmp_path / "document.pdf"
        test_file.write_bytes(b"%PDF-1.4\n")

        # Register multiple detectors with various issues
        rotation_issue = IssueReport(
            issue_type=IssueType.ROTATION,
            page_numbers=[1],
            confidence=0.90,
            severity="high",
            details="Rotation needed"
        )

        quality_issue = IssueReport(
            issue_type=IssueType.QUALITY,
            page_numbers=[2],
            confidence=0.75,  # Above default threshold of 0.70
            severity="medium",
            details="Low quality"
        )

        rotation_detector = AsyncMock()
        rotation_detector.detect = AsyncMock(return_value=[rotation_issue])
        analyzer.register_detector("rotation", rotation_detector)

        quality_detector = AsyncMock()
        quality_detector.detect = AsyncMock(return_value=[quality_issue])
        analyzer.register_detector("quality", quality_detector)

        # Mock pymupdf
        with patch('pymupdf.open') as mock_open:
            mock_doc = MagicMock()
            mock_doc.__len__.return_value = 2
            mock_open.return_value = mock_doc

            result = await analyzer.analyze(test_file)

        # Should have collected issues from both detectors
        assert len(result.issues) == 2
        assert result.requires_correction is True
        assert any(issue.issue_type == IssueType.ROTATION for issue in result.issues)
        assert any(issue.issue_type == IssueType.QUALITY for issue in result.issues)
