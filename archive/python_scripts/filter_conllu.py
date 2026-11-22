"""
filter_conllu.py
----------------
Filters a merged CoNLL-U file, keeping only sentences whose sent_id
appears in at least N files according to sent_id_comparison.xlsx.

Usage:
    python3 filter_conllu.py sent_id_comparison.xlsx merged.conllu
    python3 filter_conllu.py sent_id_comparison.xlsx merged.conllu -o data_to_eval.conllu
    python3 filter_conllu.py sent_id_comparison.xlsx merged.conllu --min-files 3
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

import pandas as pd

SENT_ID_RE = re.compile(r'^#\s*sent_id\s*=\s*(.+)$')


def load_valid_ids(xlsx_path: Path, min_files: int) -> set:
    df = pd.read_excel(xlsx_path, dtype={"sent_id": str, "count_of_files": int})
    if "sent_id" not in df.columns or "count_of_files" not in df.columns:
        print(f"Error: expected columns 'sent_id' and 'count_of_files' in {xlsx_path.name}")
        print(f"  Found: {list(df.columns)}")
        sys.exit(1)
    valid = set(df.loc[df["count_of_files"] >= min_files, "sent_id"].str.strip())
    print(f"  {len(valid)} sent_ids with count_of_files >= {min_files}")
    return valid


def filter_conllu(conllu_path: Path, valid_ids: set, output_path: Path) -> None:
    kept = 0
    skipped = 0
    current_sentence = []
    current_id = None
    in_valid = False

    with conllu_path.open("r", encoding="utf-8") as f, \
         output_path.open("w", encoding="utf-8") as out:

        for line in f:
            current_sentence.append(line)

            # Detect sent_id line
            m = SENT_ID_RE.match(line.rstrip("\n"))
            if m:
                current_id = m.group(1).strip()
                in_valid = current_id in valid_ids

            # Blank line = end of sentence
            if line.strip() == "":
                if in_valid:
                    out.writelines(current_sentence)
                    kept += 1
                else:
                    skipped += 1
                current_sentence = []
                current_id = None
                in_valid = False

        # Handle file not ending with a blank line
        if current_sentence and any(l.strip() for l in current_sentence):
            if in_valid:
                out.writelines(current_sentence)
                kept += 1
            else:
                skipped += 1

    print(f"  Kept:    {kept} sentences")
    print(f"  Skipped: {skipped} sentences")
    print(f"\nOutput written to: {output_path.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter a CoNLL-U file to sentences present in >= N source files."
    )
    parser.add_argument("comparison", help="sent_id_comparison.xlsx from find_common_sent_ids.py")
    parser.add_argument("conllu",     help="Merged CoNLL-U file to filter")
    parser.add_argument(
        "--output", "-o",
        default="data_to_eval.conllu",
        help="Output file (default: data_to_eval.conllu)"
    )
    parser.add_argument(
        "--min-files", "-m",
        type=int,
        default=2,
        help="Minimum count_of_files threshold (default: 2)"
    )
    args = parser.parse_args()

    xlsx_path   = Path(args.comparison)
    conllu_path = Path(args.conllu)
    output_path = Path(args.output)

    for p in (xlsx_path, conllu_path):
        if not p.exists():
            print(f"File not found: {p}")
            sys.exit(1)

    print(f"\nLoading comparison table: {xlsx_path.name}")
    valid_ids = load_valid_ids(xlsx_path, args.min_files)

    print(f"\nFiltering: {conllu_path.name}")
    filter_conllu(conllu_path, valid_ids, output_path)