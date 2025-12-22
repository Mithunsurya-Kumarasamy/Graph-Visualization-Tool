import pygame
import networkx as nx
import random
import collections

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

# --- NEW Bootstrap-style Button Colors ---
BTN_LIGHT = (248, 249, 250)      # Default button color
BTN_LIGHT_HOVER = (233, 236, 239) # Default button hover
BTN_LIGHT_BORDER = (218, 220, 224) # Border for default
BTN_LIGHT_TEXT = (33, 37, 41)     # Dark text for light buttons

BTN_PRIMARY = (13, 110, 253)      # Active button color (Bootstrap Blue)
BTN_PRIMARY_HOVER = (11, 94, 215) # Active button hover
BTN_PRIMARY_TEXT = (255, 255, 255)  # White text for dark buttons
# --- END NEW Button Colors ---

# --- Node Settings ---
NODE_RADIUS = 20
NODE_COLOR = BLUE
SELECTED_NODE_COLOR = RED
HOVER_NODE_COLOR = (100, 100, 255)

# --- Font ---
font = pygame.font.Font(None, 24)
btn_font = pygame.font.Font(None, 20)
weight_font = pygame.font.Font(None, 22)


# --- Graph Data Structure ---
graph = nx.Graph()
nodes_dict = {}  # {node_id: NodeObject}
next_node_id = 0
mst_edges = set()
prims_weight = 0
bfs_edges = set()      # For BFS visualization
component_count = 0  # For component count display

# --- Manual Weight Input Variables ---
number_of_weights = 0 # Tracks edges that HAVE a weight assigned
popup_active = False # Start inactive
text_in_popup = ""
# Center the input box initially, will be updated in drawing loop
input_box = pygame.Rect(0, 0, 200, 32)
input_box.center = SCREEN.get_rect().center


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
        # Simple distance check for click collision
        return (self.x - mouse_pos[0])**2 + (self.y - mouse_pos[1])**2 < NODE_RADIUS**2

# --- Button Class ---
class Button:
    def __init__(self, x, y, w, h, text, mode_id):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.mode_id = mode_id # The mode this button sets
        self.border_radius = 6  # Bootstrap-style rounded corners

    def draw(self, screen, is_active, mouse_pos):
        mouse_pressed = pygame.mouse.get_pressed()[0]
        is_hovering = self.rect.collidepoint(mouse_pos)
        is_being_pressed = is_hovering and mouse_pressed
        # Include all action button IDs here
        is_action_button = self.mode_id in ('run_prims', 'clear_mst', 'run_bfs', 'run_components')

        # --- Select Colors ---
        if is_being_pressed:
            bg_color = BTN_PRIMARY_HOVER
            text_color = BTN_PRIMARY_TEXT
        elif is_active and not is_action_button:
            bg_color = BTN_PRIMARY
            text_color = BTN_PRIMARY_TEXT
        elif is_hovering:
            bg_color = BTN_LIGHT_HOVER
            text_color = BTN_LIGHT_TEXT
        else:
            bg_color = BTN_LIGHT
            text_color = BTN_LIGHT_TEXT

        # --- Draw Button ---
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=self.border_radius)
        if not (bg_color == BTN_PRIMARY or bg_color == BTN_PRIMARY_HOVER):
             pygame.draw.rect(screen, BTN_LIGHT_BORDER, self.rect, 1, border_radius=self.border_radius)

        # Draw Text
        text_surface = btn_font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        if is_being_pressed:
            text_rect.move_ip(0, 1) # Shift text down slightly when pressed
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

def clear_visualizations():
    """Clears all algorithm visualization data."""
    global mst_edges, prims_weight, bfs_edges, component_count
    mst_edges.clear()
    prims_weight = 0
    bfs_edges.clear()
    component_count = 0

