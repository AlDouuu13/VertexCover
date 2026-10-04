#!/usr/bin/env python3
"""
experiments/compare.py
------------------------
Experimento comparativo preliminar entre los dos algoritmos aproximados
(greedy por grado y matching maximal), usando el exacto por fuerza bruta
como referencia en instancias pequenas.

Metricas registradas, segun lo previsto en el Avance 2:
  - tamano de la cobertura obtenida por cada algoritmo
  - ratio de aproximacion empirico frente al optimo (|cover| / |optimo|)
  - tiempo de ejecucion (ms)

Metodologia:
  - Grafos aleatorios G(n, p) (Erdos-Renyi), con semilla fija por
    instancia para que el experimento sea reproducible.
  - n variando entre 6 y 18 (limite practico de la fuerza bruta en esta
    maquina; para n mayor se necesitaria el solver ILP, pendiente de
    incorporar a este script en la Entrega 2).
  - p fijo en 0.3 (densidad media), para aislar el efecto de n.

Salida: experiments/results/comparison.csv
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

# Permite ejecutar "python experiments/compare.py" directamente desde la
# raiz del repositorio sin instalar el paquete (sys.path[0] seria
# experiments/, no la raiz, asi que "from src...." fallaria sin esto).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph import Graph
from src.solver import VertexCoverSolver
from src.verify import is_vertex_cover, approximation_ratio

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_CSV = RESULTS_DIR / "comparison.csv"

N_VALUES = [6, 8, 10, 12, 14, 16, 18]
P = 0.3
SEED_BASE = 100  # desplazamiento de semilla para no chocar con otras instancias del repo


def timed(fn):
    start = time.perf_counter()
    result = fn()
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms


def run_experiment():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for n in N_VALUES:
        seed = SEED_BASE + n
        graph = Graph.random_graph(n=n, p=P, seed=seed)
        solver = VertexCoverSolver(graph)

        exact, t_exact = timed(solver.exact_vertex_cover_bruteforce)
        greedy, t_greedy = timed(solver.greedy_degree_vertex_cover)
        matching, t_matching = timed(solver.maximal_matching_vertex_cover)

        assert is_vertex_cover(graph, exact)
        assert is_vertex_cover(graph, greedy)
        assert is_vertex_cover(graph, matching)

        optimal = len(exact)
        row = {
            "n": n,
            "m_edges": graph.num_edges(),
            "optimo": optimal,
            "greedy_tamano": len(greedy),
            "greedy_ratio": round(approximation_ratio(len(greedy), optimal), 3),
            "greedy_tiempo_ms": round(t_greedy, 4),
            "matching_tamano": len(matching),
            "matching_ratio": round(approximation_ratio(len(matching), optimal), 3),
            "matching_tiempo_ms": round(t_matching, 4),
            "exacto_tiempo_ms": round(t_exact, 4),
        }
        rows.append(row)

        print(
            f"n={n:>3} |E|={row['m_edges']:>3}  optimo={optimal:>2}  "
            f"greedy={row['greedy_tamano']:>2} ({row['greedy_ratio']:.2f}x)  "
            f"matching={row['matching_tamano']:>2} ({row['matching_ratio']:.2f}x)  "
            f"t_exacto={row['exacto_tiempo_ms']:.2f}ms"
        )

    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nResultados guardados en {RESULTS_CSV}")
    return rows


if __name__ == "__main__":
    run_experiment()
