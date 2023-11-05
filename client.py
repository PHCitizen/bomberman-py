import pygame
import pickle
import socket
import threading
import zlib
import os

from player import *
from settings import *
from game import Game
from assets import *
from button import *


class State:
    def __init__(self):
        self.matrix = None
        self.players: list[Player] = []
        self.player_index = -1

        self.socket = None
        self.file = None


def socket_thread(state: State):
    global matrix, players

    buffer = b""
    while True:
        try:
            new_data = state.file.readline()
        except Exception as e:
            print(e)
            print("Server probably disconnected")
            os._exit(1)

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
            state.players = pickle.loads(data)
        elif buffer.startswith(b"matrix:"):
            data = buffer.removesuffix(b"$|$\n")
            data = data.split(b":", 1)[1]
            try:
                data = zlib.decompress(data)
                state.matrix = np.frombuffer(
                    data, dtype=np.uint8).reshape(MATRIX.shape)
            except zlib.error as e:
                print(buffer, e)
        else:
            print("Unknown message", buffer)

        buffer = b""


def waiting_phase(state: State):
    window = pygame.display.set_mode((500, 200))
    clock = pygame.time.Clock()

    waiting_text = text(15, 'Waiting for host to start...', True, "#d7fcd4")
    select_text = text(15, 'Choose your character', True, "#d7fcd4")
    pname_text = text(15, 'Enter name:', True, "#d7fcd4")
    player_name = InputBox(185, 45, 200, 25, 15,
                           f"Player {state.player_index}")

    def sumbit_name(name):
        pygame.display.set_caption(f"BomberPy - {name}")
        state.file.write(f"name:{name}\n".encode())

    characters = [
        Button(pygame.transform.scale2x(PlayerSprite(i).get()), ((64 * i) + 70, 140),
               "", font(20), "#d7fcd4", "White")
        for i in range(1, 6)
    ]

    selected_character = 0
    box_surface = pygame.Surface((64, 64))
    box_surface.fill("#00ff00")

    while True:
        mouse_position = pygame.mouse.get_pos()
        window.blit(get_background(), (0, 0))

        if state.matrix is not None:
            break

        # Main screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for id, character in enumerate(characters):
                    if character.checkForInput(mouse_position):
                        state.file.write(f"character:{id + 1}\n".encode())
                        selected_character = id

            player_name.handle_event(event, sumbit_name)

        window.blit(pname_text, (20, 50))
        window.blit(waiting_text, (20, 10))
        player_name.draw(window)
        window.blit(select_text, (20, 90))

        for id, character in enumerate(characters):
            character.update(window, mouse_position)
        pygame.draw.rect(window, "#00ff00",
                         ((selected_character * 64) + 100, 110, 64, 64), 2)

        pygame.display.update()
        clock.tick(FPS)


def game_phase(state: State):
    bgmusic().play(-1)

    clock = pygame.time.Clock()
    game_obj = Game(state.socket, state.file)
    stats_window = pygame.Surface((GAME_WIDTH, CELL_SIZE))
    window = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT + CELL_SIZE))
    current_player = state.players[state.player_index]

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                state.file.write(b"bomber_man\n")

        stats_window.fill("#ffffff")
        for i in range(current_player.bombs):
            stats_window.blit(bomb_frame(0), (i * CELL_SIZE, 0))

        for i in range(current_player.lives):
            stats_window.blit(
                heart_sprites(), (GAME_WIDTH - ((i + 1) * CELL_SIZE), 0))

        window.blit(stats_window, (0, 0))
        game_obj.update(state.players, state.matrix)
        window.blit(game_obj.surface, (0, CELL_SIZE))

        pygame.display.update()
        clock.tick(FPS)


def main():
    pygame.init()

    state = State()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("localhost", 8888))
        client_file = socket.SocketIO(client_socket, "rwb")

        state.file = client_file
        state.socket = client_socket
    except Exception as e:
        print(e)
        print("Failed to connect to server")
        os._exit(1)

    # the server will sent the player index once we connect
    player_index = client_file.readline().rstrip()
    player_index = int.from_bytes(player_index, "big")
    state.player_index = player_index
    pygame.display.set_caption(f"BomberPy - Player {player_index}")

    # start the app
    threading.Thread(target=socket_thread, args=(state,), daemon=True).start()
    waiting_phase(state)
    game_phase(state)


if __name__ == "__main__":
    main()
