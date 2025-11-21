"""PDF correction and analysis for messy documents.

v0.3.5: Automated detection and correction of PDF issues (rotation, ordering, duplicates).
"""

from src.correction.analyzer import PDFAnalyzer, AnalysisResult, AnalyzerConfig
from src.correction.corrector import PDFCorrector, CorrectorConfig
from src.correction.schemas import (
    IssueReport,
    IssueType,
    QualityGrade,
    CorrectionAction,
    CorrectionResult,
)
from src.correction.transformers import (
    RotationTransformer,
    DuplicateRemover,
    PageReorderTransformer,
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
    # Transformers
    "RotationTransformer",
    "DuplicateRemover",
    "PageReorderTransformer",
    # Schemas
    "IssueReport",
    "IssueType",
    "QualityGrade",
]
