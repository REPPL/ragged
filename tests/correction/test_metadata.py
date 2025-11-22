"""Tests for PDF correction metadata generation.

v0.3.5: Tests for MetadataGenerator.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.correction.metadata import MetadataGenerator
from src.correction.schemas import (
    AnalysisResult,
    CorrectionAction,
    CorrectionResult,
    IssueReport,
    IssueType,
    QualityGrade,
)


@pytest.fixture
def metadata_dir(tmp_path):
    """Create temporary metadata directory."""
    return tmp_path / "metadata"


@pytest.fixture
def clean_analysis():
    """Analysis result with no issues."""
    return AnalysisResult(
        document_path=Path("test.pdf"),
        total_pages=10,
        overall_quality_score=0.95,
        quality_grade=QualityGrade.EXCELLENT,
        requires_correction=False,
        analysis_duration=1.5,
        issues=[],
        metadata={"test": "value"},
    )


@pytest.fixture
def analysis_with_issues():
    """Analysis result with multiple issues."""
    return AnalysisResult(
        document_path=Path("test.pdf"),
        total_pages=15,
        overall_quality_score=0.65,
        quality_grade=QualityGrade.FAIR,
        requires_correction=True,
        analysis_duration=3.2,
        issues=[
            IssueReport(
                issue_type=IssueType.ROTATION,
                page_numbers=[1, 2, 3],
                confidence=0.95,
                severity="high",
                details="Pages rotated 90 degrees clockwise",
                suggested_correction="Rotate counter-clockwise",
            ),
            IssueReport(
                issue_type=IssueType.DUPLICATE,
                page_numbers=[7, 8],
                confidence=0.90,
                severity="medium",
                details="Duplicate pages detected",
                suggested_correction="Remove duplicates",
            ),
            IssueReport(
                issue_type=IssueType.QUALITY,
                page_numbers=[10],
                confidence=0.60,
                severity="low",
                details="Low OCR confidence",
                suggested_correction="Review content",
            ),
        ],
        metadata={"scanner": "HP", "dpi": 300},
    )


@pytest.fixture
def correction_result():
    """Correction result with successful actions."""
    return CorrectionResult(
        original_path=Path("test.pdf"),
        corrected_path=Path("corrected.pdf"),
        quality_before=0.65,
        quality_after=0.88,
        improvement=0.23,
        total_duration=6.5,
        actions=[
            CorrectionAction(
                action_type="rotation",
                pages_affected=[1, 2, 3],
                success=True,
                issue=IssueReport(
                    issue_type=IssueType.ROTATION,
                    page_numbers=[1, 2, 3],
                    confidence=0.95,
                    severity="high",
                    details="Pages rotated 90 degrees",
                    suggested_correction="Rotate",
                ),
            ),
            CorrectionAction(
                action_type="duplicate",
                pages_affected=[7, 8],
                success=True,
                issue=IssueReport(
                    issue_type=IssueType.DUPLICATE,
                    page_numbers=[7, 8],
                    confidence=0.90,
                    severity="medium",
                    details="Duplicates",
                    suggested_correction="Remove",
                ),
            ),
        ],
    )


class TestMetadataGenerator:
    """Tests for MetadataGenerator."""

    def test_generator_initialization(self, metadata_dir):
        """Test generator creates output directory."""
        generator = MetadataGenerator(metadata_dir)

        assert generator.output_dir == metadata_dir
        assert metadata_dir.exists()

    def test_generate_quality_report_clean(self, metadata_dir, clean_analysis):
        """Test quality report generation for clean PDF."""
        generator = MetadataGenerator(metadata_dir)
        report_path = generator.generate_quality_report(clean_analysis)

        assert report_path.exists()
        assert report_path == metadata_dir / "quality_report.json"

        # Verify content
        with open(report_path) as f:
            data = json.load(f)

        assert data["document_path"] == "test.pdf"
        assert data["total_pages"] == 10
        assert data["overall_quality"]["score"] == 0.95
        assert data["overall_quality"]["grade"] == "excellent"
        assert data["requires_correction"] is False
        assert data["issues_detected"] == 0
        assert data["issues_by_type"] == {}
        assert data["affected_pages"] == []
        assert data["critical_issues"] is False
        assert data["metadata"] == {"test": "value"}

    def test_generate_quality_report_with_issues(
        self, metadata_dir, analysis_with_issues
    ):
        """Test quality report generation for PDF with issues."""
        generator = MetadataGenerator(metadata_dir)
        report_path = generator.generate_quality_report(analysis_with_issues)

        assert report_path.exists()

        with open(report_path) as f:
            data = json.load(f)

        assert data["total_pages"] == 15
        assert data["overall_quality"]["score"] == 0.65
        assert data["overall_quality"]["grade"] == "fair"
        assert data["requires_correction"] is True
        assert data["issues_detected"] == 3

        # Verify issues grouped by type
        assert data["issues_by_type"]["rotation"] == 1
        assert data["issues_by_type"]["duplicate"] == 1
        assert data["issues_by_type"]["quality"] == 1

        # Verify affected pages
        affected = data["affected_pages"]
        assert 1 in affected
        assert 2 in affected
        assert 7 in affected
        assert 10 in affected

    def test_generate_corrections_metadata(
        self, metadata_dir, correction_result
    ):
        """Test corrections metadata generation."""
        generator = MetadataGenerator(metadata_dir)
        corrections_path = generator.generate_corrections_metadata(correction_result)

        assert corrections_path.exists()
        assert corrections_path == metadata_dir / "corrections.json"

        with open(corrections_path) as f:
            data = json.load(f)

        assert data["original_path"] == "test.pdf"
        assert data["corrected_path"] == "corrected.pdf"
        assert data["quality_improvement"]["before"] == 0.65
        assert data["quality_improvement"]["after"] == 0.88
        assert data["quality_improvement"]["improvement"] == 0.23
        assert data["corrections_applied"] == 2
        assert data["successful_corrections"] == 2
        assert data["failed_corrections"] == 0

        # Verify actions
        assert len(data["actions"]) == 2
        assert data["actions"][0]["action_type"] == "rotation"
        assert data["actions"][0]["pages_affected"] == [1, 2, 3]
        assert data["actions"][0]["success"] is True

    def test_generate_page_mapping(self, metadata_dir, correction_result):
        """Test page mapping generation."""
        generator = MetadataGenerator(metadata_dir)
        mapping_path = generator.generate_page_mapping(correction_result)

        assert mapping_path.exists()
        assert mapping_path == metadata_dir / "page_mapping.json"

        with open(mapping_path) as f:
            data = json.load(f)

        # Pages 7 and 8 were removed (duplicates)
        assert data["pages_removed"] == [7, 8]
        assert data["original_to_corrected"]["7"] is None  # Removed
        assert data["original_to_corrected"]["8"] is None  # Removed

        # Other pages should map correctly
        assert data["original_to_corrected"]["1"] == 1
        assert data["original_to_corrected"]["6"] == 6
        assert data["original_to_corrected"]["9"] == 7  # Shifted down by 2

    def test_generate_uncertainties(self, metadata_dir, analysis_with_issues):
        """Test uncertainties metadata generation."""
        generator = MetadataGenerator(metadata_dir)

        # Extract only quality issues
        quality_issues = [
            issue
            for issue in analysis_with_issues.issues
            if issue.issue_type == IssueType.QUALITY
        ]

        uncertainties_path = generator.generate_uncertainties(quality_issues)

        assert uncertainties_path.exists()
        assert uncertainties_path == metadata_dir / "uncertainties.json"

        with open(uncertainties_path) as f:
            data = json.load(f)

        assert data["total_uncertain_pages"] == 1
        assert len(data["pages"]) == 1

        page_info = data["pages"][0]
        assert page_info["page_number"] == 10
        assert page_info["confidence"] == 0.60
        assert page_info["severity"] == "low"
        assert "OCR confidence" in page_info["details"]

    def test_generate_all_clean_pdf(self, metadata_dir, clean_analysis):
        """Test generate_all with clean PDF (no corrections)."""
        generator = MetadataGenerator(metadata_dir)
        files = generator.generate_all(clean_analysis, None)

        # Should only generate quality report (no corrections or uncertainties)
        assert "quality" in files
        assert "corrections" not in files
        assert "uncertainties" not in files
        assert "page_mapping" not in files

        assert files["quality"].exists()

    def test_generate_all_with_corrections(
        self, metadata_dir, analysis_with_issues, correction_result
    ):
        """Test generate_all with corrections applied."""
        generator = MetadataGenerator(metadata_dir)
        files = generator.generate_all(analysis_with_issues, correction_result)

        # Should generate all metadata files
        assert "quality" in files
        assert "corrections" in files
        assert "page_mapping" in files
        assert "uncertainties" in files  # Has quality issues

        for file_type, path in files.items():
            assert path.exists(), f"{file_type} file not created"

    def test_generate_all_issues_but_no_corrections(
        self, metadata_dir, analysis_with_issues
    ):
        """Test generate_all with issues but no corrections applied."""
        generator = MetadataGenerator(metadata_dir)
        files = generator.generate_all(analysis_with_issues, None)

        # Should generate quality and uncertainties, but not corrections/mapping
        assert "quality" in files
        assert "uncertainties" in files
        assert "corrections" not in files
        assert "page_mapping" not in files

    def test_group_issues_by_type(self, metadata_dir, analysis_with_issues):
        """Test issue grouping by type."""
        generator = MetadataGenerator(metadata_dir)
        grouped = generator._group_issues_by_type(analysis_with_issues.issues)

        assert grouped["rotation"] == 1
        assert grouped["duplicate"] == 1
        assert grouped["quality"] == 1

    def test_write_json_formatting(self, metadata_dir):
        """Test JSON files are properly formatted."""
        generator = MetadataGenerator(metadata_dir)
        test_data = {"key": "value", "nested": {"a": 1, "b": 2}}

        test_file = metadata_dir / "test.json"
        generator._write_json(test_file, test_data)

        # Verify file exists and is valid JSON
        assert test_file.exists()

        with open(test_file) as f:
            content = f.read()
            loaded = json.loads(content)

        assert loaded == test_data
        # Verify pretty formatting (indented)
        assert "\n" in content
        assert "  " in content  # Indentation

    def test_failed_correction_actions(self, metadata_dir):
        """Test metadata generation with failed corrections."""
        correction = CorrectionResult(
            original_path=Path("test.pdf"),
            corrected_path=Path("corrected.pdf"),
            quality_before=0.65,
            quality_after=0.70,  # Minimal improvement
            improvement=0.05,
            total_duration=3.5,
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
                    error_message="Could not remove duplicate",
                    issue=IssueReport(
                        issue_type=IssueType.DUPLICATE,
                        page_numbers=[5],
                        confidence=0.80,
                        severity="medium",
                        details="Duplicate",
                        suggested_correction="Remove",
                    ),
                ),
            ],
        )

        generator = MetadataGenerator(metadata_dir)
        corrections_path = generator.generate_corrections_metadata(correction)

        with open(corrections_path) as f:
            data = json.load(f)

        assert data["successful_corrections"] == 1
        assert data["failed_corrections"] == 1
        assert data["actions"][1]["success"] is False
        assert data["actions"][1]["error_message"] == "Could not remove duplicate"