# --- Algorithm Functions ---
def calculate_prims_mst():
    """Calculates MST using Prim's and updates visualization variables."""
    global mst_edges, prims_weight
    clear_visualizations() # Clear others first

    if graph.number_of_nodes() < 1:
        print("Graph is empty. Cannot run Prim's.")
        return

    # Check for missing weights before proceeding
    edges_without_weight = [(u, v) for u, v, data in graph.edges(data=True) if 'weight' not in data or data['weight'] is None]
    if edges_without_weight:
        print(f"ERROR: Cannot run Prim's. The following edges are missing weights: {edges_without_weight}")
        print("Please ensure all edges have weights before running Prim's.")
        return # Stop if weights are missing

    subgraph_to_process = graph # Assume connected initially

    if not nx.is_connected(graph):
        print("Graph is not connected. Running Prim's on the largest component.")
        try:
            largest_cc_nodes = max(nx.connected_components(graph), key=len)
            subgraph_to_process = graph.subgraph(largest_cc_nodes).copy() # Use a copy to avoid modifying original graph data if needed later
        except ValueError:
             print("No components to run on.")
             return
    else:
        subgraph_to_process = graph

    if subgraph_to_process.number_of_nodes() < 1:
         print("No nodes in the component to process.")
         return
    # Check if the component has edges - MST requires edges
    if subgraph_to_process.number_of_edges() == 0 and subgraph_to_process.number_of_nodes() > 0:
        print("Component has nodes but no edges. MST weight is 0.")
        prims_weight = 0 # Explicitly set weight to 0
        # No edges to add to mst_edges
        return

    try:
        mst_graph = nx.minimum_spanning_tree(subgraph_to_process, algorithm='prim', weight='weight')
        for u, v in mst_graph.edges():
            mst_edges.add(tuple(sorted((u, v))))
        prims_weight = mst_graph.size(weight='weight') # Calculate total weight
        # Ensure weight is treated as a number, default to 0 if calculation fails unexpectedly
        prims_weight = prims_weight if prims_weight is not None else 0
        print(f"Prim's MST calculated. Edges: {mst_edges}, Total Weight: {prims_weight}")
    except nx.NetworkXException as e:
        print(f"Could not run Prim's: {e}")
        print("Ensure all edges in the processed component have numeric weights.")
    except Exception as e:
        print(f"An error occurred during Prim's calculation: {e}")

