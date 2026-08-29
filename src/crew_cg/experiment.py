from .column_generation import run_column_generation
from .master import solve_master
from .model import toy_flights
from .pairing import enumerate_pairings


def main():
    flights = toy_flights()
    full_pairings = enumerate_pairings(flights)
    full = solve_master(flights, full_pairings)
    cg, active, history = run_column_generation(flights)

    print(f"full_enumeration_columns={len(full_pairings)}")
    print(f"cg_columns={len(active)}")
    print(f"full_lp_objective={full['objective']:.3f}")
    print(f"cg_lp_objective={cg['objective']:.3f}")
    print("iteration,objective,columns,best_reduced_cost")
    for row in history:
        print(
            f"{row['iteration']},{row['objective']:.3f},"
            f"{row['columns']},{row['best_reduced_cost']:.6f}"
        )


if __name__ == "__main__":
    main()
