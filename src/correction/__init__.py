"""PDF correction and analysis for messy documents.

v0.3.5: Automated detection and correction of PDF issues (rotation, ordering, duplicates).
"""

from src.correction.analyzer import AnalysisResult, AnalyzerConfig, PDFAnalyzer
from src.correction.corrector import CorrectorConfig, PDFCorrector
from src.correction.metadata import MetadataGenerator
from src.correction.pipeline import CorrectionPipeline
from src.correction.schemas import (
    CorrectionAction,
    CorrectionResult,
    IssueReport,
    IssueType,
    QualityGrade,
)
from src.correction.transformers import (
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
