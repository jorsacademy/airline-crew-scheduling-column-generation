# Airline Crew Scheduling with Column Generation

Research-oriented Operations Research implementation of a crew-pairing style set-covering model solved with **Dantzig-Wolfe column generation**.

## Research question

Can a restricted master problem plus resource-constrained shortest-path pricing recover the full LP relaxation without enumerating the combinatorial pairing space, and how large is the integer recovery gap after column generation terminates?

## Current status

**Phase 3 implemented: RCSP column generation + integer restricted-master recovery.**

The repository contains:

- flight and pairing data structures;
- legal-duty checks and exhaustive pairing generation for transparent reference cases;
- a restricted master LP solved with HiGHS through SciPy;
- explicit dual-price extraction;
- exhaustive reduced-cost pricing for correctness checks;
- an acyclic label-setting pricing algorithm for the connection network;
- an RCSP-driven column-generation loop;
- a deterministic hub-and-spoke timetable generator;
- a binary restricted-master MILP solved after LP column generation;
- integrality-gap reporting;
- tests proving pricing and LP correctness on reference instances;
- CI across supported Python versions.

## LP master formulation

For pairing set `P` and flights `F`, the LP relaxation is

```text
min  sum(c_p x_p)                p in P
s.t. sum(a_fp x_p) >= 1          f in F
     x_p >= 0
```

Coverage duals `pi_f` define pairing reduced cost

```text
c_bar_p = c_p - sum(pi_f : f in p).
```

A negative-reduced-cost legal pairing is added as a new column. The process terminates only when RCSP pricing cannot find an improving column within tolerance.

## Integer recovery

After column generation converges, the generated pairing set is frozen and a binary set-covering master is solved:

```text
x_p in {0, 1}
```

The experiment reports the LP lower bound, integer restricted-master objective and relative integrality gap. This is **not labeled as full branch-and-price**: branching does not yet trigger new pricing subproblems. The distinction is intentional.

## Pricing problem

Flights form a directed acyclic connection network because feasible connections move forward in time. Labels store the current duty path, first departure, last arrival, location and accumulated reduced cost. Extensions enforce airport continuity, minimum connection time, maximum duty duration and maximum legs. Exhaustive pricing remains as an oracle on small instances.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
python -m crew_cg.experiment
```

The experiment checks:

1. full enumeration, exhaustive-pricing CG and RCSP-pricing CG reach the same toy LP objective;
2. label-setting pricing agrees with exhaustive pricing on tractable reference cases;
3. the integer restricted master covers every flight;
4. LP and integer objectives are reported together;
5. the larger synthetic hub case runs without constructing the full pairing set.

## Repository map

```text
src/crew_cg/
  model.py                   # flight and pairing structures
  generator.py               # synthetic hub timetable
  pairing.py                 # exhaustive reference pricing
  master.py                  # restricted master LP and duals
  pricing_rcsp.py            # label-setting RCSP pricing
  column_generation.py       # exhaustive-pricing reference CG
  column_generation_rcsp.py  # scalable pricing loop
  integer_master.py          # binary recovery + integrality gap
  experiment.py              # correctness and scaling benchmark
tests/
  test_column_generation.py
  test_rcsp_pricing.py
  test_integer_master.py
configs/
  experiment.json
.github/workflows/
  ci.yml
```

## Scientific validation contract

A result is accepted only if coverage remains feasible, dual signs are correct, RCSP pricing agrees with exhaustive pricing wherever tractable, termination occurs only without negative reduced cost, LP objectives agree with full enumeration on references, and integer recovery is reported separately from the LP bound.

## Next research stages

### Phase 4 — richer crew resources
Add maximum block time, maximum sit time, explicit crew base return, overnight state and duty/resource counters directly to labels.

### Phase 5 — realistic scaling
Benchmark flights, generated columns, master iterations, pricing time, master time, MILP recovery time and memory.

### Phase 6 — true branch-and-price-lite
Introduce branching decisions that preserve pricing structure and re-run pricing at branch nodes. Until then, the repository deliberately uses the term **integer restricted master**, not branch-and-price.

### Phase 7 — stabilization
Investigate dual stabilization and column management for larger instances.

## Portfolio signal

The repository exposes the decomposition algorithm itself: master formulation, dual information, reduced-cost pricing, label dominance, convergence tests and integer recovery rather than merely calling a monolithic solver.

## License

MIT
