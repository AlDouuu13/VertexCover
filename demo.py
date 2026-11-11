#!/usr/bin/env python3
"""
demo.py
--------
Prototipo ejecutable CLI e Interfaz Gráfica para la demostración del proyecto.

Permite:
  1. Lanzar la Interfaz Gráfica interactiva con `--gui`.
  2. Cargar instancias didácticas (JSON), redes reales de internet (SNAP .txt),
     o generar grafos sintéticos aleatorios (Erdos-Renyi o Barabasi-Albert).
  3. Ejecutar algoritmos de cobertura:
     - greedy_fast (Optimizado O((V+E) log V))
     - matching (2-aproximación O(V+E))
     - ilp (Exacto por programación lineal entera PuLP)
     - exact (Fuerza bruta |V| <= 20)
     - all (Comparativa completa)
  4. Validar automáticamente corrección (100% aristas cubiertas) y ratios.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from src.graph import Graph
from src.solver import VertexCoverSolver
from src.verify import is_vertex_cover, approximation_ratio, uncovered_edges


ALGORITHMS = {
    "greedy_fast": ("Greedy Optimizado (Heap O((V+E)log V))", "greedy_degree_vertex_cover_optimized"),
    "greedy": ("Greedy por grado (O(V*E))", "greedy_degree_vertex_cover"),
    "matching": ("Matching maximal (2-aprox O(V+E))", "maximal_matching_vertex_cover"),
    "ilp": ("Exacto ILP (PuLP Branch&Bound)", "exact_vertex_cover_ilp"),
    "exact": ("Exacto (fuerza bruta O(2^V))", "exact_vertex_cover_bruteforce"),
}


def run_algorithm(solver: VertexCoverSolver, key: str):
    label, method_name = ALGORITHMS[key]
    method = getattr(solver, method_name)
    start = time.perf_counter()
    res = method()
    elapsed = time.perf_counter() - start
    cover = res[0] if isinstance(res, tuple) else res
    return label, cover, elapsed


def main():
    parser = argparse.ArgumentParser(description="Demo: Cobertura de Vértices para ubicación de IDS")
    parser.add_argument("--gui", action="store_true", help="Lanzar la interfaz gráfica de usuario interactiva")
    parser.add_argument("--instance", type=str, help="Ruta a un archivo JSON o de lista de aristas (.txt SNAP)")
    parser.add_argument(
        "--random", nargs=2, type=float, metavar=("N", "P"),
        help="Generar un grafo aleatorio G(n, p) en vez de leer un archivo",
    )
    parser.add_argument(
        "--barabasi", nargs=2, type=int, metavar=("N", "M"),
        help="Generar una red backbone Barabási-Albert con hubs",
    )
    parser.add_argument("--seed", type=int, default=None, help="Semilla para el generador aleatorio")
    parser.add_argument(
        "--algorithm", choices=["greedy_fast", "greedy", "matching", "ilp", "exact", "all"], default="all",
        help="Algoritmo(s) a ejecutar (default: all)",
    )
    args = parser.parse_args()

    if args.gui:
        from src.gui_app import launch_gui
        launch_gui()
        return

    if args.instance:
        p = Path(args.instance)
        if not p.exists():
            print(f"No se encontró el archivo de instancia: {args.instance}", file=sys.stderr)
            sys.exit(1)
        try:
            if p.suffix.lower() == ".json":
                graph = Graph.from_json(p)
            else:
                graph = Graph.from_edge_list(p)
        except Exception as e:
            print(f"Error al leer la instancia: {e}", file=sys.stderr)
            sys.exit(1)
        origin = f"instancia '{args.instance}'"
    elif args.random:
        n, p = int(args.random[0]), float(args.random[1])
        graph = Graph.random_graph(n=n, p=p, seed=args.seed)
        origin = f"grafo aleatorio Erdos-Renyi G({n}, {p}), seed={args.seed}"
    elif args.barabasi:
        n, m = args.barabasi[0], args.barabasi[1]
        graph = Graph.barabasi_albert(n=n, m=m, seed=args.seed)
        origin = f"red backbone Barabási-Albert (|V|={n}, m={m}), seed={args.seed}"
    else:
        print("Debes indicar --instance <archivo>, --random N P, o usar --gui", file=sys.stderr)
        sys.exit(1)

    print("=" * 65)
    print(f"Cargado: {origin}")
    print(f"  |V| (Routers) = {graph.num_vertices():,}   |E| (Enlaces) = {graph.num_edges():,}")
    print("=" * 65)
    print()

    solver = VertexCoverSolver(graph)

    if args.algorithm == "all":
        keys = ["greedy_fast", "matching"]
        if graph.num_vertices() <= 500:
            keys.append("ilp")
        if graph.num_vertices() <= 20:
            keys.append("exact")
    else:
        keys = [args.algorithm]

    results = {}
    for key in keys:
        if key == "exact" and graph.num_vertices() > 20:
            print(f"[{ALGORITHMS[key][0]}] omitido: {graph.num_vertices()} vértices > 20 (fuerza bruta no escala)")
            continue
        if key == "ilp" and graph.num_vertices() > 500:
            print(f"[{ALGORITHMS[key][0]}] omitido: {graph.num_vertices()} vértices > 500 (ILP branch&bound puede tardar)")
            continue
        try:
            label, cover, elapsed = run_algorithm(solver, key)
        except Exception as e:
            print(f"[{ALGORITHMS[key][0]}] error: {e}")
            continue

        valid = is_vertex_cover(graph, cover)
        results[key] = (label, cover, elapsed, valid)

        sample_cover = sorted(list(cover), key=str)[:10]
        sample_str = str(sample_cover) + (f" ... (+{len(cover)-10} más)" if len(cover) > 10 else "")

        print(f"[{label}]")
        print(f"  Routers IDS seleccionados (|C|): {len(cover):,} ({(len(cover)/max(1, graph.num_vertices())*100.0):.2f}% de la red)")
        print(f"  Muestra de routers: {sample_str}")
        print(f"  Válida (100% enlaces cubiertos): {'SÍ' if valid else 'NO'}")
        print(f"  Tiempo CPU: {elapsed * 1000.0:.3f} ms")
        print()

    # Comparativa de ratios
    opt_key = "ilp" if "ilp" in results else ("exact" if "exact" in results else None)
    if opt_key:
        optimal_size = len(results[opt_key][1])
        print("Ratios de aproximación frente al óptimo:")
        for key, (label, cover, _, _) in results.items():
            if key == opt_key:
                print(f"  {label}: 1.000x (Solución Óptima, |C*|={optimal_size})")
            else:
                ratio = approximation_ratio(len(cover), optimal_size)
                print(f"  {label}: {ratio:.3f}x")


if __name__ == "__main__":
    main()
