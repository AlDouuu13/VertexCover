"""
gui_app.py
----------
Interfaz Gráfica de Usuario (GUI) interactiva para el sistema de optimización
de ubicación de Sistemas de Detección de Intrusos (IDS) mediante Cobertura
de Vértices (Vertex Cover).

Diseñada para soportar de manera fluida tanto instancias didácticas de prueba
como redes reales masivas de internet (ej. Stanford SNAP AS-733 y CAIDA BGP).

Características principales:
  1. Renderizado interactivo sobre Canvas con Zoom y Pan (arrastre) continuo.
  2. Soporte inteligente de escala:
     - Grafos pequeños: renderizado completo.
     - Redes grandes de internet: modo "Backbone Hubs" (subgrafo de routers principales),
       modo "Ego-Network" (vecindario local de router seleccionado), o métricas globales.
  3. Ejecución asíncrona (multithreading) para evitar bloqueos de la interfaz durante
     cálculos pesados.
  4. Comparativa multi-algoritmo (Greedy Optimizado, Matching Maximal, ILP con PuLP, Fuerza Bruta).
  5. Inspector interactivo de nodos al hacer clic y cálculo de métricas en tiempo real.
"""

from __future__ import annotations

import csv
import json
import math
import os
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .graph import Graph
from .solver import VertexCoverSolver
from .verify import is_vertex_cover, coverage_statistics


