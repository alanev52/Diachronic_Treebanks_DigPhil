#!/bin/bash
# Reruns rule extraction for all patterns reported in the paper.
#
# Usage, from the top folder of this repository:
#     GREX_DIR=/path/to/grex bash grex/run_all.sh
# GREX_DIR is a local copy of the Grex code (extract_rules_via_lasso.py,
# json_to_csv.py); Grew must be installed (e.g. via opam).

set -u
: "${GREX_DIR:?Set GREX_DIR to your local copy of Grex}"

# Grew installed via opam (adjust to your opam version if needed)
export PATH=$HOME/.opam/5.2.1/bin:$PATH

DATA=grex/input/sv_preprocessed_cor_nf.conllu
OUT=grex/results
NAMES=("negation" "aux_omission" "rel_pronoun_som" "rel_pronoun_vilken")
mkdir -p "$OUT"

for NAME in "${NAMES[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Processing: $NAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    PATTERNS_FILE=grex/patterns/${NAME}.yaml
    OUTPUT_JSON=$OUT/rules_${NAME}.json
    OUTPUT_CSV=$OUT/rules_${NAME}.csv

    python3 "$GREX_DIR/extract_rules_via_lasso.py" "$DATA" \
        --config ud \
        --patterns "$PATTERNS_FILE" \
        --output "$OUTPUT_JSON" \
        --max-degree 3 || { echo "ERROR: extract_rules failed for $NAME"; continue; }

    python3 "$GREX_DIR/json_to_csv.py" "$OUTPUT_JSON" "$OUTPUT_CSV" \
        || { echo "ERROR: json_to_csv failed for $NAME"; continue; }

    python3 scripts/bonferroni_patterns.py \
        --input "$OUTPUT_CSV" --alpha 0.05 --min-q 10 \
        || { echo "ERROR: bonferroni failed for $NAME"; continue; }

    BONF_DIR=$OUT/bonferroni_results_minf_$NAME
    mkdir -p "$BONF_DIR"
    mv bonferroni_all_patterns.csv "$BONF_DIR/bonferroni_all_patterns_$NAME.csv"
    mv bonferroni_significant.csv  "$BONF_DIR/bonferroni_significant_$NAME.csv"
    mv bonferroni_raw_sig_only.csv "$BONF_DIR/bonferroni_raw_sig_only_$NAME.csv"

    echo "Done: $NAME → $BONF_DIR"
done

echo "All patterns processed."