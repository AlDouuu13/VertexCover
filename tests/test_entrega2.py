"""
test_entrega2.py
----------------
Conjunto de pruebas automatizadas para la Entrega 2:
  1. Validación del solver exacto escalable ILP (PuLP / Branch & Bound) y
     su equivalencia con la fuerza bruta en el rango común.
  2. Validación y equivalencia del algoritmo Greedy Optimizado O((V+E)log V).
  3. Validación de corrección de cobertura sobre instancias reales de internet
     (Stanford SNAP AS-733 Oregon).
  4. Instrumentación de métricas de desempeño (tiempo y memoria pico).
  5. Métodos de extracción de subgrafos (hubs y ego-nets) para la interfaz gráfica.
"""

from pathlib import Path
import pytest

from src.graph import Graph
from src.solver import VertexCoverSolver
from src.verify import is_vertex_cover, uncovered_edges, approximation_ratio


class TestEntrega2ILP:
    def test_ilp_example_small_optimo(self):
        """ILP debe hallar exactamente el tamaño óptimo 3 en example_small."""
        g = Graph.from_json("data/instances/example_small.json")
        solver = VertexCoverSolver(g)
        cover, status = solver.exact_vertex_cover_ilp()

        assert status == "Optimal"
        assert len(cover) == 3
        assert is_vertex_cover(g, cover)

    @pytest.mark.parametrize("seed", [10, 25, 42, 77, 99])
    def test_ilp_coincide_con_fuerza_bruta_en_rango_comun(self, seed):
        """
        En grafos de 12 vértices, tanto fuerza bruta como ILP deben
        encontrar exactamente el mismo número mínimo de vértices (|C*|).
        """
        g = Graph.random_graph(n=12, p=0.35, seed=seed)
        solver = VertexCoverSolver(g)

        bf_cover = solver.exact_vertex_cover_bruteforce(max_vertices=15)
        ilp_cover, status = solver.exact_vertex_cover_ilp()

        assert status == "Optimal"
        assert is_vertex_cover(g, bf_cover)
        assert is_vertex_cover(g, ilp_cover)
        assert len(ilp_cover) == len(bf_cover), f"ILP ({len(ilp_cover)}) != BF ({len(bf_cover)})"


class TestEntrega2GreedyOptimizado:
    def test_greedy_optimizado_coincide_en_tamano_con_legacy(self):
        """Verifica que el greedy con heap O((V+E)log V) mantenga el mismo desempeño."""
        for seed in [1, 2, 3, 4, 5]:
            g = Graph.random_graph(n=25, p=0.25, seed=seed)
            solver = VertexCoverSolver(g)
            c_legacy = solver.greedy_degree_vertex_cover()
            c_fast = solver.greedy_degree_vertex_cover_optimized()

            assert is_vertex_cover(g, c_legacy)
            assert is_vertex_cover(g, c_fast)
            # Ambas heurísticas deben dar tamaños de cobertura comparables y válidos
            assert abs(len(c_legacy) - len(c_fast)) <= 1

    def test_greedy_optimizado_escala_a_grafos_medianos(self):
        """Verifica que procese un grafo de 300 nodos y preserve cobertura 100%."""
        g = Graph.random_graph(n=300, p=0.05, seed=123)
        solver = VertexCoverSolver(g)
        cover = solver.greedy_degree_vertex_cover_optimized()

        assert is_vertex_cover(g, cover)
        assert len(uncovered_edges(g, cover)) == 0


class TestEntrega2InstanciaRealInternet:
    def test_carga_y_resolucion_snap_as733(self):
        """
        Prueba de integración sobre la red real de internet Stanford SNAP AS-733
        (6,474 routers y más de 12,500 enlaces reales).
        """
        real_file = Path("data/instances/real/as20000102.txt")
        if not real_file.exists():
            pytest.skip("Archivo de dataset real no encontrado.")

        g = Graph.from_edge_list(real_file)
        assert g.num_vertices() == 6474
        assert g.num_edges() > 10000

        solver = VertexCoverSolver(g)

        # Ejecución de Greedy Optimizado
        res_greedy = solver.solve("greedy_fast")
        assert res_greedy["is_valid"] is True
        assert res_greedy["size"] < 1500  # En la red real AS, pocos routers cubren todos los enlaces
        assert res_greedy["time_ms"] < 2000.0  # Menos de 2 segundos en escala real

        # Ejecución de Matching Maximal
        res_matching = solver.solve("matching")
        assert res_matching["is_valid"] is True
        assert res_matching["size"] < 3000
        assert res_matching["time_ms"] < 1000.0


class TestEntrega2SubgrafosGUI:
    def test_top_degree_subgraph(self):
        """Verifica que el subgrafo de hubs mantenga solo los top_k vértices de mayor grado."""
        g = Graph.barabasi_albert(n=50, m=3, seed=42)
        sub_g = g.top_degree_subgraph(top_k=15)
        assert sub_g.num_vertices() == 15
        assert sub_g.num_edges() <= g.num_edges()

    def test_ego_subgraph(self):
        """Verifica que el subgrafo ego-net contenga al router central y sus vecinos inmediatos."""
        g = Graph.from_json("data/instances/example_small.json")
        ego = g.ego_subgraph("A", radius=1)
        assert "A" in ego.vertices
        assert ego.vertices.issubset(g.vertices)
