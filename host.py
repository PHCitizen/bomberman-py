import socket
import threading
import pygame
import zlib
import pickle
import sys
import time
from datetime import datetime

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
        self.bomb_factory = BombFactory(self.task_manager, self.players)

        # ? if our host will run on server without display
        self.headless = False


def message_handler(players, index: int):
    """
    Handle player msg.
    if message match certain action, do it
    """

    while True:
        conn, file, current_player = players[index]

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
                current_player.character_id = character
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
    server_socket.listen()
    print("server started")

    i = 0
    while True:
        if state.start:
            break

        # player connection obj
        player_socket, _ = server_socket.accept()
        print(f"Player {i} connected")
        file = socket.SocketIO(player_socket, "rwb")
        ptile = player_tile(len(state.players) + 1)[i]
        new_player = Player(state.task_manager, state.bomb_factory,
                            ptile, f"Player {i}", 1)

        # send to player the player_id
        player_socket.sendall(i.to_bytes(16, "big") + b"\n")

        # update state
        state.players.append((player_socket, file, new_player))
        state.bomb_factory = BombFactory(state.task_manager, state.players)

        # process player message individually, (non-blocking)
        threading.Thread(
            target=message_handler,
            args=(state.players, i),
            daemon=True).start()

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


def game(round, state: State):
    reset_matrix(len(state.players))

    max_round = get_max_round(len(state.players))
    broadcast(state.players, f"round:{round} of {max_round}$|$\n".encode())
    for i in range(PLAY_WAIT_TIME, 0, -1):
        broadcast(state.players, f"countdown:{i}$|$\n".encode())
        time.sleep(1)

    countdown = PLAY_TIME
    last_time = datetime.now().timestamp()
    broadcast(state.players, f"countdown:{countdown}$|$\n".encode())
    broadcast(state.players, "go$|$\n".encode())
    clock = pygame.time.Clock()

    last_matrix = b""
    last_pdata = b""

    while True:
        winner = has_winner(list(map(lambda p: p[2], state.players)))
        if winner is not None:
            break

        current_time = datetime.now().timestamp()
        if current_time - last_time >= 1:
            countdown -= 1
            broadcast(state.players, f"countdown:{countdown}$|$\n".encode())
            last_time = current_time

        if countdown <= 0:
            break

        # check if player steps on tile with explosion
        player_tile = [(player.calc_player_tile(), player)  # pre-calc player tile
                       for _, _, player in state.players]
        for (y, x), matrix_value in np.ndenumerate(MATRIX):
            for (px, py), player in player_tile:
                if px == x and py == y:
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

        # send current matrix and player data for each player
        pdata = pickle.dumps(list(map(lambda p: p[2], state.players)))
        if pdata != last_pdata:
            broadcast(state.players, b"pdata:" + pdata + b"$|$\n")
            last_pdata = pdata

        matrix_data = MATRIX.tobytes()
        if matrix_data != last_matrix:
            broadcast(state.players, b"matrix:" + f"{MATRIX.shape[0]}:{MATRIX.shape[1]}:".encode() +
                      zlib.compress(matrix_data) + b"$|$\n")
            last_matrix = matrix_data

        # update
        state.task_manager.tick()
        clock.tick(FPS)

    # update player info for each player
    for _, _, player in state.players:
        player.points += player.lives * LIFE_PTS_CONVERTION
    pdata = pickle.dumps(list(map(lambda p: p[2], state.players)))
    broadcast(state.players, b"pdata:" + pdata + b"$|$\n")


def play(state: State):
    current_round = 1
    while True:
        if not state.start:
            time.sleep(1)
            continue

        game(current_round, state)

        state.task_manager.task_list = []
        # reset player to default attr
        for id, (conn, file, player) in enumerate(state.players):
            new_player = Player(state.task_manager, state.bomb_factory,
                                player.pos, player.name, player.character_id)
            new_player.points = player.points
            state.players[id] = (conn, file, new_player)

        if current_round >= get_max_round(len(state.players)):
            break

        current_round += 1

    broadcast(state.players, f"ranking$|$\n".encode())


def event_loop(state: State):
    """
    Pygame window
    """

    pygame.init()
    window = pygame.display.set_mode((500, 200))
    pygame.display.set_caption("BomberPy - Host")
    clock = pygame.time.Clock()

    start_btn = Button(None, (window.get_width()//2, 20),
                       " Start ", font(30), "#d7fcd4", "White")

    threading.Thread(target=play, args=(state,), daemon=True).start()

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

        offset = start_btn.rect.bottom + 20
        for player_socket, _, player in state.players:
            is_connected = "Disconnected" if player_socket is None else "Connected"
            player_name = text(
                15, f'{player.name} - {is_connected}', True, "#d7fcd4")
            window.blit(player_name, (0, offset))
            offset += player_name.get_height()

        if state.start:
            # game status
            game_start = text(20, 'Game started', True, "#d7fcd4")
            game_start_rect = game_start.get_rect(
                center=(window.get_width()//2, 30))
            window.blit(game_start, game_start_rect)
        else:
            start_btn.update(window, mouse_position)

        # update
        state.task_manager.tick()
        pygame.display.update()
        clock.tick(FPS)


def main():
    host = '0.0.0.0'
    try:
        port = int(sys.argv[1])
    except IndexError:
        port = 8888

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
