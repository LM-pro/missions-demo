"""Create a tiny valid PDF at data/sample.pdf using only stdlib.

Useful so contributors have a real binary fixture without committing a large
file or depending on reportlab. Run once: `python scripts/make_sample_pdf.py`.
"""
from pathlib import Path

PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 84>>stream
BT /F1 14 Tf 30 100 Td (doc-intel-claude sample) Tj 0 -20 Td (Invoice #2026-001) Tj ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000053 00000 n 
0000000098 00000 n 
0000000191 00000 n 
0000000324 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
389
%%EOF
"""

out = Path(__file__).parent.parent / "data" / "sample.pdf"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(PDF)
print(f"wrote {out} ({out.stat().st_size} bytes)")
