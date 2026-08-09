#!/usr/bin/env python3
"""
plot_transient.py
Plots time evolution of the cafeteria simulator from transient.csv.
Used to identify the warm-up period.

Usage:
    python3 plot_transient.py [transient.csv]
"""
import sys
import csv
import matplotlib.pyplot as plt

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "transient.csv"

t              = []
n_in_system    = []
n_standing     = []
chairs_occ     = []
waiters_busy   = []
avg_total      = []
avg_standing   = []
avg_seated     = []
util_chairs    = []
util_waiters   = []
throughput     = []

with open(CSV_PATH) as f:
    reader = csv.DictReader(f)
    for row in reader:
        t.append(float(row["t"]))
        n_in_system.append(int(row["n_in_system"]))
        n_standing.append(int(row["n_standing"]))
        chairs_occ.append(int(row["chairs_occupied"]))
        waiters_busy.append(int(row["waiters_busy"]))
        avg_total.append(float(row["avg_total"]))
        avg_standing.append(float(row["avg_standing"]))
        avg_seated.append(float(row["avg_seated"]))
        util_chairs.append(float(row["util_chairs"]))
        util_waiters.append(float(row["util_waiters"]))
        throughput.append(float(row["throughput"]))

# convert time to hours for nicer x-axis
t_h = [x / 60.0 for x in t]

fig, axes = plt.subplots(2, 2, figsize=(13, 8))

# --- 1) Instantaneous number in system ---
ax = axes[0, 0]
ax.plot(t_h, n_in_system, linewidth=0.6, label="total in system")
ax.plot(t_h, n_standing, linewidth=0.6, label="standing")
ax.set_xlabel("time (h)")
ax.set_ylabel("customers")
ax.set_title("Instantaneous number in system")
ax.legend(loc="upper right")
ax.grid(True, alpha=0.3)

# --- 2) Running averages of times ---
ax = axes[0, 1]
ax.plot(t_h, avg_total,    label="total time")
ax.plot(t_h, avg_standing, label="standing wait")
ax.plot(t_h, avg_seated,   label="seated wait")
ax.set_xlabel("time (h)")
ax.set_ylabel("minutes")
ax.set_title("Running average of customer times")
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)

# --- 3) Utilizations ---
ax = axes[1, 0]
ax.plot(t_h, util_chairs,  label="chairs")
ax.plot(t_h, util_waiters, label="waiters")
ax.set_xlabel("time (h)")
ax.set_ylabel("utilization")
ax.set_title("Time-integrated utilizations")
ax.set_ylim(0, 1)
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)

# --- 4) Throughput ---
ax = axes[1, 1]
ax.plot(t_h, throughput)
ax.axhline(1.0 / 3.0, color="red", linestyle="--", alpha=0.6,
           label=f"expected lambda = 1/3 = {1/3:.4f}")
ax.set_xlabel("time (h)")
ax.set_ylabel("customers / min")
ax.set_title("Cumulative throughput")
ax.legend(loc="lower right")
ax.grid(True, alpha=0.3)

plt.suptitle("Cafeteria simulator - transient analysis", fontsize=13, y=1.0)
plt.tight_layout()

out = "transient.png"
plt.savefig(out, dpi=120, bbox_inches="tight")
print(f"Saved figure to {out}")

# also show on screen if a display is available
try:
    plt.show()
except Exception:
    pass
