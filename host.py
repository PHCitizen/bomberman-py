import socket
import threading
import pygame
import zlib
import random
import pickle

from player import Player
from settings import *
from assets import *
from task import Task
from button import Button


def message_handler(players, index: int, conn: socket.socket, file: socket.SocketIO):
    """
    Handle player msg.
    if message match certain action, do it
    """
    current_player = players[index][2]

    while True:
        try:
            data = file.readline()
            if not data:
                break

            if data == b"move_left\n":
                current_player.move_left()
            elif data == b"move_right\n":
                current_player.move_right()
            elif data == b"move_up\n":
                current_player.move_up()
            elif data == b"move_down\n":
                current_player.move_down()
            elif data == b"bomber_man\n":
                current_player.bomber_man()
            elif data.startswith(b"name:"):
                current_player.name = data.rstrip().split(b":")[1].decode()
            else:
                print(data)
        except Exception:
            break

    # Player disconnect. do cleanup
    print(f"player {index} disconnect")
    players[index] = (None, None, current_player)
    conn.close()


def host_thread(host, port, task_manager, players):
    """
    This host thread
    used to accept new connection and create new player
    """

    # listen to port using TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(MAX_PLAYER)
    print("server started")

    # accept only 'MAX_PLAYER' amount of connection
    for i in range(MAX_PLAYER):
        # player connection obj
        player_socket, _ = server_socket.accept()
        file = socket.SocketIO(player_socket, "rwb")
        new_player = Player(task_manager, DEFAULT_COORD[i], f"Player {i}", 2)

        # send to player the player_id
        player_socket.sendall(i.to_bytes(16, "big") + b"\n")
        players.append((player_socket, file, new_player))

        # process player message individually, (non-blocking)
        threading.Thread(
            target=message_handler,
            args=(players, i, player_socket, file),
            daemon=True).start()

        print(f"Player {i} connected")


def broadcast(players, data):
    for player_socket, _, _ in players:
        # if player are disconnected, skip it
        if player_socket is None:
            continue

        try:
            player_socket.sendall(data)
        except Exception:
            continue


def event_loop(task_manager, players):
    """
    Pygame window
    """

    pygame.init()
    window = pygame.display.set_mode((500, 200))
    pygame.display.set_caption("BomberPy - Host")
    clock = pygame.time.Clock()

    # Singleton
    start_btn = Button(None, (250, 50),
                       " Start ", font(30), "#d7fcd4", "White")

    # States:
    start = False

    while True:
        window.blit(get_background(), (0, 0))
        mouse_position = pygame.mouse.get_pos()

        # process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.checkForInput(mouse_position):
                    start = True
            elif event.type == E_EXPLOSION:
                broadcast(players, b"explosion$|$\n")
            elif event.type == E_GHOST:
                broadcast(players, b"ghost$|$\n")

        # check if player steps on tile with explotion
        for y, x in np.argwhere((MATRIX >= K_EXPLOSION_START) & (MATRIX < K_EXPLOSION_END)):
            for _, _, player in players:
                px, py = player.calc_player_tile()
                if px == x and py == y:
                    player.kill()

        for i, (player_socket, _, player) in enumerate(players):
            is_connected = "Disconnected" if player_socket is None else "Connected"
            window.blit(
                text(20, f'{player.name} - {is_connected}', True, "#d7fcd4"),
                (0, 100 + (20 * i))
            )

        if start:
            # send current matrix and player data for each player
            pdata = pickle.dumps(list(map(lambda p: p[2], players))) + b"$|$"
            matrix = MATRIX.tobytes() + b"$|$"
            broadcast(players, zlib.compress(pdata + matrix) + b"$|$\n")

            # game status
            window.blit(
                text(20, 'Game started', True, "#d7fcd4"),
                (125, 30),
            )
        else:
            start_btn.update(window, mouse_position)

        # update
        task_manager.tick()
        pygame.display.update()
        clock.tick(FPS)


def main():
    host, port = '0.0.0.0', 8888

    # randomize field
    for y, x in np.argwhere(MATRIX == K_RANDOM):
        MATRIX[y][x] = random.choice([K_SPACE, K_BOX])

    # shared state
    task_manager = Task()
    players: list[tuple[socket.socket, socket.SocketIO, Player]] = []

    # pass shared state different process
    threading.Thread(target=host_thread, args=(
        host, port, task_manager, players), daemon=True).start()
    event_loop(task_manager, players)


if __name__ == "__main__":
    main()
