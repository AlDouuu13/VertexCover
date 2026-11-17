#!/usr/bin/env python3
"""
experiments/compare_entrega2.py
--------------------------------
Batería experimental exhaustiva para la Entrega 2:
  1. Comparación de escalabilidad (N = 10 a 500) en tiempo (ms) y memoria (KB).
  2. Comparación de algoritmos exactos (Fuerza Bruta vs ILP Branch & Bound) frente
     a las estrategias de aproximación (Greedy Optimizado vs Matching Maximal).
  3. Evaluación de impacto de topología y densidad (Erdos-Renyi vs Barabási-Albert).
  4. Evaluación de rendimiento a escala real sobre datasets de internet (SNAP AS-733 y CAIDA BGP).
  5. Generación automática de gráficos científicos con Matplotlib para el informe técnico.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

# Añadir raíz al path para ejecución directa
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.graph import Graph
from src.solver import VertexCoverSolver
from src.verify import is_vertex_cover, approximation_ratio

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_scalability_experiments():
    print("=" * 70)
    print(" EXPERIMENTO 1: ESCALABILIDAD TEMPORAL Y APROXIMACIÓN (SINTÉTICO)")
    print("=" * 70)

    n_values = [10, 15, 20, 30, 50, 80, 120, 200, 350, 500]
    p = 0.20
    rows = []

    for n in n_values:
        g = Graph.random_graph(n=n, p=p, seed=100 + n)
        solver = VertexCoverSolver(g)
        m = g.num_edges()

        # 1. Greedy Optimizado
        res_greedy = solver.solve("greedy_fast")
        # 2. Matching Maximal
        res_matching = solver.solve("matching")

        # 3. Exacto ILP (hasta n=60)
        res_ilp = None
        if n <= 60:
            res_ilp = solver.solve("ilp", time_limit=30)

        # 4. Fuerza Bruta (hasta n=18)
        res_bf = None
        if n <= 18:
            res_bf = solver.solve("bruteforce")

        opt_size = res_ilp["size"] if res_ilp else (res_bf["size"] if res_bf else None)

        greedy_ratio = approximation_ratio(res_greedy["size"], opt_size) if opt_size else None
        matching_ratio = approximation_ratio(res_matching["size"], opt_size) if opt_size else None

        row = {
            "n": n,
            "edges": m,
            "greedy_size": res_greedy["size"],
            "greedy_time_ms": round(res_greedy["time_ms"], 4),
            "greedy_mem_kb": round(res_greedy["memory_peak_kb"], 2),
            "greedy_ratio": round(greedy_ratio, 3) if greedy_ratio else "",
            "matching_size": res_matching["size"],
            "matching_time_ms": round(res_matching["time_ms"], 4),
            "matching_mem_kb": round(res_matching["memory_peak_kb"], 2),
            "matching_ratio": round(matching_ratio, 3) if matching_ratio else "",
            "ilp_size": res_ilp["size"] if res_ilp else "",
            "ilp_time_ms": round(res_ilp["time_ms"], 4) if res_ilp else "",
            "bf_time_ms": round(res_bf["time_ms"], 4) if res_bf else "",
        }
        rows.append(row)

        print(
            f"n={n:>3} |E|={m:>4} | Greedy: {row['greedy_size']:>3} ({row['greedy_time_ms']:>6.2f}ms) | "
            f"Matching: {row['matching_size']:>3} ({row['matching_time_ms']:>6.2f}ms) | "
            f"ILP: {str(row['ilp_size']):>3} ({str(row['ilp_time_ms']):>6}ms)"
        )

    out_csv = RESULTS_DIR / "scalability_comparison.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"-> Guardado en: {out_csv}\n")
    return rows


def run_real_world_experiments():
    print("=" * 70)
    print(" EXPERIMENTO 2: EVALUACIÓN SOBRE REDES REALES DE INTERNET Y DIDÁCTICAS")
    print("=" * 70)

    datasets = [
        ("example_small", "data/instances/example_small.json", "json"),
        ("network_backbone_18", "data/instances/network_backbone_18.json", "json"),
        ("SNAP AS-733 Oregon", "data/instances/real/as20000102.txt", "txt"),
        ("SNAP CAIDA BGP Backbone", "data/instances/real/as-caida20071105.txt", "txt"),
    ]

    rows = []
    for label, path_str, kind in datasets:
        p = Path(path_str)
        if not p.exists():
            print(f"Archivo no encontrado, omitiendo: {path_str}")
            continue

        t0 = time.perf_counter()
        if kind == "json":
            g = Graph.from_json(p)
        else:
            g = Graph.from_edge_list(p)
        load_time = (time.perf_counter() - t0) * 1000.0

        n_v = g.num_vertices()
        n_e = g.num_edges()
        solver = VertexCoverSolver(g)

        # Greedy Optimizado
        res_greedy = solver.solve("greedy_fast")
        # Matching Maximal
        res_matching = solver.solve("matching")

        # ILP si es manejable
        res_ilp = None
        if n_v <= 50:
            res_ilp = solver.solve("ilp")

        greedy_pct = (res_greedy["size"] / n_v * 100.0) if n_v > 0 else 0.0
        matching_pct = (res_matching["size"] / n_v * 100.0) if n_v > 0 else 0.0

        ratio_m_g = res_matching["size"] / max(1, res_greedy["size"])

        row = {
            "dataset": label,
            "routers_V": n_v,
            "enlaces_E": n_e,
            "load_time_ms": round(load_time, 2),
            "greedy_ids": res_greedy["size"],
            "greedy_pct": round(greedy_pct, 2),
            "greedy_time_ms": round(res_greedy["time_ms"], 2),
            "greedy_mem_kb": round(res_greedy["memory_peak_kb"], 1),
            "matching_ids": res_matching["size"],
            "matching_pct": round(matching_pct, 2),
            "matching_time_ms": round(res_matching["time_ms"], 2),
            "matching_mem_kb": round(res_matching["memory_peak_kb"], 1),
            "ratio_matching_vs_greedy": round(ratio_m_g, 3),
            "ilp_optimo": res_ilp["size"] if res_ilp else "N/A (Gran Escala)",
        }
        rows.append(row)

        print(f"[{label}] |V|={n_v:,}, |E|={n_e:,}")
        print(f"   Greedy:   {res_greedy['size']:,} IDS ({greedy_pct:.2f}% de la red) en {res_greedy['time_ms']:.2f} ms")
        print(f"   Matching: {res_matching['size']:,} IDS ({matching_pct:.2f}% de la red) en {res_matching['time_ms']:.2f} ms")
        print(f"   Ratio Matching/Greedy: {ratio_m_g:.3f}x")
        print()

    out_csv = RESULTS_DIR / "real_networks_comparison.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"-> Guardado en: {out_csv}\n")
    return rows


def generate_charts(scal_rows, real_rows):
    print("=" * 70)
    print(" GENERACIÓN DE GRÁFICOS CIENTÍFICOS CON MATPLOTLIB")
    print("=" * 70)
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use("Agg")  # Sin requerir display gráfico interactivo
    except ImportError:
        print("Matplotlib no disponible para generar gráficos automáticos.")
        return

    # Gráfico 1: Tiempo vs N (Escalabilidad en escala logarítmica)
    fig, ax = plt.subplots(figsize=(8, 5))
    ns = [r["n"] for r in scal_rows]
    t_greedy = [r["greedy_time_ms"] for r in scal_rows]
    t_matching = [r["matching_time_ms"] for r in scal_rows]

    ax.plot(ns, t_greedy, marker="o", color="#1f77b4", label="Greedy Optimizado O((V+E)log V)", linewidth=2)
    ax.plot(ns, t_matching, marker="s", color="#2ca02c", label="Matching Maximal O(V+E)", linewidth=2)

    # Filtrar ILP donde esté disponible
    ilp_pts = [(r["n"], float(r["ilp_time_ms"])) for r in scal_rows if r["ilp_time_ms"] != ""]
    if ilp_pts:
        ax.plot([p[0] for p in ilp_pts], [p[1] for p in ilp_pts], marker="^", color="#d62728", linestyle="--", label="Exacto ILP / Branch & Bound", linewidth=2)

    bf_pts = [(r["n"], float(r["bf_time_ms"])) for r in scal_rows if r["bf_time_ms"] != ""]
    if bf_pts:
        ax.plot([p[0] for p in bf_pts], [p[1] for p in bf_pts], marker="x", color="#9467bd", linestyle=":", label="Fuerza Bruta O(2^V)", linewidth=2)

    ax.set_yscale("log")
    ax.set_xlabel("Número de Vértices (|V|)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Tiempo de Ejecución en CPU (ms, escala log)", fontsize=11, fontweight="bold")
    ax.set_title("Comparación de Escalabilidad Temporal: Algoritmos de Vertex Cover", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(fontsize=9)
    plt.tight_layout()
    chart1_path = RESULTS_DIR / "fig_scalability_time.png"
    plt.savefig(chart1_path, dpi=300)
    plt.close()
    print(f"-> Gráfico 1 guardado en: {chart1_path}")

    # Gráfico 2: Porcentaje de routers IDS en instancias didácticas vs reales
    fig, ax = plt.subplots(figsize=(9, 4.8))
    labels = [r["dataset"] for r in real_rows]
    g_pcts = [r["greedy_pct"] for r in real_rows]
    m_pcts = [r["matching_pct"] for r in real_rows]

    import numpy as np
    x = np.arange(len(labels))
    width = 0.35

    rects1 = ax.bar(x - width/2, g_pcts, width, label="Greedy Optimizado", color="#1f77b4")
    rects2 = ax.bar(x + width/2, m_pcts, width, label="Matching Maximal (2-Aprox)", color="#ff7f0e")

    ax.set_ylabel("% de Routers que Requieren IDS", fontsize=11, fontweight="bold")
    ax.set_title("Eficiencia de Ubicación de IDS en Redes Reales vs Sintéticas", fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, rotation=10)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

    plt.tight_layout()
    chart2_path = RESULTS_DIR / "fig_real_networks_ids.png"
    plt.savefig(chart2_path, dpi=300)
    plt.close()
    print(f"-> Gráfico 2 guardado en: {chart2_path}")


def main():
    scal_rows = run_scalability_experiments()
    real_rows = run_real_world_experiments()
    generate_charts(scal_rows, real_rows)
    print("=" * 70)
    print(" EXPERIMENTOS DE LA ENTREGA 2 COMPLETADOS EXITOSAMENTE")
    print("=" * 70)


if __name__ == "__main__":
    main()
