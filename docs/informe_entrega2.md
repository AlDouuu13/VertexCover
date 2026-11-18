# Informe Técnico — Segunda Entrega
## Proyecto Semestral: Algoritmos Avanzados (2026-2)
**Universidad Nacional de San Antonio Abad del Cusco (UNSAAC)**  
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
En esta **Segunda Entrega**, se presenta la implementación funcional, integración de sistemas, pruebas automatizadas, interfaz gráfica interactiva y evaluación experimental a escala real para el problema de **Cobertura de Vértices (Vertex Cover)** aplicado a la ubicación de **Sistemas de Detección de Intrusos (IDS)** en redes de comunicaciones:
1. **Algoritmos Implementados:**
   - **Greedy por Grado Optimizado:** Implementado con max-heap (`heapq`) y actualización perezosa de grados (*lazy updates*), reduciendo la complejidad temporal de $O(V \cdot E)$ a **$O((V+E)\log V)$**.
   - **2-Aproximación por Emparejamiento Maximal (*Maximal Matching*):** Algoritmo determinístico lineal **$O(V+E)$** con garantía matemática demostrada de $|C| \le 2 \cdot |C^*|$.
   - **Exacto por Fuerza Bruta:** Búsqueda combinatoria $O(2^V \cdot E)$ para validación en instancias pequeñas ($|V| \le 20$).
   - **Exacto Escalable (ILP y Branch & Bound):** Formulación de Programación Lineal Entera resuelta mediante PuLP y complementada con un motor autónomo propio de *Branch & Bound* con poda analítica mediante cotas inferiores de emparejamiento maximal.
2. **Soporte de Instancias Reales Masivas de Internet:**
   - Adquisición e integración de topologías reales BGP de la colección científica **Stanford SNAP**:
     * **SNAP AS-733 Oregon:** 6,474 routers y 12,572 enlaces físicos.
     * **SNAP CAIDA BGP Core:** 26,475 routers y 53,381 enlaces físicos.
   - Demostración empírica de que en la red de CAIDA, el algoritmo Greedy requiere solo **3,695 routers (13.96% de la red)** para monitorear el **100% de los enlaces globales**, logrando un ahorro del 86.04% en hardware IDS.
3. **Interfaz Gráfica de Usuario (GUI):**
   - Interfaz interactiva de escritorio desarrollada en Python con Tkinter/ttk (`gui.py` / `src/gui_app.py`).
   - Soporte fluido para grafos masivos mediante **concurrencia multihilo asíncrona** y renderizado multinivel: modo *Backbone Hubs* (top routers principales), modo *Ego-Network* (vecindario local) y modo de métricas globales.
   - Canvas interactivo con **Zoom continuo** (rueda del ratón) y **Pan** (arrastre con clic), inspector interactivo de routers al hacer clic, tarjetas KPI y exportación en JSON/CSV.
4. **Verificación y Pruebas Automatizadas:**
   - **38 pruebas automatizadas** con `pytest` pasando al 100% (unitarias, límite, adversarias, escala e integración).
   - Instrumentación de tiempo de CPU ($\mu$s/ms) y memoria pico RAM (KB) con `tracemalloc`.

---

## 2. Formulación y Justificación del Problema en Redes
Dado un grafo no dirigido $G = (V, E)$ que modela una red de comunicaciones:
- $V$: Conjunto de routers o conmutadores troncales.
- $E$: Enlaces físicos de transmisión de datos.
- **Objetivo:** Encontrar el subconjunto $C \subseteq V$ de tamaño mínimo tal que cada enlace $(u, v) \in E$ tenga al menos un extremo en $C$ ($u \in C \lor v \in C$).
- **Relevancia:** Instalar un IDS en un router permite inspeccionar todos los paquetes que entran o salen por sus interfaces. Al cubrir todas las aristas, ningún flujo de red entre dos routers puede transitar sin ser analizado por al menos un IDS.

---

## 3. Cumplimiento de Indicadores de Desempeño (Rúbrica AG_C06)

### Indicador AG-C06.01: Aprendizaje Autónomo y Proceso sin Supervisión (40%)
- **Superación de dependencias de solvers:** Ante la variabilidad de binarios compilados de CBC en Windows, se diseñó e implementó de forma autónoma un solver exacto Branch & Bound en Python puro podado con cotas de matching maximal.
- **Determinismo canónico en colas de prioridad:** Se diseñó el esquema de tuplas compuestas `(-grado, str(id), id)` en `heapq` para evitar fallos de reproducibilidad por hash aleatorizado entre ejecuciones.
- **Bitácora de aprendizaje:** 8 sesiones detalladas en `docs/bitacora.md` con objetivos, obstáculos reales, decisiones tomadas y tareas futuras.

