import pygame
import networkx as nx
import random
import collections
import heapq

pygame.init()

WIDTH, HEIGHT = 1280, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Graph Editor")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

BTN_LIGHT = (248, 249, 250)
BTN_LIGHT_HOVER = (233, 236, 239)
BTN_LIGHT_BORDER = (218, 220, 224)
BTN_LIGHT_TEXT = (33, 37, 41)

BTN_PRIMARY = (13, 110, 253)
BTN_PRIMARY_HOVER = (11, 94, 215)
BTN_PRIMARY_TEXT = (255, 255, 255)

NODE_RADIUS = 20
NODE_COLOR = BLUE
SELECTED_NODE_COLOR = RED
HOVER_NODE_COLOR = (100, 100, 255)

font = pygame.font.Font(None, 24)
btn_font = pygame.font.Font(None, 20)
weight_font = pygame.font.Font(None, 22)
dist_font = pygame.font.Font(None, 18)

graph = nx.Graph()
nodes_dict = {}
next_node_id = 0
mst_edges = set()
prims_weight = 0
bfs_edges = set()
component_count = 0
dfs_edges = set()
dijkstra_paths = {}
dijkstra_source = None

number_of_weights = 0
popup_active = False
text_in_popup = ""
input_box = pygame.Rect(0, 0, 200, 32)
input_box.center = SCREEN.get_rect().center

current_mode = 'select_move'

selected_node = None
dragging_node = None
drawing_edge_from = None

class Node:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y

    def draw(self, screen, color):
        pygame.draw.circle(screen, color, (self.x, self.y), NODE_RADIUS)
        pygame.draw.circle(screen, BLACK, (self.x, self.y), NODE_RADIUS, 2)

        text_surface = font.render(str(self.id), True, WHITE)
        text_rect = text_surface.get_rect(center=(self.x, self.y))
        screen.blit(text_surface, text_rect)

    def is_clicked(self, mouse_pos):
        return (self.x - mouse_pos[0])**2 + (self.y - mouse_pos[1])**2 < NODE_RADIUS**2

class Button:
    def __init__(self, x, y, w, h, text, mode_id):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.mode_id = mode_id
        self.border_radius = 6

    def draw(self, screen, is_active, mouse_pos):
        mouse_pressed = pygame.mouse.get_pressed()[0]
        is_hovering = self.rect.collidepoint(mouse_pos)
        is_being_pressed = is_hovering and mouse_pressed
        is_action_button = self.mode_id in ('run_prims', 'clear_mst', 'run_bfs', 'run_components')

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

        pygame.draw.rect(screen, bg_color, self.rect, border_radius=self.border_radius)
        if not (bg_color == BTN_PRIMARY or bg_color == BTN_PRIMARY_HOVER):
             pygame.draw.rect(screen, BTN_LIGHT_BORDER, self.rect, 1, border_radius=self.border_radius)

        text_surface = btn_font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        if is_being_pressed:
            text_rect.move_ip(0, 1)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

def get_node_at_pos(mouse_pos):
    for node_obj in nodes_dict.values():
        if node_obj.is_clicked(mouse_pos):
            return node_obj
    return None

def clear_visualizations():
    global mst_edges, prims_weight, bfs_edges, component_count, dfs_edges, dijkstra_paths, dijkstra_source
    mst_edges.clear()
    prims_weight = 0
    bfs_edges.clear()
    dfs_edges.clear()
    component_count = 0
    dijkstra_paths.clear()
    dijkstra_source = None

