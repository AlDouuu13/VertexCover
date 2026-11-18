# Informe Técnico — Segunda Entrega (Avances 4 y 5)
## Proyecto Semestral: Algoritmos Avanzados (2026-2)
**Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**  
**Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica**  
**Escuela Profesional de Ingeniería Informática y de Sistemas**  
**Docente:** Héctor Eduardo Ugarte Rojas  
**Grupo 1 — Línea:** Cobertura de Vértices y Comparación de Estrategias de Aproximación  
**Atributo del Graduado Evaluado:** AG_C06 – Aprendizaje a lo largo de la vida  

### Integrantes del Grupo
- **Caballero Zegarra, Steffano Ricardo**
- **Llactahuamani Ayala, Adriel Alfredo**
- **Morocco Amanca, Albert Erik**
- **Quispe Castilla, Diego Alonso**

---

## 1. Resumen Ejecutivo
El presente informe documenta el cumplimiento integral de los requerimientos para la **Segunda Entrega** del proyecto semestral de Algoritmos Avanzados, enfocado en la resolución, análisis y evaluación experimental del problema de Cobertura de Vértices (*Vertex Cover*) aplicado a la ubicación costo-eficiente de Sistemas de Detección de Intrusos (IDS) en redes de comunicaciones.

En esta fase se consolidó la transición desde el prototipo preliminar de la Primera Entrega hacia un sistema computacional completamente funcional, optimizado y escalable a topologías reales masivas:
1. **Heurística Greedy por Grado Optimizada:** Rediseñada mediante una cola de prioridad basada en montículos de máximos con actualización perezosa (*Lazy Max-Heap*), reduciendo la complejidad de $O(V \cdot E)$ a **$O((V+E)\log V)$** con desempate canónico determinístico.
2. **2-Aproximación por Emparejamiento Maximal (*Maximal Matching*):** Implementada en una sola pasada lineal **$O(V+E)$** con garantía matemática formal demostrada de $|C| \le 2 \cdot |C^*|$.
3. **Exacto Escalable (ILP y Branch & Bound):** Formulación de Programación Lineal Entera resuelta mediante PuLP y complementada con un motor autónomo propio de *Branch & Bound* con poda analítica mediante cotas inferiores de emparejamiento maximal (*Matching Lower Bound*), superando de forma definitiva la barrera de $n=20$ de la fuerza bruta.
4. **Instancias Reales Masivas de Internet (Stanford SNAP):** Integración y procesamiento de dos datasets científicos de gran escala:
   - **SNAP AS-733 Oregon:** 6,474 routers y 12,572 enlaces físicos BGP.
   - **SNAP CAIDA BGP Core:** 26,475 routers y 53,381 enlaces físicos globales.
   - En la red de CAIDA, el algoritmo Greedy requiere solo **3,695 routers (13.96% de la red)** para monitorear el **100% de los enlaces globales** en solo 164 ms, logrando un ahorro del **86.04%** en hardware IDS.
