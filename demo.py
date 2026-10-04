#!/usr/bin/env python3
"""
demo.py
--------
Prototipo minimo ejecutable para la demostracion del Avance 3.

Permite:
  1. Cargar una instancia desde un archivo JSON (o generar una aleatoria).
  2. Ejecutar uno o varios algoritmos (greedy, matching, exacto).
  3. Validar automaticamente que la salida sea una cobertura correcta.
  4. Mostrar el ratio de aproximacion frente al optimo cuando se calcula.

Ejemplos de uso:

    # Instancia de ejemplo del Avance 1, los tres algoritmos
    python demo.py --instance data/instances/example_small.json --algorithm all

    # Solo el greedy, sobre una instancia nueva propuesta en el momento
    python demo.py --instance data/instances/mi_instancia.json --algorithm greedy

    # Grafo aleatorio generado al vuelo (sin archivo), para una demo en vivo
    python demo.py --random 12 0.3 --seed 1 --algorithm all
"""

from __future__ import annotations

import argparse
import sys
import time

from src.graph import Graph
from src.solver import VertexCoverSolver
from src.verify import is_vertex_cover, approximation_ratio, uncovered_edges


ALGORITHMS = {
    "greedy": ("Greedy por grado", "greedy_degree_vertex_cover"),
    "matching": ("Matching maximal (2-aprox)", "maximal_matching_vertex_cover"),
    "exact": ("Exacto (fuerza bruta)", "exact_vertex_cover_bruteforce"),
}


def run_algorithm(solver: VertexCoverSolver, key: str):
    label, method_name = ALGORITHMS[key]
    method = getattr(solver, method_name)
    start = time.perf_counter()
    cover = method()
    elapsed = time.perf_counter() - start
    return label, cover, elapsed


def main():
    parser = argparse.ArgumentParser(description="Demo: Cobertura de Vertices para ubicacion de IDS")
    parser.add_argument("--instance", type=str, help="Ruta a un archivo JSON de instancia")
    parser.add_argument(
        "--random", nargs=2, type=float, metavar=("N", "P"),
        help="Generar un grafo aleatorio G(n, p) en vez de leer un archivo",
    )
    parser.add_argument("--seed", type=int, default=None, help="Semilla para el grafo aleatorio")
    parser.add_argument(
        "--algorithm", choices=["greedy", "matching", "exact", "all"], default="all",
        help="Que algoritmo(s) ejecutar (default: all)",
    )
    args = parser.parse_args()

    if args.instance:
        try:
            graph = Graph.from_json(args.instance)
        except FileNotFoundError:
            print(f"No se encontro el archivo de instancia: {args.instance}", file=sys.stderr)
            sys.exit(1)
        except (KeyError, ValueError) as e:
            print(f"El archivo de instancia tiene un formato invalido: {e}", file=sys.stderr)
            sys.exit(1)
        origin = f"instancia '{args.instance}'"
    elif args.random:
        n, p = int(args.random[0]), float(args.random[1])
        graph = Graph.random_graph(n=n, p=p, seed=args.seed)
        origin = f"grafo aleatorio G({n}, {p}), seed={args.seed}"
    else:
        print("Debes indicar --instance <archivo.json> o --random N P", file=sys.stderr)
        sys.exit(1)

    print(f"Cargado: {origin}")
    print(f"  |V| = {graph.num_vertices()}   |E| = {graph.num_edges()}")
    print()

    solver = VertexCoverSolver(graph)
    keys = list(ALGORITHMS) if args.algorithm == "all" else [args.algorithm]

    results = {}
    for key in keys:
        if key == "exact" and graph.num_vertices() > 20:
            print(f"[{ALGORITHMS[key][0]}] omitido: {graph.num_vertices()} vertices > 20 (fuerza bruta no escala)")
            continue
        try:
            label, cover, elapsed = run_algorithm(solver, key)
        except ValueError as e:
            print(f"[{ALGORITHMS[key][0]}] error: {e}")
            continue

        valid = is_vertex_cover(graph, cover)
        results[key] = (label, cover, elapsed, valid)

        print(f"[{label}]")
        print(f"  Cobertura: {sorted(cover, key=str)}")
        print(f"  Tamano: {len(cover)}")
        print(f"  Valida: {'SI' if valid else 'NO -- faltan aristas: ' + str(uncovered_edges(graph, cover))}")
        print(f"  Tiempo: {elapsed * 1000:.3f} ms")
        print()

    if "exact" in results:
        optimal_size = len(results["exact"][1])
        print("Ratios de aproximacion frente al optimo:")
        for key, (label, cover, _, _) in results.items():
            if key == "exact":
                continue
            ratio = approximation_ratio(len(cover), optimal_size)
            print(f"  {label}: {ratio:.3f}x")


if __name__ == "__main__":
    main()
