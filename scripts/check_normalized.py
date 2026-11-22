"""
Which texts in a Grex input file were normalized, and how many sentences/tokens per period?

Usage:  python3 check_normalized.py  merged_file.conllu

A token counts as normalized if its MISC column holds a word form
(not just SpaceAfter / start_char / end_char information).
Sentence IDs are expected to look like 1700_1749_1026_sec25.
"""
import re
import sys
from collections import defaultdict

texts = defaultdict(lambda: [0, 0, 0])          # (period, text) -> sentences, tokens, normalized tokens
key = ("?", "?")
with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
    for line in f:
        if line.startswith("# sent_id"):
            sid = line.split("=", 1)[1].strip()
            m = re.match(r"(\d{4}_\d{4})_\d+_(.+)", sid)
            key = (m.group(1), m.group(2)) if m else ("?", sid)
            texts[key][0] += 1
        elif line[:1].isdigit():
            c = line.rstrip("\n").split("\t")
            if len(c) >= 10 and c[0].isdigit():
                texts[key][1] += 1
                misc = [x for x in c[9].split("|") if x not in ("_", "")
                        and not x.startswith(("SpaceAfter", "SpacesAfter", "start_char", "end_char"))]
                texts[key][2] += bool(misc)

print("Normalized texts:")
for (p, t), (s, n, k) in sorted(texts.items()):
    if k:
        print(f"  {p}  {t:16} {s:>6} sentences  {100 * k / n:4.0f}% of tokens with normalized form")

print("\nPer period:")
periods = defaultdict(lambda: [0, 0, 0, 0])
for (p, t), (s, n, k) in texts.items():
    d = periods[p]; d[0] += 1; d[1] += bool(k); d[2] += s; d[3] += n
for p, (nt, nn, s, n) in sorted(periods.items()):
    print(f"  {p}: {nt} texts ({nn} normalized), {s:,} sentences, {n:,} tokens")