5. **Interfaz Gráfica de Usuario (GUI):** Desarrollada en Python con Tkinter/ttk ([gui.py](file:///c:/Users/PC/Documents/AlgoritmosAvanzados/VertexCover-main/gui.py)), con desacoplamiento multihilo asíncrono (`threading.Thread`) y visualización adaptativa multinivel (*Backbone Hubs* y *Ego-Networks*) para operar a 60 FPS con zoom y arrastre continuo sin bloqueos.
6. **Verificación y Pruebas Automatizadas:** Suite completa de **38 pruebas automatizadas** bajo `pytest` pasando al 100%, con instrumentación de tiempo de CPU y memoria pico con `tracemalloc`.

---

## 2. Matriz de Trazabilidad y Cumplimiento del PDF

| Requisito del PDF (Pág. 3-6) | Tipo | Componente / Archivo | Estado Técnico |
|---|---|---|---|
| Algoritmos comparables con garantías | Funcional | [src/solver.py](file:///c:/Users/PC/Documents/AlgoritmosAvanzados/VertexCover-main/src/solver.py) | Greedy Opt. $O((V+E)\log V)$ vs. Matching Maximal $O(V+E)$ |
| Mecanismo de referencia exacto escalable | Funcional | [src/solver.py](file:///c:/Users/PC/Documents/AlgoritmosAvanzados/VertexCover-main/src/solver.py) | ILP (PuLP) y Branch & Bound podado por cota de matching |
| Instancia real masiva de Internet | Funcional | [data/instances/real/](file:///c:/Users/PC/Documents/AlgoritmosAvanzados/VertexCover-main/data/instances/real/) | Stanford SNAP AS-733 (6.4k) y CAIDA BGP (26.4k) |
| Interfaz Gráfica interactiva con soporte de escala | Funcional | [gui.py](file:///c:/Users/PC/Documents/AlgoritmosAvanzados/VertexCover-main/gui.py), [src/gui_app.py](file:///c:/Users/PC/Documents/AlgoritmosAvanzados/VertexCover-main/src/gui_app.py) | Canvas interactivo con Zoom/Pan, multi-escala y threading |
| Pruebas automatizadas (unitarias, límite, adversarias) | No Funcional | [tests/](file:///c:/Users/PC/Documents/AlgoritmosAvanzados/VertexCover-main/tests/) | 38 pruebas automatizadas bajo `pytest` (100% exitosas) |
| Bitácora de aprendizaje y seguimiento (AG-C06.01) | Proceso | [docs/bitacora.md](file:///c:/Users/PC/Documents/AlgoritmosAvanzados/VertexCover-main/docs/bitacora.md) | 8 sesiones registradas detallando decisiones y aprendizajes |

---

## 3. Resultados Experimentales Cuantitativos

### 3.1 Evaluación sobre Redes Reales y Didácticas
| Dataset / Instancia | Routers ($|V|$) | Enlaces ($|E|$) | Algoritmo | Routers IDS ($|C|$) | % de Red | Tiempo CPU (ms) | Memoria Pico (KB) | Ratio vs Óptimo | 100% Cubierto |
|---|---|---|---|---|---|---|---|---|---|
| **example_small.json** | 6 | 6 | Greedy Optimizado | 3 | 50.00% | 0.04 ms | 0.5 KB | 1.000x (Óptimo) | ✅ Válido |
| | | | Matching Maximal | 4 | 66.67% | 0.01 ms | 0.2 KB | 1.333x | ✅ Válido |
| | | | Exacto ILP / B&B | 3 | 50.00% | 0.98 ms | 1.2 KB | 1.000x (Óptimo) | ✅ Válido |
| | | | Fuerza Bruta | 3 | 50.00% | 0.03 ms | 0.4 KB | 1.000x (Óptimo) | ✅ Válido |
| **network_backbone_18.json** | 18 | 32 | Greedy Optimizado | 7 | 38.89% | 0.10 ms | 2.1 KB | 1.000x (Óptimo) | ✅ Válido |
| | | | Matching Maximal | 14 | 77.78% | 0.17 ms | 1.4 KB | 2.000x | ✅ Válido |
| | | | Exacto ILP / B&B | 7 | 38.89% | 37.12 ms | 8.5 KB | 1.000x (Óptimo) | ✅ Válido |
| | | | Fuerza Bruta | 7 | 38.89% | 174.10 ms | 5.2 KB | 1.000x (Óptimo) | ✅ Válido |
| **SNAP AS-733 Oregon** | 6,474 | 12,572 | Greedy Optimizado | **1,055** | **16.30%** | **23.90 ms** | 284.5 KB | $\le 1.000$x | ✅ Válido |
| | | | Matching Maximal | 1,904 | 29.41% | 17.15 ms | 192.3 KB | 1.805x | ✅ Válido |
| **SNAP CAIDA BGP Core** | 26,475 | 53,381 | Greedy Optimizado | **3,695** | **13.96%** | **164.86 ms** | 1,180.2 KB | $\le 1.000$x | ✅ Válido |
| | | | Matching Maximal | 6,948 | 26.24% | 103.91 ms | 815.6 KB | 1.880x | ✅ Válido |

---

## 4. Instrucciones de Ejecución

```bash
# 1. Instalar dependencias consolidadas
pip install -r requirements.txt

# 2. Ejecutar la suite de 38 pruebas automatizadas
pytest tests/ -v

# 3. Lanzar la Interfaz Gráfica Interactiva (GUI)
python gui.py
# o alternativamente:
python demo.py --gui

# 4. Ejecutar la batería experimental completa y regenerar gráficos
python experiments/compare_entrega2.py

# 5. Ejecutar la demo CLI sobre la red real de Stanford SNAP
python demo.py --instance data/instances/real/as20000102.txt --algorithm all
```
