# Automatic Rule Extraction for Diachronic Language Change Detection in Late Modern Swedish

Data and code for the paper *Automatic Rule Extraction for Diachronic Language Change
Detection in Late Modern Swedish* (under review).

We parse Late Modern Swedish texts (1700–1950) with an off-the-shelf parser (Stanza,
trained on UD Swedish-Talbanken), evaluate the parses on a small manually corrected
gold standard, and apply the Grex rule-extraction method (Herrera et al., 2025) to
four syntactic structures in order to test whether diachronic change can be detected
in automatically parsed historical data.

## Repository structure

```
data/
  raw/                 selected texts from the Swedish Diachronic Corpus, one folder per 50-year period
  gold/                gold standard: 109 manually corrected sentences (CoNLL-U), consensus version
  annotators/          the annotators' independent corrections (Arborator exports), used for agreement
parsing/
  stanza_original/     Stanza output on the original text of the gold-standard texts
  stanza_normalized/   Stanza output on spelling-normalized text, FORM restored to the original spelling
  normalization/       normalizer (rules + Flex lexicon) and the 11 texts that were normalized
  evaluation/          evaluation scripts (CoNLL 2018 evaluation, extended)
grex/
  input/               the parsed corpus used for rule extraction (51,584 sentences)
  patterns/            Grex scope/conclusion patterns and feature configurations (YAML)
  results/             extracted rules, Bonferroni-corrected rule lists, and the figure
  run_all.sh           reruns rule extraction for all patterns reported in the paper
scripts/               agreement, counting and figure scripts
archive/               earlier experiments not reported in the paper (kept for reference)
```

## From the paper to the files

| In the paper | Files | How to reproduce |
|---|---|---|
| Table: dataset overview | `grex/input/` | `python3 scripts/check_normalized.py grex/input/sv_preprocessed_cor_nf.conllu` |
| Table: inter-annotator agreement | `data/annotators/` | `scripts/inter_annotator_agreement.ipynb` (per annotator pair and text, averaged per period) |
| Table: LAS on original and normalized text | `data/gold/`, `parsing/stanza_original/`, `parsing/stanza_normalized/` | `python3 parsing/evaluation/execute_eval.py data/gold parsing/stanza_original` (and `parsing/stanza_normalized`) |
| Figure: share of scope matches per period | `grex/results/Ratio_occurences_scope.pdf` | `python3 scripts/make_figure.py` |
| Appendix: counts table | `grex/input/` | `python3 scripts/count_patterns.py grex/input/sv_preprocessed_cor_nf.conllu`; objects: `python3 scripts/count_obj_aux.py grex/input/sv_preprocessed_cor_nf.conllu` |
| Results: extracted rules | `grex/patterns/`, `grex/results/` | `GREX_DIR=/path/to/grex bash grex/run_all.sh` |
| Appendix: GREW patterns | `grex/patterns/*.yaml` | — |

## Notes

- **Inter-annotator agreement** is computed at the token level on the annotators'
  independent corrections before consensus: UPOS tags, heads (UAS) and head–relation
  pairs (LAS). Tokens that two annotators split or merged differently count as
  disagreement. Raw agreement and Cohen's κ (scikit-learn) are computed per annotator
  pair and text, then averaged per period without weighting by text length. The
  notebook was written for Colab; set `zip_path` to
  `data/annotators/dump_DigPhil_Diachronic_Treebanks_clean 3.zip`.
- **Normalization.** Spelling normalization (`parsing/normalization/`) was applied to the
  11 texts with the most variable spelling. `rules_based_norm.py` applies hand-crafted
  substitution rules; `v2_normalization.py` then matches the result against the Flex
  frequency lexicon and replaces the token with the best candidate. Unzip
  `flex.csv.zip` next to the scripts and run
  `python3 v2_normalization.py INPUT_FOLDER OUTPUT_FOLDER`.
  The original form is stored in MISC and was swapped back into FORM after parsing, so
  all trees in `grex/input/` contain the original spelling.
  Two rules (7 and 27) do not behave exactly as their comments describe; they are kept
  unchanged so that the published results can be reproduced.
- **LAS on normalized text** is computed on aligned tokens (aligned accuracy in the
  evaluation output), since normalization can merge or split tokens.
- **Counts in the figure.** `make_figure.py` contains the counts as lists at the top of
  the script; `count_patterns.py` and `count_obj_aux.py` print the exact lines to paste.
- **Object between auxiliary and verb** (`grex/patterns/object_aux_verb.yaml`) is not
  part of `run_all.sh`: the conclusion is too rare (22 matches) for rule extraction, so
  the paper reports counts and a manual check of all matches instead.
- **Negation** (`grex/patterns/negation.yaml`) is kept exactly as run. Some
  position-based features partly encode the conclusion; the resulting trivial rules are
  not interpreted in the paper.
- **Bonferroni output.** `scripts/bonferroni_patterns.py` reports precision, coverage and
  *p*-values, which are used in the paper. Its φ column is not reliable (values above 1
  occur) and is not reported.
- **Grex** itself is not included. Install it from its own repository and point
  `GREX_DIR` to it; Grew must be installed as well.

## Data sources

The texts are taken from the Swedish Diachronic Corpus (Pettersson and Borin, 2022).
Please refer to the corpus for licensing of the original texts.

The normalizer uses the Flex frequency lexicon (CC BY 4.0):
Zechner, Niklas (2025). *Flex – frequency lexicon* (updated 2025-12-06). Data set,
enriched and distributed by Språkbanken. https://doi.org/10.23695/7kq9-6n10

## Citation

To be added after review.