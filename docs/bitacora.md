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

<!--
Plantilla para la siguiente entrada — copiar y completar:

## Sesión N — AAAA-MM-DD — [título corto]

**Qué se hizo:**

**Qué tuvimos que aprender / decidir por cuenta propia:**

**Pendiente para la siguiente sesión:**
-->
