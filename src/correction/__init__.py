"""PDF correction and analysis for messy documents.

v0.3.5: Automated detection and correction of PDF issues (rotation, ordering, duplicates).
"""

from src.correction.analyzer import PDFAnalyzer, AnalysisResult
from src.correction.schemas import IssueReport, IssueType

__all__ = [
    "PDFAnalyzer",
    "AnalysisResult",
    "IssueReport",
    "IssueType",
]
