"""End-to-end integration tests for PDF correction (v0.3.5).

Tests the complete flow:
1. PDF analysis
2. Correction application
3. Metadata generation
4. CLI integration
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.correction import CorrectionPipeline, MetadataGenerator
from src.correction.schemas import (
    AnalysisResult,
    CorrectionAction,
    CorrectionResult,
    IssueReport,
    IssueType,
    QualityGrade,
)


@pytest.fixture
def mock_pdf_with_issues(tmp_path):
    """Create a mock PDF file with issues."""
    pdf_file = tmp_path / "messy_document.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\nMock messy PDF")
    return pdf_file


@pytest.fixture
def mock_clean_pdf(tmp_path):
    """Create a mock clean PDF file."""
    pdf_file = tmp_path / "clean_document.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\nMock clean PDF")
    return pdf_file


@pytest.fixture
def analysis_result_messy():
    """Analysis result for messy PDF."""
    return AnalysisResult(
        document_path=Path("messy_document.pdf"),
        total_pages=20,
        overall_quality_score=0.55,
        quality_grade=QualityGrade.POOR,
        requires_correction=True,
        analysis_duration=4.8,
        issues=[
            IssueReport(
                issue_type=IssueType.ROTATION,
                page_numbers=[1, 2, 3, 4],
                confidence=0.98,
                severity="critical",
                details="Pages rotated 90 degrees clockwise",
                suggested_correction="Rotate counter-clockwise",
            ),
            IssueReport(
                issue_type=IssueType.DUPLICATE,
                page_numbers=[10, 11, 12],
                confidence=0.95,
                severity="high",
                details="Consecutive duplicate pages",
                suggested_correction="Remove duplicates",
            ),
            IssueReport(
                issue_type=IssueType.ORDERING,
                page_numbers=[15, 16, 17],
                confidence=0.85,
                severity="medium",
                details="Pages out of order",
                suggested_correction="Reorder pages",
            ),
            IssueReport(
                issue_type=IssueType.QUALITY,
                page_numbers=[8],
                confidence=0.45,
                severity="low",
                details="Low OCR confidence on page 8",
                suggested_correction="Manual review recommended",
            ),
        ],
        metadata={"scanner": "HP", "dpi": 300, "scanned_date": "2024-01-15"},
    )


@pytest.fixture
def correction_result_messy():
    """Correction result for messy PDF."""
    return CorrectionResult(
        original_path=Path("messy_document.pdf"),
        corrected_path=Path(".corrected_messy_document.pdf"),
        quality_before=0.55,
        quality_after=0.92,
        improvement=0.37,
        total_duration=12.5,
        actions=[
            CorrectionAction(
                action_type="rotation",
                pages_affected=[1, 2, 3, 4],
                success=True,
                issue=IssueReport(
                    issue_type=IssueType.ROTATION,
                    page_numbers=[1, 2, 3, 4],
                    confidence=0.98,
                    severity="critical",
                    details="Pages rotated",
                    suggested_correction="Rotate",
                ),
            ),
            CorrectionAction(
                action_type="duplicate",
                pages_affected=[10, 11, 12],
                success=True,
                issue=IssueReport(
                    issue_type=IssueType.DUPLICATE,
                    page_numbers=[10, 11, 12],
                    confidence=0.95,
                    severity="high",
                    details="Duplicates",
                    suggested_correction="Remove",
                ),
            ),
            CorrectionAction(
                action_type="ordering",
                pages_affected=[15, 16, 17],
                success=True,
                issue=IssueReport(
                    issue_type=IssueType.ORDERING,
                    page_numbers=[15, 16, 17],
                    confidence=0.85,
                    severity="medium",
                    details="Out of order",
                    suggested_correction="Reorder",
                ),
            ),
        ],
    )


class TestCorrectionPipelineIntegration:
    """End-to-end integration tests for correction pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_messy_pdf(
        self,
        mock_pdf_with_issues,
        analysis_result_messy,
        correction_result_messy,
        tmp_path,
    ):
        """Test complete pipeline with messy PDF requiring corrections."""
        pipeline = CorrectionPipeline()
        corrected_path = tmp_path / ".corrected_messy.pdf"

        with patch.object(
            pipeline.analyzer, "analyze", new_callable=AsyncMock
        ) as mock_analyze, patch.object(
            pipeline.corrector, "correct"
        ) as mock_correct:
            mock_analyze.return_value = analysis_result_messy
            mock_correct.return_value = correction_result_messy

            # Run pipeline
            analysis, correction = await pipeline.analyze_and_correct(
                mock_pdf_with_issues, corrected_path
            )

            # Verify analysis
            assert analysis.overall_quality_score == 0.55
            assert analysis.quality_grade == QualityGrade.POOR
            assert len(analysis.issues) == 4
            assert analysis.requires_correction is True

            # Verify correction
            assert correction is not None
            assert correction.quality_after > correction.quality_before
            assert correction.improvement == 0.37
            assert len(correction.actions) == 3
            assert all(action.success for action in correction.actions)

    @pytest.mark.asyncio
    async def test_full_pipeline_clean_pdf(self, mock_clean_pdf, tmp_path):
        """Test complete pipeline with clean PDF (no corrections needed)."""
        clean_analysis = AnalysisResult(
            document_path=mock_clean_pdf,
            total_pages=10,
            overall_quality_score=0.98,
            quality_grade=QualityGrade.EXCELLENT,
            requires_correction=False,
            analysis_duration=0.8,
            issues=[],
            metadata={},
        )

        pipeline = CorrectionPipeline()
        corrected_path = tmp_path / ".corrected_clean.pdf"

        with patch.object(
            pipeline.analyzer, "analyze", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = clean_analysis

            # Run pipeline
            analysis, correction = await pipeline.analyze_and_correct(
                mock_clean_pdf, corrected_path
            )

            # Verify no correction needed
            assert analysis.overall_quality_score == 0.98
            assert len(analysis.issues) == 0
            assert correction is None  # No correction applied

    def test_metadata_generation_full_workflow(
        self, tmp_path, analysis_result_messy, correction_result_messy
    ):
        """Test complete metadata generation workflow."""
        metadata_dir = tmp_path / ".ragged" / "doc_12345"
        generator = MetadataGenerator(metadata_dir)

        # Generate all metadata
        files = generator.generate_all(analysis_result_messy, correction_result_messy)

        # Verify all expected files created
        assert "quality" in files
        assert "corrections" in files
        assert "page_mapping" in files
        assert "uncertainties" in files

        # Verify quality report
        with open(files["quality"]) as f:
            quality_data = json.load(f)

        assert quality_data["overall_quality"]["grade"] == "poor"
        assert quality_data["overall_quality"]["score"] == 0.55
        assert quality_data["issues_detected"] == 4
        assert quality_data["requires_correction"] is True
        assert quality_data["critical_issues"] is True

        # Verify corrections metadata
        with open(files["corrections"]) as f:
            corrections_data = json.load(f)

        assert corrections_data["quality_improvement"]["improvement"] == 0.37
        assert corrections_data["successful_corrections"] == 3
        assert corrections_data["corrections_applied"] == 3

        # Verify page mapping
        with open(files["page_mapping"]) as f:
            mapping_data = json.load(f)

        # Pages 10, 11, 12 were removed (duplicates)
        assert 10 in mapping_data["pages_removed"]
        assert 11 in mapping_data["pages_removed"]
        assert 12 in mapping_data["pages_removed"]

        # Verify uncertainties
        with open(files["uncertainties"]) as f:
            uncertainties_data = json.load(f)

        assert uncertainties_data["total_uncertain_pages"] == 1
        assert uncertainties_data["pages"][0]["page_number"] == 8
        assert uncertainties_data["pages"][0]["confidence"] == 0.45

    @pytest.mark.asyncio
    async def test_pipeline_formatting_summary(
        self, mock_pdf_with_issues, analysis_result_messy
    ):
        """Test pipeline summary formatting for display."""
        pipeline = CorrectionPipeline()

        with patch.object(
            pipeline.analyzer, "analyze", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = analysis_result_messy

            analysis, _ = await pipeline.analyze_and_correct(
                mock_pdf_with_issues, None
            )

            # Format summary
            summary = pipeline.format_analysis_summary(analysis)

            # Verify traffic light system
            assert summary["quality_icon"] == "⚠"  # Poor quality
            assert summary["quality_color"] == "red"
            assert summary["quality_score"] == "55%"
            assert summary["quality_grade"] == "Poor"

            # Verify issue summary
            assert "rotation" in summary["issue_summary"]
            assert "duplicate" in summary["issue_summary"]
            assert "ordering" in summary["issue_summary"]
            assert "quality" in summary["issue_summary"]
            assert summary["requires_correction"] == "True"

    def test_quality_improvement_calculation(self, correction_result_messy):
        """Test quality improvement calculation in corrections."""
        assert correction_result_messy.quality_before == 0.55
        assert correction_result_messy.quality_after == 0.92
        assert correction_result_messy.improvement == 0.37

        # Verify percentage improvement
        percentage_improvement = (
            correction_result_messy.improvement / correction_result_messy.quality_before
        ) * 100
        assert percentage_improvement > 50  # More than 50% improvement

    def test_affected_pages_aggregation(self, analysis_result_messy):
        """Test affected pages aggregation across all issues."""
        affected_pages = analysis_result_messy.affected_pages()

        # Should include all pages from all issues
        expected_pages = {1, 2, 3, 4, 8, 10, 11, 12, 15, 16, 17}
        assert set(affected_pages) == expected_pages

    def test_critical_issues_detection(self, analysis_result_messy):
        """Test detection of critical issues."""
        assert analysis_result_messy.has_critical_issues() is True

        # Should have at least one critical severity issue
        critical_issues = [
            issue
            for issue in analysis_result_messy.issues
            if issue.severity == "critical"
        ]
        assert len(critical_issues) > 0

    def test_high_severity_issues_detection(self, analysis_result_messy):
        """Test detection of high severity issues."""
        assert analysis_result_messy.has_high_severity_issues() is True

        high_issues = [
            issue
            for issue in analysis_result_messy.issues
            if issue.severity in ("high", "critical")
        ]
        assert len(high_issues) >= 2  # Rotation (critical) + Duplicate (high)


class TestCLIIntegrationMocked:
    """Test CLI integration with mocked components."""

    def test_cli_imports(self):
        """Test that CLI imports work correctly."""
        from src.main import cli

        # Verify show command registered
        assert "show" in cli.commands

        # Verify show subcommands
        show_cmd = cli.commands["show"]
        assert "quality" in show_cmd.commands
        assert "corrections" in show_cmd.commands
        assert "uncertainties" in show_cmd.commands

    def test_add_command_has_auto_correct_option(self):
        """Test add command has auto-correct-pdf option."""
        from src.main import cli

        add_cmd = cli.commands["add"]
        param_names = [p.name for p in add_cmd.params]

        assert "auto_correct_pdf" in param_names

        # Find the parameter
        auto_correct_param = next(
            p for p in add_cmd.params if p.name == "auto_correct_pdf"
        )

        # Verify default is True
        assert auto_correct_param.default is True

    def test_show_quality_command_structure(self):
        """Test show quality command accepts document_id."""
        from src.main import cli

        show_cmd = cli.commands["show"]
        quality_cmd = show_cmd.commands["quality"]

        # Verify it accepts document_id argument
        assert len(quality_cmd.params) == 1
        assert quality_cmd.params[0].name == "document_id"

    def test_show_corrections_command_structure(self):
        """Test show corrections command accepts document_id."""
        from src.main import cli

        show_cmd = cli.commands["show"]
        corrections_cmd = show_cmd.commands["corrections"]

        assert len(corrections_cmd.params) == 1
        assert corrections_cmd.params[0].name == "document_id"

    def test_show_uncertainties_command_structure(self):
        """Test show uncertainties command accepts document_id."""
        from src.main import cli

        show_cmd = cli.commands["show"]
        uncertainties_cmd = show_cmd.commands["uncertainties"]

        assert len(uncertainties_cmd.params) == 1
        assert uncertainties_cmd.params[0].name == "document_id"


class TestErrorHandling:
    """Test error handling in correction pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_handles_analysis_failure(self, mock_pdf_with_issues):
        """Test pipeline gracefully handles analysis failures."""
        pipeline = CorrectionPipeline()

        with patch.object(
            pipeline.analyzer, "analyze", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.side_effect = Exception("PDF parsing failed")

            with pytest.raises(Exception, match="PDF parsing failed"):
                await pipeline.analyze_and_correct(mock_pdf_with_issues)

    def test_metadata_generator_handles_write_failure(self, tmp_path):
        """Test metadata generator handles write failures gracefully."""
        # Create a read-only directory
        metadata_dir = tmp_path / "readonly"
        metadata_dir.mkdir()
        metadata_dir.chmod(0o444)  # Read-only

        try:
            generator = MetadataGenerator(metadata_dir)

            analysis = AnalysisResult(
                document_path=Path("test.pdf"),
                total_pages=1,
                overall_quality_score=1.0,
                quality_grade=QualityGrade.EXCELLENT,
                requires_correction=False,
                analysis_duration=0.5,
                issues=[],
                metadata={},
            )

            # This should raise a permission error
            with pytest.raises(PermissionError):
                generator.generate_quality_report(analysis)

        finally:
            # Cleanup: restore permissions
            metadata_dir.chmod(0o755)

    def test_partial_correction_success(self):
        """Test handling of partial correction success."""
        correction = CorrectionResult(
            original_path=Path("test.pdf"),
            corrected_path=Path("corrected.pdf"),
            quality_before=0.60,
            quality_after=0.75,  # Partial improvement
            improvement=0.15,
            total_duration=4.2,
            actions=[
                CorrectionAction(
                    action_type="rotation",
                    pages_affected=[1],
                    success=True,
                    issue=IssueReport(
                        issue_type=IssueType.ROTATION,
                        page_numbers=[1],
                        confidence=0.95,
                        severity="high",
                        details="Rotated",
                        suggested_correction="Fix",
                    ),
                ),
                CorrectionAction(
                    action_type="duplicate",
                    pages_affected=[5],
                    success=False,
                    error_message="Unable to remove duplicate",
                    issue=IssueReport(
                        issue_type=IssueType.DUPLICATE,
                        page_numbers=[5],
                        confidence=0.85,
                        severity="medium",
                        details="Duplicate",
                        suggested_correction="Remove",
                    ),
                ),
            ],
        )

        # Verify we can identify failed actions
        failed = correction.failed_actions()
        assert len(failed) == 1
        assert failed[0].action_type == "duplicate"
        assert failed[0].error_message == "Unable to remove duplicate"

        # Verify improvement despite partial failure
        assert correction.improvement == 0.15
        assert correction.quality_after > correction.quality_before
