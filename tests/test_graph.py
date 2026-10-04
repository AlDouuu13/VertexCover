"""Pruebas de la estructura Graph."""

import pytest

from src.graph import Graph


def test_add_edge_updates_both_adjacency_lists():
    g = Graph()
    g.add_edge("A", "B")
    assert g.is_edge("A", "B")
    assert g.is_edge("B", "A")
    assert g.degree("A") == 1
    assert g.degree("B") == 1


def test_no_self_loops():
    g = Graph()
    with pytest.raises(ValueError):
        g.add_edge("A", "A")


def test_num_vertices_and_edges():
    g = Graph(vertices=["A", "B", "C"], edges=[("A", "B"), ("B", "C")])
    assert g.num_vertices() == 3
    assert g.num_edges() == 2


def test_isolated_vertex_has_degree_zero():
    g = Graph(vertices=["A", "B"], edges=[])
    g.add_vertex("Z")
    assert g.degree("Z") == 0
    assert "Z" in g.vertices


def test_from_json_loads_known_instance():
    g = Graph.from_json("data/instances/example_small.json")
    assert g.num_vertices() == 6
    assert g.num_edges() == 6
    assert g.degree("A") == 3  # vertice de mayor grado en la instancia de ejemplo


def test_random_graph_respects_vertex_count():
    g = Graph.random_graph(n=15, p=0.3, seed=42)
    assert g.num_vertices() == 15


def test_barabasi_albert_requires_valid_m():
    with pytest.raises(ValueError):
        Graph.barabasi_albert(n=5, m=5)