def calculate_prims_mst():
    global mst_edges, prims_weight
    clear_visualizations()

    if graph.number_of_nodes() < 1:
        print("Graph is empty. Cannot run Prim's.")
        return

    edges_without_weight = [(u, v) for u, v, data in graph.edges(data=True) if 'weight' not in data or data['weight'] is None]
    if edges_without_weight:
        print(f"ERROR: Cannot run Prim's. The following edges are missing weights: {edges_without_weight}")
        print("Please ensure all edges have weights before running Prim's.")
        return

    subgraph_to_process = graph

    if not nx.is_connected(graph):
        print("Graph is not connected. Running Prim's on the largest component.")
        try:
            largest_cc_nodes = max(nx.connected_components(graph), key=len)
            subgraph_to_process = graph.subgraph(largest_cc_nodes).copy()
        except ValueError:
            print("No components to run on.")
            return
    else:
        subgraph_to_process = graph

    if subgraph_to_process.number_of_nodes() < 1:
        print("No nodes in the component to process.")
        return
        
    if subgraph_to_process.number_of_edges() == 0 and subgraph_to_process.number_of_nodes() > 0:
        print("Component has nodes but no edges. MST weight is 0.")
        prims_weight = 0
        return

    try:
        prims_weight = 0
        in_mst = set()
        edge_heap = []

        start_node = list(subgraph_to_process.nodes())[0]
        in_mst.add(start_node)

        for neighbor, data in subgraph_to_process.adj[start_node].items():
            weight = data.get('weight')
            if weight is not None:
                heapq.heappush(edge_heap, (weight, start_node, neighbor))

        num_nodes_in_component = subgraph_to_process.number_of_nodes()
        while edge_heap and len(in_mst) < num_nodes_in_component:
            
            weight, u, v = heapq.heappop(edge_heap)

            if v in in_mst:
                continue

            in_mst.add(v)
            
            mst_edges.add(tuple(sorted((u, v))))
            prims_weight += weight

            for neighbor, data in subgraph_to_process.adj[v].items():
                if neighbor not in in_mst:
                    neighbor_weight = data.get('weight')
                    if neighbor_weight is not None:
                        heapq.heappush(edge_heap, (neighbor_weight, v, neighbor))

        print(f"Prim's MST (manual) calculated. Edges: {mst_edges}, Total Weight: {prims_weight}")

    except Exception as e:
        print(f"An error occurred during Prim's calculation: {e}")
        print("Ensure all edges in the processed component have valid numeric weights.")

def run_bfs(no_comps=0):
    global bfs_edges
    
    if graph.number_of_nodes() == 0:
        print("Graph is empty. Cannot run BFS.")
        return
        
    clear_visualizations()
    print("Running BFS for all components...")

    visited = set()
    queue = collections.deque()
    
    has_edges = False
    count=0
    for node in graph.nodes():
        if node not in visited:
            count+=1
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
    if(no_comps==1):
        bfs_edges=set()
        return count
def calculate_components():
    global component_count
    clear_visualizations()
    component_count = run_bfs(1)
    print(f"Graph has {component_count} connected component(s).")

def run_dfs():
    global dfs_edges
    if graph.number_of_nodes() == 0:
        print("Graph is empty. Cannot run DFS.")
        return

    clear_visualizations()
    print("Running DFS for all components...")

    visited = set()
    for start_node in graph.nodes():
        if start_node not in visited:
            dfs(start_node,visited,dfs_edges)
            
    print(f"DFS complete. Edges found: {dfs_edges}")
def dfs(node,visited,dfs_edges):
    visited.add(node)
    for neighbor in graph.neighbors(node):
        if(neighbor not in visited):
            dfs_edges.add(tuple(sorted((node,neighbor))))
            dfs(neighbor,visited,dfs_edges)

def dijikstra(initial_node):
    global dijkstra_paths, dijkstra_source
    clear_visualizations()
    dijkstra_source = initial_node
    predecessors = {node: None for node in graph.nodes()}

    dist_dict={}
    for node in graph.nodes():
        if(node==initial_node):
            dist_dict[node]=0
        else:
            dist_dict[node]=float('inf')
    visited=set()
    priorityq=[]
    heapq.heappush(priorityq,(0,initial_node))
    while(len(priorityq)!=0):
        curr_dist, curr_node = heapq.heappop(priorityq)
        if(curr_node in visited):
            continue
        visited.add(curr_node)
        for neighbor in graph.neighbors(curr_node):
            weight = graph[curr_node][neighbor].get('weight', 1)
            new_dist=curr_dist + weight
            if(new_dist<dist_dict[neighbor]):
                dist_dict[neighbor]=new_dist
                predecessors[neighbor] = curr_node
                heapq.heappush(priorityq,(new_dist,neighbor))
    print(dist_dict)

    for node, pred in predecessors.items():
        if pred is not None:
             dijkstra_paths[node] = (pred, dist_dict[node])
    dijkstra_paths[initial_node] = (None, 0)

