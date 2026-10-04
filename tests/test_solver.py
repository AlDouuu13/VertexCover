"""
test_solver.py
----------------
Plan de pruebas del Avance 2, organizado en tres categorias tal como pide
la guia del proyecto:

  1. BASICAS   -> instancias pequenas con solucion conocida/manual.
  2. LIMITE    -> grafo vacio, una sola arista, vertices aislados, grafo
                  completo (casos borde de la definicion del problema).
  3. ADVERSARIAS -> instancias disenadas para poner a prueba el caso donde
                  el greedy y el matching maximal se comportan distinto
                  (grafo estrella), y una verificacion general de que el
                  matching maximal jamas viola su cota teorica de 2x el
                  optimo, probada sobre varias instancias aleatorias.

Criterio de verificacion de salidas (para las tres categorias): toda
cobertura devuelta se valida con `is_vertex_cover`, nunca se confia
unicamente en el tamano devuelto.
"""

import pytest

from src.graph import Graph
from src.solver import VertexCoverSolver
from src.verify import is_vertex_cover, uncovered_edges


def make_solver(g: Graph) -> VertexCoverSolver:
    return VertexCoverSolver(g)


# ======================================================================
# 1. CASOS BASICOS
# ======================================================================

class TestCasosBasicos:
    def test_example_small_coincide_con_solucion_manual(self):
        """Debe reproducir exactamente lo resuelto a mano en el Avance 1."""
        g = Graph.from_json("data/instances/example_small.json")
        s = make_solver(g)

        greedy = s.greedy_degree_vertex_cover()
        matching = s.maximal_matching_vertex_cover()
        exact = s.exact_vertex_cover_bruteforce()

        assert is_vertex_cover(g, greedy)
        assert is_vertex_cover(g, matching)
        assert is_vertex_cover(g, exact)

        assert len(greedy) == 3   # {A, B, E} en la traza del Avance 1
        assert len(matching) == 4  # {A, B, D, E} en la traza del Avance 1
        assert len(exact) == 3     # optimo conocido: {A, C, E}

    def test_triangulo_optimo_es_dos(self):
        """En un triangulo (K3) el optimo es siempre 2 (cualquier par)."""
        g = Graph(vertices=["X", "Y", "Z"], edges=[("X", "Y"), ("Y", "Z"), ("X", "Z")])
        s = make_solver(g)
        exact = s.exact_vertex_cover_bruteforce()
        assert len(exact) == 2
        assert is_vertex_cover(g, exact)


# ======================================================================
# 2. CASOS LIMITE
# ======================================================================

class TestCasosLimite:
    def test_grafo_sin_aristas_devuelve_cobertura_vacia(self):
        g = Graph(vertices=["A", "B", "C"], edges=[])
        s = make_solver(g)
        for cover in (
            s.greedy_degree_vertex_cover(),
            s.maximal_matching_vertex_cover(),
            s.exact_vertex_cover_bruteforce(),
        ):
            assert cover == set()
            assert is_vertex_cover(g, cover)

    def test_una_sola_arista(self):
        g = Graph(vertices=["A", "B"], edges=[("A", "B")])
        s = make_solver(g)

        greedy = s.greedy_degree_vertex_cover()
        matching = s.maximal_matching_vertex_cover()
        exact = s.exact_vertex_cover_bruteforce()

        assert len(greedy) == 1          # greedy toma un solo extremo
        assert len(matching) == 2        # matching toma ambos extremos (peor caso real del 2x)
        assert len(exact) == 1
        assert is_vertex_cover(g, greedy)
        assert is_vertex_cover(g, matching)

    def test_vertices_aislados_no_aparecen_en_la_cobertura(self):
        """Un vertice sin aristas nunca deberia ser necesario en la cobertura."""
        g = Graph(vertices=["A", "B", "Z"], edges=[("A", "B")])
        s = make_solver(g)
        for cover in (
            s.greedy_degree_vertex_cover(),
            s.maximal_matching_vertex_cover(),
            s.exact_vertex_cover_bruteforce(),
        ):
            assert "Z" not in cover

    def test_grafo_completo_optimo_es_n_menos_uno(self):
        """En K_n, el optimo conocido es n-1 (todos menos uno cualquiera)."""
        vertices = ["A", "B", "C", "D"]
        edges = [(u, v) for i, u in enumerate(vertices) for v in vertices[i + 1:]]
        g = Graph(vertices=vertices, edges=edges)
        s = make_solver(g)
        exact = s.exact_vertex_cover_bruteforce()
        assert len(exact) == len(vertices) - 1
        assert is_vertex_cover(g, exact)

    def test_componentes_desconectadas(self):
        """Dos componentes separadas: la cobertura debe seguir siendo valida."""
        g = Graph(
            vertices=["A", "B", "C", "D"],
            edges=[("A", "B"), ("C", "D")],
        )
        s = make_solver(g)
        exact = s.exact_vertex_cover_bruteforce()
        assert len(exact) == 2  # un vertice por componente
        assert is_vertex_cover(g, exact)

    def test_fuerza_bruta_rechaza_instancias_demasiado_grandes(self):
        g = Graph.random_graph(n=25, p=0.1, seed=1)
        s = make_solver(g)
        with pytest.raises(ValueError):
            s.exact_vertex_cover_bruteforce(max_vertices=20)


# ======================================================================
# 3. CASOS ADVERSARIOS
# ======================================================================

class TestCasosAdversarios:
    def test_grafo_estrella_greedy_optimo_matching_subobtimo(self):
        """
        Grafo estrella: un centro conectado a 6 hojas. El greedy por grado
        elige el centro de inmediato (grado maximo) y logra el optimo (1).
        El matching maximal, al tomar una arista arbitraria centro-hoja,
        tambien agrega la hoja innecesariamente -> tamano 2. Ambos son
        validos, pero el ejemplo evidencia que la heuristica sin garantia
        formal puede superar en la practica al algoritmo con garantia
        teorica.
        """
        leaves = [f"L{i}" for i in range(6)]
        g = Graph(vertices=["C"] + leaves, edges=[("C", leaf) for leaf in leaves])
        s = make_solver(g)

        greedy = s.greedy_degree_vertex_cover()
        matching = s.maximal_matching_vertex_cover()
        exact = s.exact_vertex_cover_bruteforce()

        assert len(exact) == 1
        assert len(greedy) == 1
        assert len(matching) == 2
        assert is_vertex_cover(g, greedy)
        assert is_vertex_cover(g, matching)

    @pytest.mark.parametrize("seed", range(10))
    def test_matching_maximal_nunca_supera_el_doble_del_optimo(self, seed):
        """
        Verificacion de la cota teorica |cover_matching| <= 2 * |optimo|
        sobre 10 instancias aleatorias pequenas distintas.
        """
        g = Graph.random_graph(n=10, p=0.35, seed=seed)
        s = make_solver(g)

        matching = s.maximal_matching_vertex_cover()
        exact = s.exact_vertex_cover_bruteforce()

        assert is_vertex_cover(g, matching)
        if exact:  # evita division por cero si el grafo no tiene aristas
            assert len(matching) <= 2 * len(exact)

    def test_sin_aristas_sin_cobertura_pendiente(self):
        """Caso adverso de verificacion: toda arista debe quedar cubierta,
        nunca debe haber aristas 'olvidadas' por los algoritmos."""
        g = Graph.random_graph(n=12, p=0.4, seed=7)
        s = make_solver(g)
        for cover in (s.greedy_degree_vertex_cover(), s.maximal_matching_vertex_cover()):
            assert uncovered_edges(g, cover) == set()
