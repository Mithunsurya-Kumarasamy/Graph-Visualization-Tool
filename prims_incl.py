import pygame
import networkx as nx
import random  # --- NEW ---: Needed for random edge weights

# --- Pygame Initialization ---
pygame.init()

WIDTH, HEIGHT = 1280, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Graph Editor (Modal)")

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
BTN_COLOR = (220, 220, 220)
BTN_HOVER_COLOR = (180, 180, 180)
BTN_ACTIVE_COLOR = (140, 140, 140)

# --- Node Settings ---
NODE_RADIUS = 20
NODE_COLOR = BLUE
SELECTED_NODE_COLOR = RED
HOVER_NODE_COLOR = (100, 100, 255)

# --- Font ---
font = pygame.font.Font(None, 24)
btn_font = pygame.font.Font(None, 20)
# --- NEW ---: Font for edge weights
weight_font = pygame.font.Font(None, 22)


# --- Graph Data Structure ---
graph = nx.Graph()
nodes_dict = {}  # {node_id: NodeObject}
next_node_id = 0
mst_edges = set()  # --- NEW ---: Stores the edges of the MST

# --- State Management ---
current_mode = 'select_move' # Start in select mode

# --- Interaction State ---
selected_node = None
dragging_node = None
drawing_edge_from = None

# --- Node Class (Visual Representation) ---
class Node:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y

    def draw(self, screen, color):

        pygame.draw.circle(screen, color, (self.x, self.y), NODE_RADIUS)
        pygame.draw.circle(screen, BLACK, (self.x, self.y), NODE_RADIUS, 2) # Border

        text_surface = font.render(str(self.id), True, WHITE)
        text_rect = text_surface.get_rect(center=(self.x, self.y))
        screen.blit(text_surface, text_rect)

    def is_clicked(self, mouse_pos):
        return (self.x - mouse_pos[0])**2 + (self.y - mouse_pos[1])**2 < NODE_RADIUS**2

# --- Button Class ---
class Button:
    def __init__(self, x, y, w, h, text, mode_id):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.mode_id = mode_id # The mode this button sets

    def draw(self, screen, is_active, mouse_pos):
        color = BTN_COLOR
        if is_active:
            color = BTN_ACTIVE_COLOR
        elif self.rect.collidepoint(mouse_pos):
            color = BTN_HOVER_COLOR
        
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2) # Border

        text_surface = btn_font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

# --- Helper Functions ---
def get_node_at_pos(mouse_pos):
    """Returns the Node object at mouse_pos, or None if no node is there."""
    for node_obj in nodes_dict.values():
        if node_obj.is_clicked(mouse_pos):
            return node_obj
    return None

# --- NEW ---: Function to calculate and store the MST
def calculate_prims_mst():
    """
    Calculates the MST using Prim's algorithm and stores its 
    edges in the global 'mst_edges' set for visualization.
    """
    global mst_edges
    global prims_weight
    mst_edges.clear()  # Clear previous MST
    prims_weight = 0

    if graph.number_of_nodes() < 1:
        print("Graph is empty. Cannot run Prim's.")
        return

    # Handle disconnected graphs: run Prim's on the largest component
    if not nx.is_connected(graph):
        print("Graph is not connected. Running Prim's on the largest component.")
        try:
            largest_cc = max(nx.connected_components(graph), key=len)
            subgraph = graph.subgraph(largest_cc)
        except ValueError:
             print("No components to run on.")
             return
    else:
        subgraph = graph
    
    if subgraph.number_of_nodes() < 1:
         print("No nodes to process.")
         return

    # Run Prim's algorithm. NetworkX's function returns a new graph
    try:
        mst_graph = nx.minimum_spanning_tree(subgraph, algorithm='prim', weight='weight')
        
        # Store the edges for visualization
        # We store them as sorted tuples to make drawing checks simple
        for u, v in mst_graph.edges():
            mst_edges.add(tuple(sorted((u, v))))
        
        prims_weight = mst_graph.size(weight='weight')
        print(f"Prim's MST calculated. Edges: {mst_edges}, Total Weight: {prims_weight}")

    except nx.NetworkXException as e:
        print(f"Could not run Prim's: {e}")
        print("This can happen if a component has no edges or weights.")
    except Exception as e:
        print(f"An error occurred during Prim's calculation: {e}")


