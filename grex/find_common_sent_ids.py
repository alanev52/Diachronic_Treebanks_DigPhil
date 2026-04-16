"""
find_common_sent_ids.py
-----------------------
Scans multiple Excel files, extracts sent_id values from each row,
and reports which sent_ids appear in all files, some files, or only one file.

By default only sheets whose name contains "sent_" are processed.

Usage examples:
    # Use default filter (sheets containing "sent_"):
    python find_common_sent_ids.py *.xlsx

    # Use a custom sheet name filter:
    python find_common_sent_ids.py *.xlsx --sheet my_table

    # Process ALL sheets (no filter):
    python find_common_sent_ids.py *.xlsx --sheet ""

    # First, preview which sheets exist and which would be matched:
    python find_common_sent_ids.py *.xlsx --list

Requirements:
    pip install pandas openpyxl
"""

from __future__ import annotations

import sys
import re
import argparse
import pandas as pd
from pathlib import Path
from collections import defaultdict
from typing import Optional

# ── helpers ───────────────────────────────────────────────────────────────────

SENT_ID_PATTERN = re.compile(r"sent_id:\s*([^\s|]+)")


def extract_sent_id(cell_value) -> Optional[str]:
    """Return the sent_id from a cell string, or None if not found."""
    if not isinstance(cell_value, str):
        return None
    m = SENT_ID_PATTERN.search(cell_value)
    return m.group(1).strip() if m else None


def list_sheets(path: Path) -> list:
    """Return all sheet names in an Excel file."""
    try:
        return pd.ExcelFile(path).sheet_names
    except Exception as e:
        print(f"  WARNING  Could not open {path.name}: {e}")
        return []


def collect_ids_from_file(path: Path, sheet_filter: Optional[str] = "sent_") -> set:
    """
    Read matching sheets from an Excel file and collect all sent_ids.

    sheet_filter:
      - None / ""  -> read ALL sheets
      - str        -> read only sheets whose name contains this substring (case-insensitive)
    """
    ids = set()
    all_sheets = list_sheets(path)
    if not all_sheets:
        return ids

    if sheet_filter:
        target_sheets = [s for s in all_sheets if sheet_filter.lower() in s.lower()]
    else:
        target_sheets = all_sheets

    if not target_sheets:
        print(f"    WARNING  No sheets matching '{sheet_filter}' in {path.name}.")
        print(f"             Available sheets: {all_sheets}")
        print(f"             Tip: run with --list to preview, or --sheet '' for all sheets.")
        return ids

    print(f"    Sheets matched: {target_sheets}")
    for sheet_name in target_sheets:
        df = pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=str)
        for col in df.columns:
            for val in df[col]:
                sid = extract_sent_id(val)
                if sid:
                    ids.add(sid)
    return ids


# ── main ──────────────────────────────────────────────────────────────────────

def main(file_paths, sheet_filter="sent_", list_only=False):
    if not file_paths:
        print("No files provided.")
        sys.exit(1)

    # ── --list mode: preview sheets and exit ──────────────────────────────────
    if list_only:
        filter_label = f"'{sheet_filter}'" if sheet_filter else "ALL sheets"
        print(f"\nSheet preview for {len(file_paths)} file(s)  [filter: {filter_label}]\n")
        for path in file_paths:
            sheets = list_sheets(path)
            print(f"  {path.name}:")
            for s in sheets:
                if sheet_filter and sheet_filter.lower() in s.lower():
                    print(f"    [MATCH] {s}")
                else:
                    print(f"    [skip]  {s}")
        print("\nRe-run without --list to process the matched sheets.")
        return

    filter_label = f"'{sheet_filter}'" if sheet_filter else "ALL sheets"
    print(f"\nScanning {len(file_paths)} file(s)  [sheet filter: {filter_label}]\n")

    id_to_files = defaultdict(set)
    file_id_sets = {}

    for path in file_paths:
        print(f"  Reading: {path.name}")
        ids = collect_ids_from_file(path, sheet_filter=sheet_filter)
        file_id_sets[path.name] = ids
        for sid in ids:
            id_to_files[sid].add(path.name)
        print(f"    -> {len(ids)} unique sent_id(s) found")

    total_files = len(file_paths)
    all_ids = set(id_to_files.keys())

    in_all  = sorted(sid for sid, files in id_to_files.items() if len(files) == total_files)
    in_some = sorted(sid for sid, files in id_to_files.items() if 1 < len(files) < total_files)
    in_one  = sorted(sid for sid, files in id_to_files.items() if len(files) == 1)

    # ── Console report ────────────────────────────────────────────────────────
    sep = "-" * 70
    print(f"\n{sep}")
    print(f"SUMMARY  (sheet filter: {filter_label})")
    print(sep)
    print(f"Total unique sent_ids across all files : {len(all_ids)}")
    print(f"  Present in ALL {total_files} files              : {len(in_all)}")
    print(f"  Present in SOME files (2-{total_files-1})         : {len(in_some)}")
    print(f"  Present in exactly ONE file          : {len(in_one)}")
    print(sep)

    if in_all:
        print(f"\nOK  sent_ids in ALL {total_files} files ({len(in_all)} total):")
        for sid in in_all:
            print(f"    {sid}")
    else:
        print(f"\nNo sent_id is common to ALL {total_files} files.")

    if in_some:
        print(f"\nPARTIAL  sent_ids in SOME files ({len(in_some)} total):")
        for sid in in_some:
            files_list = ", ".join(sorted(id_to_files[sid]))
            print(f"    {sid}  ->  [{files_list}]")

    # ── Excel output ──────────────────────────────────────────────────────────
    out_path = Path("sent_id_comparison.xlsx")
    rows = []
    for sid in sorted(all_ids):
        row = {"sent_id": sid, "count_of_files": len(id_to_files[sid])}
        for path in file_paths:
            row[path.name] = "v" if sid in file_id_sets[path.name] else ""
        rows.append(row)

    result_df = pd.DataFrame(rows).sort_values(
        ["count_of_files", "sent_id"], ascending=[False, True]
    )
    result_df.to_excel(out_path, index=False)
    print(f"\nFull results saved to: {out_path.resolve()}")
    print(sep)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find common sent_ids across multiple Excel files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python find_common_sent_ids.py *.xlsx
      Process all sheets containing "sent_" (default)

  python find_common_sent_ids.py *.xlsx --list
      Preview which sheets exist and which would be matched, then exit

  python find_common_sent_ids.py *.xlsx --sheet my_table
      Only process sheets whose name contains "my_table"

  python find_common_sent_ids.py *.xlsx --sheet ""
      Process ALL sheets (no filter)
        """,
    )
    parser.add_argument("files", nargs="+", help="Excel files to scan (.xlsx)")
    parser.add_argument(
        "--sheet", "-s",
        default="sent_",
        metavar="FILTER",
        help=(
            "Only process sheets whose name contains FILTER (case-insensitive). "
            "Default: 'sent_'. Pass an empty string to process ALL sheets."
        ),
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        dest="list_only",
        help="Preview sheet names in each file (highlighting matches) and exit.",
    )
    args = parser.parse_args()

    paths = [Path(p) for p in args.files]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print("File(s) not found:")
        for m in missing:
            print(f"  {m}")
        sys.exit(1)

    main(paths, sheet_filter=args.sheet or None, list_only=args.list_only)
