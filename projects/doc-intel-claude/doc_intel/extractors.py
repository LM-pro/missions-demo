"""Modular text extraction for PDF, DOCX, and TXT documents.

Each extractor is pure (path -> text) and degrades gracefully on corrupt
input by returning an empty string and surfacing the error to the caller.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from doc_intel.models import DocFormat

logger = logging.getLogger(__name__)


# ---------- Format detection ---------------------------------------------------

_EXTENSION_MAP: dict[str, DocFormat] = {
    ".pdf": DocFormat.PDF,
    ".docx": DocFormat.DOCX,
    ".txt": DocFormat.TXT,
    ".md": DocFormat.TXT,
}


def detect_format(path: str | Path) -> DocFormat:
    """Detect document format from file extension."""
    suffix = Path(path).suffix.lower()
    return _EXTENSION_MAP.get(suffix, DocFormat.UNKNOWN)


# ---------- Individual extractors ---------------------------------------------

def _extract_pdf(path: Path) -> tuple[str, int]:
    """Return (text, page_count). Empty + 0 if pypdf trips on a malformed file."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pypdf is required for PDF extraction") from exc

    try:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages), len(reader.pages)
    except Exception as exc:
        logger.warning("PDF extraction failed for %s: %s", path, exc)
        return "", 0


def _extract_docx(path: Path) -> tuple[str, int]:
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("python-docx is required for DOCX extraction") from exc

    try:
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        # Tables can hold structured data — flatten them in row-order
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    paragraphs.append(" | ".join(cells))
        return "\n".join(paragraphs), None
    except Exception as exc:
        logger.warning("DOCX extraction failed for %s: %s", path, exc)
        return "", None


def _extract_txt(path: Path) -> tuple[str, int]:
    try:
        return path.read_text(encoding="utf-8", errors="replace"), None
    except Exception as exc:
        logger.warning("TXT read failed for %s: %s", path, exc)
        return "", None


_EXTRACTORS: dict[DocFormat, Callable[[Path], tuple[str, int]]] = {
    DocFormat.PDF: _extract_pdf,
    DocFormat.DOCX: _extract_docx,
    DocFormat.TXT: _extract_txt,
}


# ---------- Public façade ------------------------------------------------------

def extract_text(path: str | Path) -> tuple[str, DocFormat, int | None]:
    """Dispatch to the right extractor.

    Returns (text, format, page_count_or_none). Raises FileNotFoundError if
    the file is missing; otherwise returns ("", UNKNOWN, None) for unsupported
    extensions.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Document not found: {p}")

    fmt = detect_format(p)
    extractor = _EXTRACTORS.get(fmt)
    if extractor is None:
        logger.warning("Unsupported format for %s", p)
        return "", DocFormat.UNKNOWN, None

    text, pages = extractor(p)
    return text, fmt, pages
