import pygame
import math
from heapq import heappush, heappop

# color for different cell types
cell_colors = {
    "default": (240, 240, 240),  # white for default cell
    "trap": (206, 147, 216),     # purple for trap cell
    "reward": (76, 182, 172),    # green for reward cell
    "treasure": (255, 183, 76),  # yellow for treasure cell
    "obstacle": (127, 127, 127), # grey for obstacle cell
    "border": (40, 40, 40),      # black for boundary
    "path": (0, 255, 0),         # green for cell movement
    "player": (255, 0, 0),       # red for current position
}

# Definition of special hexagons on the map with their coordinates and colors
hexagons_legend = {
    "T1": {"coordinate": [(8,2)], "color": cell_colors["trap"]},
    "T2": {"coordinate": [(1,1), (2,4)], "color": cell_colors["trap"]},
    "T3": {"coordinate": [(5,3), (6,1)], "color": cell_colors["trap"]},
    "T4": {"coordinate": [(3,1)], "color": cell_colors["trap"]},
    "R1": {"coordinate": [(1,3), (4,0)], "color": cell_colors["reward"]},
    "R2": {"coordinate": [(5,5), (7,2)], "color": cell_colors["reward"]},
    "TR": {"coordinate": [(3,4), (4,1), (7,3), (9,3)], "color": cell_colors["treasure"]},
    "O": {"coordinate": [(0,3), (2,2), (3,3), (4,2), (4,4), (6,3), (6,4), (7,4), (8,1)], "color": cell_colors["obstacle"]},
}

# Movement patterns for odd and even columns in hexagonal grid
moves_odd = [(0, -1), (0, 1), (1, -1), (-1, -1), (1, 0), (-1, 0)]
moves_even = [(0, -1), (0, 1), (1, 0), (-1, 0), (1, 1), (-1, 1)]

# Map configuration
map_size = (6, 10)
map_redius = 30
map_height = math.sqrt(3) * map_redius
map_width = 2 * map_redius * 0.75

# Screen dimensions
screen_padding = map_redius * 2
screen_width = int(map_size[1] * map_width + screen_padding * 1.25)
screen_height = int(map_size[0] * map_height + 300)

# Function to draw a hexagon at given coordinates
def draw_hexagon(x, y, color):
    points = [
        (x + map_redius * math.cos(math.radians(angle)),
         y + map_redius * math.sin(math.radians(angle)))
        for angle in range(0, 360, 60)
    ]
    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, cell_colors["border"], points, 2)

# Function to put text on the screen
def put_text(text, x, y, font_size=24, alignment="left", width_max=None):
    font = pygame.font.Font(None, font_size)

    if width_max is None:
        surface_text = font.render(text, True, cell_colors["border"])
        if alignment.lower() == "center":
            text_rectangle = surface_text.get_rect(center=(x, y))
        else:
            text_rectangle = surface_text.get_rect(topleft=(x, y))
        screen.blit(surface_text, text_rectangle)
    else:
        words = text.split(' ')
        lines = []
        current_line = ''
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.size(test_line)[0] <= width_max:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines):
            surface_text = font.render(line, True, cell_colors["border"])
            if alignment.lower() == "center":
                text_rectangle = surface_text.get_rect(center=(x, y + i * font_size))
            else:
                text_rectangle = surface_text.get_rect(topleft=(x, y + i * font_size))
            screen.blit(surface_text, text_rectangle)

# Function to check if a coordinate is valid within the map boundaries
def is_valid(coordinate):
    return 0 <= coordinate[0] < map_size[1] and 0 <= coordinate[1] < map_size[0]

# Function to check if a coordinate is an obstacle
def is_obstacle(coord):
    return coord in hexagons_legend["O"]["coordinate"]

# Function to get possible moves based on the column parity (even/odd)
def get_moves(coord):
    return moves_even if coord[0] % 2 == 0 else moves_odd

