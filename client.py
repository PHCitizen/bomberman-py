import pygame
import pickle
import socket
import threading
import zlib

from player import Player
from settings import *
from game import Game
from sprites import *


pygame.init()
WINDOW = pygame.display.set_mode((500, 200))

matrix = None
players: list[Player] = []
clock = pygame.time.Clock()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("localhost", 8888))
client_file = socket.SocketIO(client_socket, "rwb")

player_index = client_file.readline().rstrip()
player_index = int.from_bytes(player_index, "big")
pygame.display.set_caption(f"BomberPy - Player {player_index}")


def socket_thread():
    global matrix, players

    buffer = b""
    while True:
        try:
            new_data = client_file.readline()
            if not new_data.endswith(b"$|$\n"):
                buffer += new_data
                continue

            data = zlib.decompress(buffer + new_data.removesuffix(b"$|$\n"))
            data = data.split(b"$|$")

            players = pickle.loads(data[0])
            matrix = np.frombuffer(
                data[1], dtype=np.uint8).reshape(MATRIX.shape)
            buffer = b""
        except zlib.error as e:
            print(buffer, e)
            continue


threading.Thread(target=socket_thread, daemon=True).start()


waiting_text = text(30, 'Waiting for host \nto start...', True, "#d7fcd4")

while True:
    WINDOW.blit(get_background(), (0, 0))

    if matrix is not None:
        break

    # Main screen
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    WINDOW.blit(waiting_text, (10, 50))

    pygame.display.update()
    clock.tick(FPS)


game_obj = Game(client_socket, client_file)
stats_window = pygame.Surface((GAME_WIDTH, CELL_SIZE))
WINDOW = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT + CELL_SIZE))


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            client_file.write(b"bomber_man\n")

    stats_window.fill("#ffffff")
    for i in range(players[player_index].bombs):
        stats_window.blit(bomb_sprites(), (i * CELL_SIZE, 0))

    for i in range(players[player_index].lives):
        stats_window.blit(
            heart_sprites(), (GAME_WIDTH - ((i + 1) * CELL_SIZE), 0))

    WINDOW.blit(stats_window, (0, 0))
    game_obj.update(players, matrix)
    WINDOW.blit(game_obj.surface, (0, CELL_SIZE))

    pygame.display.update()
    clock.tick(FPS)
