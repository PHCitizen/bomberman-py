import pygame
import random
from settings import CELL_RECT
from functools import cache


@cache
def wall_sprites():
    image = pygame.image.load("./graphics/wall1.png").convert_alpha()
    return pygame.transform.scale(image, CELL_RECT)


@cache
def box_sprites():
    image = pygame.image.load("./graphics/box1.png").convert_alpha()
    return pygame.transform.scale(image, CELL_RECT)


@cache
def bomb_sprites():
    image = pygame.image.load("./graphics/bomb.png").convert_alpha()
    return pygame.transform.scale(image, CELL_RECT)


@cache
def heart_sprites():
    image = pygame.image.load("./graphics/heart.png").convert_alpha()
    return pygame.transform.scale(image, CELL_RECT)


@cache
def player_sprites():
    image = pygame.image.load("./graphics/characters/1.png").convert_alpha()
    return pygame.transform.scale(image, CELL_RECT)


@cache
def explosion_sprites():
    return pygame.image.load("./graphics/explosions.png").convert_alpha()


@cache
def explosion_frame(n):
    return get_image(explosion_sprites(), n, 32, 32)


@cache
def get_image(sprite, frame, width, height):
    surface = pygame.Surface(
        (width, height), pygame.SRCALPHA, 32).convert_alpha()
    surface.blit(sprite, (0, 0), ((frame * width), 0, width, height))
    return pygame.transform.scale(surface, CELL_RECT)


@cache
def font(size):
    return pygame.font.Font("./graphics/font.ttf", size)


def text(size, *args):
    return font(size).render(*args)


@cache
def get_background():
    return pygame.image.load("./graphics/Background.png").convert_alpha()


class Grass:
    def __init__(self):
        sprite = pygame.image.load("./graphics/grass2.png").convert_alpha()
        self.grass = {i: get_image(sprite, i, 32, 32)
                      for i in range(32)}
        self.seeded_grass = {}

    def get(self, seed):
        surface = self.seeded_grass.get(seed)
        if surface:
            return surface

        frame = random.randrange(0, 32)
        grass = self.grass[frame]
        self.seeded_grass[seed] = grass
        return grass


class SpriteFrame:
    def __init__(self, sprite, width, height, speed):
        self.sprite = sprite
        self.width = width
        self.height = height
        self.speed = speed

        self.max_frame = sprite.get_width() / width
        self.frame = 0
        self.last_tick = 0

        self.surface = get_image(
            self.sprite, self.frame, self.width, self.height)

    def get(self):
        current_tick = pygame.time.get_ticks()
        if current_tick - self.last_tick < self.speed:
            return self.surface

        self.surface = get_image(
            self.sprite, self.frame, self.width, self.height)
        self.frame += 1
        if self.frame == self.max_frame:
            self.frame = 0

        self.last_tick = current_tick
        return self.surface