# --- Create UI Buttons ---
# --- MODIFIED ---: Added new buttons for Prim's and Clear
buttons = [
    Button(10, 10, 160, 40, "Select/Move (S)", 'select_move'),
    Button(180, 10, 160, 40, "Add Node (A)", 'add_node'),
    Button(350, 10, 160, 40, "Add/Remove Edge (E)", 'add_edge'),
    Button(520, 10, 160, 40, "Delete Node (D)", 'del_node'),
    Button(690, 10, 160, 40, "Run Prim's MST (P)", 'run_prims'),  # --- NEW ---
    Button(860, 10, 160, 40, "Clear MST Viz (C)", 'clear_mst'), # --- NEW ---
]

# --- Main Game Loop ---
running = True
#clock = pygame.time.Clock()

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Handle Mouse Click Down ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                
                # 1. Check if a UI button was clicked
                ui_clicked = False
                for btn in buttons:
                    if btn.is_clicked(mouse_pos):
                        # --- MODIFIED ---: Handle new special buttons
                        if btn.mode_id == 'run_prims':
                            calculate_prims_mst()
                        elif btn.mode_id == 'clear_mst':
                            mst_edges.clear()
                            print("Cleared MST visualization.")
                        else:
                            current_mode = btn.mode_id
                        
                        # Reset interaction state on tool change
                        selected_node = None
                        dragging_node = None
                        drawing_edge_from = None
                        ui_clicked = True
                        break
                
                if ui_clicked:
                    continue # Don't process the click on the graph

                # 2. Handle graph clicks based on the current mode
                clicked_node = get_node_at_pos(mouse_pos)
                presently_clicked_node = get_node_at_pos(mouse_pos)
                if current_mode == 'select_move':
                    if clicked_node:
                        selected_node = clicked_node
                        dragging_node = clicked_node # Start dragging
                    else:
                        selected_node = None # Clicked empty space, deselect
                
                elif current_mode == 'add_node':
                    if not clicked_node: # Click on empty space
                        
                        new_node = Node(next_node_id, mouse_pos[0], mouse_pos[1])
                        nodes_dict[next_node_id] = new_node
                        graph.add_node(next_node_id)
                        mst_edges.clear() # --- NEW ---: Invalidate MST
                        print(f"Added node: {next_node_id}")
                        
                        # --- MODIFIED ---: Simplified your next_node_id logic
                        existing_ids = set(nodes_dict.keys())
                        i = 0
                        while i in existing_ids:
                            i += 1
                        next_node_id = i
                        
                elif current_mode == 'add_edge':
                    if clicked_node:
                        # Start drawing an edge
                        drawing_edge_from = clicked_node
                elif current_mode == 'del_node':
                    if presently_clicked_node:
                        node_id_to_remove = presently_clicked_node.id
                        graph.remove_node(node_id_to_remove)
                        del nodes_dict[node_id_to_remove]
                        mst_edges.clear() # --- NEW ---: Invalidate MST
                        print(f"Removed node: {node_id_to_remove}")
                        selected_node = None

                        # --- MODIFIED ---: Simplified your next_node_id logic
                        existing_ids = set(nodes_dict.keys())
                        i = 0
                        while i in existing_ids:
                            i += 1
                        next_node_id = i


        # --- Handle Mouse Motion ---
        if event.type == pygame.MOUSEMOTION:
            if dragging_node and current_mode == 'select_move':
                dragging_node.x, dragging_node.y = mouse_pos
                # Moving a node doesn't change graph topology, but we'll
                # clear the MST viz to be safe and force a re-calc.
                if len(mst_edges) > 0:
                    mst_edges.clear()
                    print("Node moved, cleared MST visualization.")


        # --- Handle Mouse Click Up ---
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Left click up
                
                if current_mode == 'select_move':
                    dragging_node = None # Stop dragging
                
                elif current_mode == 'add_edge':
                    if drawing_edge_from:
                        released_on_node = get_node_at_pos(mouse_pos)
                        if released_on_node and released_on_node != drawing_edge_from:
                            # Toggle edge
                            u, v = drawing_edge_from.id, released_on_node.id
                            if graph.has_edge(u, v):
                                graph.remove_edge(u, v)
                                mst_edges.clear() # --- NEW ---: Invalidate MST
                                print(f"Removed edge: {u}-{v}")
                            else:
                                # --- MODIFIED ---: Add edge WITH a random weight
                                weight = random.randint(1, 10)
                                graph.add_edge(u, v, weight=weight)
                                mst_edges.clear() # --- NEW ---: Invalidate MST
                                print(f"Added edge: {u}-{v} with weight {weight}")
                        
                        drawing_edge_from = None # Always reset on mouse up

        # --- Handle Key Presses ---
        if event.type == pygame.KEYDOWN:
            # 1. Tool selection shortcuts
            if event.key == pygame.K_s:
                current_mode = 'select_move'
                selected_node = None # Reset state
            elif event.key == pygame.K_a:
                current_mode = 'add_node'
            elif event.key == pygame.K_e:
                current_mode = 'add_edge'
            elif event.key == pygame.K_d:
                current_mode = 'del_node' # --- BUG FIX ---: Was 'del_edge'

            # --- NEW ---: Hotkeys for Prim's, Clear, and Planarity
            elif event.key == pygame.K_p: # 'P' for Prim's
                calculate_prims_mst()
            elif event.key == pygame.K_c: # 'C' for Clear
                mst_edges.clear()
                print("Cleared MST visualization.")
            elif event.key == pygame.K_l: # 'L' for pLanarity (was P)
                if graph.number_of_nodes() == 0:
                    print("Graph is empty.")
                elif nx.is_planar(graph):
                    print("Graph is Planar!")
                else:
                    print("Graph is NOT Planar!")

            # 2. Deletion
            if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                if selected_node and current_mode == 'select_move':
                    node_id_to_remove = selected_node.id
                    graph.remove_node(node_id_to_remove)
                    del nodes_dict[node_id_to_remove]
                    mst_edges.clear() # --- NEW ---: Invalidate MST
                    print(f"Removed node: {node_id_to_remove}")
                    selected_node = None
                    
                    # --- MODIFIED ---: Simplified ID logic
                    existing_ids = set(nodes_dict.keys())
                    i = 0
                    while i in existing_ids:
                        i += 1
                    next_node_id = i

    # --- Drawing ---
    SCREEN.fill(WHITE)

    # --- MODIFIED ---: Draw edges and weights, highlighting MST
    # 1. Draw Edges
    for u, v in graph.edges():
        if u in nodes_dict and v in nodes_dict: # Ensure nodes haven't been deleted
            node_u = nodes_dict[u]
            node_v = nodes_dict[v]
            
            # Check if this edge is in the MST
            edge_tuple = tuple(sorted((u, v)))
            
            if edge_tuple in mst_edges:
                # --- NEW ---: Draw MST edge
                pygame.draw.line(SCREEN, RED, (node_u.x, node_u.y), (node_v.x, node_v.y), 6) # Thicker, red
            else:
                # Draw normal edge
                pygame.draw.line(SCREEN, GRAY, (node_u.x, node_u.y), (node_v.x, node_v.y), 3)

            # --- NEW ---: Draw edge weight
            try:
                weight = graph[u][v].get('weight', '?')
                mid_x = (node_u.x + node_v.x) / 2
                mid_y = (node_u.y + node_v.y) / 2
                
                text_surface = weight_font.render(str(weight), True, BLACK)
                text_rect = text_surface.get_rect(center=(mid_x, mid_y))
                
                # Add a small white background for the text to make it readable
                bg_rect = text_rect.inflate(6, 4)
                pygame.draw.rect(SCREEN, WHITE, bg_rect)
                pygame.draw.rect(SCREEN, BLACK, bg_rect, 1) # Border
                SCREEN.blit(text_surface, text_rect)
            except Exception as e:
                pass # Should not happen

    # 2. Draw temporary edge
    if drawing_edge_from and current_mode == 'add_edge':
        pygame.draw.line(SCREEN, GREEN, (drawing_edge_from.x, drawing_edge_from.y), mouse_pos, 2)

    # 3. Draw Nodes
    for node_obj in nodes_dict.values():
        color = NODE_COLOR # Default
        
        # Highlight based on state
        if node_obj == selected_node and current_mode == 'select_move':
            color = SELECTED_NODE_COLOR
        elif node_obj == drawing_edge_from and current_mode == 'add_edge':
            color = GREEN
        elif node_obj.is_clicked(mouse_pos):
             # Simple hover effect
             if current_mode in ('select_move', 'add_edge', 'del_node'):
                color = HOVER_NODE_COLOR
        
        node_obj.draw(SCREEN, color)

    # 4. Draw UI Buttons (on top of everything)
    for btn in buttons:
        btn.draw(SCREEN, is_active=(current_mode == btn.mode_id), mouse_pos=mouse_pos)

    pygame.display.flip()
    #clock.tick(120) # Limit to 60 FPS

pygame.quit()