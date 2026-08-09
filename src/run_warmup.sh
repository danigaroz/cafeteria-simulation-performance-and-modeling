#!/bin/bash
# run_warmup.sh
# Runs the cafeteria simulator with multiple seeds in NORMAL mode
# (transient CSV generated each time) and renames the file per seed.
# Used as input for Welch's method (warm-up identification).
#
# Usage:
#   ./run_warmup.sh [N_SEEDS] [OUTDIR]
# Defaults: N_SEEDS=30, OUTDIR=transients

set -e

N_SEEDS="${1:-30}"
OUTDIR="${2:-transients}"
BIN="./cafeteria_sim"

if [ ! -x "$BIN" ]; then
    echo "Error: $BIN not found. Run 'gcc -Wall -o cafeteria_sim cafeteria_sim.c rngs.c -lm' first."
    exit 1
fi

mkdir -p "$OUTDIR"
rm -f "$OUTDIR"/transient_*.csv

echo "Generating $N_SEEDS transient CSVs into $OUTDIR/"
for seed in $(seq 1 "$N_SEEDS"); do
    "$BIN" "$seed" > /dev/null
    mv transient.csv "$OUTDIR/transient_${seed}.csv"
    if [ $((seed % 5)) -eq 0 ]; then
        echo "  $seed / $N_SEEDS done"
    fi
done

echo "Done. ${N_SEEDS} transient CSVs in $OUTDIR/"
