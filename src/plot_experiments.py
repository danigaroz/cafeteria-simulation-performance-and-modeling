#!/usr/bin/env python3
"""
plot_experiments.py
Generates the figures for the report from experiments_summary.csv.

Produces:
    fig_W_vs_lambda.png       - mean response time vs arrival rate, per config
    fig_L_vs_lambda.png       - mean number in system vs arrival rate, per config
    fig_util_chairs.png       - chair utilization vs arrival rate, per config
    fig_util_waiters.png      - waiter utilization vs arrival rate, per config
    fig_benefit_vs_lambda.png - hourly benefit vs arrival rate, per config

Usage:
    python3 plot_experiments.py [experiments_summary.csv]
"""
import csv
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

PATH = sys.argv[1] if len(sys.argv) > 1 else "experiments_summary.csv"

# Read tidy summary
records = []
with open(PATH) as f:
    reader = csv.DictReader(f)
    for row in reader:
        records.append({
            "C": int(row["C"]),
            "S": int(row["S"]),
            "lambda_per_hour": float(row["lambda_per_hour"]),
            "metric": row["metric"],
            "mean": float(row["mean"]),
            "ci_hw": float(row["ci_half_width"]),
        })

# Configurations to plot (in order)
CONFIGS = [(2, 4), (2, 5), (3, 4), (3, 5)]
LABELS  = {(2, 4): "C=2, S=4 (baseline)",
           (2, 5): "C=2, S=5",
           (3, 4): "C=3, S=4",
           (3, 5): "C=3, S=5"}
COLORS  = {(2, 4): "C0", (2, 5): "C1", (3, 4): "C2", (3, 5): "C3"}
MARKERS = {(2, 4): "o", (2, 5): "s", (3, 4): "^", (3, 5): "D"}

# Mix and prices for economic analysis
P_CAFE      = 0.7
PRICE_CAFE  = 1.5
PRICE_DESAY = 5.0
COST_WAITER = 12.0
COST_CHAIR  = 1.0

REV_PER_CUST = P_CAFE * PRICE_CAFE + (1 - P_CAFE) * PRICE_DESAY  # = 2.55

def filter_metric(metric):
    """Return dict config -> sorted list of (lambda, mean, ci_hw)."""
    out = defaultdict(list)
    for r in records:
        if r["metric"] != metric:
            continue
        out[(r["C"], r["S"])].append((r["lambda_per_hour"], r["mean"], r["ci_hw"]))
    for k in out:
        out[k].sort()
    return out

def plot_metric(metric, ylabel, title, fname, ylim=None):
    data = filter_metric(metric)
    fig, ax = plt.subplots(figsize=(8, 5))
    for cfg in CONFIGS:
        pts = data[cfg]
        xs  = [p[0] for p in pts]
        ys  = [p[1] for p in pts]
        es  = [p[2] for p in pts]
        ax.errorbar(xs, ys, yerr=es,
                    label=LABELS[cfg], color=COLORS[cfg], marker=MARKERS[cfg],
                    linewidth=1.5, markersize=7, capsize=4)
    ax.set_xlabel("arrival rate $\\lambda$ (customers/hour)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    if ylim:
        ax.set_ylim(*ylim)
    plt.tight_layout()
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"saved {fname}")

# -- Mean response time --
plot_metric("W",
            "mean response time $W$ (min)",
            "Mean response time vs arrival rate",
            "fig_W_vs_lambda.png")

# Same but log scale to also show saturation cases
data = filter_metric("W")
fig, ax = plt.subplots(figsize=(8, 5))
for cfg in CONFIGS:
    pts = data[cfg]
    xs  = [p[0] for p in pts]
    ys  = [p[1] for p in pts]
    es  = [p[2] for p in pts]
    ax.errorbar(xs, ys, yerr=es,
                label=LABELS[cfg], color=COLORS[cfg], marker=MARKERS[cfg],
                linewidth=1.5, markersize=7, capsize=4)
ax.set_yscale("log")
ax.set_xlabel("arrival rate $\\lambda$ (customers/hour)")
ax.set_ylabel("mean response time $W$ (min, log scale)")
ax.set_title("Mean response time vs arrival rate (log scale)")
ax.grid(True, alpha=0.3, which="both")
ax.legend(loc="best")
plt.tight_layout()
plt.savefig("fig_W_vs_lambda_log.png", dpi=150, bbox_inches="tight")
plt.close()
print("saved fig_W_vs_lambda_log.png")

# -- L --
plot_metric("L",
            "mean number in system $L$",
            "Mean number in system vs arrival rate",
            "fig_L_vs_lambda.png")

# -- Utilizations --
plot_metric("U_chairs",
            "chair utilization $\\rho_{\\mathrm{chairs}}$",
            "Chair utilization vs arrival rate",
            "fig_util_chairs.png",
            ylim=(0, 1.05))

plot_metric("U_waiters",
            "waiter utilization $\\rho_{\\mathrm{waiters}}$",
            "Waiter utilization vs arrival rate",
            "fig_util_waiters.png",
            ylim=(0, 1.05))

# -- Economic benefit --
data_X = filter_metric("X_per_hour")

fig, ax = plt.subplots(figsize=(8, 5))
for cfg in CONFIGS:
    Cv, Sv = cfg
    pts_X = data_X[cfg]
    xs    = [p[0] for p in pts_X]
    X_h   = [p[1] for p in pts_X]
    benefit = [REV_PER_CUST * x - COST_WAITER * Cv - COST_CHAIR * Sv for x in X_h]
    ax.plot(xs, benefit,
            label=LABELS[cfg], color=COLORS[cfg], marker=MARKERS[cfg],
            linewidth=1.5, markersize=7)
ax.set_xlabel("arrival rate $\\lambda$ (customers/hour)")
ax.set_ylabel("hourly benefit (€/h)")
ax.set_title("Hourly benefit vs arrival rate")
ax.grid(True, alpha=0.3)
ax.axhline(0, color="black", linewidth=0.6, alpha=0.5)
ax.legend(loc="best")
plt.tight_layout()
plt.savefig("fig_benefit_vs_lambda.png", dpi=150, bbox_inches="tight")
plt.close()
print("saved fig_benefit_vs_lambda.png")

print("\nAll figures generated.")
