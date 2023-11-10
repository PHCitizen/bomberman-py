import socket
import threading
import pygame
import zlib
import random
import pickle
import sys

from player import *
from settings import *
from assets import *
from task import Task
from button import Button


def message_handler(players, index: int, conn: socket.socket, file: socket.SocketIO):
    """
    Handle player msg.
    if message match certain action, do it
    """
    current_player: Player = players[index][2]

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
            elif data.startswith(b"character:"):
                character = data.rstrip().split(b":")[1].decode()
                character = int(character)
                current_player.character = PlayerSprite(character)
            else:
                print(data)
        except Exception as e:
            print(e)
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
        new_player = Player(task_manager, DEFAULT_COORD[i], f"Player {i}", 1)

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


def has_winner(players: list[Player]):
    if len(players) <= 1:
        return (False, -1)

    lives = list(map(lambda v: v[2].lives, players))
    count = 0
    for index, live in enumerate(lives):
        if live != 0:
            count += 1

    if count == 1:
        return (True, index)
    return (False, -1)


def event_loop(task_manager, players: list[tuple[None, None, Player]], appstate):
    """
    Pygame window
    """

    pygame.init()
    window = pygame.display.set_mode((500, 200))
    pygame.display.set_caption("BomberPy - Host")
    clock = pygame.time.Clock()

    start_btn = Button(None, (250, 50),
                       " Start ", font(30), "#d7fcd4", "White")

    last_matrix = b""
    last_pdata = b""
    winner = -1

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
                    appstate["start"] = True
            elif event.type == E_EXPLOSION:
                broadcast(players, b"explosion$|$\n")
            elif event.type == E_GHOST:
                broadcast(players, b"ghost$|$\n")

        one_alive, index = has_winner(players)
        if one_alive:
            winner = players[index][2].name
            break

        # check if player steps on tile with explosion
        player_tile = [(player.calc_player_tile(), player)  # pre-calc player tile
                       for _, _, player in players]
        for (y, x), matrix_value in np.ndenumerate(MATRIX):
            for (px, py), player in player_tile:
                if px == x and py == y:
                    if matrix_value in K_EXPLOSION:
                        player.kill()

                    if matrix_value in POWER_UP and not player.ghost_mode:
                        if matrix_value == K_LIVES:
                            player.lives += 1
                        elif matrix_value == K_EXTRA_BOMB:
                            player.bombs += 1
                        elif matrix_value == K_INC_BOMB_RANGE:
                            player.bomb_range += 1
                        elif matrix_value == K_MOVE_SPEED:
                            player.movement_speed += 1
                        elif matrix_value == K_DEATH:
                            player.lives -= 1

                        MATRIX[y][x] = K_SPACE

        for i, (player_socket, _, player) in enumerate(players):
            is_connected = "Disconnected" if player_socket is None else "Connected"
            is_alive = "Alive" if player.lives > 0 else "Dead"
            window.blit(
                text(
                    15, f'{player.name} - {is_alive} - {is_connected}', True, "#d7fcd4"),
                (0, 100 + (20 * i))
            )

        if appstate["start"]:
            # send current matrix and player data for each player

            pdata = pickle.dumps(list(map(lambda p: p[2], players)))
            if pdata != last_pdata:
                broadcast(players, b"pdata:" + pdata + b"$|$\n")
                last_pdata = pdata

            matrix_data = MATRIX.tobytes()
            if matrix_data != last_matrix:
                broadcast(players, b"matrix:" +
                          zlib.compress(matrix_data) + b"$|$\n")
                last_matrix = matrix_data

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

    broadcast(players, f"winner:{winner}$|$\n".encode())

    winner_text = text(20, f'{winner} wins!!!', True, "#d7fcd4")
    exit_btn = Button(None, (250, 100),
                      " Exit ", font(20), "#d7fcd4", "White")
    run = True
    while run:
        mouse_position = pygame.mouse.get_pos()
        window.blit(get_background(), (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if exit_btn.checkForInput(mouse_position):
                    run = False

        window.blit(winner_text, (0, 50))
        exit_btn.update(window, mouse_position)

        pygame.display.update()
        clock.tick(FPS)


def main():
    host = '0.0.0.0'
    try:
        port = int(sys.argv[1])
    except IndexError:
        port = 8888

    # randomize field
    for y, x in np.argwhere(MATRIX == K_RANDOM):
        MATRIX[y][x] = random.choice([K_SPACE, K_BOX])

    # shared state
    app_state = {"start": False}
    task_manager = Task()
    players: list[tuple[socket.socket, socket.SocketIO, Player]] = []

    # pass shared state different process
    threading.Thread(target=host_thread, args=(
        host, port, task_manager, players), daemon=True).start()
    # threading.Thread(target=event_loop, args=(
    #     task_manager, players, app_state), daemon=True).start()
    # input(":")
    # app_state["start"] = True
    # input(":")
    event_loop(task_manager, players, app_state)


if __name__ == "__main__":
    main()
