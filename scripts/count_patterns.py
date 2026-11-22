"""
Per-period scope and conclusion counts for the Grex patterns of the paper,
computed directly from a CoNLL-U file (reproducing the GREW patterns).

Usage:  python3 count_patterns.py  merged_file.conllu

Patterns (as in pattern files / appendix):
  negation      scope: CLH-[csubj|ccomp|advcl|acl]->X; X[upos=VERB|AUX];
                       Y[upos=PART|ADV, Polarity=Neg]; X-[advmod]->Y
                conclusion: X << Y
  aux-omission  scope: CLH-[csubj|ccomp|advcl|acl]->X; X[VerbForm=Sup]
                conclusion: X-[aux]->Y          (conclusion = auxiliary present)
  rel. pronoun  scope: X[upos=PRON, PronType=Rel]; V[upos=VERB];
                       CLH-[acl:relcl]->V; V->X
                conclusions: X[lemma="som"]  /  X[lemma in VILKEN]
Relations are matched exactly, as in GREW (acl does not match acl:relcl).
Period: first year in the sentence id (e.g. 1700_1749_1026_sec25) or "# period".
"""
import re
import sys
from collections import defaultdict

SUB = {"csubj", "ccomp", "advcl", "acl"}
VILKEN = {"vilken", "hvilken", "hvilk", "hwilke", "hwilk", "hvad", "en", "hvarmed", "varom", "vem"}
BINS = [(1700, 1749), (1750, 1799), (1800, 1849), (1850, 1899), (1900, 1950)]
PERIODS = [f"{s}-{e}" for s, e in BINS]
ROWS = ["negation (V << NEG)", "aux-omission (aux present)", "rel. pronoun: som", "rel. pronoun: vilken"]


def period_of(meta):
    for text in (meta.get("period", ""), meta.get("sent_id", "")):
        m = re.search(r"1[6-9]\d\d", text)
        if m:
            y = int(m.group())
            for s, e in BINS:
                if s <= y <= e:
                    return f"{s}-{e}"
    return None


def sentences(path):
    meta, toks = {}, []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                if toks:
                    yield meta, toks
                meta, toks = {}, []
            elif line.startswith("#"):
                if "=" in line:
                    k, v = line[1:].split("=", 1)
                    meta.setdefault(k.strip(), v.strip())
            else:
                c = line.split("\t")
                if len(c) >= 8 and c[0].isdigit():
                    feats = dict(x.split("=", 1) for x in c[5].split("|") if "=" in x)
                    toks.append({"id": int(c[0]), "lemma": c[2], "upos": c[3], "feats": feats,
                                 "head": int(c[6]) if c[6].isdigit() else -1, "deprel": c[7]})
    if toks:
        yield meta, toks


def count(toks):
    """Return {row: [scope, conclusion]} for one sentence."""
    res = defaultdict(lambda: [0, 0])
    kids = defaultdict(list)
    for t in toks:
        kids[t["head"]].append(t)
    for x in toks:
        # X must be the dependent of some CLH with a subordinate relation
        if x["deprel"] in SUB and x["head"] > 0:
            # negation
            if x["upos"] in ("VERB", "AUX"):
                for y in kids[x["id"]]:
                    if (y["deprel"] == "advmod" and y["upos"] in ("PART", "ADV")
                            and y["feats"].get("Polarity") == "Neg"):
                        r = res[ROWS[0]]; r[0] += 1; r[1] += x["id"] < y["id"]
            # aux-omission
            if x["feats"].get("VerbForm") == "Sup":
                r = res[ROWS[1]]; r[0] += 1
                r[1] += any(k["deprel"] == "aux" for k in kids[x["id"]])
    # relative pronouns: V[upos=VERB], CLH-[acl:relcl]->V, V -> X (any relation)
    for v in toks:
        if v["upos"] == "VERB" and v["deprel"] == "acl:relcl" and v["head"] > 0:
            for x in kids[v["id"]]:
                if x["upos"] == "PRON" and x["feats"].get("PronType") == "Rel":
                    for row, ok in ((ROWS[2], x["lemma"] == "som"), (ROWS[3], x["lemma"] in VILKEN)):
                        r = res[row]; r[0] += 1; r[1] += ok
    return res


def main(path):
    tot = {row: {p: [0, 0] for p in PERIODS} for row in ROWS}
    n_sent = defaultdict(int)
    for meta, toks in sentences(path):
        p = period_of(meta)
        if p is None:
            continue
        n_sent[p] += 1
        for row, (s, c) in count(toks).items():
            tot[row][p][0] += s; tot[row][p][1] += c

    print(f"\nSentences per period: " + ", ".join(f"{p}: {n_sent[p]:,}" for p in PERIODS))
    print(f"\n{'':30}" + "".join(f"{p:>16}" for p in PERIODS) + f"{'total':>16}")
    for row in ROWS:
        cells = [tot[row][p] for p in PERIODS]
        s, c = sum(x[0] for x in cells), sum(x[1] for x in cells)
        print(f"{row:30}" + "".join(f"{x[1]:>7} / {x[0]:<6}" for x in cells) + f"{c:>7} / {s:<6}")
    print("(conclusion / scope)\n\nLaTeX rows (scope & concl. per period):")
    names = ["Negation (V before NEG)", "Aux-omission (aux present)",
             r"Rel.\ pronoun: \textit{som}", r"Rel.\ pronoun: \textit{vilken}"]
    for row, name in zip(ROWS, names):
        print(f"{name:32}& " + " & ".join(f"{tot[row][p][0]:,} & {tot[row][p][1]:,}" for p in PERIODS) + r" \\")
    print("\nFor make_figure.py:")
    for row, key in zip(ROWS, ["neg", "aux", "som", "vilken"]):
        print(f'"{key}": ({[tot[row][p][0] for p in PERIODS]}, {[tot[row][p][1] for p in PERIODS]}),')


if __name__ == "__main__":
    main(sys.argv[1])