### Indicador AG-C06.02: Adaptación y Uso Competente de Tecnologías (40%)
- **Stack Tecnológico Justificado:** Python 3, Tkinter/ttk para GUI nativa sin dependencias pesadas, PuLP/Branch & Bound para exactitud matemática, pytest para pruebas continuas, Matplotlib y Pandas para visualización de experimentos.
- **Arquitectura Multihilo:** Desacoplamiento de la lógica computacional del hilo principal de la GUI (`threading.Thread`) con eventos sincronizados vía `root.after()`.
- **Integración de Datasets Científicos:** Procesamiento directo de archivos en formato de lista de aristas de Stanford SNAP mediante `Graph.from_edge_list()`.

### Indicador AG-C06.03: Pensamiento Crítico y Análisis de Alternativas (20%)
- **Contraste Teoría vs. Evidencia:** Aunque el Matching Maximal tiene una garantía formal matemática de 2.0x y el Greedy no tiene cota constante en el peor caso patológico, los experimentos demuestran que en redes reales de Internet el Greedy es muy superior (ratio ~1.88x a favor del Greedy). Esto se debe a la estructura *libre de escala* (ley de potencias) de las redes de routers reales, donde los hubs concentran gran cantidad de aristas que el Greedy aprovecha inmediatamente.
- **Instrumentación Rigurosa:** Medición de tiempo real de CPU con `time.perf_counter()` y memoria RAM con `tracemalloc`.

---

## 4. Tabla Comparativa de Resultados Experimentales

### 4.1 Evaluación en Instancias Didácticas y Redes Reales de Internet
| Dataset / Instancia | Routers ($|V|$) | Enlaces ($|E|$) | Algoritmo | Routers IDS ($|C|$) | % de Red | Tiempo CPU (ms) | Memoria Pico (KB) | Ratio vs Óptimo | 100% Cubierto |
|---|---|---|---|---|---|---|---|---|---|
| **example_small** | 6 | 6 | Greedy Optimizado | 3 | 50.00% | 0.04 ms | 0.5 KB | 1.000x (Óptimo) | ✅ Válido |
| | | | Matching Maximal | 4 | 66.67% | 0.01 ms | 0.2 KB | 1.333x | ✅ Válido |
| | | | Exacto ILP / B&B | 3 | 50.00% | 0.98 ms | 1.2 KB | 1.000x (Óptimo) | ✅ Válido |
| | | | Fuerza Bruta | 3 | 50.00% | 0.03 ms | 0.4 KB | 1.000x (Óptimo) | ✅ Válido |
| **network_backbone_18** | 18 | 32 | Greedy Optimizado | 7 | 38.89% | 0.10 ms | 2.1 KB | 1.000x (Óptimo) | ✅ Válido |
| | | | Matching Maximal | 14 | 77.78% | 0.17 ms | 1.4 KB | 2.000x | ✅ Válido |
| | | | Exacto ILP / B&B | 7 | 38.89% | 37.12 ms | 8.5 KB | 1.000x (Óptimo) | ✅ Válido |
| | | | Fuerza Bruta | 7 | 38.89% | 174.10 ms | 5.2 KB | 1.000x (Óptimo) | ✅ Válido |
| **SNAP AS-733 Oregon** | 6,474 | 12,572 | Greedy Optimizado | **1,055** | **16.30%** | **23.90 ms** | 284.5 KB | $\le 1.000$x | ✅ Válido |
| | | | Matching Maximal | 1,904 | 29.41% | 17.15 ms | 192.3 KB | 1.805x | ✅ Válido |
| **SNAP CAIDA BGP Core** | 26,475 | 53,381 | Greedy Optimizado | **3,695** | **13.96%** | **164.86 ms** | 1,180.2 KB | $\le 1.000$x | ✅ Válido |
| | | | Matching Maximal | 6,948 | 26.24% | 103.91 ms | 815.6 KB | 1.880x | ✅ Válido |

---

## 5. Manual de Uso y Ejecución Rápida

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar la suite completa de pruebas automatizadas (38 pruebas)
pytest tests/ -v

# 3. Lanzar la Interfaz Gráfica Interactiva (GUI)
python gui.py
# o también:
python demo.py --gui

# 4. Correr la batería experimental y regenerar gráficos
python experiments/compare_entrega2.py

# 5. Ejecutar la demo CLI sobre la red real de Stanford SNAP
python demo.py --instance data/instances/real/as20000102.txt --algorithm all
```
