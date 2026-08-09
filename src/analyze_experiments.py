#!/usr/bin/env python3
"""
analyze_experiments.py
Reads experiments.csv (output of run_experiments.sh) and produces
the per-scenario summary: mean +/- 95% CI half-width for every metric.

Method: replication-deletion (lect 14) - independent replications per scenario.

Usage:
    python3 analyze_experiments.py [experiments.csv]
"""
import csv
import math
import statistics
import sys
from collections import defaultdict

# t-Student critical values for 95% two-sided CI (alpha = 0.05).
T_CRIT = {
    10: 2.262, 16: 2.131, 20: 2.093, 30: 2.045, 32: 2.040,
    40: 2.023, 50: 2.010, 60: 2.001, 64: 1.998, 80: 1.991,
    100: 1.984, 128: 1.979,
}
def t_value(n):
    if n >= 300: return 1.96
    return T_CRIT.get(n, T_CRIT.get(min(T_CRIT.keys(), key=lambda k: abs(k-n))))

METRICS = ["W", "W_standing", "W_seated", "X_per_hour",
           "U_chairs", "U_waiters", "L"]

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "experiments.csv"
    grouped = defaultdict(list)

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (int(row["C"]), int(row["S"]), float(row["mean_iarrival"]))
            grouped[key].append({m: float(row[m]) for m in METRICS})

    # ordering: by mean_iarrival (descending = higher lambda first), then C, S
    keys = sorted(grouped.keys(), key=lambda k: (-1/k[2], k[0], k[1]))

    print(f"\nSummary by scenario (n replications per scenario varies)")
    print(f"Format: mean (CI half-width %)\n")
    header = f"{'C':>2} {'S':>2} {'IAR':>5} {'lambda/h':>9}"
    for m in METRICS:
        header += f" {m:>17}"
    print(header)
    print("-" * len(header))

    for key in keys:
        Cv, Sv, iar = key
        runs = grouped[key]
        n = len(runs)
        tcrit = t_value(n)
        lam_h = 60.0 / iar
        line = f"{Cv:>2} {Sv:>2} {iar:>5.2f} {lam_h:>9.1f}"
        for m in METRICS:
            vals = [r[m] for r in runs]
            mean = statistics.mean(vals)
            stdev = statistics.stdev(vals) if n > 1 else 0.0
            hw   = tcrit * stdev / math.sqrt(n)
            rel  = (hw / mean * 100) if mean != 0 else 0.0
            line += f" {mean:>11.4f} ({rel:>3.1f}%)"
        print(line)

    # also write a tidied CSV for plotting
    out = "experiments_summary.csv"
    with open(out, "w") as f:
        f.write("C,S,mean_iarrival,lambda_per_hour,metric,mean,ci_half_width\n")
        for key in keys:
            Cv, Sv, iar = key
            runs = grouped[key]
            n = len(runs)
            tcrit = t_value(n)
            lam_h = 60.0 / iar
            for m in METRICS:
                vals = [r[m] for r in runs]
                mean = statistics.mean(vals)
                stdev = statistics.stdev(vals) if n > 1 else 0.0
                hw   = tcrit * stdev / math.sqrt(n)
                f.write(f"{Cv},{Sv},{iar},{lam_h:.2f},{m},{mean:.6f},{hw:.6f}\n")
    print(f"\nTidy summary saved to {out}")

if __name__ == "__main__":
    main()
