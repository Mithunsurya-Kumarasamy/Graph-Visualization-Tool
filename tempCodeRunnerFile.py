import pygame
import networkx as nx

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

# --- Graph Data Structure ---
graph = nx.Graph()
nodes_dict = {}    # {node_id: NodeObject}
next_node_id = 0

# --- State Management ---
# We have three modes:
# 'select_move': Click to select, drag to move, 'Delete' to remove.
# 'add_node': Click on empty space to add a node.
# 'add_edge': Click-drag from one node to another to add/remove an edge.
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


# --- Create UI Buttons ---
buttons = [
    Button(10, 10, 160, 40, "Select/Move (S)", 'select_move'),
    Button(180, 10, 160, 40, "Add Node (A)", 'add_node'),
    Button(350, 10, 160, 40, "Add/Remove Edge (E)", 'add_edge'),
    Button(520,10,160,40,"Delete Node (D)", 'del_node')
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
                        print(f"Added node: {next_node_id}")
                        mis_num = sorted(list(nodes_dict.keys()))
                        flag = False
                        for i in range(0, len(mis_num)):
                            if i != mis_num[i]:
                                x = i
                                flag = True
                                break
                        
                        if flag == False:
                            next_node_id = len(mis_num)
                        else:
                            next_node_id = x
                        
                elif current_mode == 'add_edge':
                    if clicked_node:
                        # Start drawing an edge
                        drawing_edge_from = clicked_node
                elif current_mode == 'del_node':
                    if presently_clicked_node:
                        node_id_to_remove = presently_clicked_node.id
                        graph.remove_node(node_id_to_remove)
                        del nodes_dict[node_id_to_remove]
                        print(f"Removed node: {node_id_to_remove}")
                        selected_node = None
                        mis_num = sorted(list(nodes_dict.keys()))
                        flag = False
                        for i in range(0, len(mis_num)):
                            if i != mis_num[i]:
                                x = i
                                flag = True
                                break
                        
                        if flag == False:
                            next_node_id = len(mis_num)
                        else:
                            next_node_id = x


        # --- Handle Mouse Motion ---
        if event.type == pygame.MOUSEMOTION:
            if dragging_node and current_mode == 'select_move':
                dragging_node.x, dragging_node.y = mouse_pos

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
                                print(f"Removed edge: {u}-{v}")
                            else:
                                graph.add_edge(u, v)
                                print(f"Added edge: {u}-{v}")
                    
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
                current_mode = 'del_edge'

            # 2. Deletion
            if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                if selected_node and current_mode == 'select_move':
                    node_id_to_remove = selected_node.id
                    graph.remove_node(node_id_to_remove)
                    del nodes_dict[node_id_to_remove]
                    print(f"Removed node: {node_id_to_remove}")
                    selected_node = None
                    mis_num = sorted(list(nodes_dict.keys()))
                    flag = False
                    for i in range(0, len(mis_num)):
                        if i != mis_num[i]:
                            x = i
                            flag = True
                            break
                    
                    if flag == False:
                        next_node_id = len(mis_num)
                    else:
                        next_node_id = x
            # 3. Planarity Check
            if event.key == pygame.K_p:
                if graph.number_of_nodes() == 0:
                    print("Graph is empty.")
                elif nx.is_planar(graph):
                    print("Graph is Planar!")
                else:
                    print("Graph is NOT Planar!")

    # --- Drawing ---
    SCREEN.fill(WHITE)

    # 1. Draw Edges
    for u, v in graph.edges():
        if u in nodes_dict and v in nodes_dict: # Ensure nodes haven't been deleted
            node_u = nodes_dict[u]
            node_v = nodes_dict[v]
            pygame.draw.line(SCREEN, GRAY, (node_u.x, node_u.y), (node_v.x, node_v.y), 3)

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
            if current_mode == 'select_move' or current_mode == 'add_edge':
                color = HOVER_NODE_COLOR
        
        node_obj.draw(SCREEN, color)

    # 4. Draw UI Buttons (on top of everything)
    for btn in buttons:
        btn.draw(SCREEN, is_active=(current_mode == btn.mode_id), mouse_pos=mouse_pos)

    pygame.display.flip()
    #clock.tick(120) # Limit to 60 FPS

pygame.quit()

