# Pygame Graph Editor & Visualizer

A graphical, interactive tool built with Python, Pygame, and NetworkX to create graphs and visualize classic graph algorithms.

## Features
* **Interactive Graph Building**: Add, move, and delete nodes and edges directly on the canvas.
* **Custom Edge Weights**: Automatically prompts for a positive integer weight whenever a new edge is drawn.
* **Algorithm Visualization**:
    * **Prim's Algorithm**: Calculates and highlights the Minimum Spanning Tree (MST) and displays the total weight.
    * **BFS (Breadth-First Search)**: Explores and highlights the BFS traversal forest.
    * **DFS (Depth-First Search)**: Explores and highlights the DFS traversal forest.
    * **Dijkstra's Algorithm**: Calculates the shortest path from a selected source node and displays the shortest distance above each node.
* **Graph Analysis**: 
    * Count and display the number of connected components.
    * Check graph planarity via hotkey.
    * View the degree of a currently selected node.

## Prerequisites
You need Python installed on your system along with the `pygame` and `networkx` libraries.

Install the dependencies using pip:
```bash
pip install pygame networkx
```
## Controls & Hotkeys

* **S – Select / Move Mode**:
  * Click and drag nodes to move them on the canvas.
  * Click a node to select it and view its degree.
  * Press **Delete** or **Backspace** to remove the selected node.

* **A – Add Node Mode**:
  * Click anywhere on the empty canvas to create a new node.

* **E – Add Edge Mode**:
  * Click and drag from one node to another to create an edge.
  * A pop-up will appear at the bottom-left asking for the edge weight.
  * Enter the weight and press **Enter**.

* **D – Delete Node Mode**:
  * Click on a node to delete it along with all its connected edges.

* **J – Dijkstra Mode**:
  * Activate Dijkstra mode and click on a node to set it as the source.
  * The algorithm calculates the shortest paths to all reachable nodes.

---

## Actions

* **P – Prim's Algorithm**: Run Prim’s Algorithm to generate and highlight the Minimum Spanning Tree (MST).
* **B – BFS (Breadth-First Search)**: Execute BFS and highlight the traversal path.
* **F – DFS (Depth-First Search)**: Execute DFS and highlight the traversal path.
* **K – Connected Components**: Calculate and display the number of connected components in the graph.
* **C – Clear Visualization**: Clear all currently displayed algorithm results.
* **L – Planarity Check**: Print to the console whether the graph is **Planar** or **Not Planar**.
---

## Visual Guide (Edge Colors)
* **Gray (Thin)**: Default unvisited edge.
* **Red (Thick)**: Edges included in the **Minimum Spanning Tree (Prim’s)**.
* **Green (Thick)**: Edges visited during **Breadth-First Search (BFS)**.
* **Purple (Thick)**: Edges visited during **Depth-First Search (DFS)**.
* **Orange (Thick)**: Edges representing **Dijkstra’s shortest paths**.
