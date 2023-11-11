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
from bomb import BombFactory


class State:
    def __init__(self):
        self.start = False
        self.players: list[tuple[socket.socket, socket.SocketIO, Player]] = []
        self.task_manager = Task()
        self.bomb_factory = BombFactory(self.task_manager, list(map(lambda p: p[2], self.players)))

        # ? if our host will run on server without display
        self.headless = False


def message_handler(players, index: int):
    """
    Handle player msg.
    if message match certain action, do it
    """
    conn, file, current_player = players[index]

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


def host_thread(host, port, state: State):
    """
    This host thread
    used to accept new connection and create new player
    """

    # listen to port using TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(MAX_PLAYER)
    print("server started")

    i = 0
    while True:
        if state.start:
            break

        # player connection obj
        player_socket, _ = server_socket.accept()
        file = socket.SocketIO(player_socket, "rwb")
        new_player = Player(state.task_manager, state.bomb_factory, DEFAULT_COORD[i], f"Player {i}", 1)

        # send to player the player_id
        player_socket.sendall(i.to_bytes(16, "big") + b"\n")

        # update state
        state.players.append((player_socket, file, new_player))
        state.bomb_factory = BombFactory(state.task_manager, list(map(lambda p: p[2], state.players)))

        # process player message individually, (non-blocking)
        threading.Thread(
            target=message_handler,
            args=(state.players, i),
            daemon=True).start()

        print(f"Player {i} connected")
        i += 1


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
        return None

    alive: list[tuple[int, Player]] = []
    for i, player in enumerate(players):
        if player.lives != 0:
            alive.append((i, player))

    if len(alive) == 1:
        return alive[0]
    return None


def event_loop(state: State):
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
                    state.start = True
            elif event.type == E_EXPLOSION:
                broadcast(state.players, b"explosion$|$\n")
            elif event.type == E_GHOST:
                broadcast(state.players, b"ghost$|$\n")

        winner = has_winner(list(map(lambda p: p[2], state.players)))
        if winner is not None:
            break

        # check if player steps on tile with explosion
        player_tile = [(player.calc_player_tile(), player)  # pre-calc player tile
                       for _, _, player in state.players]
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

        for i, (player_socket, _, player) in enumerate(state.players):
            is_connected = "Disconnected" if player_socket is None else "Connected"
            is_alive = "Alive" if player.lives > 0 else "Dead"
            window.blit(
                text(
                    15, f'{player.name} - {is_alive} - {is_connected}', True, "#d7fcd4"),
                (0, 100 + (20 * i))
            )

        if state.start:
            # send current matrix and player data for each player

            pdata = pickle.dumps(list(map(lambda p: p[2], state.players)))
            if pdata != last_pdata:
                broadcast(state.players, b"pdata:" + pdata + b"$|$\n")
                last_pdata = pdata

            matrix_data = MATRIX.tobytes()
            if matrix_data != last_matrix:
                broadcast(state.players, b"matrix:" + zlib.compress(matrix_data) + b"$|$\n")
                last_matrix = matrix_data

            # game status
            window.blit(
                text(20, 'Game started', True, "#d7fcd4"),
                (125, 30),
            )
        else:
            start_btn.update(window, mouse_position)

        # update
        state.task_manager.tick()
        pygame.display.update()
        clock.tick(FPS)

    broadcast(state.players, f"winner:{winner[0]}$|$\n".encode())

    winner_text = text(20, f'{winner[1].name} wins!!!', True, "#d7fcd4")
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
    state = State()

    # pass shared state different process
    threading.Thread(target=host_thread, args=(
        host, port, state), daemon=True).start()
    # threading.Thread(target=event_loop, args=(
    #     task_manager, players, app_state), daemon=True).start()
    # input(":")
    # app_state["start"] = True
    # input(":")
    event_loop(state)


if __name__ == "__main__":
    main()
