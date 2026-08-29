# Airline Crew Scheduling with Column Generation

Research-grade Operations Research implementation of a crew-pairing style set-covering model solved with **column generation** rather than only a monolithic MILP.

## Research question

How much computational leverage can decomposition provide when the number of feasible crew pairings grows combinatorially?

## Core formulation

Each legal pairing is a column. The restricted master problem minimizes pairing cost while covering every flight. Dual prices from the master are passed to a pricing problem, which searches for a new legal pairing with negative reduced cost.

The project separates three concerns:

- legality and resource accounting for crew pairings;
- restricted-master optimization and dual extraction;
- pricing via a resource-constrained path/labeling procedure.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
python -m crew_cg.experiment
```

## Repository map

```text
src/crew_cg/
  model.py          # flight and pairing data structures
  pairing.py        # legal pairing enumeration / pricing primitives
  master.py         # restricted master LP and duals
  column_generation.py
  experiment.py
tests/
  test_column_generation.py
configs/
  experiment.json
.github/workflows/
  ci.yml
```

## Research protocol

The small built-in instance is intentionally transparent and testable. Larger experiments should compare:

1. full pairing enumeration + LP;
2. monolithic set-covering MILP;
3. restricted master + column generation;
4. optional branch-and-price extension.

Report objective value, number of generated columns, pricing iterations, master solve time, pricing solve time and optimality gap where a full-enumeration reference is available.

## Methodological standard

A successful result is not simply “column generation runs.” The implementation should demonstrate that reduced costs are computed correctly, terminating pricing implies no improving column for the current LP relaxation, and all pairing resource constraints are independently validated.

## License

MIT