# Heuristic function for A* algorithm (Manhattan distance)
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Function to calculate the step cost and energy multiplier based on special hexagons
def stepcost_calc(current, neighbor, special_hexagons, energy_multiply):
    base_cost = 1
    new_energy = energy_multiply
    
    # Check if we're stepping on a special hexagon (neighbor is the one we're moving to)
    for stepping_key, hex_data in special_hexagons.items():
        if neighbor in hex_data["coordinate"]:
            if stepping_key == "T1":
                new_energy *= 2
            elif stepping_key == "T2":
                base_cost *= 2
            elif stepping_key == "R1":
                new_energy *= 0.5
            elif stepping_key == "R2":
                new_energy *= 0.5
    return base_cost * energy_multiply, new_energy

# Function to get neighbors of the current position, considering T3 forced movement
def get_neighbors_with_t3_effect(current, path):
    """Get all possible neighbors, handling T3 forced movement."""
    neighbors = []
    
    for dx, dy in get_moves(current):
        neighbor = (current[0] + dx, current[1] + dy)
        
        if not is_valid(neighbor) or is_obstacle(neighbor):
            continue
            
        if neighbor in hexagons_legend["T3"]["coordinate"]:
            intermediate_position = (neighbor[0] + dx, neighbor[1] + dy)
            final_pos = (neighbor[0] + dx * 2, neighbor[1] + dy * 2)
            
            if (is_valid(intermediate_position) and not is_obstacle(intermediate_position) and
                is_valid(final_pos) and not is_obstacle(final_pos)):
                neighbors.append((neighbor, intermediate_position, final_pos, True)) 
        else:
            neighbors.append((neighbor, neighbor, neighbor, False)) 
    
    return neighbors

# Function to collect treasures using A* algorithm
# This function finds the optimal path to collect all treasures while avoiding traps and obstacles.
def collect_treasure(start):
    treasures = set(hexagons_legend["TR"]["coordinate"])
    open_set = []
    heappush(open_set, (0, start, frozenset(), 1.0, 0, [start]))
    visited = set()

    while open_set:
        f, current, collected, energy_multiplier, g, path = heappop(open_set)
        
        state = (current, collected)
        if state in visited:
            continue
        visited.add(state)

        # Check if we have collected a treasure at current position
        new_collected = set(collected)
        if current in treasures:
            new_collected.add(current)

        # Check if we have collected all treasures
        if len(new_collected) == len(treasures):
            return path, g

        # Get neighbors with T3 effect handling
        neighbors = get_neighbors_with_t3_effect(current, path)
        
        for step_pos, intermediate_pos, final_pos, is_t3_effect in neighbors:
            # Check T4 restriction (can't step on T4 if we have treasures)
            if step_pos in hexagons_legend.get("T4", {}).get("coordinate", []) and new_collected:
                continue
            if intermediate_pos in hexagons_legend.get("T4", {}).get("coordinate", []) and new_collected:
                continue
            if final_pos in hexagons_legend.get("T4", {}).get("coordinate", []) and new_collected:
                continue
            
            if is_t3_effect:
                cost1, energy1 = stepcost_calc(current, step_pos, hexagons_legend, energy_multiplier)
                cost2, energy2 = stepcost_calc(step_pos, intermediate_pos, hexagons_legend, energy1)
                cost3, final_energy = stepcost_calc(intermediate_pos, final_pos, hexagons_legend, energy2)
                total_cost = cost1 + cost2 + cost3
                new_energy = final_energy
                
                # Check for treasures at each position
                final_collected = set(new_collected)
                if step_pos in treasures:
                    final_collected.add(step_pos)
                if intermediate_pos in treasures:
                    final_collected.add(intermediate_pos)
                if final_pos in treasures:
                    final_collected.add(final_pos)
                
                new_path = path + [step_pos, intermediate_pos, final_pos]
            else:
                total_cost, new_energy = stepcost_calc(current, step_pos, hexagons_legend, energy_multiplier)
                
                final_collected = set(new_collected)
                if final_pos in treasures:
                    final_collected.add(final_pos)
                
                new_path = path + [final_pos]
            
            # Calculate heuristic to nearest uncollected treasure
            if len(final_collected) < len(treasures):
                h = min(heuristic(final_pos, t) for t in treasures if t not in final_collected)
            else:
                h = 0
            
            heappush(open_set, (g + total_cost + h, final_pos, frozenset(final_collected), new_energy, g + total_cost, new_path))
    
    return [], float('inf')

