import numpy as np

K_SPACE = 0
K_WALL = 1
K_BOMB = 2
K_BOX = 4
K_RANDOM = 5

K_EXPLOSION_START = 10
K_EXPLOSION_END = 23
K_EXPLOSION = range(K_EXPLOSION_START, K_EXPLOSION_END + 1)

MATRIX = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 0, 0, 1],
    [1, 0, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 0, 1],
    [1, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 1],
    [1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1],
    [1, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1],
    [1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1],
    [1, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 1],
    [1, 0, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 0, 1],
    [1, 0, 0, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
], dtype=np.uint8)


FPS = 30
CELL_SIZE = 32
CELL_RECT = (CELL_SIZE, CELL_SIZE)
GAME_ROWS, GAME_COLS = len(MATRIX), len(MATRIX[0])
GAME_HEIGHT, GAME_WIDTH = GAME_ROWS * CELL_SIZE, GAME_COLS * CELL_SIZE
BOMB_EXPLOSION_RANGE = 2
MAX_PLAYER = 4
DEFAULT_COORD = [
    (1, 1),
    (16, 16),
    (16, 1),
    (1, 16),
]
