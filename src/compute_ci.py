#!/usr/bin/env python3
"""
compute_ci.py
Reads the per-replication summary CSV produced by run_replications.sh
and computes mean, standard deviation, and 95% confidence interval
for each metric using the t-Student distribution.

Method: replication-deletion with independent runs (Kurkowski sec. III).

Usage:
    python3 compute_ci.py [replications.csv]
"""
import csv
import math
import statistics
import sys

# Critical t values for 95% two-sided CI (alpha = 0.05, alpha/2 = 0.025).
# Hard-coded for common sample sizes used in our experiments.
T_CRIT = {
    10: 2.262, 20: 2.093, 30: 2.045, 40: 2.023,
    50: 2.010, 60: 2.001, 64: 1.998, 80: 1.991,
    100: 1.984, 128: 1.979, 256: 1.969,
}

def t_value(n):
    """Return t-Student critical value for 95% CI with n-1 dof.
    Falls back to the closest hard-coded value, or 1.96 for n>=300."""
    if n >= 300:
        return 1.96
    return T_CRIT.get(n, T_CRIT.get(min(T_CRIT.keys(), key=lambda k: abs(k-n))))

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "replications.csv"
    data = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key, val in row.items():
                if key in ("seed", "C", "S"):
                    continue
                data.setdefault(key, []).append(float(val))

    n = len(next(iter(data.values())))
    t_crit = t_value(n)

    print(f"\n=== Confidence intervals (n={n} replications, 95%, t={t_crit}) ===\n")
    print(f"{'Metric':<14} {'Mean':>12} {'StdDev':>12} {'CI half-width':>16} {'95% CI':>30}")
    print("-" * 86)
    for metric, values in data.items():
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if n > 1 else 0.0
        hw = t_crit * stdev / math.sqrt(n)
        rel = (hw / mean * 100) if mean != 0 else 0.0
        ci_lo, ci_hi = mean - hw, mean + hw
        print(f"{metric:<14} {mean:>12.4f} {stdev:>12.4f} {hw:>14.4f} ({rel:>4.1f}%) "
              f"[{ci_lo:>10.4f}, {ci_hi:>10.4f}]")
    print()

if __name__ == "__main__":
    main()