# Function to visualize the path found by the A* algorithm
# This function displays the path on the screen, allowing the user to step through it.
def path_visualization(path):
    clock = pygame.time.Clock()
    step_count = 0
    auto_play = True
    auto_delay = 500  # in miliseconds
    last_auto_advance = pygame.time.get_ticks()
    collected_treasures = set()
    energy_multiplier = 1.0
    total_cost = 0

    while True:
        screen.fill(cell_colors["default"])

        label_positions = []
        for row in range(map_size[0]):
            for col in range(map_size[1]):
                x = col * map_width
                y = row * map_height + (map_height / 2 if col % 2 == 0 else 0)
                screen_x = x + screen_padding
                screen_y = y + screen_padding

                hex_coord = (col, row)
                color = cell_colors["default"]
                label = ""

                for key, value in hexagons_legend.items():
                    if hex_coord in value["coordinate"]:
                        color = value["color"]
                        label = key
                        break

                draw_hexagon(screen_x, screen_y, color)
                if label:
                    label_positions.append((screen_x, screen_y, label))

        for i in range(step_count + 1):
            col, row = path[i]
            x = col * map_width
            y = row * map_height + (map_height / 2 if col % 2 == 0 else 0)
            screen_x = x + screen_padding
            screen_y = y + screen_padding
            color = cell_colors["player"] if i == step_count else cell_colors["path"]
            draw_hexagon(screen_x, screen_y, color)

        for x, y, label in label_positions:
            put_text(label, x, y, font_size=24, alignment="center")

        put_text(f"Step: {step_count}/{len(path)-1}", 10, screen_height-120)
        put_text(f"Total Cost: {round(total_cost, 2)}", 10, screen_height-100)
        put_text(f"Treasures Collected: {len(collected_treasures)}", 10, screen_height-80)
        put_text("Path: ", 10, screen_height-60)
        put_text(str(path[:step_count+1]), 60, screen_height-60, width_max=screen_width-80)
        put_text("Use LEFT and RIGHT arrow keys to move through the path", screen_width // 2, screen_height - 170, alignment="center")

        pygame.display.flip()
        clock.tick(60)

        if auto_play:
            now = pygame.time.get_ticks()
            if now - last_auto_advance >= auto_delay:
                if step_count < len(path) - 1:
                    step_count += 1
                    current = path[step_count]
                    previous = path[step_count - 1]

                    cost, energy_multiplier = stepcost_calc(previous, current, hexagons_legend, energy_multiplier)
                    total_cost += cost

                    if current in hexagons_legend["TR"]["coordinate"]:
                        collected_treasures.add(current)
                    if current in hexagons_legend.get("T4", {}).get("coordinate", []):
                        collected_treasures.clear()

                    last_auto_advance = now
                else:
                    auto_play = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and step_count < len(path) - 1 and not auto_play:
                    step_count += 1
                    current = path[step_count]
                    previous = path[step_count-1]

                    cost, energy_multiplier = stepcost_calc(previous, current, hexagons_legend, energy_multiplier)
                    total_cost += cost

                    if current in hexagons_legend["TR"]["coordinate"]:
                        collected_treasures.add(current)
                    if current in hexagons_legend.get("T4", {}).get("coordinate", []):
                        collected_treasures.clear()

                elif event.key == pygame.K_LEFT and step_count > 0 and not auto_play:
                    step_count -= 1
                    total_cost = 0
                    collected_treasures.clear()
                    energy_multiplier = 1.0

                    for i in range(step_count):
                        current = path[i+1]
                        previous = path[i]
                        cost, energy_multiplier = stepcost_calc(previous, current, hexagons_legend, energy_multiplier)
                        total_cost += cost
                        if current in hexagons_legend["TR"]["coordinate"]:
                            collected_treasures.add(current)
                        if current in hexagons_legend.get("T4", {}).get("coordinate", []):
                            collected_treasures.clear()

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("A* Treasure Collection Visualization")
    screen = pygame.display.set_mode((screen_width, screen_height))
    start = (0, 0)
    path, cost = collect_treasure(start)
    path_visualization(path)
    pygame.quit()