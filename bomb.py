import pygame
import random
from settings import *


class Bomb:
    def __init__(self, players, player, task, position):
        self.task = task
        self.player = player
        self.players = players
        self.position = position

        self.frame = 0
        self.speed = 250
        self.move_frame()

    def move_frame(self):
        MATRIX[self.position[1]][self.position[0]] = K_BOMB_START + self.frame

        if self.frame <= K_BOMB_END - K_BOMB_START:
            self.task.add(self.speed, self.move_frame)
            self.frame += 1
        else:
            self.explode()

    def calc_vertical_expl(self):
        player_x, player_y = self.position

        tiles = []
        boxs = []
        for i in range(1, self.player.bomb_range + 1):
            val = MATRIX[player_y - i][player_x]
            if val == K_WALL or val in K_BOMB or val in K_EXPLOSION:
                break

            if val in POWER_UP:
                continue

            tiles.append((player_x, player_y - i))

            if val == K_BOX:
                boxs.append((player_x, player_y - i))
                break

        for i in range(1, self.player.bomb_range + 1):
            val = MATRIX[player_y + i][player_x]
            if val == K_WALL or val in K_BOMB or val in K_EXPLOSION:
                break

            if val in POWER_UP:
                continue

            tiles.append((player_x, player_y + i))

            if val == K_BOX:
                boxs.append((player_x, player_y + i))
                break

        return tiles, boxs

    def calc_horizontal_expl(self):
        player_x, player_y = self.position

        tiles = []
        boxs = []

        for i in range(1, self.player.bomb_range + 1):
            val = MATRIX[player_y][player_x - i]
            if val == K_WALL or val in K_BOMB or val in K_EXPLOSION:
                break

            if val in POWER_UP:
                continue

            tiles.append((player_x - i, player_y))

            if val == K_BOX:
                boxs.append((player_x - i, player_y))
                break

        for i in range(1, self.player.bomb_range + 1):
            val = MATRIX[player_y][player_x + i]
            if val == K_WALL or val in K_BOMB or val in K_EXPLOSION:
                break

            if val in POWER_UP:
                continue

            tiles.append((player_x + i, player_y))

            if val == K_BOX:
                boxs.append((player_x + i, player_y))
                break

        return tiles, boxs

    def explode(self):
        pygame.event.post(pygame.Event(E_EXPLOSION))

        tile1, boxs1 = self.calc_vertical_expl()
        tile2, boxs2 = self.calc_horizontal_expl()
        tiles = tile1 + tile2
        tiles.append(self.position)
        boxs = boxs1 + boxs2

        # ? increment player points by how many box it destroy
        self.player.points += len(boxs) * PTS_BOX

        Explosion(self.task, self.players, self.player, tiles, boxs)


class BombFactory:
    def __init__(self, task, players):
        self.task = task
        self.players = players

    def place(self, player, position):
        Bomb(self.players, player, self.task, position)


class Explosion:
    def __init__(self, task, players, player, tiles, boxs):
        self.task = task
        self.players = players
        self.player = player
        self.tiles = tiles
        self.boxs = boxs
        self.speed = 100
        self.frame = 0
        self.move_frame()

    def move_frame(self):
        self.set_frame(K_EXPLOSION_START + self.frame)

        player_tile = [(player.calc_player_tile(), player)  # pre-calc player tile
                       for _, _, player in self.players]
        for (y, x), matrix_value in np.ndenumerate(MATRIX):
            for (px, py), player in player_tile:
                if px == x and py == y:
                    if matrix_value in K_EXPLOSION:
                        if player == self.player:
                            if not self.player.ghost_mode:
                                self.player.kill()
                                self.player.points += PTS_SUICIDE
                        else:
                            if not player.ghost_mode:
                                player.kill()
                                self.player.points += PTS_KILL

        if self.frame <= K_EXPLOSION_END - K_EXPLOSION_START:
            self.task.add(self.speed, self.move_frame)
            self.frame += 1
        else:
            self.set_frame(K_SPACE)
            for x, y in self.boxs:
                # ? 1 means we will output power up
                if random.choice([0, 1, 1]) == 1:
                    MATRIX[y][x] = random.choice(POWER_UP)

    def set_frame(self, n):
        for x, y in self.tiles:
            MATRIX[y][x] = n
