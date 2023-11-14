import random
import pygame
import numpy as np


E_EXPLOSION = pygame.USEREVENT + 1
E_GHOST = pygame.USEREVENT + 2

PTS_BOX = 5
PTS_KILL = 15
PTS_SUICIDE = -10
PLAY_TIME = 60 * 3
PLAY_WAIT_TIME = 5
LIFE_PTS_CONVERTION = 50

C_ACTIVE = "#00ff00"
C_INACTIVE = "#999594"

K_SPACE = 0
K_WALL = 1
K_BOX = 4
K_RANDOM = 5

K_EXPLOSION_START = 10
K_EXPLOSION_END = 18
K_EXPLOSION = range(K_EXPLOSION_START, K_EXPLOSION_END + 1)

K_BOMB_START = 20
K_BOMB_END = 29
K_BOMB = range(K_BOMB_START, K_BOMB_END + 1)

K_LIVES = 30
K_EXTRA_BOMB = 31
K_INC_BOMB_RANGE = 32
K_MOVE_SPEED = 33
K_DEATH = 34
POWER_UP = [K_LIVES, K_EXTRA_BOMB, K_MOVE_SPEED, K_INC_BOMB_RANGE, K_DEATH]


MATRIX = np.zeros((0, 0), dtype=np.uint8)


def rows_cols(length):
    if length <= 4:
        return 11, 17
    else:
        return 19, 25


def player_tile(length):
    rows, cols = rows_cols(length)
    return [(1, 1), (cols-2, rows-2), (cols-2, 1), (1, rows-2),]


def reset_matrix(length):
    global MATRIX

    rows, cols = rows_cols(length)

    MATRIX.resize((rows, cols), refcheck=False)
    MATRIX[:, :] = K_WALL
    MATRIX[1:-1, 1:-1] = K_RANDOM
    MATRIX[2:-2:2, 2:-2:2] = K_WALL  # checkered pattern inside

    for x, y in player_tile(length):
        MATRIX[y][x] = K_SPACE

        if MATRIX[y-1][x] == 5:
            MATRIX[y-1][x] = K_SPACE
            MATRIX[y-2][x] = K_BOX

        if MATRIX[y+1][x] == 5:
            MATRIX[y+1][x] = K_SPACE
            MATRIX[y+2][x] = K_BOX

        if MATRIX[y][x-1] == 5:
            MATRIX[y][x-1] = K_SPACE
            MATRIX[y][x-2] = K_BOX

        if MATRIX[y][x+1] == 5:
            MATRIX[y][x+1] = K_SPACE
            MATRIX[y][x+2] = K_BOX

    # randomize field
    for y, x in np.argwhere(MATRIX == K_RANDOM):
        MATRIX[y][x] = random.choice([K_SPACE, K_BOX])


FPS = 30
CHARACTER_LENGTH = 5
CELL_SIZE = 20
CELL_RECT = (CELL_SIZE, CELL_SIZE)


def get_rows_cols():
    return MATRIX.shape


def get_height_width(shape):
    rows, cols = shape
    return rows * CELL_SIZE, cols * CELL_SIZE


class GameState:
    WAITING_PHASE = "WAITING_PHASE"
    RANKING_PHASE = "RANKING_PHASE"
    GAME_PHASE = "GAME_PHASE"
    WINNER_PHASE = "WINNER_PHASE"
    TUTORIAL = "TUTORIAL"


def get_max_round(player_len):
    if player_len > 8:
        return 7
    elif player_len > 4:
        return 5

    return 3
