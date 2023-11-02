from settings import *


class Bomb:
    def __init__(self, task, tile_x, tile_y):
        self.task = task
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.range = BOMB_EXPLOSION_RANGE

        self.wait_before_expl = 2400
        self.expl_duration = 1500

        MATRIX[tile_y][tile_x] = K_BOMB
        self.task.add(self.wait_before_expl, self.explode)

    def calc_vertical_expl(self):
        player_x, player_y = self.tile_x, self.tile_y

        tiles = []
        for i in range(1, self.range + 1):
            val = MATRIX[player_y - i][player_x]
            if val in [K_WALL, K_BOMB] or val in K_EXPLOSION:
                break

            tiles.append((player_x, player_y - i))

            if val == K_BOX:
                break

        for i in range(1, self.range + 1):
            val = MATRIX[player_y + i][player_x]
            if val in [K_WALL, K_BOMB] or val in K_EXPLOSION:
                break

            tiles.append((player_x, player_y + i))

            if val == K_BOX:
                break

        return tiles

    def calc_horizontal_expl(self):
        player_x, player_y = self.tile_x, self.tile_y

        tiles = []
        for i in range(1, self.range + 1):
            val = MATRIX[player_y][player_x - i]
            if val in [K_WALL, K_BOMB] or val in K_EXPLOSION:
                break

            tiles.append((player_x - i, player_y))

            if val == K_BOX:
                break

        for i in range(1, self.range + 1):
            val = MATRIX[player_y][player_x + i]
            if val in [K_WALL, K_BOMB] or val in K_EXPLOSION:
                break

            tiles.append((player_x + i, player_y))

            if val == K_BOX:
                break

        return tiles

    def explode(self):
        tile_x, tile_y = self.tile_x, self.tile_y

        MATRIX[tile_y][tile_x] = K_EXPLOSION_START
        tile1 = self.calc_vertical_expl()
        tile2 = self.calc_horizontal_expl()
        tiles = tile1 + tile2
        tiles.append((tile_x, tile_y))

        Explotion(self.task, tiles, 100)


class Explotion:
    def __init__(self, task, tiles, speed):
        self.task = task
        self.tiles = tiles
        self.speed = speed
        self.frame = 0
        self.move_frame()

    def move_frame(self):
        self.set_frame(K_EXPLOSION_START + self.frame)

        if self.frame <= K_EXPLOSION_END - K_EXPLOSION_START:
            self.task.add(self.speed, self.move_frame)
            self.frame += 1
        else:
            self.set_frame(K_SPACE)

    def set_frame(self, n):
        for x, y in self.tiles:
            MATRIX[y][x] = n