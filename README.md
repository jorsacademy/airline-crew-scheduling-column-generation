# Airline Crew Scheduling with Column Generation

Research-oriented Operations Research implementation of a crew-pairing style set-covering model solved with **Dantzig-Wolfe column generation**.

## Research question

Can a restricted master problem plus resource-constrained shortest-path pricing recover the full LP relaxation without enumerating the combinatorial pairing space?

## Current status

**Phase 2 implemented: label-setting RCSP pricing.**

The repository contains:

- flight and pairing data structures;
- legal-duty checks and exhaustive pairing generation for transparent reference cases;
- a restricted master LP solved with HiGHS through SciPy;
- explicit dual-price extraction;
- exhaustive reduced-cost pricing for correctness checks;
- an acyclic label-setting pricing algorithm for the connection network;
- an RCSP-driven column-generation loop;
- a deterministic hub-and-spoke timetable generator;
- tests proving the label-setting price and final LP objective match exhaustive references on the toy instance;
- CI across supported Python versions.

## Formulation

For pairing set `P` and flights `F`, the LP relaxation is

```text
min  sum(c_p x_p)                p in P
s.t. sum(a_fp x_p) >= 1          f in F
     x_p >= 0
```

The restricted master contains only a subset of pairings. Its coverage duals `pi_f` define pairing reduced cost

```text
c_bar_p = c_p - sum(pi_f : f in p).
```

A negative-reduced-cost legal pairing is added as a new column. The process terminates when pricing cannot find an improving pairing.

## Pricing problem

Flights form a directed acyclic connection network because feasible connections move forward in time. A label stores the current duty path, first departure, last arrival, location and accumulated reduced cost. Extensions enforce:

- airport continuity;
- minimum connection time;
- maximum duty duration;
- maximum number of legs.

Labels sharing the same relevant boundary state are compared by reduced cost so dominated alternatives can be removed.

This is materially different from generating every legal pairing first and then searching that list.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
python -m crew_cg.experiment
```

The experiment performs two checks:

1. on the toy network, full enumeration, exhaustive-pricing column generation and RCSP-pricing column generation must reach the same LP objective;
2. on a larger synthetic hub timetable, RCSP column generation runs without constructing the full pairing set.

## Repository map

```text
src/crew_cg/
  model.py                   # flight and pairing structures
  generator.py               # synthetic hub timetable
  pairing.py                 # legality, costing and exhaustive reference pricing
  master.py                  # restricted master LP and dual extraction
  pricing_rcsp.py            # label-setting resource-constrained pricing
  column_generation.py       # exhaustive-pricing reference CG
  column_generation_rcsp.py  # scalable pricing loop
  experiment.py              # correctness + scaling smoke benchmark
tests/
  test_column_generation.py
  test_rcsp_pricing.py
configs/
  experiment.json
.github/workflows/
  ci.yml
```

## Scientific validation contract

A column-generation result is accepted only if:

- coverage remains feasible;
- reduced costs use the master duals with the correct sign convention;
- the pricing algorithm agrees with exhaustive pricing wherever exhaustive enumeration is tractable;
- termination occurs only when no negative-reduced-cost column is found within tolerance;
- the restricted-master objective agrees with the full LP on reference instances.

## Next research stages

### Phase 3 — richer crew resources
Add duty-time, sit-time, base-return, maximum block time and overnight/resource states directly to the label structure.

### Phase 4 — realistic benchmark scaling
Generate or ingest larger airline timetable instances. Report number of flights, generated columns, master iterations, pricing time, master time and memory usage.

### Phase 5 — integer recovery
Compare LP lower bounds with a final integer restricted master. Then evaluate a branch-and-price-lite extension for cases where integrality gaps matter.

### Phase 6 — stabilization
Investigate dual stabilization or column management when larger instances exhibit oscillatory duals or slow convergence.

## Portfolio signal

The purpose of this repository is not to demonstrate use of a solver API. It exposes the decomposition algorithm itself: master formulation, dual information, reduced-cost pricing, dominance and convergence checks.

## License

MIT
