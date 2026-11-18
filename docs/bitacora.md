# Bitácora de aprendizaje

Evidencia de proceso para el indicador **AG-C06.01** (aprendizaje autónomo y desarrollo
sin supervisión externa). Cada entrada corresponde a una sesión real de trabajo: qué se
hizo, qué se tuvo que aprender o decidir por cuenta propia, y qué quedó pendiente.

> Cómo seguir esta bitácora: agreguen una entrada nueva cada vez que se sienten a trabajar
> en el proyecto (no solo antes de cada entrega). Una entrada corta de 5 líneas honestas
> vale más que una entrada larga escrita de memoria varias semanas después.

---

## Sesión 1 — 2026-10-03 — Formulación del problema (Avance 1)

**Qué se hizo:** Se definió la aplicación concreta de Vertex Cover (ubicación de IDS en una
red), se formuló el problema (entradas, salidas, restricciones, supuestos, función
objetivo) y se resolvió a mano una instancia de 6 routers con los dos algoritmos ya
acordados (greedy por grado y matching maximal).

**Qué tuvimos que aprender / decidir por cuenta propia:**
- Cómo se demuestra formalmente la garantía de 2-aproximación del matching maximal
  (el argumento de que las aristas elegidas forman un *matching* y por qué eso acota el
  óptimo).
- Por qué el greedy por grado no tiene una cota de aproximación fija en el peor caso,
  a pesar de funcionar bien en la práctica.

**Pendiente para la siguiente sesión:** Diseñar la estructura de datos del grafo y decidir
el formato de archivo para las instancias.

---

## Sesión 2 — 2026-10-04 — Implementación del núcleo y pruebas (Avance 2)

**Qué se hizo:** Se implementó `Graph` (lista de adyacencia), `VertexCoverSolver` con los
tres algoritmos (greedy, matching maximal, exacto por fuerza bruta), `verify.py`, y un plan
de pruebas de 27 casos (básicos, límite, adversarios) con `pytest`.

**Qué tuvimos que aprender / decidir por cuenta propia:**
- **Bug de reproducibilidad (el hallazgo más importante de esta sesión).** Al escribir las
  pruebas, un mismo algoritmo sobre la misma instancia devolvía coberturas de distinto
  tamaño en ejecuciones distintas. Investigando, encontramos que Python aleatoriza el hash
  de los `str` entre procesos (`PYTHONHASHSEED`), así que iterar directamente sobre un
  `set()` de aristas no tiene un orden garantizado entre ejecuciones. Tuvimos que aprender
  sobre hashing en Python y rediseñar ambos algoritmos para que usen un orden canónico fijo
  (`_sorted_edges`), no porque lo pidiera el enunciado del algoritmo, sino porque el
  proyecto exige reproducibilidad (instrucción adicional 7 de la guía) y sin este arreglo
  no podíamos confiar en nuestros propios resultados experimentales.
- Cómo estructurar pruebas con `pytest` (fixtures implícitas, `@pytest.mark.parametrize`
  para repetir una verificación sobre varias instancias aleatorias sin duplicar código).
- Diferencia práctica entre lista de adyacencia y matriz de adyacencia para grafos dispersos,
  y por qué importa para este problema específico (redes reales son dispersas).

**Decisiones tomadas:**
- JSON como formato de instancia (en vez de un formato propio o CSV de aristas), por ser
  nativo en Python y fácil de diffear en Git.
- Separar la verificación (`verify.py`) de los algoritmos (`solver.py`), para que ninguna
  prueba pueda "hacer trampa" confiando solo en el tamaño devuelto.

**Pendiente para la siguiente sesión:** Escribir el prototipo ejecutable (`demo.py`) y el
primer experimento comparativo.

---

## Sesión 3 — 2026-10-04 — Prototipo, experimentos y documentación (Avance 2 cierre / Avance 3)

**Qué se hizo:** Se construyó `demo.py` (CLI de demostración), `experiments/compare.py`
(primer experimento reproducible), y se redactó el documento del Avance 2 con los
resultados reales obtenidos (no estimados).

**Qué tuvimos que aprender / decidir por cuenta propia:**
- Manejo de `argparse` para una CLI con múltiples modos (archivo vs. instancia generada al
  vuelo), pensando en que la demostración del Avance 3 se hace en vivo y el docente puede
  pedir una instancia nueva en el momento.
