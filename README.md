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
Controls & Hotkeys
You can control the application using the top menu buttons or the following keyboard shortcuts:

Modes
S (Select/Move): Click and drag nodes to move them. Click a node to select it (shows its degree). Press Delete or Backspace to delete the selected node.
A (Add Node): Click anywhere on the empty white canvas to create a new node.
E (Add Edge): Click and drag from one node to another to create an edge. A pop-up will appear at the bottom-left asking for the edge weight. Type a number and press Enter.
D (Delete Node): Click a node to remove it and all its connected edges.
J (Dijkstra): Enter Dijkstra mode, then click on a node to set it as the source. It will calculate shortest paths to all other reachable nodes.

Actions
P: Run Prim's Algorithm (MST).
B: Run BFS.
F: Run DFS.
K: Calculate and display the number of Connected Components.
C: Clear all current algorithm visualizations.
L: Print to the console whether the graph is Planar or NOT Planar.

Visual Guide (Edge Colors)
When algorithms are run, the edges are highlighted in different colors to show the result:

Gray (Thin): Default unvisited edge.
Red (Thick): Minimum Spanning Tree (Prim's).
Green (Thick): Breadth-First Search (BFS) path.
Purple (Thick): Depth-First Search (DFS) path.
Orange (Thick): Dijkstra's Shortest Path.