class InteractiveGraphCanvas(tk.Canvas):
    """
    Canvas de alto rendimiento para visualización y exploración de topologías de red.
    Soporta traslación (pan), escala (zoom), selección interactiva e inspección de routers.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#16161e", highlightthickness=0, **kwargs)
        self.node_positions: dict = {}  # {node: (x, y)} en coordenadas lógicas
        self.node_degrees: dict = {}
        self.cover_nodes: set = set()
        self.edges: list[tuple] = []
        self.selected_node = None
        self.hovered_node = None

        # Parámetros de transformación de vista
        self.scale_factor = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Enlazar eventos de interacción de ratón
        self.bind("<ButtonPress-1>", self._on_mouse_press)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<MouseWheel>", self._on_mouse_wheel)
        # Soporte para Linux/X11
        self.bind("<Button-4>", lambda event: self._zoom(1.15, event.x, event.y))
        self.bind("<Button-5>", lambda event: self._zoom(0.85, event.x, event.y))

        self.on_node_selected_callback = None

    def set_data(self, graph: Graph, cover: set | None = None, positions: dict | None = None):
        """Carga los datos del grafo y calcula o asigna coordenadas."""
        self.cover_nodes = set(cover) if cover else set()
        self.edges = graph.canonical_edges()
        self.node_degrees = {v: graph.degree(v) for v in graph.vertices}

        if positions:
            self.node_positions = dict(positions)
        else:
            self.node_positions = self._compute_layout(graph)

        self.selected_node = None
        self.hovered_node = None
        self.reset_view()

    def _compute_layout(self, graph: Graph) -> dict:
        """
        Calcula coordenadas (x, y) de los routers usando un layout de resortes
        o circular optimizado en Python puro para máxima portabilidad y velocidad.
        """
        nodes = sorted(graph.vertices, key=str)
        n = len(nodes)
        if n == 0:
            return {}
        if n == 1:
            return {nodes[0]: (0.0, 0.0)}

        # Para grafos medianos/grandes, intentar usar networkx si está disponible
        try:
            import networkx as nx
            G = nx.Graph()
            for v in nodes:
                G.add_node(v)
            for u, v in graph.canonical_edges():
                G.add_edge(u, v)

            if n <= 150:
                pos = nx.spring_layout(G, seed=42, iterations=50, k=2.0 / math.sqrt(n))
            else:
                pos = nx.spring_layout(G, seed=42, iterations=25, k=1.5 / math.sqrt(n))
            return {node: (float(coords[0]) * 350.0, float(coords[1]) * 350.0) for node, coords in pos.items()}
        except Exception:
            # Fallback robusto sin dependencias externas: Fruchterman-Reingold simplificado
            return self._fallback_spring_layout(nodes, graph.canonical_edges())

    def _fallback_spring_layout(self, nodes: list, edges: list[tuple], iterations: int = 40) -> dict:
        """Layout de resortes autónomo en Python puro para evitar dependencias."""
        n = len(nodes)
        node_idx = {node: i for i, node in enumerate(nodes)}
        # Posición inicial en círculo
        pos = {}
        for i, node in enumerate(nodes):
            angle = 2.0 * math.pi * i / n
            radius = 280.0
            pos[node] = [radius * math.cos(angle), radius * math.sin(angle)]

        if n > 120:
            return {k: (v[0], v[1]) for k, v in pos.items()}

        k_const = 300.0 / math.sqrt(max(1, n))
        temp = 80.0
        dt = temp / iterations

        for _ in range(iterations):
            disp = {node: [0.0, 0.0] for node in nodes}
            # Fuerzas repulsivas
            for i in range(n):
                u = nodes[i]
                for j in range(i + 1, n):
                    v = nodes[j]
                    dx = pos[u][0] - pos[v][0]
                    dy = pos[u][1] - pos[v][1]
                    dist = math.hypot(dx, dy) + 0.01
                    force = (k_const * k_const) / dist
                    fx = (dx / dist) * force
                    fy = (dy / dist) * force
                    disp[u][0] += fx
                    disp[u][1] += fy
                    disp[v][0] -= fx
                    disp[v][1] -= fy

            # Fuerzas atractivas por enlaces
            for u, v in edges:
                if u in pos and v in pos:
                    dx = pos[u][0] - pos[v][0]
                    dy = pos[u][1] - pos[v][1]
                    dist = math.hypot(dx, dy) + 0.01
                    force = (dist * dist) / k_const
                    fx = (dx / dist) * force
                    fy = (dy / dist) * force
                    disp[u][0] -= fx
                    disp[u][1] -= fy
                    disp[v][0] += fx
                    disp[v][1] += fy

            # Actualizar posiciones
            for node in nodes:
                d_len = math.hypot(disp[node][0], disp[node][1]) + 0.001
                step = min(d_len, temp)
                pos[node][0] += (disp[node][0] / d_len) * step
                pos[node][1] += (disp[node][1] / d_len) * step

            temp = max(1.0, temp - dt)

        return {k: (v[0], v[1]) for k, v in pos.items()}

    def reset_view(self):
        """Centra y escala el grafo para ajustarlo a las dimensiones del canvas."""
        w = max(400, self.winfo_width())
        h = max(300, self.winfo_height())
        if not self.node_positions:
            self.redraw()
            return

        xs = [coords[0] for coords in self.node_positions.values()]
        ys = [coords[1] for coords in self.node_positions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(20.0, max_x - min_x)
        span_y = max(20.0, max_y - min_y)

        margin = 60.0
        scale_x = (w - 2 * margin) / span_x
        scale_y = (h - 2 * margin) / span_y
        self.scale_factor = min(scale_x, scale_y, 2.5)

        mid_x = (min_x + max_x) / 2.0
        mid_y = (min_y + max_y) / 2.0
        self.offset_x = (w / 2.0) - (mid_x * self.scale_factor)
        self.offset_y = (h / 2.0) - (mid_y * self.scale_factor)

        self.redraw()

    def _world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        return (x * self.scale_factor + self.offset_x, y * self.scale_factor + self.offset_y)

    def _screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        return ((sx - self.offset_x) / self.scale_factor, (sy - self.offset_y) / self.scale_factor)

    def redraw(self):
        """Redibuja todos los elementos con estilo cyber-blue y estados de IDS."""
        self.delete("all")

        w = self.winfo_width()
        h = self.winfo_height()

        # Cuadrícula de fondo sutil
        grid_step = int(60 * self.scale_factor)
        if 20 <= grid_step <= 200:
            ox = int(self.offset_x % grid_step)
            oy = int(self.offset_y % grid_step)
            for x in range(ox, w, grid_step):
                self.create_line(x, 0, x, h, fill="#1a1c29", width=1)
            for y in range(oy, h, grid_step):
                self.create_line(0, y, w, y, fill="#1a1c29", width=1)

        if not self.node_positions:
            self.create_text(
                w / 2, h / 2,
                text="No hay grafo cargado para visualizar.",
                fill="#565f89", font=("Segoe UI", 12, "italic")
            )
            return

        # Dibujar aristas / enlaces de red
        for u, v in self.edges:
            if u in self.node_positions and v in self.node_positions:
                x1, y1 = self._world_to_screen(*self.node_positions[u])
                x2, y2 = self._world_to_screen(*self.node_positions[v])

                is_covered = (u in self.cover_nodes) or (v in self.cover_nodes)
                edge_color = "#3b4261" if is_covered else "#f7768e"
                edge_width = 1.8 if is_covered else 2.5
                self.create_line(x1, y1, x2, y2, fill=edge_color, width=edge_width)

        # Dibujar routers / vértices
        n_nodes = len(self.node_positions)
        show_labels = (n_nodes <= 80) or (self.scale_factor > 1.2)

        for node, coords in self.node_positions.items():
            sx, sy = self._world_to_screen(*coords)
            is_ids = node in self.cover_nodes
            is_selected = (node == self.selected_node)
            is_hovered = (node == self.hovered_node)
            deg = self.node_degrees.get(node, 0)

            # Radio adaptativo según grado e importancia
            base_r = 7.0 if n_nodes > 100 else 11.0
            r = base_r + min(6.0, math.sqrt(deg) * 1.2)
            if is_selected:
                r += 3.0

            # Selección de color
            if is_selected:
                fill_color = "#ff9e64"  # Naranja destacado
                outline_color = "#ffffff"
            elif is_hovered:
                fill_color = "#bb9af7"  # Púrpura hover
                outline_color = "#ffffff"
            elif is_ids:
                fill_color = "#9ece6a"  # Verde esmeralda IDS ACTIVO
                outline_color = "#10b981"
            else:
                fill_color = "#2ac3de"  # Cian router regular
                outline_color = "#1d3b53"

            # Círculo del nodo
            self.create_oval(
                sx - r, sy - r, sx + r, sy + r,
                fill=fill_color, outline=outline_color, width=2,
                tags=("node", str(node))
            )

            # Etiqueta del router
            if show_labels:
                lbl = str(node)
                if len(lbl) > 7:
                    lbl = lbl[:6] + "…"
                text_color = "#0f141c" if (is_ids or is_selected) else "#ffffff"
                self.create_text(
                    sx, sy,
                    text=lbl,
                    fill=text_color,
                    font=("Segoe UI", 8, "bold" if is_ids else "normal")
                )

        # Leyenda en esquina inferior
        self._draw_legend(w, h)

    def _draw_legend(self, w: int, h: int):
        lx, ly = 15, h - 85
        self.create_rectangle(lx, ly, lx + 230, ly + 72, fill="#1f2335", outline="#292e42", width=1)
        # Elemento 1: IDS Router
        self.create_oval(lx + 12, ly + 14, lx + 24, ly + 26, fill="#9ece6a", outline="#10b981", width=1.5)
        self.create_text(lx + 32, ly + 20, anchor="w", text="Router con IDS (Cobertura)", fill="#c0caf5", font=("Segoe UI", 8, "bold"))
        # Elemento 2: Router Regular
        self.create_oval(lx + 12, ly + 36, lx + 24, ly + 48, fill="#2ac3de", outline="#1d3b53", width=1.5)
        self.create_text(lx + 32, ly + 42, anchor="w", text="Router Regular (Monitoreado)", fill="#a9b1d6", font=("Segoe UI", 8))
        # Elemento 3: Enlace Protegido
        self.create_line(lx + 12, ly + 58, lx + 24, ly + 58, fill="#3b4261", width=2.5)
        self.create_text(lx + 32, ly + 58, anchor="w", text="Enlace físico cubierto", fill="#7aa2f7", font=("Segoe UI", 8))

    # ---------- Eventos de Navegación e Inspección ----------
    def _on_mouse_press(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._check_node_click(event.x, event.y)

    def _on_mouse_drag(self, event):
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        self.offset_x += dx
        self.offset_y += dy
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self.redraw()

    def _on_mouse_release(self, event):
        pass

    def _zoom(self, factor: float, center_x: float, center_y: float):
        new_scale = max(0.08, min(15.0, self.scale_factor * factor))
        if new_scale == self.scale_factor:
            return
        ratio = new_scale / self.scale_factor
        self.offset_x = center_x - ratio * (center_x - self.offset_x)
        self.offset_y = center_y - ratio * (center_y - self.offset_y)
        self.scale_factor = new_scale
        self.redraw()

    def _on_mouse_wheel(self, event):
        factor = 1.15 if event.delta > 0 else 0.85
        self._zoom(factor, event.x, event.y)

    def _on_mouse_move(self, event):
        node = self._find_node_at(event.x, event.y)
        if node != self.hovered_node:
            self.hovered_node = node
            self.redraw()

    def _find_node_at(self, sx: float, sy: float):
        for node, coords in self.node_positions.items():
            nx, ny = self._world_to_screen(*coords)
            r = 14.0
            if (sx - nx) ** 2 + (sy - ny) ** 2 <= r * r:
                return node
        return None

    def _check_node_click(self, sx: float, sy: float):
        clicked = self._find_node_at(sx, sy)
        if clicked is not None:
            self.selected_node = clicked
            self.redraw()
            if self.on_node_selected_callback:
                self.on_node_selected_callback(clicked)


class VertexCoverGUI:
    """Ventana principal del sistema de optimización de IDS y Vertex Cover."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Vertex Cover IDS Placement — Optimizador de Redes (Entrega 2)")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 700)
        self.root.configure(bg="#1a1b26")

        self.current_graph = Graph()
        self.current_graph_name = "Ninguna"
        self.active_cover = set()
        self.last_results: dict[str, dict] = {}
        self.is_busy = False

        self._configure_styles()
        self._build_layout()
        self._load_preset_list()

        # Cargar por defecto la instancia de ejemplo
        self.root.after(100, lambda: self._load_preset("example_small"))

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Configuración de paleta dark cyber
        style.configure(".", background="#1a1b26", foreground="#c0caf5", font=("Segoe UI", 9))
        style.configure("TFrame", background="#1a1b26")
        style.configure("Card.TFrame", background="#24283b", relief="flat")
        style.configure("Sidebar.TFrame", background="#1f2335")

        style.configure("TLabel", background="#1a1b26", foreground="#c0caf5")
        style.configure("CardTitle.TLabel", background="#24283b", foreground="#7aa2f7", font=("Segoe UI", 10, "bold"))
        style.configure("CardText.TLabel", background="#24283b", foreground="#a9b1d6", font=("Segoe UI", 9))
        style.configure("Header.TLabel", background="#1a1b26", foreground="#7dcfff", font=("Segoe UI", 14, "bold"))

        style.configure("TButton", background="#3b4261", foreground="#c0caf5", borderwidth=0, padding=6, font=("Segoe UI", 9, "bold"))
        style.map("TButton", background=[("active", "#7aa2f7"), ("disabled", "#292e42")], foreground=[("active", "#1a1b26"), ("disabled", "#565f89")])

        style.configure("Primary.TButton", background="#7aa2f7", foreground="#1a1b26", padding=7, font=("Segoe UI", 9, "bold"))
        style.map("Primary.TButton", background=[("active", "#2ac3de")])

        style.configure("Success.TButton", background="#9ece6a", foreground="#1a1b26", padding=7, font=("Segoe UI", 9, "bold"))
        style.map("Success.TButton", background=[("active", "#73daca")])

        style.configure("TCombobox", fieldbackground="#1f2335", background="#3b4261", foreground="#c0caf5")
        style.configure("TNotebook", background="#1a1b26", tabmargins=[4, 4, 4, 0])
        style.configure("TNotebook.Tab", background="#24283b", foreground="#a9b1d6", padding=[14, 6], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#7aa2f7")], foreground=[("selected", "#1a1b26")])

        style.configure("Treeview", background="#1f2335", foreground="#c0caf5", fieldbackground="#1f2335", rowheight=26)
        style.configure("Treeview.Heading", background="#292e42", foreground="#7aa2f7", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#3d59a1")])

    def _build_layout(self):
        # 1. Cabecera superior (Header & KPI cards)
        header_frame = ttk.Frame(self.root, padding=12)
        header_frame.pack(fill="x", side="top")

        title_lbl = ttk.Label(header_frame, text="🛡️ Vertex Cover IDS Placement", style="Header.TLabel")
        title_lbl.pack(side="left", padx=5)

        subtitle_lbl = ttk.Label(
            header_frame,
            text="Optimizador de Ubicación de Sistemas de Detección de Intrusos en Redes | Entrega 2",
            foreground="#565f89", font=("Segoe UI", 9)
        )
        subtitle_lbl.pack(side="left", padx=10, pady=(4, 0))

        # KPI Cards (Resumen rápido en la cabecera)
        kpi_container = ttk.Frame(header_frame)
        kpi_container.pack(side="right")

        self.kpi_nodes = self._create_kpi_card(kpi_container, "Routers (|V|)", "0")
        self.kpi_edges = self._create_kpi_card(kpi_container, "Enlaces (|E|)", "0")
        self.kpi_ids = self._create_kpi_card(kpi_container, "IDS Activos (|C|)", "0", highlight=True)
        self.kpi_time = self._create_kpi_card(kpi_container, "Tiempo (ms)", "0.0")

        # 2. Contenedor Principal (Panel Lateral + Área Central)
        main_container = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        main_container.pack(fill="both", expand=True)

        # Barra lateral izquierda (Controles)
        sidebar = ttk.Frame(main_container, width=320, style="Sidebar.TFrame")
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)

        self._build_sidebar(sidebar)

        # Área central (Notebook con Pestañas)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(side="right", fill="both", expand=True)

        # Tab 1: Topología de Red Interactiva
        tab_topology = ttk.Frame(self.notebook)
        self.notebook.add(tab_topology, text="🌐 Topología Interactiva")
        self._build_topology_tab(tab_topology)

        # Tab 2: Comparativa de Algoritmos
        tab_compare = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab_compare, text="⚖️ Comparativa de Algoritmos")
        self._build_compare_tab(tab_compare)

        # Tab 3: Métricas y Distribución
        tab_metrics = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(tab_metrics, text="📊 Análisis Estructural & Métricas")
        self._build_metrics_tab(tab_metrics)

        # 3. Barra de Estado Inferior
        self.status_bar = ttk.Frame(self.root, padding=(12, 4))
        self.status_bar.pack(fill="x", side="bottom")

        self.status_label = ttk.Label(self.status_bar, text="Listo.", foreground="#7aa2f7")
        self.status_label.pack(side="left")

        self.progress_bar = ttk.Progressbar(self.status_bar, mode="indeterminate", length=180)

    def _create_kpi_card(self, parent, title: str, value: str, highlight: bool = False):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(12, 4))
        card.pack(side="left", padx=4)
        t_lbl = ttk.Label(card, text=title, style="CardText.TLabel", font=("Segoe UI", 8))
        t_lbl.pack(anchor="w")
        v_color = "#9ece6a" if highlight else "#7dcfff"
        v_lbl = ttk.Label(card, text=value, foreground=v_color, background="#24283b", font=("Segoe UI", 12, "bold"))
        v_lbl.pack(anchor="w")
        return v_lbl

    def _build_sidebar(self, parent):
        scroll_canvas = tk.Canvas(parent, bg="#1f2335", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=scroll_canvas.yview)
        scroll_content = ttk.Frame(scroll_canvas, style="Sidebar.TFrame", padding=10)

        scroll_content.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.create_window((0, 0), window=scroll_content, anchor="nw", width=300)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Card 1: Cargar Instancia
        c1 = ttk.Frame(scroll_content, style="Card.TFrame", padding=10)
        c1.pack(fill="x", pady=6)
        ttk.Label(c1, text="📁 Cargar Instancia de Red", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))

        ttk.Label(c1, text="Instancias Preconfiguradas:", style="CardText.TLabel").pack(anchor="w")
        self.preset_combo = ttk.Combobox(c1, state="readonly")
        self.preset_combo.pack(fill="x", pady=(2, 6))
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_selected)

        btn_load_file = ttk.Button(c1, text="📂 Examinar Archivo (.json, .txt)...", command=self._open_file_dialog)
        btn_load_file.pack(fill="x", pady=2)

        # Card 2: Modo de Vista para Escala Real
        c2 = ttk.Frame(scroll_content, style="Card.TFrame", padding=10)
        c2.pack(fill="x", pady=6)
        ttk.Label(c2, text="🔍 Modo de Renderizado Visual", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Label(
            c2,
            text="Permite explorar redes gigantescas sin congelar la interfaz:",
            style="CardText.TLabel", wraplength=270
        ).pack(anchor="w", pady=(0, 6))

        self.view_mode_var = tk.StringVar(value="hubs")
        r_hubs = ttk.Radiobutton(c2, text="Backbone Hubs (Top N Routers)", value="hubs", variable=self.view_mode_var, command=self._update_graph_view)
        r_hubs.pack(anchor="w", pady=2)
        r_ego = ttk.Radiobutton(c2, text="Vecindario / Ego-Net (Router Seleccionado)", value="ego", variable=self.view_mode_var, command=self._update_graph_view)
        r_ego.pack(anchor="w", pady=2)
        r_full = ttk.Radiobutton(c2, text="Grafo Completo (Pequeño/Mediano)", value="full", variable=self.view_mode_var, command=self._update_graph_view)
        r_full.pack(anchor="w", pady=2)

        self.hubs_scale_frame = ttk.Frame(c2, style="Card.TFrame")
        self.hubs_scale_frame.pack(fill="x", pady=(6, 0))
        self.hubs_count_lbl = ttk.Label(self.hubs_scale_frame, text="Hubs visibles: 60 routers", style="CardText.TLabel")
        self.hubs_count_lbl.pack(anchor="w")
        self.hubs_slider = ttk.Scale(self.hubs_scale_frame, from_=15, to_=250, value=60, command=self._on_hubs_slider_change)
        self.hubs_slider.pack(fill="x")

        # Card 3: Algoritmos de Cobertura
        c3 = ttk.Frame(scroll_content, style="Card.TFrame", padding=10)
        c3.pack(fill="x", pady=6)
        ttk.Label(c3, text="⚡ Ejecución de Algoritmos", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))

        btn_greedy = ttk.Button(c3, text="▶ Greedy por Grado (Optimizado)", style="Primary.TButton", command=lambda: self._run_solver("greedy_fast"))
        btn_greedy.pack(fill="x", pady=3)

        btn_matching = ttk.Button(c3, text="▶ 2-Aprox. Matching Maximal", style="Primary.TButton", command=lambda: self._run_solver("matching"))
        btn_matching.pack(fill="x", pady=3)

        self.btn_ilp = ttk.Button(c3, text="▶ Exacto ILP (PuLP / CBC)", command=lambda: self._run_solver("ilp"))
        self.btn_ilp.pack(fill="x", pady=3)

        self.btn_bruteforce = ttk.Button(c3, text="▶ Exacto Fuerza Bruta (|V|≤20)", command=lambda: self._run_solver("bruteforce"))
        self.btn_bruteforce.pack(fill="x", pady=3)

        btn_all = ttk.Button(c3, text="⚖️ Comparar Todos los Algoritmos", style="Success.TButton", command=self._run_all_comparison)
        btn_all.pack(fill="x", pady=(8, 3))

        # Card 4: Inspector de Router
        c4 = ttk.Frame(scroll_content, style="Card.TFrame", padding=10)
        c4.pack(fill="x", pady=6)
        ttk.Label(c4, text="🔎 Inspector de Router", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 4))
        self.inspector_label = ttk.Label(
            c4,
            text="Haga clic en cualquier router del canvas para inspeccionar sus conexiones y estado IDS.",
            style="CardText.TLabel", wraplength=270
        )
        self.inspector_label.pack(anchor="w")

        # Card 5: Exportación
        c5 = ttk.Frame(scroll_content, style="Card.TFrame", padding=10)
        c5.pack(fill="x", pady=6)
        ttk.Label(c5, text="💾 Exportar Resultados", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 4))

        btn_exp_json = ttk.Button(c5, text="Exportar Solución (.json)", command=self._export_solution_json)
        btn_exp_json.pack(fill="x", pady=2)
        btn_exp_csv = ttk.Button(c5, text="Exportar Comparativa (.csv)", command=self._export_comparison_csv)
        btn_exp_csv.pack(fill="x", pady=2)

    def _build_topology_tab(self, parent):
        # Canvas interactivo
        self.canvas = InteractiveGraphCanvas(parent)
        self.canvas.on_node_selected_callback = self._on_node_inspected

        # Barra superior con controles de vista
        top_ctrl = ttk.Frame(parent, padding=(8, 6))
        top_ctrl.pack(fill="x", side="top")

        ttk.Button(top_ctrl, text="🔍+ Acercar", width=12, command=lambda: self.canvas._zoom(1.25, self.canvas.winfo_width()/2, self.canvas.winfo_height()/2)).pack(side="left", padx=2)
        ttk.Button(top_ctrl, text="🔍- Alejar", width=12, command=lambda: self.canvas._zoom(0.8, self.canvas.winfo_width()/2, self.canvas.winfo_height()/2)).pack(side="left", padx=2)
        ttk.Button(top_ctrl, text="🎯 Centrar Vista", width=14, command=lambda: self.canvas.reset_view()).pack(side="left", padx=2)

        self.view_info_lbl = ttk.Label(top_ctrl, text="Visualizando: -", foreground="#7aa2f7")
        self.view_info_lbl.pack(side="right", padx=10)

        self.canvas.pack(fill="both", expand=True)

    def _build_compare_tab(self, parent):
        ttk.Label(
            parent,
            text="Tabla Comparativa de Estrategias de Cobertura sobre la Red Activa",
            style="Header.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        columns = ("alg", "size", "pct", "time", "mem", "valid", "ratio")
        self.compare_tree = ttk.Treeview(parent, columns=columns, show="headings", height=10)

        self.compare_tree.heading("alg", text="Algoritmo / Estrategia")
        self.compare_tree.heading("size", text="Routers IDS (|C|)")
        self.compare_tree.heading("pct", text="% Red")
        self.compare_tree.heading("time", text="Tiempo CPU (ms)")
        self.compare_tree.heading("mem", text="Memoria Pico (KB)")
        self.compare_tree.heading("valid", text="100% Enlaces Cubiertos")
        self.compare_tree.heading("ratio", text="Ratio vs Óptimo")

        self.compare_tree.column("alg", width=220, anchor="w")
        self.compare_tree.column("size", width=120, anchor="center")
        self.compare_tree.column("pct", width=100, anchor="center")
        self.compare_tree.column("time", width=130, anchor="center")
        self.compare_tree.column("mem", width=130, anchor="center")
        self.compare_tree.column("valid", width=160, anchor="center")
        self.compare_tree.column("ratio", width=120, anchor="center")

        self.compare_tree.pack(fill="x", pady=6)

        # Gráfico comparativo de barras simple dibujado en Canvas
        ttk.Label(parent, text="Comparativa Visual de Cardinalidad (|C|):", style="CardTitle.TLabel").pack(anchor="w", pady=(12, 4))
        self.bar_canvas = tk.Canvas(parent, height=180, bg="#16161e", highlightthickness=0)
        self.bar_canvas.pack(fill="both", expand=True, pady=6)

    def _build_metrics_tab(self, parent):
        ttk.Label(
            parent,
            text="Métricas Estructurales de la Red y Análisis de Eficiencia",
            style="Header.TLabel"
        ).pack(anchor="w", pady=(0, 8))

        self.metrics_text = tk.Text(parent, bg="#16161e", fg="#c0caf5", font=("Consolas", 10), relief="flat", padx=12, pady=12)
        self.metrics_text.pack(fill="both", expand=True)

    # ---------- Gestión de Instancias ----------
    def _load_preset_list(self):
        presets = [
            ("example_small", "Mini-red didáctica (6 routers, Avance 1)"),
            ("network_backbone_18", "Red Backbone Barabási-Albert (18 routers, Avance 3)"),
            ("as_oregon_real", "Internet Real: SNAP AS-733 Oregon (6,474 routers)"),
            ("as_caida_real", "Internet Real: SNAP CAIDA BGP Core (26,475 routers)"),
        ]
        self.preset_map = {p[1]: p[0] for p in presets}
        self.preset_combo["values"] = [p[1] for p in presets]
        self.preset_combo.current(0)

    def _on_preset_selected(self, event):
        val = self.preset_combo.get()
        key = self.preset_map.get(val)
        if key:
            self._load_preset(key)

    def _load_preset(self, key: str):
        self._set_status(f"Cargando instancia '{key}'...", busy=True)
        threading.Thread(target=self._worker_load_preset, args=(key,), daemon=True).start()

    def _worker_load_preset(self, key: str):
        try:
            if key == "example_small":
                p = Path("data/instances/example_small.json")
                g = Graph.from_json(p)
                name = "example_small (6 routers)"
            elif key == "network_backbone_18":
                p = Path("data/instances/network_backbone_18.json")
                g = Graph.from_json(p)
                name = "network_backbone_18 (18 routers)"
            elif key == "as_oregon_real":
                p = Path("data/instances/real/as20000102.txt")
                if not p.exists():
                    p = Path("data/instances/real/as20000102.txt.gz")
                g = Graph.from_edge_list(p)
                name = "SNAP AS-733 Oregon (6,474 routers)"
            elif key == "as_caida_real":
                p = Path("data/instances/real/as-caida20071105.txt")
                g = Graph.from_edge_list(p)
                name = "SNAP CAIDA BGP (26,475 routers)"
            else:
                return

            self.root.after(0, lambda: self._apply_loaded_graph(g, name))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error al cargar", f"No se pudo cargar la instancia: {e}"))
            self.root.after(0, lambda: self._set_status("Error al cargar instancia."))

    def _open_file_dialog(self):
        fpath = filedialog.askopenfilename(
            title="Seleccionar archivo de red",
            filetypes=[("Archivos soportados", "*.json *.txt *.edgelist"), ("JSON", "*.json"), ("Texto / Edgelist", "*.txt *.edgelist"), ("Todos", "*.*")]
        )
        if fpath:
            self._set_status(f"Cargando archivo: {os.path.basename(fpath)}...", busy=True)
            threading.Thread(target=self._worker_load_custom, args=(fpath,), daemon=True).start()

    def _worker_load_custom(self, fpath: str):
        try:
            p = Path(fpath)
            if p.suffix.lower() == ".json":
                g = Graph.from_json(p)
            else:
                g = Graph.from_edge_list(p)
            name = p.stem
            self.root.after(0, lambda: self._apply_loaded_graph(g, name))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{e}"))
            self.root.after(0, lambda: self._set_status("Error de carga."))

    def _apply_loaded_graph(self, g: Graph, name: str):
        self.current_graph = g
        self.current_graph_name = name
        self.active_cover = set()
        self.last_results.clear()

        n_v = g.num_vertices()
        n_e = g.num_edges()

        self.kpi_nodes.config(text=f"{n_v:,}")
        self.kpi_edges.config(text=f"{n_e:,}")
        self.kpi_ids.config(text="0")
        self.kpi_time.config(text="0.0")

        # Configuración inteligente de controles según tamaño
        if n_v > 500:
            self.view_mode_var.set("hubs")
            self.btn_ilp.config(state="disabled")
            self.btn_bruteforce.config(state="disabled")
        else:
            self.view_mode_var.set("full")
            self.btn_ilp.config(state="normal")
            if n_v <= 20:
                self.btn_bruteforce.config(state="normal")
            else:
                self.btn_bruteforce.config(state="disabled")

        self._update_graph_view()
        self._update_metrics_tab()
        self._clear_compare_tab()
        self._set_status(f"Instancia '{name}' cargada exitosamente (|V|={n_v:,}, |E|={n_e:,}).")

    def _on_hubs_slider_change(self, val):
        count = int(float(val))
        self.hubs_count_lbl.config(text=f"Hubs visibles: {count} routers")
        if self.view_mode_var.get() == "hubs":
            self._update_graph_view()

    def _update_graph_view(self):
        """Actualiza el subgrafo a mostrar en el canvas según el modo seleccionado."""
        g = self.current_graph
        if g.num_vertices() == 0:
            self.canvas.set_data(Graph())
            return

        mode = self.view_mode_var.get()
        if mode == "full":
            if g.num_vertices() > 800:
                messagebox.showwarning(
                    "Grafo muy grande",
                    f"El grafo actual tiene {g.num_vertices():,} routers. Renderizarlo completo puede ralentizar la pantalla. Se recomienda usar 'Backbone Hubs'."
                )
            sub_g = g
            info_text = f"Grafo Completo ({sub_g.num_vertices():,} routers, {sub_g.num_edges():,} enlaces)"
        elif mode == "ego":
            center = self.canvas.selected_node
            if center is None or center not in g.vertices:
                # Tomar el router de mayor grado como predeterminado
                center = max(g.vertices, key=lambda v: g.degree(v))
            sub_g = g.ego_subgraph(center, radius=1)
            info_text = f"Vecindario Local de Router {center} ({sub_g.num_vertices()} routers, {sub_g.num_edges()} enlaces)"
        else:  # "hubs"
            top_k = int(self.hubs_slider.get())
            sub_g = g.top_degree_subgraph(top_k=top_k)
            info_text = f"Backbone Hubs (Top {sub_g.num_vertices()} routers por conectividad, {sub_g.num_edges()} enlaces)"

        self.view_info_lbl.config(text=info_text)
        sub_cover = self.active_cover.intersection(sub_g.vertices) if self.active_cover else set()
        self.canvas.set_data(sub_g, cover=sub_cover)

    # ---------- Ejecución Asíncrona de Algoritmos ----------
    def _run_solver(self, algorithm: str):
        if self.is_busy or self.current_graph.num_vertices() == 0:
            return
        alg_names = {
            "greedy_fast": "Greedy Optimizado O((V+E) log V)",
            "matching": "2-Aproximación por Matching Maximal O(V+E)",
            "ilp": "Exacto Óptimo ILP (PuLP Branch & Bound)",
            "bruteforce": "Exacto por Fuerza Bruta O(2^V)",
        }
        self._set_status(f"Ejecutando {alg_names.get(algorithm, algorithm)}...", busy=True)
        threading.Thread(target=self._worker_run_solver, args=(algorithm,), daemon=True).start()

    def _worker_run_solver(self, algorithm: str):
        try:
            solver = VertexCoverSolver(self.current_graph)
            res = solver.solve(algorithm=algorithm, time_limit=30, max_vertices=20)
            self.root.after(0, lambda: self._apply_solver_result(res))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error en Algoritmo", str(e)))
            self.root.after(0, lambda: self._set_status("Error en ejecución."))

    def _apply_solver_result(self, res: dict):
        alg = res["algorithm"]
        cover = res["cover"]
        self.active_cover = cover
        self.last_results[alg] = res

        n_v = self.current_graph.num_vertices()
        c_size = len(cover)
        pct = (c_size / n_v * 100.0) if n_v > 0 else 0.0

        self.kpi_ids.config(text=f"{c_size:,} ({pct:.1f}%)")
        self.kpi_time.config(text=f"{res['time_ms']:.2f}")

        # Actualizar visualización
        self._update_graph_view()
        self._update_compare_tab()
        self._update_metrics_tab()

        self._set_status(
            f"Listo: {alg} finalizó en {res['time_ms']:.2f} ms con |C|={c_size:,} routers ({pct:.1f}% de red). Válido: {res['is_valid']}."
        )

    def _run_all_comparison(self):
        if self.is_busy or self.current_graph.num_vertices() == 0:
            return
        self._set_status("Ejecutando batería completa de algoritmos...", busy=True)
        threading.Thread(target=self._worker_run_all, daemon=True).start()

    def _worker_run_all(self):
        try:
            solver = VertexCoverSolver(self.current_graph)
            n_v = self.current_graph.num_vertices()
            results = {}

            # 1. Greedy Optimizado
            results["greedy_fast"] = solver.solve("greedy_fast")

            # 2. Matching Maximal
            results["matching"] = solver.solve("matching")

            # 3. ILP (si |V| <= 500)
            if n_v <= 500:
                try:
                    results["ilp"] = solver.solve("ilp", time_limit=25)
                except Exception:
                    pass

            # 4. Fuerza Bruta (si |V| <= 20)
            if n_v <= 20:
                try:
                    results["bruteforce"] = solver.solve("bruteforce")
                except Exception:
                    pass

            self.root.after(0, lambda: self._apply_all_results(results))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, lambda: self._set_status("Error en comparativa."))

    def _apply_all_results(self, results: dict):
        self.last_results.update(results)
        # Mostrar por defecto la solución del greedy
        if "greedy_fast" in results:
            self.active_cover = results["greedy_fast"]["cover"]
            c_size = len(self.active_cover)
            n_v = self.current_graph.num_vertices()
            pct = (c_size / n_v * 100.0) if n_v > 0 else 0.0
            self.kpi_ids.config(text=f"{c_size:,} ({pct:.1f}%)")
            self.kpi_time.config(text=f"{results['greedy_fast']['time_ms']:.2f}")

        self._update_graph_view()
        self._update_compare_tab()
        self._update_metrics_tab()
        self.notebook.select(1)  # Cambiar a la pestaña de comparativa
        self._set_status("Comparativa multi-algoritmo completada con éxito.")

    # ---------- Pestañas de Resultados y Gráficos ----------
    def _clear_compare_tab(self):
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)
        self.bar_canvas.delete("all")

    def _update_compare_tab(self):
        self._clear_compare_tab()
        if not self.last_results:
            return

        # Determinar óptimo de referencia si existe
        opt_size = None
        if "ilp" in self.last_results:
            opt_size = self.last_results["ilp"]["size"]
        elif "bruteforce" in self.last_results:
            opt_size = self.last_results["bruteforce"]["size"]

        n_v = self.current_graph.num_vertices()
        display_names = {
            "greedy_fast": "Greedy Optimizado (Heap O((V+E)logV))",
            "matching": "Matching Maximal (2-Aprox O(V+E))",
            "ilp": "Exacto ILP (PuLP / Branch&Bound)",
            "bruteforce": "Exacto Fuerza Bruta (O(2^V))",
        }

        sizes = []
        labels = []
        colors = []

        for alg, res in self.last_results.items():
            name = display_names.get(alg, alg)
            size = res["size"]
            pct = f"{(size / n_v * 100.0):.1f}%" if n_v > 0 else "-"
            t_ms = f"{res['time_ms']:.2f} ms"
            mem = f"{res['memory_peak_kb']:.1f} KB"
            val = "✅ SÍ (100%)" if res["is_valid"] else "❌ NO"

            if opt_size and opt_size > 0:
                ratio = f"{(size / opt_size):.2f}x"
            else:
                ratio = "Referencia" if alg in ("ilp", "bruteforce") else "≤ 2.0x (teórico)"

            self.compare_tree.insert("", "end", values=(name, f"{size:,}", pct, t_ms, mem, val, ratio))

            sizes.append(size)
            labels.append(alg)
            if alg == "greedy_fast":
                colors.append("#7aa2f7")
            elif alg == "matching":
                colors.append("#bb9af7")
            else:
                colors.append("#9ece6a")

        self._draw_bar_chart(sizes, labels, colors)

    def _draw_bar_chart(self, values: list[int], labels: list[str], colors: list[str]):
        """Dibuja barras comparativas directas en el bar_canvas."""
        self.bar_canvas.delete("all")
        if not values:
            return

        w = max(400, self.bar_canvas.winfo_width())
        h = max(150, self.bar_canvas.winfo_height())
        max_val = max(values) if max(values) > 0 else 1

        n_bars = len(values)
        bar_w = min(80.0, (w - 120.0) / (n_bars * 1.6))
        gap = bar_w * 0.6
        start_x = 60.0

        for i, (val, lbl, col) in enumerate(zip(values, labels, colors)):
            bx = start_x + i * (bar_w + gap)
            bar_h = (val / max_val) * (h - 70.0)
            by1 = h - 35.0
            by0 = by1 - bar_h

            self.bar_canvas.create_rectangle(bx, by0, bx + bar_w, by1, fill=col, outline="")
            self.bar_canvas.create_text(bx + bar_w / 2, by0 - 10, text=f"{val:,}", fill="#c0caf5", font=("Segoe UI", 9, "bold"))
            self.bar_canvas.create_text(bx + bar_w / 2, by1 + 15, text=lbl, fill="#a9b1d6", font=("Segoe UI", 8))

    def _update_metrics_tab(self):
        g = self.current_graph
        n_v = g.num_vertices()
        n_e = g.num_edges()
        if n_v == 0:
            self.metrics_text.delete("1.0", "end")
            return

        deg_dist = [g.degree(v) for v in g.vertices]
        avg_deg = sum(deg_dist) / max(1, n_v)
        max_deg = max(deg_dist) if deg_dist else 0
        min_deg = min(deg_dist) if deg_dist else 0
        density = g.density()

        top_hubs = sorted(g.vertices, key=lambda v: g.degree(v), reverse=True)[:8]
        top_hubs_str = ", ".join(f"Router {v} (grado={g.degree(v)})" for v in top_hubs)

        report = []
        report.append("=" * 70)
        report.append(f" REPORTE DE ANÁLISIS ESTRUCTURAL DE RED: {self.current_graph_name}")
        report.append("=" * 70)
        report.append(f"• Total de Routers (|V|):            {n_v:,}")
        report.append(f"• Total de Enlaces de Red (|E|):      {n_e:,}")
        report.append(f"• Grado Promedio de Conexión:       {avg_deg:.2f} enlaces/router")
        report.append(f"• Grado Máximo (Hub Principal):     {max_deg} enlaces")
        report.append(f"• Grado Mínimo:                     {min_deg} enlaces")
        report.append(f"• Densidad de Topología:            {density:.6f} ({'Dispersa / Backbone Real' if density < 0.05 else 'Densa'})")
        report.append("")
        report.append("• Routers Concentradores (Hubs Críticos):")
        report.append(f"  {top_hubs_str}")
        report.append("")

        if self.active_cover:
            stats = coverage_statistics(g, self.active_cover)
            report.append("-" * 70)
            report.append(" COBERTURA IDS ACTIVA Y PROTECCIÓN DE ENLACES")
            report.append("-" * 70)
            report.append(f"• Routers con IDS Instalado (|C|):    {stats['cover_size']:,}")
            report.append(f"• Porcentaje de Red Protegida:      {stats['vertex_coverage_fraction']*100.0:.2f}% de la infraestructura")
            report.append(f"• Enlaces Físicos Monitoreados:     {stats['edge_coverage_pct']:.2f}%")
            report.append(f"• Validación Formal de Cobertura:   {'100% CUBIERTO (VÁLIDO)' if stats['is_valid'] else 'INCOMPLETO'}")
            report.append(f"• Reducción de Costo vs Full Mon.:  {100.0 - stats['vertex_coverage_fraction']*100.0:.2f}% de routers ahorrados")

        self.metrics_text.delete("1.0", "end")
        self.metrics_text.insert("1.0", "\n".join(report))

    def _on_node_inspected(self, node):
        g = self.current_graph
        if node not in g.vertices:
            return
        deg = g.degree(node)
        is_ids = node in self.active_cover
        neighbors = sorted(list(g.neighbors(node)), key=str)
        neigh_str = ", ".join(map(str, neighbors[:8]))
        if len(neighbors) > 8:
            neigh_str += f" ... (+{len(neighbors)-8} más)"

        info = (
            f"Router Seleccionado: {node}\n"
            f"• Grado (Enlaces directos): {deg}\n"
            f"• Estado IDS: {'🛡️ IDS INSTALADO' if is_ids else 'Monitoreado por router adyacente'}\n"
            f"• Routers Vecinos: {neigh_str}"
        )
        self.inspector_label.config(text=info)

    # ---------- Exportación ----------
    def _export_solution_json(self):
        if not self.active_cover:
            messagebox.showinfo("Exportar", "No hay una solución calculada para exportar.")
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if fpath:
            payload = {
                "instance": self.current_graph_name,
                "num_vertices": self.current_graph.num_vertices(),
                "num_edges": self.current_graph.num_edges(),
                "cover_size": len(self.active_cover),
                "cover_routers": sorted(list(self.active_cover), key=str),
            }
            Path(fpath).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            messagebox.showinfo("Exportado", f"Solución guardada en:\n{fpath}")

    def _export_comparison_csv(self):
        if not self.last_results:
            messagebox.showinfo("Exportar", "No hay resultados comparativos calculados.")
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if fpath:
            with open(fpath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["instancia", "algoritmo", "routers_ids", "tiempo_ms", "memoria_kb", "valido"])
                for alg, res in self.last_results.items():
                    writer.writerow([self.current_graph_name, alg, res["size"], f"{res['time_ms']:.2f}", f"{res['memory_peak_kb']:.1f}", res["is_valid"]])
            messagebox.showinfo("Exportado", f"Tabla guardada en:\n{fpath}")

    def _set_status(self, text: str, busy: bool = False):
        self.status_label.config(text=text)
        self.is_busy = busy
        if busy:
            self.progress_bar.pack(side="right", padx=10)
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()


def launch_gui():
    root = tk.Tk()
    app = VertexCoverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
