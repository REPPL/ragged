"""Pydantic schemas for PDF correction and analysis.

v0.3.5: Data models for issue detection and correction tracking.
"""

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class IssueType(str, Enum):
    """Types of PDF issues that can be detected and corrected."""

    ROTATION = "rotation"
    ORDERING = "ordering"
    DUPLICATE = "duplicate"
    QUALITY = "quality"
    MISSING_PAGE = "missing_page"


class IssueReport(BaseModel):
    """Report of a detected issue in a PDF document.

    Attributes:
        issue_type: Type of issue detected.
        page_numbers: List of affected page numbers (1-indexed).
        confidence: Confidence score for detection (0.0-1.0).
        severity: Severity level: 'critical', 'high', 'medium', 'low'.
        details: Additional details about the issue.
        suggested_correction: Suggested correction action.
        metadata: Additional metadata specific to issue type.
    """

    issue_type: IssueType
    page_numbers: list[int] = Field(default_factory=list, description="Affected page numbers (1-indexed)")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence (0.0-1.0)")
    severity: str = Field(description="Severity: critical, high, medium, low")
    details: str = Field(description="Human-readable description of the issue")
    suggested_correction: str | None = Field(default=None, description="Suggested correction action")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Issue-specific metadata")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity is one of the allowed values."""
        valid_severities = {"critical", "high", "medium", "low"}
        if v not in valid_severities:
            raise ValueError(
                f"severity must be one of {valid_severities}, got '{v}'"
            )
        return v

    @field_validator("page_numbers")
    @classmethod
    def validate_page_numbers(cls, v: list[int]) -> list[int]:
        """Validate page numbers are positive."""
        if any(page <= 0 for page in v):
            raise ValueError("Page numbers must be positive (1-indexed)")
        return v


class QualityGrade(str, Enum):
    """Quality grading system for OCR confidence (traffic light system)."""

    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"  # 80-89%
    FAIR = "fair"  # 70-79%
    POOR = "poor"  # <70%


class AnalysisResult(BaseModel):
    """Result of PDF analysis containing detected issues and quality assessment.

    Attributes:
        document_path: Path to the analysed PDF document.
        total_pages: Total number of pages in document.
        issues: List of detected issues.
        requires_correction: Whether document requires correction.
        overall_quality_score: Overall quality score (0.0-1.0).
        quality_grade: Quality grade (Excellent/Good/Fair/Poor).
        estimated_correction_time: Estimated time for correction in seconds.
        analysed_at: Timestamp of analysis.
        analysis_duration: Duration of analysis in seconds.
        metadata: Additional analysis metadata.
    """

    document_path: Path
    total_pages: int = Field(gt=0, description="Total number of pages")
    issues: list[IssueReport] = Field(default_factory=list, description="Detected issues")
    requires_correction: bool = Field(description="Whether correction is needed")
    overall_quality_score: float = Field(ge=0.0, le=1.0, description="Overall quality (0.0-1.0)")
    quality_grade: QualityGrade = Field(description="Quality grade (traffic light system)")
    estimated_correction_time: float | None = Field(
        default=None,
        ge=0.0,
        description="Estimated correction time in seconds"
    )
    analysed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Analysis timestamp"
    )
    analysis_duration: float = Field(ge=0.0, description="Analysis duration in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional analysis metadata")

    @field_validator("quality_grade", mode="before")
    @classmethod
    def compute_quality_grade(cls, v: QualityGrade | None, info) -> QualityGrade:
        """Compute quality grade from overall_quality_score if not provided."""
        # If grade is already provided, use it
        if v is not None and isinstance(v, QualityGrade):
            return v

        # Otherwise compute from overall_quality_score
        score = info.data.get("overall_quality_score")
        if score is None:
            raise ValueError("Either quality_grade or overall_quality_score must be provided")

        # Traffic light system thresholds
        if score >= 0.90:
            return QualityGrade.EXCELLENT
        elif score >= 0.80:
            return QualityGrade.GOOD
        elif score >= 0.70:
            return QualityGrade.FAIR
        else:
            return QualityGrade.POOR

    def has_critical_issues(self) -> bool:
        """Check if analysis found any critical issues."""
        return any(issue.severity == "critical" for issue in self.issues)

    def has_high_severity_issues(self) -> bool:
        """Check if analysis found critical or high severity issues."""
        return any(issue.severity in {"critical", "high"} for issue in self.issues)

    def issues_by_type(self, issue_type: IssueType) -> list[IssueReport]:
        """Get all issues of a specific type."""
        return [issue for issue in self.issues if issue.issue_type == issue_type]

    def affected_pages(self) -> set[int]:
        """Get set of all page numbers affected by any issue."""
        pages = set()
        for issue in self.issues:
            pages.update(issue.page_numbers)
        return pages


class CorrectionAction(BaseModel):
    """A correction action applied to a PDF document.

    Attributes:
        action_type: Type of correction (rotation, reordering, duplicate_removal).
        issue: The issue this action addresses.
        pages_affected: Page numbers affected by this action.
        applied_at: Timestamp when correction was applied.
        success: Whether correction was successful.
        error_message: Error message if correction failed.
        rollback_available: Whether this action can be rolled back.
        metadata: Additional correction metadata.
    """

    action_type: str
    issue: IssueReport
    pages_affected: list[int] = Field(default_factory=list, description="Affected pages")
    applied_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Application timestamp"
    )
    success: bool = Field(description="Whether correction succeeded")
    error_message: str | None = Field(default=None, description="Error message if failed")
    rollback_available: bool = Field(default=True, description="Whether rollback is possible")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Correction metadata")


class CorrectionResult(BaseModel):
    """Result of applying corrections to a PDF document.

    Attributes:
        original_path: Path to original PDF.
        corrected_path: Path to corrected PDF.
        actions: List of correction actions applied.
        quality_before: Quality score before correction.
        quality_after: Quality score after correction.
        improvement: Quality improvement (after - before).
        total_duration: Total correction duration in seconds.
        corrected_at: Timestamp of correction completion.
        metadata: Additional correction metadata.
    """

    original_path: Path
    corrected_path: Path | None = Field(default=None, description="Path to corrected PDF")
    actions: list[CorrectionAction] = Field(default_factory=list, description="Applied actions")
    quality_before: float = Field(ge=0.0, le=1.0, description="Quality before correction")
    quality_after: float | None = Field(default=None, ge=0.0, le=1.0, description="Quality after")
    improvement: float | None = Field(default=None, description="Quality improvement")
    total_duration: float = Field(ge=0.0, description="Total correction duration in seconds")
    corrected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Correction timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def all_successful(self) -> bool:
        """Check if all correction actions succeeded."""
        return all(action.success for action in self.actions)

    def failed_actions(self) -> list[CorrectionAction]:
        """Get list of failed correction actions."""
        return [action for action in self.actions if not action.success]
