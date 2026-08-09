# Cafeteria Simulation — Performance Modeling Project

![Language](https://img.shields.io/badge/language-C%20%2B%20Python-blue)
![Course](https://img.shields.io/badge/course-Performance%20Modeling-red)
![Grade](https://img.shields.io/badge/grade-27%2F30-brightgreen)

Discrete-event simulation of a cafeteria system with coupled resources (seats and waiters),
developed as the final project for the course **Performance Modeling of Computer Systems and Networks**
at **Università degli Studi di Roma Tor Vergata**, A.A. 2025/2026.

**Author:** Daniel Garoz Vazquez (Erasmus)
**Grade:** 27/30

---

## Problem

A small cafeteria has `C` waiters and `S` seats. Two customer classes arrive by a Poisson process:
coffee (70%) and breakfast (30%). Seats are held throughout the entire stay; waiters only during
attention. When demand grows, should the manager **hire an extra waiter or buy an extra seat**?

## Approach

The two resources are coupled — a customer waits seated for a waiter, so the seat queue physically
materialises as seat occupation. **No closed-form product-form solution exists** for this system,
which motivates discrete-event simulation.

The study follows Algorithm 1.1 of Leemis & Park for model development, and Algorithm 1.2 for the
next-event simulation engine, using a multi-stream Lehmer pseudo-random generator with one disjoint
stream per stochastic process.

## Key results

- **The seat is the bottleneck** at every operating point — confirmed by the analytical bound
  ρ̂_seat = λ·E[T_seat] / S and by simulation.
- **Adding one seat reduces response time by 90%** at λ = 25 cust/h;
  adding one waiter reduces it by only 48%.
- **Economically, a seat is 12× cheaper than a waiter** ⇒ operational rule:
  *when in doubt, add a seat before adding a waiter*.

## Methodology

| Step | Technique |
|------|-----------|
| Model development | Algorithm 1.1 of Leemis & Park |
| Simulation engine | Next-event (Algorithm 1.2 of Leemis & Park) |
| Pseudo-random numbers | Multi-stream Lehmer generator (m = 2³¹ − 1, a = 48271) |
| Warm-up detection | Welch's method (R = 30 replications, moving average window 2w+1 = 11) |
| Steady-state estimation | Replication-deletion with 95% t-Student CI |
| Design | Full factorial 2 × 2 × 4 = 16 scenarios × 32 replications |
| Verification | Little's Law, throughput consistency, class mix |
| Validation | Comparison against isolated M/M/c bounds |

## Repository structure

```
├── report/           Compiled report (relazione.pdf) and source (.tex)
├── presentation/     Compiled slides (presentation.pdf) and source (.tex)
└── src/              Simulator (C) and analysis scripts (Python)
```

## Reproducing the study

Requirements: `gcc`, `python3`, `matplotlib`.

```bash
cd src/

# 1. Compile
gcc -O2 -o cafeteria_sim cafeteria_sim.c rngs.c -lm

# 2. Warm-up identification (Welch's method)
bash run_warmup.sh 30
python3 welch.py

# 3. Detailed baseline (n = 64)
bash run_replications.sh 64
python3 compute_ci.py replications.csv

# 4. Full factorial (16 scenarios × n = 32 = 512 runs)
bash run_experiments.sh 32
python3 analyze_experiments.py

# 5. Report figures
python3 plot_transient.py
python3 plot_experiments.py
```

Total runtime: ~10–20 minutes on a laptop.

## Documentation

- **`report/relazione.pdf`** — full technical report (12 pages) covering conceptual model,
  specification, computational model, verification, validation, Welch's method, experimental
  design, results, and economic analysis.
- **`presentation/presentation.pdf`** — defense slide deck (21 slides).

## License

MIT — see `LICENSE`.
