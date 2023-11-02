import settings
from settings import *
from assets import *


class Game:
    def __init__(self, client_socket, file):
        self.socket = client_socket
        self.file = file
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.grasses = Grass()

    def update(self, players, matrix):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.file.write(b"move_left\n")
        elif keys[pygame.K_RIGHT]:
            self.file.write(b"move_right\n")
        elif keys[pygame.K_UP]:
            self.file.write(b"move_up\n")
        elif keys[pygame.K_DOWN]:
            self.file.write(b"move_down\n")
        # elif keys[pygame.K_SPACE]:
        #     self.file.write(b"bomber_man\n")

        for (y, x), matrix_value in np.ndenumerate(matrix):
            position = (x * CELL_SIZE, y * CELL_SIZE)
            grass = self.grasses.get(f"{x}:{y}")

            if matrix_value in settings.K_EXPLOSION:
                self.surface.blit(grass, position)
                self.surface.blit(explosion_frame(
                    matrix_value - K_EXPLOSION_START), position)
            elif matrix_value in settings.K_BOMB:
                self.surface.blit(grass, position)
                self.surface.blit(bomb_frame(
                    matrix_value - K_BOMB_START), position)

            match matrix_value:
                case settings.K_WALL:
                    self.surface.blit(wall_sprites(), position)
                case settings.K_SPACE:
                    self.surface.blit(grass, position)
                case settings.K_BOX:
                    self.surface.blit(box_sprites(), position)
                case _:
                    pass

        for player in players:
            player.update(self.surface)
