"""Optional FastAPI surface. Install extras: `pip install -e .[api]`.

Run: `uvicorn doc_intel.api:app --reload`
"""
from __future__ import annotations

import tempfile
from pathlib import Path

try:
    from fastapi import FastAPI, File, HTTPException, UploadFile
except ImportError:  # pragma: no cover
    FastAPI = None  # type: ignore

from doc_intel.processor import DocumentProcessor

if FastAPI is not None:
    app = FastAPI(title="doc-intel-claude", version="0.1.0")
    _processor = DocumentProcessor()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "model": _processor.model}

    @app.post("/extract")
    async def extract(file: UploadFile = File(...)) -> dict:
        suffix = Path(file.filename or "doc").suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        try:
            result = _processor.process(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        if not result.ok:
            raise HTTPException(status_code=422, detail=result.error)
        return result.model_dump(mode="json")
