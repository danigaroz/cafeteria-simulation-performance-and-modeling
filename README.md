# Cafeteria Simulation — When does adding a seat beat hiring a waiter?

[![Language](https://img.shields.io/badge/language-C%20%2B%20Python-blue)]()
[![Course](https://img.shields.io/badge/course-Performance%20Modeling-red)]()
[![Grade](https://img.shields.io/badge/grade-27%2F30-brightgreen)]()

Discrete-event simulation of a cafeteria with coupled resources (seats and waiters),
built as the final project for **Performance Modeling of Computer Systems and Networks**
at **Università degli Studi di Roma Tor Vergata**, A.A. 2025/2026 (Erasmus exchange).

**Author:** Daniel Garoz Vazquez · **Grade:** 27/30

---

## Problem

A small cafeteria has `C` waiters and `S` seats. Two customer classes arrive by a
Poisson process: coffee (70%) and breakfast (30%). Seats are held throughout the
entire stay; waiters only during attention. The resources are coupled — a customer
waits *seated* for a waiter, so the seat queue physically materialises as seat
occupation. **No closed-form product-form solution exists**, which motivates
discrete-event simulation.

When demand grows, should the manager hire an extra waiter or buy an extra seat?

## Key results

- **The seat is the bottleneck** at every operating point.
- **Adding one seat reduces response time by 90%** at λ = 25 cust/h; adding one waiter reduces it by only 48%.
- **Economically, a seat is 12× cheaper than a waiter** → operational rule: *when in doubt, add a seat before adding a waiter*.

## Methodology

| Step | Technique |
|---|---|
| Simulation engine | Next-event (Algorithm 1.2, Leemis & Park) |
| Pseudo-random numbers | Multi-stream Lehmer generator (m = 2³¹−1, a = 48271) |
| Warm-up detection | Welch's method (R = 30 replications, window 2w+1 = 11) |
| Steady-state estimation | Replication-deletion with 95% t-Student CI |
| Experimental design | Full factorial 2×2×4 = 16 scenarios × 32 replications |
| Verification | Little's Law, throughput consistency, class mix |
| Validation | Comparison against isolated M/M/c bounds |

## Tech stack

- **Languages:** C (simulator), Python (analysis and plotting)
- **Libraries:** matplotlib, numpy
- **Docs:** LaTeX (article + Beamer)

## Repository structure

```text
├── src/            Simulator (C) and analysis scripts (Python)
├── report/         Full technical report (relazione.pdf) and LaTeX source
└── presentation/   Defense slides (presentation.pdf) and LaTeX source
```

## How to reproduce

Requirements: `gcc`, `python3`, `matplotlib`.

```bash
cd src/

# 1. Compile
gcc -O2 -o cafeteria_sim cafeteria_sim.c rngs.c -lm

# 2. Warm-up identification (Welch's method)
bash run_warmup.sh 30
python3 welch.py

# 3. Steady-state baseline (n = 64 replications)
bash run_replications.sh 64
python3 compute_ci.py replications.csv

# 4. Full factorial (16 scenarios × 32 replications = 512 runs)
bash run_experiments.sh 32
python3 analyze_experiments.py
```

Total runtime: ~10–20 minutes on a laptop.

## Note on the use of AI

The implementation was developed with AI-assisted coding. All modelling choices, experimental design, interpretation of results and written content are the author's own work.

## Context

Final project for *Performance Modeling of Computer Systems and Networks*, Università degli Studi di Roma Tor Vergata, A.A. 2025–26. Reference: Leemis & Park, *Discrete-Event Simulation: A First Course* (2006).
