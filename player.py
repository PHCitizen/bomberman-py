import pygame
from settings import *
from functools import cache
from bomb import Bomb


@cache
def get_sprites():
    from assets import SpriteFrame

    print("[ DEBUG ] Lazy loaded sprites")
    player_surface = pygame.image.load(
        "./graphics/characters/1.png").convert_alpha()
    player_surface = pygame.transform.scale(player_surface, CELL_RECT)

    ghosts_sprite = pygame.image.load(
        "./graphics/characters/ghost.png").convert_alpha()
    ghosts_sprite_len = ghosts_sprite.get_width() / 32
    ghosts_sprite = pygame.transform.scale(
        ghosts_sprite, (ghosts_sprite_len * CELL_SIZE, CELL_SIZE))
    ghosts_sprite = SpriteFrame(ghosts_sprite, CELL_SIZE, CELL_SIZE, 100)

    tomb_surface = pygame.image.load("./graphics/tomb.png").convert_alpha()

    shadow_surface = pygame.Surface(CELL_RECT)
    shadow_surface.fill("#a0a2a3")

    return player_surface, ghosts_sprite, tomb_surface, shadow_surface


def can_move(x, y, ghost_mode):
    """prevent movement when bomb or wall encounter"""
    if ghost_mode:
        return 0 < x < GAME_COLS - 1 and 0 < y < GAME_ROWS - 1

    val = MATRIX[y][x]
    if val in [K_WALL, K_BOX] or val in K_BOMB:
        return False
    return True


class Player:
    def __init__(self, task,  pos, name):
        self.name = name
        self.rect = pygame.Rect((0, 0), (CELL_SIZE, CELL_SIZE))
        self.rect.x = pos[0] * CELL_SIZE
        self.rect.y = pos[1] * CELL_SIZE

        self.task = task

        self.movement_speed = 2
        self.bombs = 2
        self.bomb_recharge_time = 5000

        self.lives = 3
        self.ghost_mode = False
        self.ghost_mode_duration = 5000

        self.frame = 0

    def __getstate__(self):
        return self.rect, self.bombs, self.lives, self.ghost_mode, self.name

    def __setstate__(self, state):
        self.rect, self.bombs, self.lives, self.ghost_mode, self.name = state

    def move_up(self):
        if self.lives == 0:
            return

        player_x, player_y = self.calc_player_tile()
        offset = self.rect.bottom // CELL_SIZE
        if can_move(player_x, player_y - 1, self.ghost_mode) or player_y != offset:
            self.rect.y -= self.movement_speed

    def move_down(self):
        if self.lives == 0:
            return

        player_x, player_y = self.calc_player_tile()
        offset = self.rect.top // CELL_SIZE
        if can_move(player_x, player_y + 1, self.ghost_mode) or player_y != offset:
            self.rect.y += self.movement_speed

    def move_left(self):
        if self.lives == 0:
            return

        player_x, player_y = self.calc_player_tile()
        offset = self.rect.right // CELL_SIZE
        if can_move(player_x - 1, player_y, self.ghost_mode) or player_x != offset:
            self.rect.x -= self.movement_speed

    def move_right(self):
        if self.lives == 0:
            return

        player_x, player_y = self.calc_player_tile()
        offset = self.rect.left // CELL_SIZE
        if can_move(player_x + 1, player_y, self.ghost_mode) or player_x != offset:
            self.rect.x += self.movement_speed

    def calc_player_tile(self):
        player_x = self.rect.centerx // CELL_SIZE
        player_y = self.rect.centery // CELL_SIZE
        return player_x, player_y

    def bomber_man(self):
        player_x, player_y = self.calc_player_tile()
        if self.bombs == 0 or self.ghost_mode or self.lives == 0 or MATRIX[player_y][player_x] != K_SPACE:
            return

        Bomb(self.task, player_x, player_y)
        self.bombs -= 1

        def recharge():
            self.bombs += 1

        self.task.add(self.bomb_recharge_time, recharge)

    def kill(self):
        if self.ghost_mode or self.lives == 0:
            return

        pygame.event.post(pygame.Event(E_GHOST))

        self.lives -= 1
        self.ghost_mode = True

        movement_speed = self.movement_speed
        self.movement_speed *= 2

        def back_to_normal_mode():
            self.ghost_mode = False
            self.movement_speed = movement_speed

        self.task.add(self.ghost_mode_duration, back_to_normal_mode)

    def update(self, game_surface):
        player_surface, ghosts_sprite, tomb_surface, shadow_surface = get_sprites()
        if self.lives == 0:
            game_surface.blit(tomb_surface, self.rect)
            return

        x, y = self.calc_player_tile()
        game_surface.blit(shadow_surface, (x * CELL_SIZE, y * CELL_SIZE))

        if self.ghost_mode:
            game_surface.blit(ghosts_sprite.get(), self.rect)
        else:
            game_surface.blit(player_surface, self.rect)
