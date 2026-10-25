"""
verify.py
----------
Utilidades de verificación de salidas para el problema de Cobertura de Vértices:
valida corrección de coberturas sobre grafos arbitrarios (sintéticos y de gran escala),
calcula ratios de aproximación frente a cotas u óptimos conocidos, y genera métricas
estructurales de protección de red.
"""

from __future__ import annotations

from typing import Iterable
from .graph import Graph


def is_vertex_cover(graph: Graph, cover: Iterable) -> bool:
    """
    Verdadero si `cover` cubre absolutamente todas las aristas de `graph`.
    Implementación de alta eficiencia O(V + E) que evita materializar conjuntos
    de aristas, permitiendo validar instancias reales masivas en milisegundos.
    """
    cover_set = cover if isinstance(cover, (set, frozenset)) else set(cover)
    for u, neighbors in graph._adj.items():
        if u not in cover_set:
            for v in neighbors:
                if v not in cover_set:
                    return False
    return True


def uncovered_edges(graph: Graph, cover: Iterable, max_sample: int | None = None) -> set[tuple]:
    """
    Devuelve el conjunto de aristas que NO quedan cubiertas por `cover` (debería ser set()).
    Retorna set de tuplas canónicas.
    """
    cover_set = cover if isinstance(cover, (set, frozenset)) else set(cover)
    uncovered = set()
    for u, neighbors in graph._adj.items():
        if u not in cover_set:
            for v in neighbors:
                if v not in cover_set and str(u) < str(v):
                    uncovered.add((u, v))
                    if max_sample and len(uncovered) >= max_sample:
                        return uncovered
    return uncovered


def approximation_ratio(cover_size: int, optimal_size: int) -> float:
    """
    Ratio empírico |cover| / |óptimo|.
    1.0 = óptimo, 2.0 = el doble del óptimo (cota teórica del matching maximal).
    """
    if optimal_size <= 0:
        return 1.0 if cover_size == 0 else float("inf")
    return cover_size / optimal_size


def coverage_statistics(graph: Graph, cover: Iterable) -> dict:
    """
    Reporte detallado de cobertura y protección de red.
    """
    cover_set = cover if isinstance(cover, (set, frozenset)) else set(cover)
    n_v = graph.num_vertices()
    n_e = graph.num_edges()
    c_size = len(cover_set)

    uncovered = uncovered_edges(graph, cover_set, max_sample=10)
    is_valid = len(uncovered) == 0

    return {
        "is_valid": is_valid,
        "total_vertices": n_v,
        "total_edges": n_e,
        "cover_size": c_size,
        "vertex_coverage_fraction": (c_size / n_v) if n_v > 0 else 0.0,
        "edge_coverage_pct": 100.0 if is_valid else (1.0 - len(uncovered) / max(1, n_e)) * 100.0,
        "uncovered_sample": list(uncovered),
    }
