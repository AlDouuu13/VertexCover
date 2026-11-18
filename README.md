# Vertex Cover IDS Placement

Ubicación óptima de sistemas de detección de intrusos (IDS) en una red, modelada
como el problema clásico de **Cobertura de Vértices (Vertex Cover)**.

> **Proyecto Semestral — Algoritmos Avanzados — UNSAAC (2026-2)**  
> **Grupo 1 — Línea:** Cobertura de vértices y comparación de estrategias de aproximación  
> **Docente:** Héctor Eduardo Ugarte Rojas  
> **Atributo del Graduado:** AG_C06 – Aprendizaje a lo largo de la vida  

## Problema

Cada enlace físico de una red debe tener al menos uno de sus dos extremos (routers)
monitoreado por un IDS/firewall. Se busca el conjunto mínimo de routers a monitorear
tal que **toda** conexión quede cubierta ($u \in C \lor v \in C, \forall (u, v) \in E$).

## Estado del proyecto

- [x] **Avance 1** — Formulación y delimitación del problema (`docs/avance1.pdf`)
- [x] **Avance 2** — Diseño algorítmico y plan de validación (`docs/avance2.pdf`)
- [x] **Avance 3** — Prototipo mínimo ejecutable (`demo.py`)
- [x] **Entrega 2** — Implementación funcional completa, Greedy optimizado $O((V+E)\log V)$, solución exacta escalable ILP/Branch&Bound, integración de instancias reales masivas de Internet (Stanford SNAP), Interfaz Gráfica de Usuario (GUI) interactiva y 38 pruebas automatizadas.
- [ ] **Entrega 3** — Sistema final consolidado, informe final completo y defensa individual.

Ver `docs/bitacora.md` para el registro detallado de las 8 sesiones de aprendizaje autónomo.

## Estructura del repositorio

```
vertex-cover-ids/
├── src/
│   ├── graph.py        # Estructura Graph, generadores sintéticos, parseo SNAP e I/O
│   ├── solver.py       # VertexCoverSolver: Greedy optimizado, Matching maximal, Exacto ILP/B&B y Fuerza Bruta
│   ├── verify.py       # Validación formal de cobertura, estadísticas y ratios de aproximación
│   └── gui_app.py      # Interfaz Gráfica interactiva (Canvas con Zoom/Pan, multi-escala y threading)
├── tests/
│   ├── test_graph.py     # Pruebas unitarias de la estructura de grafo
│   ├── test_solver.py    # Pruebas de algoritmos (27 casos básicos, límite y adversarios)
│   └── test_entrega2.py  # 11 pruebas de Entrega 2 (ILP, Greedy fast, datasets reales SNAP y subgrafos)
├── data/instances/
│   ├── example_small.json        # Instancia didáctica (6 routers, Avance 1)
│   ├── network_backbone_18.json  # Red backbone sintética (18 routers, Avance 3)
│   └── real/                     # Datasets de gran escala de Internet (Stanford SNAP)
│       ├── as20000102.txt        # SNAP AS-733 Oregon (6,474 routers, 12,572 enlaces)
│       └── as-caida20071105.txt  # SNAP CAIDA BGP Backbone (26,475 routers, 53,381 enlaces)
├── experiments/
│   ├── compare.py              # Experimento comparativo preliminar (Entrega 1)
│   ├── compare_entrega2.py     # Batería experimental de escalabilidad y redes reales (Entrega 2)
│   └── results/                # Salidas CSV y gráficos científicos generados
├── docs/
│   ├── AA_2026_II_Caballero_Castilla_Llactahuamani_Morocco_Proyecto02.tex # Informe formal Entrega 2
│   ├── informe_entrega2.md     # Versión Markdown del informe técnico de Entrega 2
│   └── bitacora.md             # Bitácora de aprendizaje (Sesiones 1 a 8)
├── gui.py                      # Punto de entrada para la Interfaz Gráfica Interactiva
├── demo.py                     # CLI ejecutable con soporte de instancias reales y modo --gui
└── requirements.txt            # Dependencias del proyecto
```

## Instalación

```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

## Uso Rápido

### 1. Interfaz Gráfica Interactiva (GUI)
La interfaz gráfica permite cargar instancias sintéticas y masivas reales de internet, navegar interactivamente con zoom continuo (rueda de ratón) y desplazamiento (arrastre), inspeccionar routers con un clic y visualizar la comparativa multi-algoritmo sin bloqueos de pantalla:

```bash
python gui.py
# o alternativamente:
python demo.py --gui
```

### 2. Ejecutar la Suite de Pruebas Automatizadas (38 pruebas)
```bash
pytest tests/ -v
```

### 3. Ejecutar la Batería Experimental y Generar Gráficos
```bash
python experiments/compare_entrega2.py
```

### 4. Demostración CLI sobre Instancias Didácticas y Reales
```bash
# Instancia didáctica de 6 routers
python demo.py --instance data/instances/example_small.json --algorithm all

# Red Real de Internet Stanford SNAP (6,474 routers)
python demo.py --instance data/instances/real/as20000102.txt --algorithm all

# Red Masiva CAIDA BGP (26,475 routers)
python demo.py --instance data/instances/real/as-caida20071105.txt --algorithm greedy_fast
```

## Algoritmos Implementados

| Algoritmo | Implementación | Garantía | Complejidad Temporal | Complejidad Espacial |
|---|---|---|---|---|
| **Greedy por Grado Optimizado** | `src/solver.py::greedy_degree_vertex_cover_optimized` | Heurística voraz (supera al matching en redes reales) | $O((V+E)\log V)$ | $O(V+E)$ |
| **Matching Maximal** | `src/solver.py::maximal_matching_vertex_cover` | $\le 2 \times |C^*|$ (Garantía formal) | $O(V+E)$ | $O(V+E)$ |
| **Exacto ILP / Branch & Bound** | `src/solver.py::exact_vertex_cover_ilp` | Óptimo estricto ($|C^*|$) | Podado por cota inferior de matching | $O(V+E)$ |
| **Exacto Fuerza Bruta** | `src/solver.py::exact_vertex_cover_bruteforce` | Óptimo estricto ($|C^*|$) | $O(2^V \cdot E)$ (Solo $|V| \le 20$) | $O(V)$ |

## Integrantes del Grupo

| Integrante | Rol Principal |
|---|---|
| **Steffano Ricardo Caballero Zegarra** | Análisis de complejidad, integración de datasets reales Stanford SNAP y suite de pruebas |
| **Adriel Alfredo Llactahuamani Ayala** | Optimización de estructuras de datos (Heap O((V+E)log V)) y batería experimental |
| **Albert Erik Morocco Amanca**         | Diseño y desarrollo de la Interfaz Gráfica interactiva y soporte de escala masiva |
| **Diego Alonso Quispe Castilla**       | Formulación matemática, diseño de ILP y Branch & Bound con cotas de matching |

## Licencia / Uso Académico

Proyecto desarrollado con fines educativos para la asignatura de Algoritmos Avanzados,
Universidad Nacional de San Antonio Abad del Cusco (UNSAAC). No destinado a uso en producción comercial.
