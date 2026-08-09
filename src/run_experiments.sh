#!/bin/bash
# run_experiments.sh
# Runs the full factorial experiment: configurations (C, S) x arrival rates (mean_iarrival)
# x N independent seeds. Compiles the simulator with -D flags per scenario.
#
# Output: master CSV with all replications and their config parameters.
#
# Usage:
#   ./run_experiments.sh [N_SEEDS]
# Default N_SEEDS = 32

set -e

N_SEEDS="${1:-32}"
OUT="experiments.csv"

# Server configurations: pairs "C,S"
CONFIGS=("2 4" "2 5" "3 4" "3 5")

# Mean inter-arrival times in minutes. Inverse gives lambda in cust/min.
#   4.0 -> 15 cust/h
#   3.0 -> 20 cust/h (baseline)
#   2.4 -> 25 cust/h
#   2.0 -> 30 cust/h
IARS=(4.0 3.0 2.4 2.0)

echo "C,S,mean_iarrival,seed,W,W_standing,W_seated,X_per_hour,U_chairs,U_waiters,L,T_eff" > "$OUT"

TOTAL=$((${#CONFIGS[@]} * ${#IARS[@]} * N_SEEDS))
DONE=0

for cfg in "${CONFIGS[@]}"; do
    Cval=$(echo "$cfg" | awk '{print $1}')
    Sval=$(echo "$cfg" | awk '{print $2}')

    for iar in "${IARS[@]}"; do
        echo ">>> Compiling C=${Cval}, S=${Sval}, mean_iarrival=${iar} ..."
        gcc -O2 -Wall \
            -DC=${Cval} -DS=${Sval} -DMEAN_IARRIVAL=${iar} \
            -o cafeteria_sim cafeteria_sim.c rngs.c -lm

        for seed in $(seq 1 "$N_SEEDS"); do
            ./cafeteria_sim "$seed" batch | grep "^RESULT," | \
                awk -F',' -v iar="$iar" \
                  'BEGIN{OFS=","} {print $3, $4, iar, $2, $5, $6, $7, $8, $9, $10, $11, $12}' \
                >> "$OUT"
            DONE=$((DONE+1))
        done
        echo "    ... done ($DONE / $TOTAL)"
    done
done

echo
echo "All experiments complete. Results in $OUT ($TOTAL rows)."