buttons = [
    Button(10, 10, 100, 30, "Select (S)", 'select_move'),
    Button(115, 10, 100, 30, "Add Node (A)", 'add_node'),
    Button(220, 10, 100, 30, "Add Edge (E)", 'add_edge'),
    Button(325, 10, 100, 30, "Del Node (D)", 'del_node'),
    Button(430, 10, 90, 30, "Prim's (P)", 'run_prims'),
    Button(525, 10, 80, 30, "BFS (B)", 'run_bfs'),
    Button(610, 10, 80, 30, "DFS (F)", 'run_dfs'),
    Button(695, 10, 100, 30, "Dijkstra(J)", 'run_dijkstra_mode'),
    Button(800, 10, 110, 30, "Components (K)", 'run_components'),
    Button(915, 10, 80, 30, "Clear (C)", 'clear_mst')
]

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:

                clicked_on_input_box = False
                if popup_active and input_box.collidepoint(event.pos):
                    clicked_on_input_box = True

                ui_clicked = False
                if not clicked_on_input_box:
                    for btn in buttons:
                        if btn.is_clicked(mouse_pos):
                            if btn.mode_id == 'run_prims': calculate_prims_mst()
                            elif btn.mode_id == 'run_bfs': run_bfs()
                            elif btn.mode_id == 'run_dfs': run_dfs()
                            elif btn.mode_id == 'run_components': calculate_components()
                            elif btn.mode_id == 'clear_mst':
                                clear_visualizations()
                                print("Cleared all visualizations.")
                            else:
                                current_mode = btn.mode_id

                            if btn.mode_id not in ('run_prims', 'run_bfs', 'run_components', 'clear_mst'):
                                selected_node = None
                                dragging_node = None
                                drawing_edge_from = None
                            ui_clicked = True
                            break

                if ui_clicked or clicked_on_input_box:
                    continue

                clicked_node = get_node_at_pos(mouse_pos)
                if current_mode == 'run_dijkstra_mode' and clicked_node:
                    dijikstra(clicked_node.id)
                elif current_mode == 'select_move':
                    selected_node = clicked_node
                    if clicked_node: dragging_node = clicked_node
                elif current_mode == 'add_node':
                    if not clicked_node:
                        new_node = Node(next_node_id, mouse_pos[0], mouse_pos[1])
                        nodes_dict[next_node_id] = new_node
                        graph.add_node(next_node_id)
                        clear_visualizations()
                        print(f"Added node: {next_node_id}")
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
                        if node_id_to_remove in nodes_dict:
                            graph.remove_node(node_id_to_remove)
                            del nodes_dict[node_id_to_remove]
                            number_of_weights = len([(u,v) for u,v,d in graph.edges(data=True) if 'weight' in d])
                            clear_visualizations()
                            print(f"Removed node: {node_id_to_remove}")
                            if selected_node and selected_node.id == node_id_to_remove:
                                selected_node = None
                            existing_ids = set(nodes_dict.keys())
                            i = 0
                            while i in existing_ids: i += 1
                            next_node_id = i

        if event.type == pygame.KEYDOWN:

            should_activate_popup = (len(graph.edges()) > number_of_weights)
            if popup_active and should_activate_popup:
                if event.key == pygame.K_RETURN:
                    try:
                        entered_weight = int(text_in_popup)
                        if entered_weight <= 0:
                             print("Weight must be positive.")
                             text_in_popup = ""
                        else:
                            assigned = False
                            for u, v, data in reversed(list(graph.edges(data=True))):
                                if 'weight' not in data or data['weight'] is None:
                                    graph[u][v]['weight'] = entered_weight
                                    print(f"Assigned weight {entered_weight} to edge ({u}-{v})")
                                    assigned = True
                                    break

                            if assigned:
                                text_in_popup = ""
                                number_of_weights += 1
                                if len(graph.edges()) <= number_of_weights:
                                    popup_active = False
                            else:
                                print("Internal Error: Could not find edge missing weight, though expected.")
                                text_in_popup = ""

                    except ValueError:
                        print("Invalid input. Please enter a number.")
                        text_in_popup = ""

                elif event.key == pygame.K_BACKSPACE:
                    text_in_popup = text_in_popup[:-1]
                elif event.unicode.isdigit():
                    text_in_popup += event.unicode
                continue

            if event.key == pygame.K_s: current_mode = 'select_move'; selected_node = None
            elif event.key == pygame.K_a: current_mode = 'add_node'
            elif event.key == pygame.K_e: current_mode = 'add_edge'
            elif event.key == pygame.K_d: current_mode = 'del_node'
            elif event.key == pygame.K_p: calculate_prims_mst()
            elif event.key == pygame.K_b: run_bfs()
            elif event.key == pygame.K_f: run_dfs()
            elif event.key == pygame.K_j: current_mode = 'run_dijkstra_mode'
            elif event.key == pygame.K_k: calculate_components()
            elif event.key == pygame.K_c: clear_visualizations(); print("Cleared all visualizations.")
            elif event.key == pygame.K_l:
                if graph.number_of_nodes() == 0: print("Graph is empty.")
                elif nx.is_planar(graph): print("Graph is Planar!")
                else: print("Graph is NOT Planar!")

            if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                 if not (popup_active and should_activate_popup and event.key == pygame.K_BACKSPACE):
                    if selected_node and current_mode == 'select_move':
                        node_id_to_remove = selected_node.id
                        if node_id_to_remove in nodes_dict:
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

        if event.type == pygame.MOUSEMOTION:
            if dragging_node and current_mode == 'select_move':
                dragging_node.x, dragging_node.y = mouse_pos
                if len(mst_edges) > 0 or len(bfs_edges) > 0 or len(dfs_edges) > 0 or component_count > 0:
                    clear_visualizations()
                    print("Node moved, cleared visualizations.")

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if current_mode == 'select_move':
                    dragging_node = None
                elif current_mode == 'add_edge':
                    if drawing_edge_from:
                        released_on_node = get_node_at_pos(mouse_pos)
                        if released_on_node and released_on_node != drawing_edge_from:
                            u, v = drawing_edge_from.id, released_on_node.id
                            if graph.has_edge(u, v):
                                had_weight = 'weight' in graph[u][v] and graph[u][v]['weight'] is not None
                                graph.remove_edge(u, v)
                                if had_weight:
                                    number_of_weights -= 1
                                clear_visualizations()
                                print(f"Removed edge: {u}-{v}")
                            else:
                                graph.add_edge(u, v)
                                clear_visualizations()
                        drawing_edge_from = None

    SCREEN.fill(WHITE)

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
            elif edge_tuple in dfs_edges:
                line_color = PURPLE
                line_width = 6
            elif (dijkstra_paths.get(v, (None,))[0] == u) or (dijkstra_paths.get(u, (None,))[0] == v):
                line_color = ORANGE
                line_width = 6


            pygame.draw.line(SCREEN, line_color, (node_u.x, node_u.y), (node_v.x, node_v.y), line_width)

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

    should_activate_popup = (len(graph.edges()) > number_of_weights)
    if should_activate_popup:
        popup_active = True
        LABEL_COLOR = (80, 80, 100)
        label_text = "Add weight for the drawn edge:"
        txt_surface = font.render(text_in_popup, True, WHITE)
        width = max(200, txt_surface.get_width() + 10)

        input_box_x = 20
        input_box_y = HEIGHT - 50
        input_box = pygame.Rect(input_box_x, input_box_y, width, 32)

        label_surface = btn_font.render(label_text, True, LABEL_COLOR)
        label_rect = label_surface.get_rect(bottomleft=(input_box.left, input_box.top - 5))

        SCREEN.blit(label_surface, label_rect)

        pygame.draw.rect(SCREEN, BLACK, input_box, border_radius=5)
        SCREEN.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(SCREEN, WHITE, input_box, 2, border_radius=5)
    else:
         if popup_active:
              popup_active = False
              text_in_popup = ""

    if drawing_edge_from and current_mode == 'add_edge':
        pygame.draw.line(SCREEN, GREEN, (drawing_edge_from.x, drawing_edge_from.y), mouse_pos, 2)

    for node_obj in nodes_dict.values():
        color = NODE_COLOR
        if node_obj == selected_node and current_mode == 'select_move': color = SELECTED_NODE_COLOR
        elif node_obj == drawing_edge_from and current_mode == 'add_edge': color = GREEN
        elif node_obj.is_clicked(mouse_pos):
             if current_mode in ('select_move', 'add_edge', 'del_node'): color = HOVER_NODE_COLOR
        node_obj.draw(SCREEN, color)
        if node_obj.id in dijkstra_paths:
             dist = dijkstra_paths[node_obj.id][1]
             dist_surf = dist_font.render(str(dist), True, WHITE)
             dist_rect = dist_surf.get_rect(center=(node_obj.x, node_obj.y - NODE_RADIUS - 10))
             pygame.draw.rect(SCREEN, ORANGE, dist_rect.inflate(6,4), border_radius=4)
             SCREEN.blit(dist_surf, dist_rect)

    for btn in buttons:
        btn.draw(SCREEN, is_active=(current_mode == btn.mode_id), mouse_pos=mouse_pos)

    if prims_weight is not None and prims_weight > 0:
        text_str = f"MST Total Weight: {prims_weight}"
        text_surface = btn_font.render(text_str, True, BLACK)
        text_rect = text_surface.get_rect(topleft=(10, 60))
        bg_rect = text_rect.inflate(10, 8)
        pygame.draw.rect(SCREEN, WHITE, bg_rect)
        pygame.draw.rect(SCREEN, BLACK, bg_rect, 2)
        SCREEN.blit(text_surface, text_rect)

    if component_count > 0:
        text_str = f"Components: {component_count}"
        text_surface = btn_font.render(text_str, True, BLACK)
        text_rect = text_surface.get_rect(topleft=(10, 85))
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