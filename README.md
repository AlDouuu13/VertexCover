# Vertex Cover IDS Placement

Ubicación óptima de sistemas de detección de intrusos (IDS) en una red, modelada
como el problema clásico de **Cobertura de Vértices (Vertex Cover)**.

> Proyecto semestral — Algoritmos Avanzados — UNSAAC
> Grupo 1 — Línea: Cobertura de vértices y comparación de estrategias de aproximación

## Problema

Cada enlace físico de una red debe tener al menos uno de sus dos extremos (routers)
monitoreado por un IDS/firewall. Se busca el conjunto mínimo de routers a monitorear
tal que **toda** conexión quede cubierta. Ver `docs/avance1.pdf` para la formulación
completa.

## Estado del proyecto

- [x] **Avance 1** — Formulación y delimitación del problema (`docs/avance1.pdf`)
- [x] **Avance 2** — Diseño algorítmico y plan de validación (`docs/avance2.pdf`)
- [x] **Avance 3** — Prototipo mínimo ejecutable (este repositorio)
- [ ] Entrega 2 — Integración completa, experimentos a mayor escala, análisis de complejidad empírico
- [ ] Entrega 3 — Sistema final, informe completo, defensa

Ver `docs/bitacora.md` para el registro de avance sesión a sesión.

## Estructura del repositorio

```
vertex-cover-ids/
├── src/
│   ├── graph.py        # Estructura de grafo (lista de adyacencia) + generadores + I/O
│   ├── solver.py        # VertexCoverSolver: greedy, matching maximal, exacto (fuerza bruta)
│   └── verify.py        # Validación de coberturas y cálculo de ratio de aproximación
├── tests/
│   ├── test_graph.py     # Pruebas de la estructura de grafo
│   └── test_solver.py    # Pruebas básicas, límite y adversarias de los algoritmos
├── data/instances/        # Instancias de ejemplo en formato JSON
├── experiments/
│   ├── compare.py        # Script de comparación empírica (tiempo, ratio)
│   └── results/           # Salidas de los experimentos (CSV)
├── docs/
│   ├── avance1.tex/.pdf
│   ├── avance2.tex/.pdf
│   ├── avance3.md
│   └── bitacora.md
├── demo.py                # Prototipo ejecutable (CLI) para la demostración
└── requirements.txt
```

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso rápido

```bash
# Ejecutar el prototipo sobre la instancia de ejemplo del Avance 1
python demo.py --instance data/instances/example_small.json --algorithm all

# Correr las pruebas
pytest tests/ -v

# Correr el experimento comparativo
python experiments/compare.py
```

## Algoritmos implementados

| Algoritmo | Archivo | Garantía | Complejidad |
|---|---|---|---|
| Greedy por grado | `src/solver.py::greedy_degree_vertex_cover` | Sin cota fija (heurística) | O(V·E) |
| Matching maximal (2-aprox) | `src/solver.py::maximal_matching_vertex_cover` | ≤ 2·óptimo | O(V+E) |
| Exacto (fuerza bruta) | `src/solver.py::exact_vertex_cover_bruteforce` | Óptimo | O(2^V · E), solo referencia en instancias pequeñas |

## Integrantes

| Nombre | Rol principal en esta fase |
|---|---|
| Integrante 1 | |
| Integrante 2 | |
| Integrante 3 | |
| Integrante 4 | |

## Licencia / uso académico

Proyecto desarrollado con fines educativos para la asignatura de Algoritmos Avanzados,
UNSAAC. No destinado a uso en producción.
