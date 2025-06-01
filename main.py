import pygame
import math

colors = {
    "default": (240, 240, 240),  # light beige
    "trap": (206, 147, 216),     # purple
    "reward": (76, 182, 172),    # green
    "treasure": (255, 183, 76),  # yellow
    "obstacle": (127, 127, 127), # grey
    "border": (40,40,40),        # black
}

special_hexagons = {
    "Trap 1": {
        "coordinate": (1,1),
        "color": colors["trap"],
        "type": "T2",
    },
    "Trap 2": {
        "coordinate": (2,4),
        "color": colors["trap"],
        "type": "T2",
    },
    "Trap 3": {
        "coordinate": (3,1),
        "color": colors["trap"],
        "type": "T4",
    },
    "Trap 4": {
        "coordinate": (5,3),
        "color": colors["trap"],
        "type": "T3",
    },
    "Trap 5": {
        "coordinate": (6,1),
        "color": colors["trap"],
        "type": "T3",
    },
    "Trap 6": {
        "coordinate": (8,2),
        "color": colors["trap"],
        "type": "T1",
    },
    "Reward 1": {
        "coordinate": (1,3),
        "color": colors["reward"],
        "type": "R1",
    },
    "Reward 2": {
        "coordinate": (4,0),
        "color": colors["reward"],
        "type": "R1",
    },
    "Reward 3": {
        "coordinate": (5,5),
        "color": colors["reward"],
        "type": "R2",
    },
    "Reward 4": {
        "coordinate": (7,2),
        "color": colors["reward"],
        "type": "R2",
    },
    "Treasure 1": {
        "coordinate": (3,4),
        "color": colors["treasure"],
        "type": "TR",
    },
    "Treasure 2": {
        "coordinate": (4,1),
        "color": colors["treasure"],
        "type": "TR",
    },
    "Treasure 3": {
        "coordinate": (7,3),
        "color": colors["treasure"],
        "type": "TR",
    },
    "Treasure 4": {
        "coordinate": (9,3),
        "color": colors["treasure"],
        "type": "TR",
    },
    "Obstacle 1": {
        "coordinate": (0,3),
        "color": colors["obstacle"],
        "type": "O",
    },
    "Obstacle 2": {
        "coordinate": (2,2),
        "color": colors["obstacle"],
        "type": "O",
    },
    "Obstacle 3": {
        "coordinate": (3,3),
        "color": colors["obstacle"],
        "type": "O",
    },
    "Obstacle 4": {
        "coordinate": (4,2),
        "color": colors["obstacle"],
        "type": "O",
    },
    "Obstacle 5": {
        "coordinate": (4,4),
        "color": colors["obstacle"],
        "type": "O",
    },
    "Obstacle 6": {
        "coordinate": (6,3),
        "color": colors["obstacle"],
        "type": "O",
    },
    "Obstacle 7": {
        "coordinate": (6,4),
        "color": colors["obstacle"],
        "type": "O",
    },
    "Obstacle 8": {
        "coordinate": (7,4),
        "color": colors["obstacle"],
        "type": "O",
    },
    "Obstacle 9": {
        "coordinate": (8,1),
        "color": colors["obstacle"],
        "type": "O",
    },
}

# Board size
board = (6, 10)  # 6 rows and 10 columns

# Hexagon properties
radius = 30
height = math.sqrt(3) * radius
width = 2 * radius * 0.75

# Screen setup
screen_width = int(board[1] * width + radius * 2)
screen_height = int(board[0] * height + 200)

# Function to draw a hexagon
def draw_hexagon(x, y, color):
    points = [
        (x + radius * math.cos(math.radians(angle)),
         y + radius * math.sin(math.radians(angle)))
        for angle in range(0, 360, 60)
    ]
    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, colors["border"], points, 2)

def draw_text(text, x, y):
    font = pygame.font.Font(None, 24)
    text_surface = font.render(text, True, colors["border"])
    screen.blit(text_surface, (x, y))

# Extract special hexagon coordinates and colors
special_coords = {v["coordinate"]: v["color"] for v in special_hexagons.values()}
special_types = {v["coordinate"]: v["type"] for v in special_hexagons.values()}

pygame.init()
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
            color = special_coords.get((col, row), colors["default"])
            text = special_types.get((col, row), "")
            draw_hexagon(x+50, y+50, color)
            draw_text(text, (x+40) if len(text)==2 else (x+45), y+45)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()


