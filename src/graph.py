"""
graph.py
---------
Estructura de datos de grafo no dirigido para el problema de Cobertura de
Vértices, usada para representar la topología de una red (routers = vértices,
enlaces = aristas).

Representación interna: lista de adyacencia (diccionario de conjuntos), elegida
por simplicidad y eficiencia:
  - obtener el grado de un vértice en O(1)
  - iterar vecinos en O(deg(v))
  - insertar/eliminar aristas en O(1) amortizado
  - soporte de grafos sintéticos (Erdos-Renyi, Barabasi-Albert) y datasets
    reales de gran escala (SNAP Autonomous Systems / CAIDA Router Topology).

Formato de archivo de instancia (JSON):
{
    "name": "example_small",
    "description": "Mini-red de 6 routers (ver Avance 1)",
    "vertices": ["A", "B", "C", "D", "E", "F"],
    "edges": [["A","B"], ["A","C"], ["A","D"], ["B","C"], ["D","E"], ["E","F"]]
}
"""

from __future__ import annotations

import json
import random
from collections import deque
from pathlib import Path
from typing import Iterable, Hashable


class Graph:
    """Grafo no dirigido y no ponderado basado en listas de adyacencia."""

    def __init__(self, vertices: Iterable[Hashable] = (), edges: Iterable[tuple] = ()):
        self._adj: dict[Hashable, set] = {v: set() for v in vertices}
        for u, v in edges:
            self.add_edge(u, v)

    # ---------- construcción ----------
    def add_vertex(self, v: Hashable) -> None:
        self._adj.setdefault(v, set())

    def add_edge(self, u: Hashable, v: Hashable) -> None:
        if u == v:
            raise ValueError(f"No se permiten auto-ciclos: ({u}, {v})")
        self.add_vertex(u)
        self.add_vertex(v)
        self._adj[u].add(v)
        self._adj[v].add(u)

    def remove_edge(self, u: Hashable, v: Hashable) -> None:
        self._adj[u].discard(v)
        self._adj[v].discard(u)

    # ---------- consultas ----------
    @property
    def vertices(self) -> set:
        return set(self._adj.keys())

    @property
    def edges(self) -> set[tuple]:
        seen = set()
        result = []
        for u in self._adj:
            for v in self._adj[u]:
                key = frozenset((u, v))
                if key not in seen:
                    seen.add(key)
                    result.append((u, v))
        return set(result)

    def canonical_edges(self) -> list[tuple]:
        """
        Devuelve la lista determinística de aristas ordenadas canónicamente.
        Evita la sobrecarga de frozenset para grafos de escala real.
        """
        result = []
        for u, neighbors in self._adj.items():
            u_str = str(u)
            for v in neighbors:
                v_str = str(v)
                if u_str < v_str:
                    result.append((u, v))
                elif u_str == v_str and u < v:
                    result.append((u, v))
        result.sort(key=lambda e: (str(e[0]), str(e[1])))
        return result

    def neighbors(self, v: Hashable) -> set:
        return set(self._adj.get(v, set()))

    def degree(self, v: Hashable) -> int:
        return len(self._adj.get(v, set()))

    def num_vertices(self) -> int:
        return len(self._adj)

    def num_edges(self) -> int:
        # Cálculo O(V) directo sin reservar conjuntos de tuplas
        return sum(len(neigh) for neigh in self._adj.values()) // 2

    def density(self) -> float:
        n = self.num_vertices()
        if n <= 1:
            return 0.0
        return (2.0 * self.num_edges()) / (n * (n - 1))

    def is_edge(self, u: Hashable, v: Hashable) -> bool:
        return v in self._adj.get(u, set())

    def copy(self) -> "Graph":
        g = Graph()
        g._adj = {v: set(neigh) for v, neigh in self._adj.items()}
        return g

    # ---------- subgrafos y vistas de escala ----------
    def subgraph(self, subset: Iterable[Hashable]) -> "Graph":
        """Genera el subgrafo inducido por el subconjunto de vértices."""
        sub_set = set(subset)
        sub_g = Graph(vertices=sub_set)
        for u in sub_set:
            if u in self._adj:
                for v in self._adj[u]:
                    if v in sub_set and str(u) < str(v):
                        sub_g.add_edge(u, v)
        return sub_g

    def top_degree_subgraph(self, top_k: int = 100) -> "Graph":
        """
        Extrae el subgrafo inducido por los top_k vértices de mayor grado (hubs).
        Fundamental para la visualización fluida de grafos masivos de internet.
        """
        if self.num_vertices() <= top_k:
            return self.copy()
        sorted_v = sorted(self._adj.keys(), key=lambda v: len(self._adj[v]), reverse=True)
        return self.subgraph(sorted_v[:top_k])

    def ego_subgraph(self, center: Hashable, radius: int = 1) -> "Graph":
        """Extrae el vecindario BFS de radio k alrededor de un router central."""
        if center not in self._adj:
            return Graph()
        visited = {center}
        queue = deque([(center, 0)])
        while queue:
            node, dist = queue.popleft()
            if dist < radius:
                for neighbor in self._adj.get(node, set()):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))
        return self.subgraph(visited)

    def __repr__(self) -> str:
        return f"Graph(|V|={self.num_vertices()}, |E|={self.num_edges()})"

    # ---------- I/O ----------
    @classmethod
    def from_json(cls, path: str | Path) -> "Graph":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        g = cls(vertices=data.get("vertices", []))
        for u, v in data["edges"]:
            g.add_edge(u, v)
        return g

    @classmethod
    def from_edge_list(
        cls,
        path: str | Path,
        delimiter: str | None = None,
        comment_char: str = "#",
        max_edges: int | None = None,
    ) -> "Graph":
        """
        Carga grafos en formato de lista de aristas (SNAP, Network Repository, etc.).
        Ignora comentarios iniciales (#) y columnas adicionales de metadatos.
        """
        g = cls()
        count = 0
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(comment_char):
                    continue
                parts = line.split(delimiter) if delimiter else line.split()
                if len(parts) >= 2:
                    u, v = parts[0], parts[1]
                    if u != v:
                        g.add_edge(u, v)
                        count += 1
                        if max_edges and count >= max_edges:
                            break
        return g

    def to_dict(self, name: str = "instance", description: str = "") -> dict:
        return {
            "name": name,
            "description": description,
            "vertices": sorted(self.vertices, key=str),
            "edges": [list(e) for e in sorted(self.edges, key=lambda e: tuple(sorted(map(str, e))))],
        }

    def save_json(self, path: str | Path, name: str = "instance", description: str = "") -> None:
        data = self.to_dict(name, description)
        vertices_json = json.dumps(data["vertices"], ensure_ascii=False)
        edges_json = ",\n    ".join(json.dumps(e, ensure_ascii=False) for e in data["edges"])
        text = (
            "{\n"
            f'  "name": {json.dumps(data["name"], ensure_ascii=False)},\n'
            f'  "description": {json.dumps(data["description"], ensure_ascii=False)},\n'
            f'  "vertices": {vertices_json},\n'
            f'  "edges": [\n    {edges_json}\n  ]\n'
            "}\n"
        )
        Path(path).write_text(text, encoding="utf-8")

    # ---------- generadores de instancias sintéticas ----------
    @staticmethod
    def random_graph(n: int, p: float, seed: int | None = None) -> "Graph":
        """Modelo Erdos-Renyi G(n, p): red aleatoria simple para pruebas de escala."""
        rng = random.Random(seed)
        g = Graph(vertices=range(n))
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < p:
                    g.add_edge(i, j)
        return g

    @staticmethod
    def barabasi_albert(n: int, m: int, seed: int | None = None) -> "Graph":
        """
        Modelo Barabasi-Albert simplificado: genera hubs de alto grado, similar
        a una topología de red backbone con routers concentradores.
        """
        rng = random.Random(seed)
        if m < 1 or m >= n:
            raise ValueError("Se requiere 1 <= m < n")
        g = Graph(vertices=range(n))
        targets = list(range(m))
        repeated_nodes = []
        for i in range(m):
            for j in range(i + 1, m):
                g.add_edge(i, j)
        for new_node in range(m, n):
            for target in targets:
                g.add_edge(new_node, target)
            repeated_nodes.extend(targets)
            repeated_nodes.extend([new_node] * m)
            targets = list(set(rng.sample(repeated_nodes, m)))
        return g
