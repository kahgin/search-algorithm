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
    
    # Check if we're stepping on a special hexagon (neighbor is the one we're moving to)
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

def get_neighbors_with_t3_effect(current, path):
    """Get all possible neighbors, handling T3 forced movement."""
    neighbors = []
    
    for dx, dy in get_moves(current):
        neighbor = (current[0] + dx, current[1] + dy)
        
        if not is_valid(neighbor) or is_obstacle(neighbor):
            continue
            
        # If stepping on T3, we get forced to move 2 more steps in the same direction
        if neighbor in special_hexagons["T3"]["coordinate"]:
            # Calculate intermediate position (1 step from T3)
            intermediate_pos = (neighbor[0] + dx, neighbor[1] + dy)
            # Calculate final position (2 steps from T3)
            final_pos = (neighbor[0] + dx * 2, neighbor[1] + dy * 2)
            
            # Check if both intermediate and final positions are valid and not obstacles
            if (is_valid(intermediate_pos) and not is_obstacle(intermediate_pos) and
                is_valid(final_pos) and not is_obstacle(final_pos)):
                # Add the T3 neighbor with both intermediate and final positions
                neighbors.append((neighbor, intermediate_pos, final_pos, True))  # True indicates T3 effect
            # If either position is invalid, we can't use this move at all
        else:
            # Normal movement
            neighbors.append((neighbor, neighbor, neighbor, False))  # False indicates no T3 effect
    
    return neighbors

def astar_collect_all_treasures(start):
    treasures = set(special_hexagons["TR"]["coordinate"])
    open_set = []
    heappush(open_set, (0, start, frozenset(), 1.0, 0, [start]))
    visited = set()

    while open_set:
        f, current, collected, energy_multiplier, g, path = heappop(open_set)
        
        state = (current, collected)
        if state in visited:
            continue
        visited.add(state)

        # Check if we collected a treasure at current position
        new_collected = set(collected)
        if current in treasures:
            new_collected.add(current)

        # Check if we've collected all treasures
        if len(new_collected) == len(treasures):
            return path, g

        # Get neighbors with T3 effect handling
        neighbors = get_neighbors_with_t3_effect(current, path)
        
        for step_pos, intermediate_pos, final_pos, is_t3_effect in neighbors:
            # Check T4 restriction (can't step on T4 if we have treasures)
            if step_pos in special_hexagons.get("T4", {}).get("coordinate", []) and new_collected:
                continue
            if intermediate_pos in special_hexagons.get("T4", {}).get("coordinate", []) and new_collected:
                continue
            if final_pos in special_hexagons.get("T4", {}).get("coordinate", []) and new_collected:
                continue
            
            if is_t3_effect:
                cost1, energy1 = calculate_step_cost(current, step_pos, special_hexagons, energy_multiplier)
                cost2, energy2 = calculate_step_cost(step_pos, intermediate_pos, special_hexagons, energy1)
                cost3, final_energy = calculate_step_cost(intermediate_pos, final_pos, special_hexagons, energy2)
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
                total_cost, new_energy = calculate_step_cost(current, step_pos, special_hexagons, energy_multiplier)
                
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

        # Draw path up to current step
        for i in range(step + 1):
            col, row = path[i]
            x = col * width
            y = row * height + (height / 2 if col % 2 == 0 else 0)
            screen_x = x + screen_padding
            screen_y = y + screen_padding
            color = colors["player"] if i == step else colors["path"]
            draw_hexagon(screen_x, screen_y, color)

        # Draw labels on top
        for x, y, label in label_positions:
            draw_text(label, x, y, font_size=24, alignment="center")

        # Update status information
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
                    prev = path[step-1]
                    
                    # Calculate cost for this step
                    cost, energy_multiplier = calculate_step_cost(prev, curr, special_hexagons, energy_multiplier)
                    total_cost += cost
                    
                    # Handle treasure collection
                    if curr in special_hexagons["TR"]["coordinate"]:
                        collected_treasures.add(curr)
                    
                    # Handle T4 effect (lose all treasures)
                    if curr in special_hexagons.get("T4", {}).get("coordinate", []):
                        collected_treasures.clear()
                        
                elif event.key == pygame.K_LEFT and step > 0:
                    step -= 1
                    # Recalculate everything from the beginning
                    total_cost = 0
                    collected_treasures.clear()
                    energy_multiplier = 1.0
                    
                    for i in range(step):
                        curr = path[i+1]
                        prev = path[i]
                        cost, energy_multiplier = calculate_step_cost(prev, curr, special_hexagons, energy_multiplier)
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