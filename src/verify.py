"""
verify.py
----------
Utilidades de verificacion de salidas: dado un grafo y una presunta
cobertura de vertices, confirma que sea valida y calcula metricas de
comparacion frente al optimo (o frente a otro algoritmo).
"""

from __future__ import annotations

from .graph import Graph


def is_vertex_cover(graph: Graph, cover: set) -> bool:
    """Verdadero si `cover` cubre absolutamente todas las aristas de `graph`."""
    return all(u in cover or v in cover for u, v in graph.edges)


def uncovered_edges(graph: Graph, cover: set) -> set:
    """Aristas que NO quedan cubiertas por `cover` (deberia ser vacio)."""
    return {(u, v) for u, v in graph.edges if u not in cover and v not in cover}


def approximation_ratio(cover_size: int, optimal_size: int) -> float:
    """
    Ratio empirico |cover| / |optimo|. 1.0 = optimo, 2.0 = el doble del
    optimo (cota teorica del matching maximal), etc.
    """
    if optimal_size == 0:
        return 1.0 if cover_size == 0 else float("inf")
    return cover_size / optimal_size
