#!/usr/bin/env python3
"""
welch.py
Welch's method for graphical warm-up identification (lect 14).

Steps:
  1. Read R replications (each is a transient CSV).
  2. At each time point, compute the ensemble average across replications.
  3. Apply a moving-average filter with window w.
  4. Plot ensemble average + smoothed curve.
  5. The user identifies T_0 visually (point where the curve stabilises).

Usage:
    python3 welch.py [DIR] [METRIC] [WINDOW]

Defaults: DIR=transients, METRIC=avg_total, WINDOW=5

Available metrics (columns of transient.csv):
    n_in_system, n_standing, chairs_occupied, waiters_busy,
    avg_total, avg_standing, avg_seated,
    util_chairs, util_waiters, throughput
"""
import csv
import glob
import math
import os
import sys
import matplotlib.pyplot as plt

DIR    = sys.argv[1] if len(sys.argv) > 1 else "transients"
METRIC = sys.argv[2] if len(sys.argv) > 2 else "avg_total"
WINDOW = int(sys.argv[3]) if len(sys.argv) > 3 else 5

files = sorted(glob.glob(os.path.join(DIR, "transient_*.csv")))
if not files:
    print(f"No CSVs found in '{DIR}/'. Run run_warmup.sh first.")
    sys.exit(1)

# ------------------------------------------------------------------ Read data
replications = []
for f in files:
    times, vals = [], []
    with open(f) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            times.append(float(row["t"]))
            vals.append(float(row[METRIC]))
    replications.append((times, vals))

R = len(replications)
ref_times = replications[0][0]
n_points  = min(len(rep[1]) for rep in replications)

# ----------------------------------------------- Ensemble average at each t
ensemble = []
for i in range(n_points):
    s = sum(rep[1][i] for rep in replications)
    ensemble.append(s / R)

# ------------------------------------------------- Moving average filter
def moving_average(arr, w):
    out = []
    n = len(arr)
    for i in range(n):
        lo = max(0, i - w)
        hi = min(n, i + w + 1)
        out.append(sum(arr[lo:hi]) / (hi - lo))
    return out

smoothed = moving_average(ensemble, WINDOW)

# ------------------------------------------------------------------- Plot
fig, ax = plt.subplots(figsize=(11, 5))

# A few individual replications (light grey, for context)
for rep in replications[:8]:
    t_h = [x / 60.0 for x in rep[0][:n_points]]
    ax.plot(t_h, rep[1][:n_points], color="gray", alpha=0.20, linewidth=0.5)

t_h = [x / 60.0 for x in ref_times[:n_points]]
ax.plot(t_h, ensemble, label=f"ensemble average (R={R})", linewidth=1.0, color="C0")
ax.plot(t_h, smoothed,
        label=f"moving average (window 2w+1, w={WINDOW})",
        linewidth=2.2, color="C1")

ax.set_xlabel("time (h)")
ax.set_ylabel(METRIC)
ax.set_title(f"Welch's method - warm-up identification on {METRIC}")
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)

plt.tight_layout()
outfile = f"welch_{METRIC}.png"
plt.savefig(outfile, dpi=120, bbox_inches="tight")
print(f"Saved figure: {outfile}")
print(f"R = {R} replications, n_points = {n_points}, window = {WINDOW}")
print("Look at the plot and identify T_0: the time at which the smoothed curve stabilises.")

try:
    plt.show()
except Exception:
    pass
