"""
merge_conllu.py
---------------
Merges multiple CoNLL-U files into one, prefixing each sent_id with
the source filename stem.

  Original:  # sent_id = 1_sec300
  Result:    # sent_id = 1700_1749_1_sec300

Usage:
    python merge_conllu.py *.conllu -o merged.conllu

The files are processed in the order given (glob order = alphabetical).
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

SENT_ID_RE = re.compile(r'^(#\s*sent_id\s*=\s*)(.+)$')


def merge(input_paths: list[Path], output_path: Path) -> None:
    total_sentences = 0

    with output_path.open("w", encoding="utf-8") as out:
        for path in input_paths:
            stem = path.stem          # e.g. "1700_1749"
            file_sentences = 0

            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    m = SENT_ID_RE.match(line.rstrip("\n"))
                    if m:
                        # Rewrite sent_id line
                        prefix, original_id = m.group(1), m.group(2).strip()
                        new_id = f"{stem}_{original_id}"
                        out.write(f"{prefix}{new_id}\n")
                        file_sentences += 1
                    else:
                        out.write(line)

            print(f"  {path.name:30s}  ->  {file_sentences} sentences")
            total_sentences += file_sentences

    print(f"\nDone. {total_sentences} sentences written to: {output_path.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge CoNLL-U files with filename-prefixed sent_ids."
    )
    parser.add_argument("files", nargs="+", help="CoNLL-U files to merge (in order)")
    parser.add_argument(
        "--output", "-o",
        default="merged.conllu",
        help="Output file name (default: merged.conllu)"
    )
    args = parser.parse_args()

    paths = [Path(p) for p in args.files]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print("File(s) not found:")
        for m in missing:
            print(f"  {m}")
        sys.exit(1)

    output = Path(args.output)
    if output in paths:
        print(f"Error: output file '{output}' is also listed as input. Choose a different name.")
        sys.exit(1)

    print(f"\nMerging {len(paths)} file(s) -> {output}\n")
    merge(paths, output)