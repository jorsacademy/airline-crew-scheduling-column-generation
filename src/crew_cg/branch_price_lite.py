from __future__ import annotations

from dataclasses import dataclass
import heapq

import numpy as np
from scipy.optimize import linprog

from .model import Pairing
from .resource_column_generation import _singleton_pairings
from .resource_pricing import CrewRules, price_pairing_resource_rcsp


@dataclass(order=True)
class Node:
    bound: float
    depth: int
    fixed: tuple[Pairing, ...]
    forbidden: frozenset[tuple[int, ...]]


def _coverage_matrix(flights, pairings):
    matrix = np.zeros((len(flights), len(pairings)), dtype=float)
    for column, pairing in enumerate(pairings):
        for flight_id in pairing.flight_ids:
            matrix[flight_id, column] = 1.0
    return matrix


def _solve_residual_master(flights, pairings, fixed):
    fixed_cover = np.zeros(len(flights), dtype=float)
    fixed_cost = 0.0
    for pairing in fixed:
        fixed_cost += pairing.cost
        for flight_id in pairing.flight_ids:
            fixed_cover[flight_id] += 1.0
    rhs = np.maximum(0.0, 1.0 - fixed_cover)
    if not pairings:
        if np.all(rhs <= 1e-12):
            return {"objective": fixed_cost, "x": np.zeros(0), "duals": np.zeros(len(flights))}
        raise RuntimeError("residual master has no columns")
    coverage = _coverage_matrix(flights, pairings)
    result = linprog(
        np.asarray([p.cost for p in pairings]),
        A_ub=-coverage,
        b_ub=-rhs,
        bounds=[(0.0, None)] * len(pairings),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(result.message)
    return {
        "objective": fixed_cost + float(result.fun),
        "x": np.asarray(result.x),
        "duals": -np.asarray(result.ineqlin.marginals),
    }


def _price_node(flights, rules, fixed, forbidden, tolerance, max_iterations):
    fixed_keys = {p.flight_ids for p in fixed}
    active = [
        p
        for p in _singleton_pairings(flights, rules)
        if p.flight_ids not in forbidden and p.flight_ids not in fixed_keys
    ]
    history = []
    for iteration in range(max_iterations):
        master = _solve_residual_master(flights, active, fixed)
        reduced, pairing = price_pairing_resource_rcsp(
            flights,
            master["duals"],
            existing=active + list(fixed),
            forbidden=set(forbidden),
            rules=rules,
        )
        history.append((iteration, master["objective"], len(active), float(reduced)))
        if pairing is None or reduced >= -tolerance:
            return master, active, history
        active.append(pairing)
    raise RuntimeError("node pricing did not converge")


def branch_and_price_lite(
    flights,
    *,
    rules: CrewRules | None = None,
    tolerance: float = 1e-8,
    max_nodes: int = 50,
    max_iterations: int = 100,
):
    """Best-bound column-variable branching with fresh pricing at every node.

    This is deliberately a compact branch-and-price implementation. It branches on
    fractional generated pairing variables. The x=0 child forbids that pairing from
    future pricing; the x=1 child fixes the pairing and reduces residual coverage.
    """
    rules = rules or CrewRules(require_base_return=False)
    root_master, root_columns, root_history = _price_node(
        flights, rules, (), frozenset(), tolerance, max_iterations
    )
    queue = [Node(root_master["objective"], 0, (), frozenset())]
    incumbent_cost = float("inf")
    incumbent: tuple[Pairing, ...] = ()
    explored = 0
    total_pricing_iterations = len(root_history)

    while queue and explored < max_nodes:
        node = heapq.heappop(queue)
        if node.bound >= incumbent_cost - tolerance:
            continue
        explored += 1
        try:
            master, columns, history = _price_node(
                flights,
                rules,
                node.fixed,
                node.forbidden,
                tolerance,
                max_iterations,
            )
        except RuntimeError:
            continue
        total_pricing_iterations += len(history)
        if master["objective"] >= incumbent_cost - tolerance:
            continue
        x = master["x"]
        fractional = [
            (abs(value - 0.5), index, value)
            for index, value in enumerate(x)
            if tolerance < value < 1.0 - tolerance
        ]
        if not fractional:
            selected = tuple(node.fixed) + tuple(
                columns[index] for index, value in enumerate(x) if value >= 1.0 - tolerance
            )
            incumbent_cost = master["objective"]
            incumbent = selected
            continue

        _, index, _ = min(fractional)
        branch_pairing = columns[index]
        forbid = frozenset(set(node.forbidden) | {branch_pairing.flight_ids})
        heapq.heappush(queue, Node(master["objective"], node.depth + 1, node.fixed, forbid))
        heapq.heappush(
            queue,
            Node(
                master["objective"],
                node.depth + 1,
                tuple(node.fixed) + (branch_pairing,),
                node.forbidden,
            ),
        )

    if not incumbent:
        raise RuntimeError("branch-and-price-lite did not find an integer incumbent")
    return {
        "objective": float(incumbent_cost),
        "selected": list(incumbent),
        "nodes_explored": explored,
        "pricing_iterations": total_pricing_iterations,
        "root_lp_objective": float(root_master["objective"]),
        "root_columns": len(root_columns),
    }
