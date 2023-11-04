import pygame
import pickle
import socket
import threading
import zlib

from player import Player
from settings import *
from game import Game
from assets import *
from button import *

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
        new_data = client_file.readline()
        if not new_data.endswith(b"$|$\n"):
            buffer += new_data
            continue
        buffer += new_data

        if buffer == b"explosion$|$\n":
            explosion_sound().play(0)
        elif buffer == b"ghost$|$\n":
            ghost_sound().play(0)
        elif buffer.startswith(b"pdata:"):
            data = buffer.removesuffix(b"$|$\n")
            data = data.split(b":", 1)[1]
            players = pickle.loads(data)
        elif buffer.startswith(b"matrix:"):
            data = buffer.removesuffix(b"$|$\n")
            data = data.split(b":", 1)[1]
            try:
                data = zlib.decompress(data)
                matrix = np.frombuffer(
                    data, dtype=np.uint8).reshape(MATRIX.shape)
            except zlib.error as e:
                print(buffer, e)
        else:
            print("Unknown message", buffer)

        buffer = b""


threading.Thread(target=socket_thread, daemon=True).start()


waiting_text = text(15, 'Waiting for host to start...', True, "#d7fcd4")
pname_text = text(15, 'Enter name:', True, "#d7fcd4")
player_name = InputBox(185, 45, 200, 25, 15, f"Player {player_index}")


def sumbit_name(name):
    pygame.display.set_caption(f"BomberPy - {name}")
    client_file.write(f"name:{name}\n".encode())


while True:
    WINDOW.blit(get_background(), (0, 0))

    if matrix is not None:
        break

    # Main screen
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        player_name.handle_event(event, sumbit_name)

    WINDOW.blit(pname_text, (20, 50))
    WINDOW.blit(waiting_text, (50, 10))
    player_name.draw(WINDOW)

    pygame.display.update()
    clock.tick(FPS)


bgmusic().play(-1)

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
        stats_window.blit(bomb_frame(0), (i * CELL_SIZE, 0))

    for i in range(players[player_index].lives):
        stats_window.blit(
            heart_sprites(), (GAME_WIDTH - ((i + 1) * CELL_SIZE), 0))

    WINDOW.blit(stats_window, (0, 0))
    game_obj.update(players, matrix)
    WINDOW.blit(game_obj.surface, (0, CELL_SIZE))

    pygame.display.update()
    clock.tick(FPS)
