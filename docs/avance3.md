# Avance 3 — Prototipo mínimo y preparación de la primera entrega

Este documento reúne lo que pide la guía para el Avance 3: mostrar un repositorio activo,
un prototipo ejecutable, explicar su funcionamiento y organización, y dejar registradas las
dificultades pendientes y los ajustes hechos a partir de los Avances 1 y 2.

## 1. Repositorio activo

El historial de commits (`git log --oneline`) refleja el desarrollo incremental real del
proyecto, no una única entrega de golpe:

```
81a064d docs: Avance 2 - diseno algoritmico y plan de validacion
19cdf63 feat: experimento comparativo preliminar (experiments/compare.py)
69e4382 feat: prototipo ejecutable (demo.py) para el Avance 3
f24ca1c test: plan de pruebas basicas, limite y adversarias (27 casos)
096435d fix: hacer deterministas greedy y matching maximal
9fe2b3c feat: VertexCoverSolver (greedy, matching maximal, exacto) + verify.py
a5393a9 feat: estructura de grafo (Graph) y carga de instancias
d823af6 chore: estructura inicial del repositorio
```

Cada commit es una unidad de trabajo revisable por separado (estructura → grafo → solver →
corrección de un bug real → pruebas → prototipo → experimento → documentación), tal como
pide la instrucción adicional 3 de la guía ("el historial debe reflejar la evolución del
trabajo y permitir identificar contribuciones, pruebas, correcciones y decisiones").

## 2. Prototipo mínimo ejecutable

`demo.py` cumple los tres requisitos explícitos del Avance 3:

| Requisito | Cómo lo cumple |
|---|---|
| Cargar o definir una instancia | `--instance archivo.json` (instancia guardada) o `--random N P [--seed S]` (instancia generada en el momento, útil si el docente propone una nueva durante la sesión) |
| Ejecutar al menos un algoritmo básico | `--algorithm greedy\|matching\|exact\|all` |
| Producir una salida verificable | Cada cobertura se valida con `is_vertex_cover` antes de mostrarse; se reporta tamaño, validez, tiempo y ratio de aproximación |

### Ejecución de referencia

```bash
pip install -r requirements.txt   # solo necesario la primera vez

# Instancia conocida (la del Avance 1)
python demo.py --instance data/instances/example_small.json --algorithm all

# Instancia tipo red más grande
python demo.py --instance data/instances/network_backbone_18.json --algorithm all

# Instancia nueva propuesta en el momento (ej. durante la sesión con el docente)
python demo.py --random 15 0.25 --seed 42 --algorithm all
```

### Validación en vivo durante la demostración

1. **Con una instancia conocida** (`example_small.json`): el resultado debe coincidir
   exactamente con la traza manual del Avance 1 — greedy y exacto dan tamaño 3, matching da
   tamaño 4 — lo que demuestra que la implementación es fiel al diseño.
2. **Con una instancia nueva propuesta en la sesión**: se puede pasar cualquier archivo
   JSON con el mismo formato, o generar un grafo aleatorio al vuelo con `--random`. En
   ambos casos el programa valida automáticamente que la cobertura devuelta sea correcta
   (`Valida: SI/NO`) antes de reportar el tamaño, así que un resultado incorrecto no puede
   pasar desapercibido en la demo.

## 3. Organización del repositorio

```
vertex-cover-ids/
├── src/            → núcleo algorítmico (graph.py, solver.py, verify.py)
├── tests/          → 27 pruebas pytest (básicas, límite, adversarias)
├── data/instances/ → instancias de ejemplo en JSON
├── experiments/    → comparación empírica reproducible (compare.py + resultados)
├── docs/           → avance1.tex/pdf, avance2.tex/pdf, avance3.md (este archivo), bitacora.md
├── demo.py         → prototipo ejecutable (CLI) para la demostración
└── requirements.txt
```

La separación sigue un criterio simple: **lo que es lógica algorítmica vive en `src/`, lo
que es evidencia de que esa lógica funciona vive en `tests/` y `experiments/`, y lo que es
interacción con una persona (demo o documentos) vive fuera de `src/`.** Así, cualquier
integrante puede explicar o modificar una parte sin tener que entender el resto completo,
que es justo lo que pide la instrucción de "dominio individual" de la guía (punto 9).

## 4. Dificultades encontradas y ajustes realizados

Esto es evidencia directa de pensamiento crítico y aprendizaje autónomo (AG-C06.01 y
AG-C06.03), documentado también con más detalle en `docs/bitacora.md`.

### Dificultad 1: resultados no reproducibles (encontrada escribiendo las pruebas)

Al implementar las pruebas del Avance 2, dos ejecuciones del mismo algoritmo sobre la misma
instancia devolvían coberturas válidas pero de **tamaño distinto**. La causa: iterar
directamente sobre un `set()` de aristas en Python no tiene un orden garantizado entre
ejecuciones (depende del hash-seed del proceso). Esto viola directamente el requisito de
reproducibilidad de la guía (instrucción adicional 7).

**Ajuste realizado:** se introdujo `VertexCoverSolver._sorted_edges()`, que fija un orden
canónico y determinístico para los desempates del greedy y la elección "arbitraria" del
matching maximal. Verificado manualmente variando `PYTHONHASHSEED` entre procesos distintos
(ver commit `fix: hacer deterministas greedy y matching maximal`).

### Dificultad 2: la fuerza bruta no escala (confirmada con datos, no solo en teoría)

El primer experimento (`experiments/compare.py`) mostró que el tiempo del algoritmo exacto
pasa de 0.02ms (n=6) a 174ms (n=18) — ya visiblemente exponencial en un rango pequeño.

**Ajuste realizado (parcial):** `exact_vertex_cover_bruteforce` rechaza explícitamente
instancias de más de 20 vértices en vez de colgarse, y `demo.py` omite automáticamente el
algoritmo exacto cuando la instancia es demasiado grande.

**Pendiente:** incorporar `exact_vertex_cover_ilp` (ya bosquejado con PuLP en
`src/solver.py`, pero sin probar a fondo) como referencia escalable para la Entrega 2.

### Dificultad 3: limitación del entorno de documentación

El entorno usado para compilar los documentos LaTeX no tenía disponible el paquete de
idioma español de `babel` (sin acceso a instalarlo). Se decidió prescindir de él y corregir
a mano los pocos puntos donde esto causaba desbordes de texto, en vez de bloquear la entrega
por una herramienta no esencial — consistente con el criterio de "prioridad del proyecto"
de la guía (el núcleo algorítmico importa más que el acabado visual de los documentos).

### Otros ajustes menores realizados entre avances

- El formato de guardado de instancias JSON se reescribió para que las aristas queden una
  por línea (más legible al revisar diffs en Git) en vez de que cada `[u, v]` se expandiera
  en 3 líneas con la indentación por defecto.
- `demo.py` captura explícitamente archivo-no-encontrado y JSON mal formado con un mensaje
  claro, en vez de un traceback, pensando en que la demo se corre en vivo frente al docente.

## 5. Checklist antes de la Entrega 1

Verificado el 2026-10-04:

- [x] El sistema se ejecuta (`python demo.py ...`) sin depender de rutas absolutas.
- [x] Los algoritmos producen resultados válidos (verificado automáticamente, no a ojo).
- [x] Las pruebas se completan: `pytest tests/ -v` → 27/27 passed.
- [x] Los experimentos son reproducibles (semillas fijas en `experiments/compare.py`).
- [x] El repositorio tiene historial incremental desde el primer commit.
- [ ] Cada integrante repasó el repositorio y puede explicar cualquier módulo sin apoyo
      (pendiente de confirmar en reunión de grupo antes de la sesión con el docente).

## 6. Hoja de ruta hacia la Entrega 2

Para que el repositorio siga mostrando avance incremental real (no una sola subida grande
antes de la fecha límite), estos son los próximos pasos sugeridos, cada uno como su propio
commit o serie de commits:

1. Implementar y probar `exact_vertex_cover_ilp` con PuLP; comparar su tiempo contra la
   fuerza bruta en el rango donde ambas funcionan (overlap de validación).
2. Optimizar `greedy_degree_vertex_cover` con una cola de prioridad (`heapq`) para bajar de
   `O(V·E)` a `O((V+E) log V)`; agregar una prueba que compare que ambas versiones dan el
   mismo resultado.
3. Ampliar `experiments/compare.py`: variar la densidad `p` además de `n`, e incluir
   instancias Barabási-Albert (tipo backbone) además de Erdos-Renyi.
4. Agregar visualización de grafos pequeños (candidato: NetworkX + matplotlib) para el
   informe final.
5. Instrumentar uso de memoria como métrica adicional.
6. Actualizar `docs/bitacora.md` en cada sesión real de trabajo del grupo.