- Al correr el primer experimento nos encontramos con que el tiempo del algoritmo exacto
  ya crecía de forma visiblemente exponencial entre 6 y 18 vértices (de 0.02ms a 174ms).
  Esto no lo "sabíamos" en abstracto hasta verlo en los datos; confirma por qué el proyecto
  pide un mecanismo de referencia aparte y por qué vamos a necesitar ILP (PuLP) para
  instancias más grandes en la Entrega 2.
- Configuración de LaTeX para generar los documentos de las entregas: tuvimos que resolver
  que el entorno de compilación no tenía el paquete de idioma español de `babel`
  disponible, lo que rompía el guionado automático del texto en tablas con palabras largas;
  se corrigió ajustando manualmente los anchos de columna y los puntos de corte de línea.

**Pendiente para la Entrega 2:**
- Incorporar `exact_vertex_cover_ilp` (PuLP) como referencia escalable más allá de
  ~20 vértices.
- Optimizar el greedy a `O((V+E) log V)` con una cola de prioridad.
- Ampliar el experimento a distintas densidades y a la topología tipo backbone
  (Barabási-Albert), no solo Erdos-Renyi.
- Instrumentar uso de memoria como métrica adicional.
- Visualización de grafos pequeños (candidato: NetworkX + matplotlib).

---

## Sesión 4 — 2026-10-18 — Solución exacta escalable: ILP y Branch & Bound

**Qué se hizo:** Se implementó y evaluó la solución exacta escalable para superar la limitación
de la fuerza bruta ($|V| \le 20$). Se integró la formulación matemática de Programación Lineal
Entera (ILP) con PuLP y se desarrolló un algoritmo exacto autónomo de Branch & Bound con poda
basada en cotas inferiores de emparejamiento maximal (Matching Lower Bound).

**Qué tuvimos que aprender / decidir por cuenta propia:**
- Al investigar la integración con PuLP en entornos modernos de Python nos topamos con que
  determinadas versiones no incluyen el binario compilado de CBC por defecto en Windows.
  Para evitar depender de solvers externos que pudieran fallar en la máquina de evaluación del
  docente, decidimos investigar y programar nosotros mismos un solver exacto por Branch & Bound:
  en cada paso se ramifica sobre el router de mayor grado residual ($v \in C$ vs $v \notin C \implies N(v) \subseteq C$)
  y se poda la rama si $|C_{\text{actual}}| + |M_{\text{restante}}| \ge |C^*_{\text{mejor}}|$.
- Este Branch & Bound autónomo demostró resolver instancias de hasta 60 vértices en milisegundos,
  sirviendo de respaldo perfecto y mecanismo de validación cruzada con ILP y fuerza bruta.

**Pendiente para la siguiente sesión:** Optimizar la complejidad del Greedy para que pueda
correr en grafos masivos sin degradar tiempo.

---

## Sesión 5 — 2026-10-25 — Optimización algorítmica: Greedy O((V+E) log V)

**Qué se hizo:** Se rediseñó el algoritmo Greedy por Grado pasando de la implementación ingenua
$O(V \cdot E)$ a una estructura optimizada con cola de prioridad max-heap (`heapq`) y
actualización perezosa de grados (*lazy updates*), reduciendo la complejidad a $O((V+E)\log V)$.

**Qué tuvimos que aprender / decidir por cuenta propia:**
- Cómo implementar colas de prioridad con actualización de claves en Python sin estructuras
  complejas de terceros: en lugar de un decrease-key costoso, se insertan nuevas tuplas
  `(-grado_actual, id_canonico, vertice)` en el heap y al extraerlas se descartan si el
  grado real del router en la lista de adyacencia ya fue reducido por vecinos cubiertos previamente.
- Mantener la reproducibilidad estricta: incluimos el `str(id)` como criterio secundario de
  desempate dentro de la tupla del heap para asegurar que dos ejecuciones en distintos sistemas
  produzcan exactamente la misma secuencia de selección de routers.

**Pendiente para la siguiente sesión:** Obtener un dataset real de infraestructura de Internet
de libre acceso y crear el parser correspondiente.

---

## Sesión 6 — 2026-11-02 — Integración de Redes Reales de Internet (Stanford SNAP)

**Qué se hizo:** Se investigó en la literatura y repositorios científicos de redes para ubicar
topologías reales de routers de Internet. Se seleccionaron y descargaron dos datasets oficiales
del *Stanford Large Network Dataset Collection* (SNAP):
1. **AS-733 (Oregon RouteViews)**: Topología de routers y sistemas autónomos BGP con 6,474 nodos
   y 12,572 enlaces reales.
