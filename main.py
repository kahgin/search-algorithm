import pygame
import math
from heapq import heappush, heappop

# Color definitions
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

# Special hexagon definitions
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

# Movement patterns for hexagonal grid
moves_odd = [(0, -1), (0, 1), (1, -1), (-1, -1), (1, 0), (-1, 0)]
moves_even = [(0, -1), (0, 1), (1, 0), (-1, 0), (1, 1), (-1, 1)]

# Map configuration
map_size = (6, 10)
map_radius = 30
map_height = math.sqrt(3) * map_radius
map_width = 2 * map_radius * 0.75

# Screen dimensions
screen_padding = map_radius * 2
screen_width = int(map_size[1] * map_width + screen_padding * 1.25)
screen_height = int(map_size[0] * map_height + 300)

# Helper function to get cell type at coordinate
def get_cell_type(coord):
    """Return the type of special cell at given coordinate, or None if default"""
    for cell_type, data in hexagons_legend.items():
        if coord in data["coordinate"]:
            return cell_type
    return None

class GameState:
    def __init__(self):
        self.energy = 1.0

game_state = GameState()

def draw_hexagon(x, y, color):
    """Draw a hexagon at given coordinates"""
    points = [
        (x + map_radius * math.cos(math.radians(angle)),
         y + map_radius * math.sin(math.radians(angle)))
        for angle in range(0, 360, 60)
    ]
    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, cell_colors["border"], points, 2)

def put_text(text, x, y, font_size=24, alignment="left", width_max=None):
    """Render text on screen with optional word wrapping"""
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
        lines, current = [], ''
        for word in words:
            test_line = f"{current} {word}".strip()
            if font.size(test_line)[0] <= width_max:
                current = test_line
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        for i, line in enumerate(lines):
            surface = font.render(line, True, cell_colors["border"])
            if alignment.lower() == "center":
                rect = surface.get_rect(center=(x, y + i * font_size))
            else:
                rect = surface.get_rect(topleft=(x, y + i * font_size))
            screen.blit(surface, rect)

def is_valid_coord(coord):
    """Check if coordinate is within map boundaries"""
    return 0 <= coord[0] < map_size[1] and 0 <= coord[1] < map_size[0]

def is_obstacle(coord):
    """Check if coordinate is an obstacle"""
    return get_cell_type(coord) == "O"

def get_moves(coord):
    """Get possible moves based on column parity"""
    return moves_even if coord[0] % 2 == 0 else moves_odd

