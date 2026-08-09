#!/bin/bash
# run_replications.sh
# Runs the cafeteria simulator with multiple independent seeds
# and collects the per-replication summary metrics into a CSV file.
#
# Usage:
#   ./run_replications.sh [N_SEEDS] [OUTPUT_FILE]
# Defaults: N_SEEDS=64, OUTPUT_FILE=replications.csv

set -e

N_SEEDS="${1:-64}"
OUT="${2:-replications.csv}"
BIN="./cafeteria_sim"

if [ ! -x "$BIN" ]; then
    echo "Error: $BIN not found or not executable. Run 'make' or gcc first."
    exit 1
fi

echo "seed,C,S,W,W_standing,W_seated,X_per_hour,U_chairs,U_waiters,L,T_sim" > "$OUT"

echo "Running $N_SEEDS replications..."
for seed in $(seq 1 "$N_SEEDS"); do
    "$BIN" "$seed" batch | grep "^RESULT," | sed 's/^RESULT,//' >> "$OUT"
    if [ $((seed % 8)) -eq 0 ]; then
        echo "  ... $seed / $N_SEEDS done"
    fi
done

echo "Done. Results in $OUT ($N_SEEDS rows)."
