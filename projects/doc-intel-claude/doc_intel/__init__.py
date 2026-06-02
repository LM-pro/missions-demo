"""doc-intel-claude — document intelligence pipeline powered by Claude."""
from doc_intel.models import DocumentInsight, ExtractedEntity, ExtractionResult
from doc_intel.processor import DocumentProcessor
from doc_intel.extractors import extract_text, detect_format

__version__ = "0.1.0"
__all__ = [
    "DocumentProcessor",
    "DocumentInsight",
    "ExtractedEntity",
    "ExtractionResult",
    "extract_text",
    "detect_format",
]
