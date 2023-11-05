from settings import *
from assets import *
from player import Player


class Game:
    def __init__(self, client_socket, file):
        self.socket = client_socket
        self.file = file
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.grasses = Grass()

    def update(self, players: list[Player], matrix):
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

            if matrix_value in K_EXPLOSION:
                self.surface.blit(grass, position)
                self.surface.blit(explosion_frame(
                    matrix_value - K_EXPLOSION_START), position)
            elif matrix_value in K_BOMB:
                self.surface.blit(grass, position)
                self.surface.blit(bomb_frame(
                    matrix_value - K_BOMB_START), position)
            elif matrix_value == K_WALL:
                self.surface.blit(wall_sprites(), position)
            elif matrix_value == K_SPACE:
                self.surface.blit(grass, position)
            elif matrix_value == K_BOX:
                self.surface.blit(box_sprites(), position)
            elif matrix_value == K_LIVES:
                self.surface.blit(grass, position)
                self.surface.blit(heart_sprites(), position)
            elif matrix_value == K_EXTRA_BOMB:
                self.surface.blit(grass, position)
                self.surface.blit(bomb_add_sprite(), position)
            elif matrix_value == K_INC_BOMB_RANGE:
                self.surface.blit(grass, position)
                self.surface.blit(expl_range_add_sprite(), position)
            elif matrix_value == K_MOVE_SPEED:
                self.surface.blit(movement_speed_sprite(), position)
            elif matrix_value == K_DEATH:
                self.surface.blit(skull_sprite(), position)

        for player in players:
            player.update(self.surface)

            msg = text(8, player.name, True, "#000000")
            self.surface.blit(msg, (player.rect.centerx - msg.get_width() // 2,
                                    player.rect.top - 10))
