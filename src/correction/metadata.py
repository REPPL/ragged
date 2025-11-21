"""Metadata generation for PDF corrections.

v0.3.5: Generates JSON metadata files documenting corrections and quality.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from src.correction.schemas import AnalysisResult, CorrectionResult, IssueType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MetadataGenerator:
    """Generates metadata files for PDF corrections.

    Creates JSON files documenting:
    - corrections.json: Applied corrections
    - uncertainties.json: Low-confidence sections
    - page_mapping.json: Page number mappings
    - quality_report.json: Detailed quality metrics
    """

    def __init__(self, output_dir: Path):
        """Initialize metadata generator.

        Args:
            output_dir: Directory to write metadata files.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(
        self,
        analysis: AnalysisResult,
        correction: CorrectionResult | None = None,
    ) -> dict[str, Path]:
        """Generate all metadata files.

        Args:
            analysis: Analysis results.
            correction: Optional correction results.

        Returns:
            Dictionary mapping metadata type to file path.
        """
        files = {}

        # Always generate quality report
        files["quality"] = self.generate_quality_report(analysis)

        # Generate corrections metadata if corrections were applied
        if correction:
            files["corrections"] = self.generate_corrections_metadata(correction)
            files["page_mapping"] = self.generate_page_mapping(correction)

        # Generate uncertainties if quality detector found issues
        quality_issues = [i for i in analysis.issues if i.issue_type == IssueType.QUALITY]
        if quality_issues:
            files["uncertainties"] = self.generate_uncertainties(quality_issues)

        logger.info(f"Generated {len(files)} metadata files in {self.output_dir}")
        return files

    def generate_quality_report(self, analysis: AnalysisResult) -> Path:
        """Generate quality_report.json with detailed metrics.

        Args:
            analysis: Analysis results.

        Returns:
            Path to generated file.
        """
        report = {
            "document_path": str(analysis.document_path),
            "analysed_at": analysis.analysed_at.isoformat(),
            "total_pages": analysis.total_pages,
            "overall_quality": {
                "score": analysis.overall_quality_score,
                "grade": analysis.quality_grade.value,
            },
            "requires_correction": analysis.requires_correction,
            "issues_detected": len(analysis.issues),
            "issues_by_type": self._group_issues_by_type(analysis.issues),
            "affected_pages": sorted(analysis.affected_pages()),
            "critical_issues": analysis.has_critical_issues(),
            "high_severity_issues": analysis.has_high_severity_issues(),
            "analysis_duration": analysis.analysis_duration,
            "metadata": analysis.metadata,
        }

        output_path = self.output_dir / "quality_report.json"
        self._write_json(output_path, report)
        return output_path

    def generate_corrections_metadata(self, correction: CorrectionResult) -> Path:
        """Generate corrections.json with applied corrections.

        Args:
            correction: Correction results.

        Returns:
            Path to generated file.
        """
        metadata = {
            "original_path": str(correction.original_path),
            "corrected_path": str(correction.corrected_path) if correction.corrected_path else None,
            "corrected_at": correction.corrected_at.isoformat(),
            "quality_improvement": {
                "before": correction.quality_before,
                "after": correction.quality_after,
                "improvement": correction.improvement,
            },
            "total_duration": correction.total_duration,
            "corrections_applied": len(correction.actions),
            "successful_corrections": len([a for a in correction.actions if a.success]),
            "failed_corrections": len(correction.failed_actions()),
            "actions": [
                {
                    "action_type": action.action_type,
                    "pages_affected": action.pages_affected,
                    "applied_at": action.applied_at.isoformat(),
                    "success": action.success,
                    "error_message": action.error_message,
                    "issue": {
                        "type": action.issue.issue_type.value,
                        "confidence": action.issue.confidence,
                        "severity": action.issue.severity,
                        "details": action.issue.details,
                    },
                }
                for action in correction.actions
            ],
        }

        output_path = self.output_dir / "corrections.json"
        self._write_json(output_path, metadata)
        return output_path

    def generate_page_mapping(self, correction: CorrectionResult) -> Path:
        """Generate page_mapping.json with original ↔ corrected page mappings.

        Args:
            correction: Correction results.

        Returns:
            Path to generated file.
        """
        # Build page mapping from correction actions
        removed_pages = set()
        for action in correction.actions:
            if action.action_type == "duplicate" and action.success:
                removed_pages.update(action.pages_affected)

        # Create mapping (original page → corrected page or None if removed)
        mapping = {}
        corrected_page = 1
        for original_page in range(1, 1000):  # Assume max 1000 pages
            if original_page in removed_pages:
                mapping[str(original_page)] = None  # Page was removed
            else:
                mapping[str(original_page)] = corrected_page
                corrected_page += 1

            # Stop when we've covered all removed pages + some buffer
            if original_page > max(removed_pages) + 10 if removed_pages else 10:
                break

        page_mapping = {
            "original_to_corrected": mapping,
            "pages_removed": sorted(removed_pages),
            "total_pages_original": len(mapping),
            "total_pages_corrected": corrected_page - 1,
        }

        output_path = self.output_dir / "page_mapping.json"
        self._write_json(output_path, page_mapping)
        return output_path

    def generate_uncertainties(self, quality_issues: list) -> Path:
        """Generate uncertainties.json with low-confidence sections.

        Args:
            quality_issues: List of quality-related issues.

        Returns:
            Path to generated file.
        """
        uncertainties = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_uncertain_pages": len(quality_issues),
            "pages": [
                {
                    "page_number": issue.page_numbers[0] if issue.page_numbers else 0,
                    "confidence": issue.confidence,
                    "severity": issue.severity,
                    "details": issue.details,
                    "suggested_action": issue.suggested_correction,
                }
                for issue in quality_issues
            ],
        }

        output_path = self.output_dir / "uncertainties.json"
        self._write_json(output_path, uncertainties)
        return output_path

    def _group_issues_by_type(self, issues: list) -> dict[str, int]:
        """Group issues by type and count them.

        Args:
            issues: List of IssueReport objects.

        Returns:
            Dictionary mapping issue type to count.
        """
        grouped = {}
        for issue in issues:
            issue_type = issue.issue_type.value
            grouped[issue_type] = grouped.get(issue_type, 0) + 1
        return grouped

    def _write_json(self, path: Path, data: dict) -> None:
        """Write JSON data to file with pretty formatting.

        Args:
            path: Output file path.
            data: Data to write.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.debug(f"Wrote metadata: {path}")
