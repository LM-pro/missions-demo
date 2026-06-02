"""Command-line entrypoint: `doc-intel <files...> [--out output/results.json]`."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from doc_intel.processor import DocumentProcessor

console = Console()


def main() -> int:
    parser = argparse.ArgumentParser(prog="doc-intel", description="Claude-powered doc IE")
    parser.add_argument("paths", nargs="+", help="Document paths (PDF/DOCX/TXT)")
    parser.add_argument("--out", default="output/results.json", help="JSON output path")
    parser.add_argument("--csv", default=None, help="Optional CSV output path")
    parser.add_argument("--model", default=None, help="Claude model override")
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()

    processor = DocumentProcessor(model=args.model, concurrency=args.concurrency)
    results = processor.process_batch(args.paths)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    processor.to_json(results, args.out)
    if args.csv:
        processor.to_csv(results, args.csv)

    table = Table(title="doc-intel results")
    for col in ("source", "format", "chars", "entities", "latency_ms", "status"):
        table.add_column(col)
    for r in results:
        table.add_row(
            Path(r.source_path).name,
            r.format.value,
            str(r.char_count),
            str(len(r.entities)),
            str(r.latency_ms),
            "OK" if r.ok else f"ERR:{r.error[:30]}",
        )
    console.print(table)
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