def heuristic(a, b):
    """Manhattan distance heuristic for A*"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def calculate_step_cost(coord):
    """Calculate step cost and energy multiplier for a coordinate"""
    step_cost = 1
    energy_multiplier = game_state.energy
    cell_type = get_cell_type(coord)
    
    if cell_type == "T1":
        energy_multiplier *= 2
    elif cell_type == "T2":
        step_cost *= 2
    elif cell_type == "R1":
        energy_multiplier *= 0.5
    elif cell_type == "R2":
        step_cost *= 0.5

    return step_cost, energy_multiplier

def get_neighbors(current):
    """Get valid neighbors, handling T3 forced movement"""
    neighbors = []
    
    for dx, dy in get_moves(current):
        nbr = (current[0] + dx, current[1] + dy)
        if not is_valid_coord(nbr) or is_obstacle(nbr): 
            continue
            
        if get_cell_type(nbr) == "T3":
            # T3 forces movement through two additional cells
            interm = (nbr[0] + dx, nbr[1] + dy)
            final = (nbr[0] + 2 * dx, nbr[1] + 2 * dy)
            if (is_valid_coord(interm) and not is_obstacle(interm) and is_valid_coord(final) and not is_obstacle(final)):
                neighbors.append((nbr, interm, final, True))
        else:
            neighbors.append((nbr, nbr, nbr, False))
    return neighbors

def update_treasure_collection(coord, collected):
    """Update treasure collection state"""
    new_collected = set(collected)
    if get_cell_type(coord) == "TR":
        new_collected.add(coord)
    return new_collected

def calculate_path_cost(segments):
    """Calculate total cost for a path segment"""
    total_cost = 0
    backup_energy = game_state.energy
    
    for start, end in segments:
        step_cost, energy_multiplier = calculate_step_cost(start)
        total_cost += step_cost * energy_multiplier
        game_state.energy = energy_multiplier
    
    # Restore energy state
    game_state.energy = backup_energy
    return total_cost

def collect_treasure(start):
    """Find optimal path to collect all treasures using A*"""
    treasure_coords = set(hexagons_legend["TR"]["coordinate"])
    open_set = []
    heappush(open_set, (0, start, frozenset(), 0, [start]))
    visited = set()

    while open_set:
        f, current, collected, g, path = heappop(open_set)
        state = (current, collected)
        
        if state in visited:
            continue
        visited.add(state)

        # Update treasure collection
        new_collected = update_treasure_collection(current, collected)

        # Check if all treasures collected
        if len(new_collected) == len(treasure_coords):
            return path, g

        # Explore neighbors
        for step, interm, final, is_t3 in get_neighbors(current):
            # Skip if T4 trap would clear treasures
            if new_collected and any(get_cell_type(p) == "T4" for p in (step, interm, final)):
                continue

            temp_collected = set(new_collected)
            temp_path = list(path)
            
            # Calculate segments for movement
            segments = [(current, step), (step, interm), (interm, final)] if is_t3 else [(current, final)]
            cost = calculate_path_cost(segments)
            
            # Update collection and path for each segment
            for _, end_coord in segments:
                temp_collected = update_treasure_collection(end_coord, temp_collected)
                temp_path.append(end_coord)

            # Calculate heuristic
            remaining_treasures = treasure_coords - temp_collected
            h = min(heuristic(final, t) for t in remaining_treasures) if remaining_treasures else 0

            heappush(open_set, (g + cost + h, final, frozenset(temp_collected), g + cost, temp_path))

    return [], float('inf')

class PathState:
    """Manages path visualization state"""
    def __init__(self):
        self.step = 0
        self.collected = set()
        self.total_step_cost = 1.0
        self.total_energy = 1.0
        self.auto = True
        self.delay = 500
        self.last_update = pygame.time.get_ticks()

    def update_costs_to_step(self, path, target_step):
        """Update costs and collection state up to target step"""
        self.total_step_cost = 1.0
        self.total_energy = 1.0
        self.collected.clear()
        game_state.energy = 1.0

        for i in range(target_step):
            prev_coord = path[i]
            next_coord = path[i + 1]
            
            step_cost, energy_multiplier = calculate_step_cost(prev_coord)
            energy_cost = step_cost * energy_multiplier
            
            self.total_step_cost += step_cost
            self.total_energy += energy_cost
            game_state.energy = energy_multiplier
            
            # Update treasure collection
            if get_cell_type(next_coord) == "TR":
                self.collected.add(next_coord)
            if get_cell_type(next_coord) == "T4":
                self.collected.clear()

    def advance_step(self, path):
        """Advance to next step"""
        if self.step < len(path) - 1:
            prev_coord = path[self.step]
            next_coord = path[self.step + 1]
            
            step_cost, energy_multiplier = calculate_step_cost(prev_coord)
            energy_cost = step_cost * energy_multiplier
            
            self.total_step_cost += step_cost
            self.total_energy += energy_cost
            game_state.energy = energy_multiplier
            
            if get_cell_type(next_coord) == "TR":
                self.collected.add(next_coord)
            if get_cell_type(next_coord) == "T4":
                self.collected.clear()
                
            self.step += 1

def render_game_state(path, path_state):
    """Render the current game state"""
    screen.fill(cell_colors["default"])
    labels = []
    
    # Draw hexagonal grid
    for row in range(map_size[0]):
        for col in range(map_size[1]):
            x = col * map_width
            y = row * map_height + (map_height / 2 if col % 2 == 0 else 0)
            sx, sy = x + screen_padding, y + screen_padding
            coord = (col, row)
            
            # Determine cell color and label
            color = cell_colors["default"]
            label = ""
            for k, v in hexagons_legend.items():
                if coord in v["coordinate"]:
                    color = v["color"]
                    label = k
                    break
                    
            draw_hexagon(sx, sy, color)
            if label:
                labels.append((sx, sy, label))

    # Draw path
    for i in range(path_state.step + 1):
        c0, r0 = path[i]
        x = c0 * map_width
        y = r0 * map_height + (map_height / 2 if c0 % 2 == 0 else 0)
        sx, sy = x + screen_padding, y + screen_padding
        
        color = cell_colors["player"] if i == path_state.step else cell_colors["path"]
        draw_hexagon(sx, sy, color)

    # Draw labels
    for x, y, lab in labels:
        put_text(lab, x, y, font_size=24, alignment="center")

    # Draw UI information
    put_text(f"Total Step Cost: {round(path_state.total_step_cost, 2)}", 10, screen_height - 120)
    put_text(f"Total Energy: {round(path_state.total_energy, 2)}", 10, screen_height - 100)
    put_text(f"Treasures Collected: {len(path_state.collected)}", 10, screen_height - 80)
    put_text("Path: ", 10, screen_height - 60)
    put_text(str(path[:path_state.step+1]), 60, screen_height - 60, width_max=screen_width - 80)
    put_text("Use LEFT and RIGHT arrow keys to move through the path", screen_width // 2, screen_height - 170, alignment="center")

def path_visualization(path):
    """Visualize the pathfinding solution"""
    clock = pygame.time.Clock()
    path_state = PathState()

    while True:
        render_game_state(path, path_state)
        pygame.display.flip()
        clock.tick(60)

        # Auto-advance logic
        if path_state.auto and pygame.time.get_ticks() - path_state.last_update >= path_state.delay:
            if path_state.step < len(path) - 1:
                path_state.advance_step(path)
                path_state.last_update = pygame.time.get_ticks()
            else:
                path_state.auto = False

        # Handle events
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            elif evt.type == pygame.KEYDOWN and not path_state.auto:
                if evt.key == pygame.K_RIGHT and path_state.step < len(path) - 1:
                    path_state.advance_step(path)
                elif evt.key == pygame.K_LEFT and path_state.step > 0:
                    path_state.step -= 1
                    path_state.update_costs_to_step(path, path_state.step)

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("A* Treasure Collection Visualization")
    screen = pygame.display.set_mode((screen_width, screen_height))
    
    start = (0, 0)
    path, cost = collect_treasure(start)
    path_visualization(path)
    pygame.quit()