def run_bfs():
    """Calculates BFS tree for ALL components and updates visualization variables."""
    global bfs_edges
    
    if graph.number_of_nodes() == 0:
        print("Graph is empty. Cannot run BFS.")
        return
        
    clear_visualizations()
    print("Running BFS for all components...")

    visited = set()
    queue = collections.deque()
    
    has_edges = False

    for node in graph.nodes():
        if node not in visited:
            print(f"Starting BFS for new component from node {node}...")
            visited.add(node)
            queue.append(node)
            
            while queue:
                current_node = queue.popleft() 
                
                for neighbor in graph.neighbors(current_node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                        bfs_edges.add(tuple(sorted((current_node, neighbor))))
                        has_edges = True
    if has_edges:
        print(f"BFS complete. Edges found: {bfs_edges}")
    elif graph.number_of_nodes() > 0:
        print("BFS complete. Graph has nodes but no edges.")
    else:
        print("BFS complete. Graph is empty.")

def calculate_components():
    """Calculates connected components and updates display variable."""
    global component_count
    clear_visualizations() # Clear others first
    component_count = nx.number_connected_components(graph)
    print(f"Graph has {component_count} connected component(s).")

# --- Create UI Buttons ---
buttons = [
    Button(10, 10, 140, 40, "Select/Move (S)", 'select_move'),
    Button(160, 10, 140, 40, "Add Node (A)", 'add_node'),
    Button(310, 10, 160, 40, "Add/Remove Edge (E)", 'add_edge'),
    Button(480, 10, 140, 40, "Delete Node (D)", 'del_node'),
    Button(630, 10, 150, 40, "Run Prim's (P)", 'run_prims'),
    Button(790, 10, 130, 40, "Run BFS (B)", 'run_bfs'),
    Button(930, 10, 160, 40, "Components (K)", 'run_components'),
    Button(1100, 10, 130, 40, "Clear Viz (C)", 'clear_mst'),
]

# --- Main Game Loop ---
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Handle Mouse Click Down ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click

                # --- Manual Weight Input Click Logic ---
                clicked_on_input_box = False
                if popup_active and input_box.collidepoint(event.pos):
                    clicked_on_input_box = True # User clicked inside the box
                # --- End Manual Weight Input Click Logic ---

                # Handle Button Clicks (if not clicking input box)
                ui_clicked = False
                if not clicked_on_input_box: # Only process buttons if not clicking input box
                    for btn in buttons:
                        if btn.is_clicked(mouse_pos):
                            if btn.mode_id == 'run_prims': calculate_prims_mst()
                            elif btn.mode_id == 'run_bfs': run_bfs()
                            elif btn.mode_id == 'run_components': calculate_components()
                            elif btn.mode_id == 'clear_mst':
                                clear_visualizations()
                                print("Cleared all visualizations.")
                            else: # Mode-setting button
                                current_mode = btn.mode_id

                            # Reset interaction state only if changing modes, not running actions
                            if btn.mode_id not in ('run_prims', 'run_bfs', 'run_components', 'clear_mst'):
                                selected_node = None
                                dragging_node = None
                                drawing_edge_from = None
                            ui_clicked = True
                            break

                if ui_clicked or clicked_on_input_box: # Skip graph interaction if UI handled it
                    continue

                # Handle graph clicks (only if no UI element was clicked)
                clicked_node = get_node_at_pos(mouse_pos)

                if current_mode == 'select_move':
                    selected_node = clicked_node # Select or deselect
                    if clicked_node: dragging_node = clicked_node # Start drag if node clicked

                elif current_mode == 'add_node':
                    if not clicked_node: # Clicked empty space
                        new_node = Node(next_node_id, mouse_pos[0], mouse_pos[1])
                        nodes_dict[next_node_id] = new_node
                        graph.add_node(next_node_id)
                        clear_visualizations()
                        print(f"Added node: {next_node_id}")
                        # Find next available ID
                        existing_ids = set(nodes_dict.keys())
                        i = 0
                        while i in existing_ids: i += 1
                        next_node_id = i

                elif current_mode == 'add_edge':
                    if clicked_node:
                        drawing_edge_from = clicked_node

                elif current_mode == 'del_node':
                    if clicked_node:
                        node_id_to_remove = clicked_node.id
                        if node_id_to_remove in nodes_dict: # Check if node exists
                            graph.remove_node(node_id_to_remove)
                            del nodes_dict[node_id_to_remove]
                            # Recalculate number of edges WITH weights
                            number_of_weights = len([(u,v) for u,v,d in graph.edges(data=True) if 'weight' in d])
                            clear_visualizations()
                            print(f"Removed node: {node_id_to_remove}")
                            if selected_node and selected_node.id == node_id_to_remove:
                                selected_node = None # Deselect if deleted
                            # Find next available ID
                            existing_ids = set(nodes_dict.keys())
                            i = 0
                            while i in existing_ids: i += 1
                            next_node_id = i

        # --- Handle Key Presses ---
        if event.type == pygame.KEYDOWN:

            # --- Pop-up Input Handling (ONLY if active) ---
            should_activate_popup = (len(graph.edges()) > number_of_weights)
            if popup_active and should_activate_popup:
                if event.key == pygame.K_RETURN:
                    try:
                        entered_weight = int(text_in_popup)
                        if entered_weight <= 0:
                             print("Weight must be positive.")
                             text_in_popup = "" # Clear invalid input
                        else:
                            assigned = False
                            # Iterate in reverse to find the last added edge potentially missing weight
                            for u, v, data in reversed(list(graph.edges(data=True))):
                                if 'weight' not in data or data['weight'] is None:
                                    graph[u][v]['weight'] = entered_weight
                                    print(f"Assigned weight {entered_weight} to edge ({u}-{v})")
                                    assigned = True
                                    break # Assign only to one

                            if assigned:
                                text_in_popup = ""
                                number_of_weights += 1
                                # Check if more weights are needed after assignment
                                if len(graph.edges()) <= number_of_weights:
                                    popup_active = False # Deactivate if all weights are assigned
                            else:
                                print("Internal Error: Could not find edge missing weight, though expected.")
                                text_in_popup = "" # Clear text on error too
                                # Consider deactivating popup here too? popup_active = False

                    except ValueError:
                        print("Invalid input. Please enter a number.")
                        text_in_popup = "" # Clear invalid text

                elif event.key == pygame.K_BACKSPACE:
                    text_in_popup = text_in_popup[:-1]
                elif event.unicode.isdigit(): # Only allow digits
                    text_in_popup += event.unicode
                # Prevent other hotkeys while typing in popup
                continue # Skip the rest of KEYDOWN handling for this event

            # --- General Hotkeys (only run if pop-up is NOT active) ---
            if event.key == pygame.K_s: current_mode = 'select_move'; selected_node = None
            elif event.key == pygame.K_a: current_mode = 'add_node'
            elif event.key == pygame.K_e: current_mode = 'add_edge'
            elif event.key == pygame.K_d: current_mode = 'del_node'
            elif event.key == pygame.K_p: calculate_prims_mst()
            elif event.key == pygame.K_b: run_bfs()
            elif event.key == pygame.K_k: calculate_components()
            elif event.key == pygame.K_c: clear_visualizations(); print("Cleared all visualizations.")
            elif event.key == pygame.K_l:
                if graph.number_of_nodes() == 0: print("Graph is empty.")
                elif nx.is_planar(graph): print("Graph is Planar!")
                else: print("Graph is NOT Planar!")

            # Deletion Hotkey (Allow even if popup was active but handled above)
            if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                 # Check again to ensure pop-up didn't handle the backspace
                 if not (popup_active and should_activate_popup and event.key == pygame.K_BACKSPACE):
                    if selected_node and current_mode == 'select_move':
                        node_id_to_remove = selected_node.id
                        if node_id_to_remove in nodes_dict: # Check existence
                            graph.remove_node(node_id_to_remove)
                            del nodes_dict[node_id_to_remove]
                            number_of_weights = len([(u,v) for u,v,d in graph.edges(data=True) if 'weight' in d])
                            clear_visualizations()
                            print(f"Removed node: {node_id_to_remove}")
                            selected_node = None

                            existing_ids = set(nodes_dict.keys())
                            i = 0
                            while i in existing_ids: i+= 1
                            next_node_id = i

        # --- Handle Mouse Motion ---
        if event.type == pygame.MOUSEMOTION:
            if dragging_node and current_mode == 'select_move':
                dragging_node.x, dragging_node.y = mouse_pos
                if len(mst_edges) > 0 or len(bfs_edges) > 0 or component_count > 0:
                    clear_visualizations()
                    print("Node moved, cleared visualizations.")

        # --- Handle Mouse Click Up ---
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Left click up
                if current_mode == 'select_move':
                    dragging_node = None # Stop dragging
                elif current_mode == 'add_edge':
                    if drawing_edge_from:
                        released_on_node = get_node_at_pos(mouse_pos)
                        if released_on_node and released_on_node != drawing_edge_from:
                            u, v = drawing_edge_from.id, released_on_node.id
                            if graph.has_edge(u, v):
                                # Removing an edge that might have had a weight
                                had_weight = 'weight' in graph[u][v] and graph[u][v]['weight'] is not None
                                graph.remove_edge(u, v)
                                if had_weight:
                                    number_of_weights -= 1 # Decrement count ONLY if it had a weight
                                clear_visualizations()
                                print(f"Removed edge: {u}-{v}")
                            else:
                                graph.add_edge(u, v) # Add edge without weight initially
                                clear_visualizations()
                                # The pop-up will be triggered in the drawing loop
                        drawing_edge_from = None # Reset edge drawing state

    # --- Drawing ---
    SCREEN.fill(WHITE)

    # 1. Draw Edges
    for u, v in graph.edges():
        if u in nodes_dict and v in nodes_dict:
            node_u = nodes_dict[u]
            node_v = nodes_dict[v]
            edge_tuple = tuple(sorted((u, v)))

            line_color = GRAY
            line_width = 3
            if edge_tuple in mst_edges:
                line_color = RED
                line_width = 6
            elif edge_tuple in bfs_edges:
                line_color = GREEN
                line_width = 6

            pygame.draw.line(SCREEN, line_color, (node_u.x, node_u.y), (node_v.x, node_v.y), line_width)

            # Draw edge weight or '?'
            try:
                if 'weight' in graph[u][v] and graph[u][v]['weight'] is not None:
                    weight_text = str(graph[u][v]['weight'])
                    text_color = BLACK
                else:
                    weight_text = '?'
                    text_color = RED

                mid_x = (node_u.x + node_v.x) / 2
                mid_y = (node_u.y + node_v.y) / 2
                text_surface = weight_font.render(weight_text, True, text_color)
                text_rect = text_surface.get_rect(center=(mid_x, mid_y))
                bg_rect = text_rect.inflate(6, 4)
                pygame.draw.rect(SCREEN, WHITE, bg_rect)
                pygame.draw.rect(SCREEN, BLACK, bg_rect, 1)
                SCREEN.blit(text_surface, text_rect)
            except KeyError: pass
            except Exception as e: pass

    # --- Draw Weight Input Pop-up ---
    should_activate_popup = (len(graph.edges()) > number_of_weights)
    if should_activate_popup:
        popup_active = True # Ensure it's active if needed
        LABEL_COLOR = (80, 80, 100)
        label_text = "Add weight for the drawn edge:"
        txt_surface = font.render(text_in_popup, True, WHITE)
        width = max(200, txt_surface.get_width() + 10)

        # Position Input Box Bottom-Left
        input_box_x = 20
        input_box_y = HEIGHT - 50
        input_box = pygame.Rect(input_box_x, input_box_y, width, 32)

        # Render and Position Label
        label_surface = btn_font.render(label_text, True, LABEL_COLOR)
        label_rect = label_surface.get_rect(bottomleft=(input_box.left, input_box.top - 5))

        # Draw Label
        SCREEN.blit(label_surface, label_rect)

        # Draw Input Box
        pygame.draw.rect(SCREEN, BLACK, input_box, border_radius=5)
        SCREEN.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(SCREEN, WHITE, input_box, 2, border_radius=5)
    else:
         # Ensure popup becomes inactive if condition is no longer met
         # (e.g., edge removed before weight assigned)
         if popup_active:
              popup_active = False
              text_in_popup = "" # Clear any leftover text

    # 2. Draw temporary edge
    if drawing_edge_from and current_mode == 'add_edge':
        pygame.draw.line(SCREEN, GREEN, (drawing_edge_from.x, drawing_edge_from.y), mouse_pos, 2)

    # 3. Draw Nodes
    for node_obj in nodes_dict.values():
        color = NODE_COLOR
        if node_obj == selected_node and current_mode == 'select_move': color = SELECTED_NODE_COLOR
        elif node_obj == drawing_edge_from and current_mode == 'add_edge': color = GREEN
        elif node_obj.is_clicked(mouse_pos):
             if current_mode in ('select_move', 'add_edge', 'del_node'): color = HOVER_NODE_COLOR
        node_obj.draw(SCREEN, color)

    # 4. Draw UI Buttons
    for btn in buttons:
        btn.draw(SCREEN, is_active=(current_mode == btn.mode_id), mouse_pos=mouse_pos)

    # 5. Draw MST Total Weight
    if prims_weight is not None and prims_weight > 0: # Check not None
        text_str = f"MST Total Weight: {prims_weight}"
        text_surface = btn_font.render(text_str, True, BLACK)
        text_rect = text_surface.get_rect(topleft=(10, 60))
        bg_rect = text_rect.inflate(10, 8)
        pygame.draw.rect(SCREEN, WHITE, bg_rect)
        pygame.draw.rect(SCREEN, BLACK, bg_rect, 2)
        SCREEN.blit(text_surface, text_rect)

    # 6. Draw Component Count
    if component_count > 0:
        text_str = f"Components: {component_count}"
        text_surface = btn_font.render(text_str, True, BLACK)
        text_rect = text_surface.get_rect(topleft=(10, 85)) # Positioned below MST weight
        bg_rect = text_rect.inflate(10, 8)
        pygame.draw.rect(SCREEN, WHITE, bg_rect)
        pygame.draw.rect(SCREEN, BLACK, bg_rect, 2)
        SCREEN.blit(text_surface, text_rect)
    
    if selected_node and current_mode == 'select_move':
        if selected_node.id in graph:
            node_id = selected_node.id
            degree = graph.degree(node_id)
            text = f"Node {node_id} Degree:{degree}"
            text_surface = btn_font.render(text, True, BLACK)
            text_rect = text_surface.get_rect(topleft=(10, 110))
            bg_rect = text_rect.inflate(10, 8)

            pygame.draw.rect(SCREEN, WHITE, bg_rect)
            pygame.draw.rect(SCREEN, BLACK, bg_rect, 2)
            SCREEN.blit(text_surface, text_rect)


    pygame.display.flip()

pygame.quit()