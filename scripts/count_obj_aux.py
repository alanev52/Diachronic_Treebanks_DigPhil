"""
Count "object between auxiliary and verb" per 50-year period, directly from CoNLL-U.

It reproduces the GREW pattern

    scope:      V[upos=VERB, VerbForm=Inf]; A[upos=AUX]; V-[aux]->A;
                X[upos=NOUN|PROPN|PRON];  + word order (see below)
    conclusion: V-[<relations>]->X

in four variants, all in one run:

    order     adjacent      A < X; X < V    (aux, X, verb next to each other)
              non-adjacent  A << X; X << V  (X anywhere between aux and verb)
    relations obj|iobj      objects only
              obj|iobj|obl  objects and obliques

Usage
    python3 count_obj_aux.py  CONLLU_FILE_OR_FOLDER

Output (written next to this script, in the folder you run it from)
    obj_aux_counts.csv      scope/conclusion counts per period for every variant
    obj_aux_matches.tsv     every conclusion match, for manual checking
    and a summary table + LaTeX row printed on screen

Period of a sentence: taken from the sentence metadata line "# period = ..."
(e.g. "1860_1879" or "1850-1899"); if missing, from the first 4-digit year in
the file name. The year is then put into the paper's 50-year bins.
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

META_KEY = "period"                       # sentence metadata field with the period
BINS = [(1700, 1749), (1750, 1799), (1800, 1849), (1850, 1899), (1900, 1950)]
X_UPOS = {"NOUN", "PROPN", "PRON"}
BREAKDOWN_VARIANT = "non-adjacent, obj|iobj"    # variant split by noun/pronoun and subject position
VARIANTS = [                              # (name, adjacent?, conclusion relations)
    ("adjacent, obj|iobj",         True,  {"obj", "iobj"}),
    ("adjacent, obj|iobj|obl",     True,  {"obj", "iobj", "obl"}),
    ("non-adjacent, obj|iobj",     False, {"obj", "iobj"}),
    ("non-adjacent, obj|iobj|obl", False, {"obj", "iobj", "obl"}),
]


def period_label(year):
    for start, end in BINS:
        if start <= year <= end:
            return f"{start}-{end}"
    return None


def read_conllu(path):
    """Yield (metadata dict, list of token dicts) per sentence."""
    meta, toks = {}, []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                if toks:
                    yield meta, toks
                meta, toks = {}, []
            elif line.startswith("#"):
                if "=" in line:
                    k, v = line[1:].split("=", 1)
                    meta[k.strip()] = v.strip()
            else:
                c = line.split("\t")
                if len(c) < 8 or not c[0].isdigit():   # skip multiword tokens and empty nodes
                    continue
                feats = dict(fv.split("=", 1) for fv in c[5].split("|") if "=" in fv)
                toks.append({"id": int(c[0]), "form": c[1], "upos": c[3],
                             "feats": feats, "head": int(c[6]) if c[6].isdigit() else -1,
                             "deprel": c[7]})
    if toks:
        yield meta, toks


def sentence_year(meta, filename):
    for text in (meta.get(META_KEY, ""), filename):
        m = re.search(r"1[6-9]\d\d", text)
        if m:
            return int(m.group())
    return None


def scope_matches(toks, adjacent):
    """All (A, X, V) triples matching the scope."""
    by_id = {t["id"]: t for t in toks}
    for v in toks:
        if v["upos"] != "VERB" or v["feats"].get("VerbForm") != "Inf":
            continue
        for a in toks:
            if a["head"] != v["id"] or a["deprel"] != "aux" or a["upos"] != "AUX":
                continue
            if adjacent:
                x = by_id.get(a["id"] + 1)
                if x and x["id"] + 1 == v["id"] and x["upos"] in X_UPOS:
                    yield a, x, v
            else:
                for x in toks:
                    if a["id"] < x["id"] < v["id"] and x["upos"] in X_UPOS:
                        yield a, x, v


def main(folder):
    path = Path(folder)
    files = [path] if path.is_file() else sorted(path.rglob("*.conllu"))
    if not files:
        sys.exit(f"No .conllu files found in {folder}")

    counts = {name: defaultdict(lambda: [0, 0]) for name, _, _ in VARIANTS}
    no_period = 0
    out_rows = []
    breakdown = defaultdict(lambda: defaultdict(int))

    for path in files:
        for meta, toks in read_conllu(path):
            year = sentence_year(meta, path.name)
            period = period_label(year) if year else None
            if period is None:
                no_period += 1
                continue
            text = meta.get("text", " ".join(t["form"] for t in toks))
            for name, adjacent, rels in VARIANTS:
                for a, x, v in scope_matches(toks, adjacent):
                    counts[name][period][0] += 1
                    if x["head"] == v["id"] and x["deprel"] in rels:
                        counts[name][period][1] += 1
                        x_type = "pronoun" if x["upos"] == "PRON" else "noun"
                        subj = any(t["head"] == v["id"] and t["deprel"].startswith("nsubj")
                                   and a["id"] < t["id"] < v["id"] for t in toks)
                        subj_txt = "subject between" if subj else "no subject between"
                        if name == BREAKDOWN_VARIANT:
                            breakdown[(x_type, subj_txt)][period] += 1
                        out_rows.append([name, period, path.name, meta.get("sent_id", ""),
                                         a["form"], x["form"], x["upos"], x["deprel"],
                                         "yes" if subj else "no", v["form"], text])

    periods = [f"{s}-{e}" for s, e in BINS]

    # summary on screen
    print(f"\nRead {len(files)} files. Sentences without a recognisable period: {no_period}\n")
    head = f"{'variant':28}" + "".join(f"{p:>16}" for p in periods) + f"{'total':>14}"
    print(head + "\n" + "-" * len(head))
    for name, _, _ in VARIANTS:
        cells = [counts[name][p] for p in periods]
        tot = [sum(c[0] for c in cells), sum(c[1] for c in cells)]
        print(f"{name:28}" + "".join(f"{c[1]:>7} / {c[0]:<6}" for c in cells)
              + f"{tot[1]:>6} / {tot[0]:<6}")
    print("\n(conclusion / scope)\n")

    # breakdown of the object-only, non-adjacent conclusion matches
    print(f"Conclusion matches of '{BREAKDOWN_VARIANT}' by type of X:")
    print(f"{'':38}" + "".join(f"{p:>11}" for p in periods) + f"{'total':>8}")
    for x_type in ("noun", "pronoun"):
        for subj_txt in ("no subject between", "subject between"):
            row = [breakdown[(x_type, subj_txt)][p] for p in periods]
            print(f"{x_type + ', ' + subj_txt:38}" + "".join(f"{n:>11}" for n in row) + f"{sum(row):>8}")
    print("(noun = NOUN or PROPN; 'subject between' = a subject of the verb stands between aux and verb)\n")

    # LaTeX rows for the appendix table
    print("LaTeX rows for tab:occurences (scope & concl. per period):")
    for name, _, _ in VARIANTS:
        cells = [counts[name][p] for p in periods]
        print(f"% {name}\nObject between aux and verb & "
              + " & ".join(f"{c[0]:,} & {c[1]:,}" for c in cells) + r" \\")

    # files
    with open("obj_aux_counts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variant", "period", "scope", "conclusion"])
        for name, _, _ in VARIANTS:
            for p in periods:
                w.writerow([name, p, *counts[name][p]])
    with open("obj_aux_matches.tsv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["variant", "period", "file", "sent_id", "aux", "X", "X_upos", "X_deprel",
                    "subject_between", "verb", "sentence"])
        w.writerows(out_rows)
    print("\nWrote obj_aux_counts.csv and obj_aux_matches.tsv")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python3 count_obj_aux.py CONLLU_FILE_OR_FOLDER")
    main(sys.argv[1])