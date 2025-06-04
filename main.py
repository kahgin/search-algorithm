import sys
sys.path.insert(0, './lib')

import pygame
import math
from heapq import heappush, heappop

colors = {
    "default": (240, 240, 240),  # white
    "trap": (206, 147, 216),     # purple
    "reward": (76, 182, 172),    # green
    "treasure": (255, 183, 76),  # yellow
    "obstacle": (127, 127, 127), # grey
    "border": (40, 40, 40),      # black
    "path": (0, 255, 0),         # green for path
    "player": (255, 0, 0),       # red for current position
}

special_hexagons = {
    "T1": {"coordinate": [(8,2)], "color": colors["trap"]},
    "T2": {"coordinate": [(1,1), (2,4)], "color": colors["trap"]},
    "T3": {"coordinate": [(5,3), (6,1)], "color": colors["trap"]},
    "T4": {"coordinate": [(3,1)], "color": colors["trap"]},
    "R1": {"coordinate": [(1,3), (4,0)], "color": colors["reward"]},
    "R2": {"coordinate": [(5,5), (7,2)], "color": colors["reward"]},
    "TR": {"coordinate": [(3,4), (4,1), (7,3), (9,3)], "color": colors["treasure"]},
    "O": {"coordinate": [(0,3), (2,2), (3,3), (4,2), (4,4), (6,3), (6,4), (7,4), (8,1)], "color": colors["obstacle"]},
}

moves_odd = [(0, -1), (0, 1), (1, -1), (-1, -1), (1, 0), (-1, 0)]
moves_even = [(0, -1), (0, 1), (1, 0), (-1, 0), (1, 1), (-1, 1)]

board = (6, 10)
radius = 30
height = math.sqrt(3) * radius
width = 2 * radius * 0.75
screen_padding = radius * 2
screen_width = int(board[1] * width + screen_padding * 1.25)
screen_height = int(board[0] * height + 300)

def draw_hexagon(x, y, color):
    points = [
        (x + radius * math.cos(math.radians(angle)),
         y + radius * math.sin(math.radians(angle)))
        for angle in range(0, 360, 60)
    ]
    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, colors["border"], points, 2)

def draw_text(text, x, y, font_size=24, alignment="left", max_width=None):
    font = pygame.font.Font(None, font_size)

    if max_width is None:
        # No wrapping: draw as usual
        text_surface = font.render(text, True, colors["border"])
        if alignment.lower() == "center":
            text_rect = text_surface.get_rect(center=(x, y))
        else:
            text_rect = text_surface.get_rect(topleft=(x, y))
        screen.blit(text_surface, text_rect)
    else:
        # Wrap text
        words = text.split(' ')
        lines = []
        current_line = ''
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines):
            text_surface = font.render(line, True, colors["border"])
            if alignment.lower() == "center":
                text_rect = text_surface.get_rect(center=(x, y + i * font_size))
            else:
                text_rect = text_surface.get_rect(topleft=(x, y + i * font_size))
            screen.blit(text_surface, text_rect)


def is_valid(coord):
    return 0 <= coord[0] < board[1] and 0 <= coord[1] < board[0]

def is_obstacle(coord):
    return coord in special_hexagons["O"]["coordinate"]

def get_moves(coord):
    return moves_even if coord[0] % 2 == 0 else moves_odd

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def calculate_step_cost(current, neighbor, special_hexagons, energy_multiplier):
    base_cost = 1
    new_energy = energy_multiplier
    
    # Check if we're stepping on a special hexagon (current is the one we're moving to)
    for key, hex_data in special_hexagons.items():
        if neighbor in hex_data["coordinate"]:
            if key == "T1":
                new_energy *= 2
            elif key == "T2":
                base_cost *= 2
            elif key == "R1":
                new_energy *= 0.5
            elif key == "R2":
                new_energy *= 0.5
    return base_cost * energy_multiplier, new_energy

def apply_t3_effect(current_pos, previous_pos, path):
    if current_pos not in special_hexagons["T3"]["coordinate"]:
        return path
    
    dx = current_pos[0] - previous_pos[0]
    dy = current_pos[1] - previous_pos[1]
    
    new_pos = (current_pos[0] + dx * 2, current_pos[1] + dy * 2)
    
    if is_valid(new_pos) and not is_obstacle(new_pos):
        # Find index of current position in path
        idx = path.index(current_pos)
        # Insert new position after current position
        path.insert(idx + 1, new_pos)
    
    return path

