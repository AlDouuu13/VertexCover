"""
gui.py
------
Punto de entrada principal para lanzar la Interfaz Gráfica de Usuario (GUI)
del proyecto Vertex Cover IDS Placement.

Permite interactuar visualmente con:
  - Instancias de prueba didácticas y sintéticas
  - Instancias reales masivas de internet (ej. Stanford SNAP AS-733 y CAIDA BGP)
  - Algoritmos Greedy Optimizado O((V+E)log V), Matching Maximal 2-Aprox O(V+E),
    Exacto ILP (PuLP) y Fuerza Bruta.

Uso:
  python gui.py
"""

from src.gui_app import launch_gui

if __name__ == "__main__":
    launch_gui()
