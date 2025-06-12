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
map_radius = 30
map_height = math.sqrt(3) * map_radius
map_width = 2 * map_radius * 0.75

# Screen dimensions
screen_padding = map_radius * 2
screen_width = int(map_size[1] * map_width + screen_padding * 1.25)
screen_height = int(map_size[0] * map_height + 300)

# Global game state holder
class GameState:
    def __init__(self):
        self.energy = 1.0

game_state = GameState()

# Function to draw a hexagon at given coordinates
def draw_hexagon(x, y, color):
    points = [
        (x + map_radius * math.cos(math.radians(angle)),
         y + map_radius * math.sin(math.radians(angle)))
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
        lines, current = [], ''
        for word in words:
            test_line = f"{current} {word}".strip()
            if font.size(test_line)[0] <= width_max:
                current = test_line
            else:
                lines.append(current); current = word
        if current: lines.append(current)

        for i, line in enumerate(lines):
            surface = font.render(line, True, cell_colors["border"])
            if alignment.lower() == "center":
                rect = surface.get_rect(center=(x, y + i * font_size))
            else:
                rect = surface.get_rect(topleft=(x, y + i * font_size))
            screen.blit(surface, rect)

# Function to check if a coordinate is valid within the map boundaries
def is_valid(coord):
    return 0 <= coord[0] < map_size[1] and 0 <= coord[1] < map_size[0]

# Function to check if a coordinate is an obstacle
def is_obstacle(coord):
    return coord in hexagons_legend["O"]["coordinate"]

# Function to get possible moves based on the column parity (even/odd)
def get_moves(coord):
    return moves_even if coord[0] % 2 == 0 else moves_odd

# Heuristic function for A* algorithm (Manhattan distance)
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Function to calculate the step cost
def stepcost_calc(neighbor):
    step = 1
    energy = game_state.energy
    coords = neighbor

    if coords in hexagons_legend.get("T1", {}).get("coordinate", []):
        energy *= 2
    elif coords in hexagons_legend.get("T2", {}).get("coordinate", []):
        step *= 2
    elif coords in hexagons_legend.get("R1", {}).get("coordinate", []):
        energy *= 0.5
    elif coords in hexagons_legend.get("R2", {}).get("coordinate", []):
        step *= 0.5

    return step, energy

# Function to get neighbors of the current position, considering T3 forced movement
def get_neighbors(current):
    neighbors = []
    
    for dx, dy in get_moves(current):
        nbr = (current[0] + dx, current[1] + dy)
        if not is_valid(nbr) or is_obstacle(nbr): 
            continue
        if nbr in hexagons_legend["T3"]["coordinate"]:
            interm = (nbr[0] + dx, nbr[1] + dy)
            final = (nbr[0] + 2 * dx, nbr[1] + 2 * dy)
            if is_valid(interm) and not is_obstacle(interm) and is_valid(final) and not is_obstacle(final):
                neighbors.append((nbr, interm, final, True))
        else:
            neighbors.append((nbr, nbr, nbr, False))
    return neighbors

# Function to collect treasures using A* algorithm
# This function finds the optimal path to collect all treasures while avoiding traps and obstacles.
def collect_treasure(start):
    treasures = set(hexagons_legend["TR"]["coordinate"])
    open_set = []
    heappush(open_set, (0, start, frozenset(), 0, [start]))
    visited = set()

    while open_set:
        f, current, collected, g, path = heappop(open_set)
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

        for step, interm, final, is_t3 in get_neighbors(current):
            if new_collected and any(p in hexagons_legend.get("T4", {}).get("coordinate", []) for p in (step, interm, final)):
                continue

            backup = game_state.energy
            temp_collected, temp_path = set(new_collected), list(path)
            cost = 0

            if is_t3:
                segs = [(current, step), (step, interm), (interm, final)]
            else:
                segs = [(current, final)]

            for a, b in segs:
                step, energy = stepcost_calc(a)
                cost += step * energy
                game_state.energy = energy  # update multiplier after each move
                if b in treasures:
                    temp_collected.add(b)
                temp_path.append(b)

            h = min(heuristic(final, t) for t in (treasures - temp_collected)) if temp_collected != treasures else 0
            heappush(open_set, (g + cost + h, final, frozenset(temp_collected), g + cost, temp_path))
            game_state.energy = backup

    return [], float('inf')

# Function to visualize the path found by the A* algorithm
# This function displays the path on the screen, allowing the user to step through it.
def path_visualization(path):
    clock = pygame.time.Clock()
    step = 0
    auto = True
    delay = 500
    last = pygame.time.get_ticks()
    collected = set()
    total_step_cost = 0
    total_energy = 0
    game_state.energy = 1.0

    while True:
        screen.fill(cell_colors["default"])
        labels = []
        for row in range(map_size[0]):
            for col in range(map_size[1]):
                x = col * map_width
                y = row * map_height + (map_height / 2 if col % 2 == 0 else 0)
                sx, sy = x + screen_padding, y + screen_padding
                coord = (col, row)
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

        for i in range(step + 1):
            c0, r0 = path[i]
            x = c0 * map_width
            y = r0 * map_height + (map_height / 2 if c0 % 2 == 0 else 0)
            sx, sy = x + screen_padding, y + screen_padding
            draw_hexagon(sx, sy, cell_colors["player"] if i == step else cell_colors["path"])

        for x, y, lab in labels:
            put_text(lab, x, y, font_size=24, alignment="center")

        put_text(f"Total Step Cost: {round(total_step_cost, 2)}", 10, screen_height - 120)
        put_text(f"Total Energy: {round(total_energy, 2)}", 10, screen_height - 100)
        put_text(f"Treasures Collected: {len(collected)}", 10, screen_height - 80)
        put_text("Path: ", 10, screen_height - 60)
        put_text(str(path[:step+1]), 60, screen_height - 60, width_max=screen_width - 80)
        put_text("Use LEFT and RIGHT arrow keys to move through the path", screen_width // 2, screen_height - 170, alignment="center")

        pygame.display.flip()
        clock.tick(60)

        if auto and pygame.time.get_ticks() - last >= delay:
            if step < len(path) - 1:
                prev, curr = path[step], path[step + 1]
                step_cost, energy_multiplier = stepcost_calc(prev)
                energy_cost = step_cost * energy_multiplier
                total_step_cost += step_cost
                total_energy += energy_cost
                game_state.energy = energy_multiplier
                if curr in hexagons_legend["TR"]["coordinate"]:
                    collected.add(curr)
                if curr in hexagons_legend.get("T4", {}).get("coordinate", []):
                    collected.clear()
                step += 1
                last = pygame.time.get_ticks()
            else:
                auto = False

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                return
            elif evt.type == pygame.KEYDOWN and not auto:
                if evt.key == pygame.K_RIGHT and step < len(path) - 1:
                    prev, curr = path[step], path[step + 1]
                    step_cost, energy_multiplier = stepcost_calc(prev)
                    energy_cost = step_cost * energy_multiplier
                    total_step_cost += step_cost
                    total_energy += energy_cost
                    game_state.energy = energy_multiplier
                    if curr in hexagons_legend["TR"]["coordinate"]:
                        collected.add(curr)
                    if curr in hexagons_legend.get("T4", {}).get("coordinate", []):
                        collected.clear()
                    step += 1
                elif evt.key == pygame.K_LEFT and step > 0:
                    step -= 1
                    total_step_cost = 0
                    total_energy = 0
                    game_state.energy = 1.0
                    collected.clear()
                    for i in range(step):
                        p0, p1 = path[i], path[i + 1]
                        step_cost, energy_multiplier = stepcost_calc(p0)
                        energy_cost = step_cost * energy_multiplier
                        total_step_cost += step_cost
                        total_energy += energy_cost
                        game_state.energy = energy_multiplier
                        if p1 in hexagons_legend["TR"]["coordinate"]:
                            collected.add(p1)
                        if p1 in hexagons_legend.get("T4", {}).get("coordinate", []):
                            collected.clear()

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("A* Treasure Collection Visualization")
    screen = pygame.display.set_mode((screen_width, screen_height))
    start = (0, 0)
    path, cost = collect_treasure(start)
    path_visualization(path)
    pygame.quit()
