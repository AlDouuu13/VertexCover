"""
solver.py
----------
VertexCoverSolver: implementa los algoritmos a comparar para el problema de
Cobertura de Vertices.

    1. greedy_degree_vertex_cover   -> heuristica voraz por grado
    2. maximal_matching_vertex_cover -> 2-aproximacion con garantia formal
    3. exact_vertex_cover_bruteforce -> solucion de referencia (optima),
       solo para instancias pequenas (|V| <= ~20)

Las dos primeras siguen el pseudocodigo acordado en el Avance 1.
"""

from __future__ import annotations

from itertools import combinations
from typing import Hashable

from .graph import Graph


class VertexCoverSolver:
    def __init__(self, graph: Graph):
        self.graph = graph

    def _sorted_edges(self) -> list[tuple]:
        """
        Devuelve las aristas en un orden canonico y deterministico.

        Python aleatoriza el hash de los strings entre procesos (PYTHONHASHSEED),
        por lo que iterar directamente sobre un set() de aristas produce un
        orden distinto en cada ejecucion. Como el proyecto exige resultados
        reproducibles (instrucciones adicionales, punto 7), tanto el "arbitrario"
        del matching maximal como el desempate del greedy se resuelven siempre
        sobre esta misma lista ordenada.
        """
        canonical = (tuple(sorted((u, v), key=str)) for u, v in self.graph.edges)
        return sorted(canonical, key=lambda e: tuple(map(str, e)))

    # ------------------------------------------------------------------
    # 1. Greedy por grado
    # ------------------------------------------------------------------
    def greedy_degree_vertex_cover(self) -> set:
        """
        En cada paso elige el vertice con mayor numero de aristas incidentes
        entre las aun no cubiertas, lo agrega a la cobertura y elimina esas
        aristas. Repite hasta no tener aristas pendientes. Los empates de
        grado se resuelven por orden canonico (ver `_sorted_edges`), para
        que el resultado sea reproducible.

        Complejidad: O(V * E) en esta implementacion directa (en cada
        iteracion se recorren las aristas restantes para recalcular grados).
        Puede optimizarse a O((V + E) log V) con una cola de prioridad.

        Garantia de aproximacion: ninguna cota fija en el peor caso general,
        pero buen desempeno empirico (ver experiments/compare.py).
        """
        remaining_edges = self._sorted_edges()
        cover: set = set()

        while remaining_edges:
            degree_count: dict[Hashable, int] = {}
            for u, v in remaining_edges:
                degree_count[u] = degree_count.get(u, 0) + 1
                degree_count[v] = degree_count.get(v, 0) + 1

            # max() devuelve el primer elemento de mayor valor segun el
            # orden de iteracion del dict, que aqui es deterministico
            # porque degree_count se construyo a partir de una lista ya
            # ordenada canonicamente.
            best_vertex = max(degree_count, key=degree_count.get)
            cover.add(best_vertex)

            remaining_edges = [
                (u, v) for (u, v) in remaining_edges
                if u != best_vertex and v != best_vertex
            ]

        return cover

    # ------------------------------------------------------------------
    # 2. Matching maximal (2-aproximacion)
    # ------------------------------------------------------------------
    def maximal_matching_vertex_cover(self) -> set:
        """
        Toma una arista arbitraria (u, v), agrega ambos extremos a la
        cobertura y elimina todas las aristas incidentes a u o v. Repite
        hasta agotar las aristas.

        Complejidad: O(V + E).

        Garantia de aproximacion: |cover| <= 2 * |optimo|, porque las
        aristas elegidas forman un matching (no comparten extremos) y toda
        cobertura valida debe incluir al menos un vertice de cada arista
        del matching. La arista "arbitraria" en cada paso se toma siempre
        la primera en el orden canonico (ver `_sorted_edges`), para que el
        resultado sea reproducible entre ejecuciones.
        """
        remaining_edges = self._sorted_edges()
        cover: set = set()

        while remaining_edges:
            u, v = remaining_edges[0]
            cover.add(u)
            cover.add(v)

            remaining_edges = [
                (a, b) for (a, b) in remaining_edges
                if a not in (u, v) and b not in (u, v)
            ]

        return cover

    # ------------------------------------------------------------------
    # 3. Solucion exacta de referencia (fuerza bruta con poda simple)
    # ------------------------------------------------------------------
    def exact_vertex_cover_bruteforce(self, max_vertices: int = 20) -> set:
        """
        Prueba subconjuntos de tamano creciente k = 0, 1, 2, ... hasta
        encontrar el primero que sea una cobertura valida. Garantiza la
        solucion OPTIMA, pero es exponencial: O(C(n, k*) * E) en el peor
        caso, por eso solo se usa como referencia en instancias pequenas.

        Se usa unicamente para validar los algoritmos aproximados en el
        plan de pruebas (Avance 2) y en los experimentos de instancias
        pequenas (Avance 2 / Entrega 2).
        """
        n = self.graph.num_vertices()
        if n > max_vertices:
            raise ValueError(
                f"Instancia demasiado grande para fuerza bruta "
                f"({n} > {max_vertices} vertices). Usar una heuristica o ILP."
            )

        vertices = list(self.graph.vertices)
        edges = self.graph.edges

        if not edges:
            return set()

        for k in range(1, n + 1):
            for subset in combinations(vertices, k):
                candidate = set(subset)
                if all(u in candidate or v in candidate for u, v in edges):
                    return candidate

        return set(vertices)  # caso extremo: el grafo completo es necesario

    # ------------------------------------------------------------------
    # 4. (opcional / Avance 2) Solucion exacta via ILP
    # ------------------------------------------------------------------
    def exact_vertex_cover_ilp(self):
        """
        Formulacion de Programacion Lineal Entera (ILP) usando PuLP, como
        alternativa escalable a la fuerza bruta para instancias algo mas
        grandes (decenas/cientos de vertices, dependiendo del solver).

            minimizar      sum_v x_v
            sujeto a       x_u + x_v >= 1   para toda arista (u, v)
                           x_v in {0, 1}

        Requiere `pip install pulp`. Se deja como componente a completar
        durante el aprendizaje autonomo del indicador AG-C06.02; por ahora
        lanza NotImplementedError si PuLP no esta instalado.
        """
        try:
            import pulp
        except ImportError as exc:
            raise NotImplementedError(
                "PuLP no esta instalado. Ejecutar: pip install pulp"
            ) from exc

        prob = pulp.LpProblem("VertexCover", pulp.LpMinimize)
        x = {v: pulp.LpVariable(f"x_{v}", cat="Binary") for v in self.graph.vertices}

        prob += pulp.lpSum(x.values())
        for u, v in self.graph.edges:
            prob += x[u] + x[v] >= 1

        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        return {v for v, var in x.items() if pulp.value(var) == 1}
