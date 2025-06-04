import pygame
import math

colors = {
    "default": (240, 240, 240),  # white
    "trap": (206, 147, 216),     # purple
    "reward": (76, 182, 172),    # green
    "treasure": (255, 183, 76),  # yellow
    "obstacle": (127, 127, 127), # grey
    "border": (40, 40, 40),      # black
}

special_hexagons = {
    "T1": {
        "coordinate": [(8,2)],
        "color": colors["trap"],
    },
    "T2": {
        "coordinate": [(1,1), (2,4)],
        "color": colors["trap"],
    },
    "T3": {
        "coordinate": [(5,3), (6,1)],
        "color": colors["trap"],
    },
    "T4": {
        "coordinate": [(3,1)],
        "color": colors["trap"],
    },
    "R1": {
        "coordinate": [(1,3), (4,0)],
        "color": colors["reward"],
    },
    "R2": {
        "coordinate": [(5,5), (7,2)],
        "color": colors["reward"],
    },
    "TR": {
        "coordinate": [(3,4), (4,1), (7,3), (9,3)],
        "color": colors["treasure"],
    },
    "O": {
        "coordinate": [(0,3), (2,2), (3,3), (4,2), (4,4), (6,3), (6,4), (7,4), (8,1)],
        "color": colors["obstacle"],
    },
}

directions = {
    "UP": (0, -1),  # Up
    "DN": (0, 1),   # Down
    "UR": (1, -1),  # Up Right
    "UL": (-1, -1), # Up Left
    "DR": (1, 1),   # Down Right
    "DL": (-1, 1),  # Down Left
}

class Hexagon:
    def __init__(self, coordinate, parent=None, hex_type="D"):
        self.coordinate = coordinate
        self.parent = parent
        self.hex_type = hex_type
        self.children = []
    
    def add_child(self, child):
        self.children.extend(child)

def get_special_coord(coord):
    for hex_type, hex_info in special_hexagons.items():
        if coord in hex_info["coordinate"]:
            return hex_info["color"], hex_type
    return colors["default"], ""

def draw_hexagon(x, y, color):
    """Draw a hexagon at the specified coordinates with the given color."""
    points = [
        (x + radius * math.cos(math.radians(angle)),
         y + radius * math.sin(math.radians(angle)))
        for angle in range(0, 360, 60)
    ]
    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, colors["border"], points, 2)

def draw_text(text, x, y, font_size=24, alignment="left"):
    """Draw text on the screen with specified alignment."""
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, colors["border"])
    if alignment.lower() == "center":
        text_rect = text_surface.get_rect(center=(x, y))
        screen.blit(text_surface, text_rect)
    else:
        text_rect = text_surface.get_rect(topleft=(x, y))
        screen.blit(text_surface, text_rect)

def is_valid(coordinate):
    """Check if the coordinate is within the board boundaries."""
    return 0 <= coordinate[0] < board[1] and 0 <= coordinate[1] < board[0]

def is_obstacle(coordinate):
    """Check if the coordinate is an obstacle."""
    return True if coordinate in special_hexagons["O"]["coordinate"] else False

if __name__ == "__main__":
    # Board size
    board = (6, 10)

    # Hexagon properties
    radius = 40
    height = math.sqrt(3) * radius
    width = 2 * radius * 0.75

    # Screen setup
    screen_padding = 80
    screen_width = int(board[1] * width + screen_padding * 1.25)
    screen_height = int(board[0] * height + 300)

    # Initialize Pygame
    pygame.init()
    pygame.display.set_caption("Search Algorithm")
    screen = pygame.display.set_mode((screen_width, screen_height))
    clock = pygame.time.Clock()
    running = True

    while running:
        screen.fill(colors["default"])

        # Draw hex grid
        for row in range(board[0]):
            for col in range(board[1]):
                x = col * width
                y = row * height
                if col % 2 == 0:
                    y += height / 2
                color, text = get_special_coord((col, row))
                draw_hexagon(x+screen_padding, y+screen_padding, color)
                draw_text(text, x+screen_padding, y+screen_padding, alignment="center")

        # Draw title
        grid_width = screen_padding / 2
        grid_height = board[0] * height + screen_padding * 2
        draw_text("Search Algorithm Visualization", grid_width, grid_height)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