def astar_collect_all_treasures(start):
    treasures = set(special_hexagons["TR"]["coordinate"])
    open_set = []
    heappush(open_set, (0, start, frozenset(), 1.0, 0, []))
    visited = set()

    while open_set:
        f, current, collected, energy_multiplier, g, path = heappop(open_set)
        if (current, collected) in visited:
            continue
        visited.add((current, collected))

        path = path + [current]
        new_collected = set(collected)
        if current in treasures:
            new_collected.add(current)

        if len(new_collected) == len(treasures):
            return path, g

        for dx, dy in get_moves(current):
            neighbor = (current[0] + dx, current[1] + dy)
            if not is_valid(neighbor) or is_obstacle(neighbor):
                continue
            if neighbor in special_hexagons.get("T4", {}).get("coordinate", []) and new_collected:
                continue
            
            # Check if neighbor is T3 and apply effect
            if neighbor in special_hexagons["T3"]["coordinate"]:
                # Create temporary path to simulate T3 effect
                temp_path = path + [neighbor]
                temp_path = apply_t3_effect(neighbor, current, temp_path)
                # The actual cost is just 1 step (the T3 step)
                cost, new_energy = calculate_step_cost(current, neighbor, special_hexagons, energy_multiplier)
                # Push both possible paths (with and without T3 effect)
                heappush(open_set, (g + cost + min(heuristic(temp_path[-1], t) for t in treasures if t not in new_collected),
                                 temp_path[-1], frozenset(new_collected), new_energy, g + cost, temp_path))
            else:
                cost, new_energy = calculate_step_cost(current, neighbor, special_hexagons, energy_multiplier)
                heappush(open_set, (g + cost + min(heuristic(neighbor, t) for t in treasures if t not in new_collected),
                                 neighbor, frozenset(new_collected), new_energy, g + cost, path))
    return [], float('inf')

def visualize_path(path):
    clock = pygame.time.Clock()
    step = 0
    auto_play = False
    collected_treasures = set()
    energy_multiplier = 1.0
    total_cost = 0

    while True:
        screen.fill(colors["default"])

        # First: draw all hexagons and track any labels
        label_positions = []
        for row in range(board[0]):
            for col in range(board[1]):
                x = col * width
                y = row * height + (height / 2 if col % 2 == 0 else 0)
                screen_x = x + screen_padding
                screen_y = y + screen_padding

                hex_coord = (col, row)
                color = colors["default"]
                label = ""

                for key, value in special_hexagons.items():
                    if hex_coord in value["coordinate"]:
                        color = value["color"]
                        label = key
                        break  # Stop at first match (one type per hex)

                draw_hexagon(screen_x, screen_y, color)
                if label:
                    label_positions.append((screen_x, screen_y, label))

        for i in range(step + 1):
            col, row = path[i]
            x = col * width
            y = row * height + (height / 2 if col % 2 == 0 else 0)
            screen_x = x + screen_padding
            screen_y = y + screen_padding
            color = colors["player"] if i == step else colors["path"]
            draw_hexagon(screen_x, screen_y, color)

        for x, y, label in label_positions:
            draw_text(label, x, y, font_size=24, alignment="center")

        draw_text(f"Step: {step}/{len(path)-1}", 10, screen_height-120)
        draw_text(f"Total Cost: {round(total_cost, 2)}", 10, screen_height-100)
        draw_text(f"Treasures Collected: {len(collected_treasures)}", 10, screen_height-80)
        draw_text("Path: ", 10, screen_height-60)
        draw_text(str(path[:step+1]), 60, screen_height-60, max_width=screen_width-80)

        pygame.display.flip()
        clock.tick(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and step < len(path) - 1:
                    step += 1
                    curr = path[step]
                    
                    # Check if previous position was T3 and we need to skip the forced movement
                    if step > 1 and path[step-1] in special_hexagons["T3"]["coordinate"]:
                        # The forced movement is already in the path, so we need to account for it
                        # But we only count it as one step cost-wise
                        prev = path[step-2]  # Position before T3
                        cost, energy_multiplier = calculate_step_cost(prev, path[step-1], special_hexagons, energy_multiplier)
                        total_cost += cost
                    else:
                        prev = path[step-1]
                        cost, energy_multiplier = calculate_step_cost(prev, curr, special_hexagons, energy_multiplier)
                        total_cost += cost
                    
                    if curr in special_hexagons["TR"]["coordinate"]:
                        collected_treasures.add(curr)
                    if curr in special_hexagons.get("T4", {}).get("coordinate", []):
                        collected_treasures.clear()
                elif event.key == pygame.K_LEFT and step > 0:
                    step -= 1
                    total_cost = 0
                    collected_treasures.clear()
                    energy_multiplier = 1.0
                    for i in range(step):
                        curr = path[i+1]
                        cost, energy_multiplier = calculate_step_cost(path[i], curr, special_hexagons, energy_multiplier)
                        total_cost += cost
                        if curr in special_hexagons["TR"]["coordinate"]:
                            collected_treasures.add(curr)
                        if curr in special_hexagons.get("T4", {}).get("coordinate", []):
                            collected_treasures.clear()

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("A* Treasure Collection Visualization")
    screen = pygame.display.set_mode((screen_width, screen_height))

    start = (0, 0)
    path, cost = astar_collect_all_treasures(start)
    visualize_path(path)
    pygame.quit()