2. **CAIDA AS Relationships (BGP Core)**: Topología troncal de interconexión global con
   26,475 nodos y 53,381 enlaces físicos.
Se amplió `src/graph.py` con el método `from_edge_list()` para procesar estos archivos directamente.

**Qué tuvimos que aprender / decidir por cuenta propia:**
- Relevancia directa con el problema: en protocolos BGP de Internet, los *Autonomous Systems* (AS)
  son gestionados por routers de borde (Border Routers). Instalar IDS en el subconjunto de cobertura
  mínima garantiza que ningún flujo inter-dominio pase desapercibido sin necesidad de comprar
  equipos IDS para los 26,475 sistemas.
- Los resultados experimentales confirmaron la hipótesis: gracias a la distribución libre de escala
  (ley de potencias) de Internet, el algoritmo Greedy requiere únicamente 1,055 routers (16.3%)
  en AS-733 y 3,695 routers (13.9%) en CAIDA para proteger el 100% de los enlaces globales.

**Pendiente para la siguiente sesión:** Construir la interfaz gráfica y asegurar que soporte
el tamaño del grafo de CAIDA sin trabarse.

---

## Sesión 7 — 2026-11-10 — Interfaz Gráfica Interactiva (GUI) y Soporte de Escala

**Qué se hizo:** Se diseñó e implementó la Interfaz Gráfica de Usuario interactiva (`gui.py` y
`src/gui_app.py`) con Tkinter y ttk, estilizada con una paleta profesional cyber-blue/dark.
Se implementó navegación con zoom (rueda de ratón), pan (arrastre), inspección de routers por clic,
tarjetas KPI en cabecera, tabla comparativa con barras visuales y exportación en JSON y CSV.

**Qué tuvimos que aprender / decidir por cuenta propia:**
- **El reto de la escala masiva en la GUI:** Al intentar renderizar 26,475 nodos y 53,381 aristas
  simultáneamente, el motor gráfico colapsaba y la ventana de Windows se congelaba mostrando "(No responde)".
- **Solución arquitectónica adoptada:**
  1. *Concurrencia multihilo:* Toda la ejecución algorítmica se desacopló a hilos secundarios
     (`threading.Thread`), comunicando el progreso a la UI mediante eventos seguros `root.after()`.
  2. *Renderizado multinivel inteligente:* Se implementó el modo "Backbone Hubs", que extrae
     el subgrafo inducido por los $N$ routers concentradores de mayor conectividad (donde se
     concentra la defensa IDS), y el modo "Ego-Network" para inspeccionar vecindarios locales.
     Esto permitió que la GUI responda a 60 FPS con fluidez absoluta incluso sobre CAIDA.

**Pendiente para la siguiente sesión:** Automatizar la batería de experimentos comparativos,
generar gráficos científicos para el informe y redactar el documento final de la Entrega 2.

---

## Sesión 8 — 2026-11-16 — Pruebas, Experimentos Sistemáticos e Informe Técnico

**Qué se hizo:**
- Se amplió la suite de pruebas a 38 casos de prueba automatizados con `pytest` (`tests/test_entrega2.py`),
  cubriendo equivalencia ILP/Fuerza Bruta, verificación del Greedy optimizado, estabilidad en
  instancias reales SNAP y extracción de subgrafos.
- Se ejecutó `experiments/compare_entrega2.py`, generando tablas cuantitativas de tiempo y memoria,
  así como dos figuras científicas con Matplotlib (`fig_scalability_time.png` y `fig_real_networks_ids.png`).
- Se redactó y compiló el informe formal de la Entrega 2 (`docs/AA_2026_II_Caballero_Castilla_Llactahuamani_Morocco_Proyecto02.tex`).

**Qué tuvimos que aprender / decidir por cuenta propia:**
- Descubrimos empíricamente que en grafos densos el Greedy se acerca mucho más al óptimo (ratios
  entre 1.0x y 1.05x), mientras que en grafos tipo backbone con topología de red real el Matching
  suele requerir casi el doble de routers que el Greedy (ratio ~1.88x), justificando por qué
  la heurística voraz por grado es preferible en ciberseguridad a pesar de no poseer una cota
  fija en el peor caso abstracto.

**Pendiente para la Entrega 3:**
- Presentación final, manual de despliegue para el usuario final y preparación de la defensa
  individual de acuerdo con la rúbrica del atributo AG_C06.
