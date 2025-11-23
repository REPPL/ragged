"""PDF correction and analysis for messy documents.

v0.3.5: Automated detection and correction of PDF issues (rotation, ordering, duplicates).
"""

from ragged.correction.analyzer import AnalysisResult, AnalyzerConfig, PDFAnalyzer
from ragged.correction.corrector import CorrectorConfig, PDFCorrector
from ragged.correction.metadata import MetadataGenerator
from ragged.correction.pipeline import CorrectionPipeline
from ragged.correction.schemas import (
    CorrectionAction,
    CorrectionResult,
    IssueReport,
    IssueType,
    QualityGrade,
)
from ragged.correction.transformers import (
    DuplicateRemover,
    PageReorderTransformer,
    RotationTransformer,
)

__all__ = [
    # Analysis
    "PDFAnalyzer",
    "AnalyzerConfig",
    "AnalysisResult",
    # Correction
    "PDFCorrector",
    "CorrectorConfig",
    "CorrectionAction",
    "CorrectionResult",
    # Pipeline
    "CorrectionPipeline",
    "MetadataGenerator",
    # Transformers
    "RotationTransformer",
    "DuplicateRemover",
    "PageReorderTransformer",
    # Schemas
    "IssueReport",
    "IssueType",
    "QualityGrade",
]
