import pygame
import pickle
import socket
import threading
import zlib
import os
import sys

from player import *
from settings import *
from game import Game
from assets import *
from button import *
from task import Task


class State:
    def __init__(self):
        self.matrix = None
        self.players: list[Player] = []
        self.player_index = -1

        self.socket = None
        self.file: socket.SocketIO = None

        self.state = GameState.HOME_SCREEN
        self.round = 1
        self.countdown = 5

        self.character = 1
        self.name = lambda: f"Player {self.player_index}"

        self.task_manager = Task()


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

        if buffer.startswith(b"pdata:"):
            data = buffer.removesuffix(b"$|$\n")
            data = data.split(b":", 1)[1]
            state.players = pickle.loads(data)
        elif buffer.startswith(b"matrix:"):
            data = buffer.removesuffix(b"$|$\n")
            _, y, x, data = data.split(b":", 3)
            shape = int(y.decode()), int(x.decode())
            try:
                data = zlib.decompress(data)
                state.matrix = np.frombuffer(
                    data, dtype=np.uint8).reshape(shape)
            except zlib.error as e:
                print(buffer, e)
        elif buffer == b"explosion$|$\n":
            explosion_sound().play(0)
        elif buffer == b"ghost$|$\n":
            ghost_sound().play(0)
        elif buffer.startswith(b"round:"):
            game_round = buffer.removesuffix(b"$|$\n").split(b":")[1].decode()
            state.state = GameState.RANKING_PHASE
            state.round = game_round
        elif buffer.startswith(b"countdown:"):
            countdown = buffer.removesuffix(b"$|$\n").split(b":")[1].decode()
            state.countdown = countdown
        elif buffer == b"go$|$\n":
            state.state = GameState.GAME_PHASE
        elif buffer == b"ranking$|$\n":
            state.state = GameState.WINNER_PHASE
        else:
            print("Unknown message", buffer)

        buffer = b""


def waiting_phase(state: State):
    window = pygame.display.set_mode((500, 200))
    clock = pygame.time.Clock()

    waiting_text = text(15, 'Waiting for host to start...', True, "#d7fcd4")
    waiting_text_rect = waiting_text.get_rect(
        center=(window.get_width()//2, 10))

    pname_text = text(15, 'Enter name:', True, "#d7fcd4")
    player_name = InputBox(185, 45, 250, 25, 15, state.name())

    select_text = text(15, 'Choose your character', True, "#d7fcd4")
    select_text_rect = select_text.get_rect(
        center=(window.get_width()//2, player_name.rect.bottom + 30))

    tutorial_text = text(10, "Press 'h' for help", True, "#d7fcd4")
    tutorial_text_rect = tutorial_text.get_rect(
        bottom=window.get_height() - 5, right=window.get_width())

    def sumbit_name(name):
        state.name = lambda: name
        pygame.display.set_caption(f"BomberPy - {name}")
        state.file.write(f"name:{name}\n".encode())

    while True:
        mouse_position = pygame.mouse.get_pos()
        window.blit(get_background(), (0, 0))

        if state.state != GameState.WAITING_PHASE:
            break

        # Main screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                try:
                    if next_btn.checkForInput(mouse_position):
                        if state.character < CHARACTER_LENGTH:
                            state.character += 1
                    elif back_btn.checkForInput(mouse_position):
                        if state.character > 1:
                            state.character -= 1
                    state.file.write(f"character:{state.character}\n".encode())
                except Exception as e:
                    pass
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_h and not player_name.active:
                state.prevstate = state.state
                state.state = GameState.TUTORIAL

            if len(player_name.text) > 15 and event.type == pygame.KEYDOWN and event.key != pygame.K_BACKSPACE:
                continue
            player_name.handle_event(event, sumbit_name)

        window.blit(waiting_text, waiting_text_rect)
        window.blit(pname_text, (20, 50))
        player_name.draw(window)
        window.blit(select_text, select_text_rect)

        character = PlayerSprite(state.character).get()
        character = pygame.transform.scale(character, (40, 40))
        character_rect = character.get_rect(
            top=select_text_rect.bottom + 10, left=50)
        window.blit(character, character_rect)
        window.blit(tutorial_text, tutorial_text_rect)

        if state.character < CHARACTER_LENGTH:
            next_btn = Button(None, (character_rect.right + 10, character_rect.centery),
                              ">", font(20), "#d7fcd4", "White")
            next_btn.update(window, mouse_position)
        if state.character > 1:
            back_btn = Button(None, (character_rect.left - 10, character_rect.centery),
                              "<", font(20), "#d7fcd4", "White")
            back_btn.update(window, mouse_position)

        pygame.display.update()
        clock.tick(FPS)


def game_phase(state: State):
    bgmusic().play(-1)

    clock = pygame.time.Clock()
    game_obj = Game(state.socket, state.file, state.matrix.shape)
    height, width = get_height_width(state.matrix.shape)
    stats_window = pygame.Surface((width, CELL_SIZE * 2))
    window = pygame.display.set_mode(
        (width, height + stats_window.get_height()))

    while True:
        if state.state != GameState.GAME_PHASE:
            break

        current_player = state.players[state.player_index]

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
            stats_window.blit(heart_sprites(), (i * CELL_SIZE, CELL_SIZE))

        countdown = text(20, f"{state.countdown}s", True, C_INACTIVE)
        countdown_rect = countdown.get_rect(
            top=0, right=stats_window.get_width())
        stats_window.blit(countdown, countdown_rect)

        pts_text = font(20).render(
            f"{current_player.points}pts", True, color=C_INACTIVE)
        pts_rect = pts_text.get_rect(
            top=countdown_rect.height, right=stats_window.get_width())
        stats_window.blit(pts_text, pts_rect)

        window.blit(stats_window, (0, 0))
        game_obj.update(state.players, state.matrix)
        window.blit(game_obj.surface, (0, stats_window.get_height()))

        pygame.display.update()
        clock.tick(FPS)

    bgmusic().stop()


def ranking_phase(state: State, with_coutdown):
    bgmusic().stop()

    window = pygame.display.set_mode((500, 200))
    clock = pygame.time.Clock()
    exit_btn = Button(None, (250, 100),
                      " Exit ", font(20), "#d7fcd4", "White")

    run = True
    while run:
        if state.state not in [GameState.RANKING_PHASE, GameState.WINNER_PHASE]:
            break

        mouse_position = pygame.mouse.get_pos()
        window.blit(get_background(), (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if exit_btn.checkForInput(mouse_position):
                    run = False

        ranked_players = sorted(
            state.players, key=lambda x: x.points, reverse=True)

        msg = f"Round {state.round} will start in {state.countdown}" if with_coutdown else f"{ranked_players[0].name} wins!!!"
        countdown = text(15, msg, True, "#d7fcd4")
        countdown_rect = countdown.get_rect(center=(window.get_width()//2, 10))
        window.blit(countdown, countdown_rect)

        if len(ranked_players) > 0:
            curr_rank = text(15, f"-- Player Ranks --", True, "#d7fcd4")
            curr_rank_rect = curr_rank.get_rect(
                center=(window.get_width()//2, countdown_rect.bottom + 50))
            window.blit(curr_rank, curr_rank_rect)

            offset = curr_rank_rect.bottom + 10
            for ranked_player in ranked_players:
                ranking = text(
                    15, f"{ranked_player.name} - {ranked_player.points} pts", True, "#d7fcd4")
                rect = ranking.get_rect(center=(window.get_width()//2, offset))
                window.blit(ranking, rect)
                offset += rect.height + 10

        # window.blit(winner, (0, 50))
        # exit_btn.update(window, mouse_position)

        pygame.display.update()
        clock.tick(FPS)


def tutorial(state):
    help_msgs = f"""
Point System:
    * Clear Box +{PTS_BOX}pts
    * Kill opponent +{PTS_KILL}pts
    * Suicide {PTS_SUICIDE}pts
Note:
    * Whoever has the highest score will 
        be the winner
    * Each round has a maximum of 3 minutes
    * After each round, life will be 
        converted to pts. 1 life = {LIFE_PTS_CONVERTION} pts
    """

    window = pygame.display.set_mode((650, 650))
    clock = pygame.time.Clock()

    exit_text = text(10, "Press 'esc' to exit", True, "#d7fcd4")
    exit_text_rect = exit_text.get_rect(
        bottom=window.get_height() - 5, right=window.get_width())

    run = True
    while run:
        window.blit(get_background(), (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                state.state = state.prevstate
                run = False

        texts = text(20, "Tutorial", True, "#d7fcd4")
        rect = texts.get_rect(centerx=window.get_width()//2, top=10)
        window.blit(texts, rect)

        # ================
        # Arrow
        # ================
        img = pygame.transform.scale(kbd_arrow(), (100, 60))
        img_rect = img.get_rect(left=0, top=rect.bottom + 20)
        window.blit(img, img_rect)
        texts = text(15, "Move the player", True, "#d7fcd4")
        rect = texts.get_rect(
            left=img_rect.right + 10, centery=img_rect.centery)
        window.blit(texts, rect)

        # ================
        # Space
        # ================

        img = pygame.transform.scale(kbd_space(), (100, 40))
        img_rect = img.get_rect(left=0, top=img_rect.bottom)
        window.blit(img, img_rect)
        texts = text(15, "Place the bomb", True, "#d7fcd4")
        rect = texts.get_rect(
            left=img_rect.right + 10, centery=img_rect.centery)
        window.blit(texts, rect)

        # ================
        # Power up
        # ================
        texts = text(15, "Power Ups:", True, "#d7fcd4")
        rect = texts.get_rect(left=0, top=img_rect.bottom + 30)
        window.blit(texts, rect)

        msg = [(heart_sprites(), "Increase life"),
               (bomb_add_sprite(), "Increase bomb capacity"),
               (movement_speed_sprite(), "Increase movement speed"),
               (expl_range_add_sprite(), "Increase explosion range")]
        for sprite, message in msg:
            img = pygame.transform.scale(sprite, (30, 30))
            img_rect = img.get_rect(left=30, top=rect.bottom + 10)
            window.blit(img, img_rect)
            texts = text(15, message, True, "#d7fcd4")
            rect = texts.get_rect(
                left=img_rect.right + 10, centery=img_rect.centery)
            window.blit(texts, rect)

        # ================
        # Curse
        # ================
        texts = text(15, "Curse:", True, "#d7fcd4")
        rect = texts.get_rect(left=0, top=img_rect.bottom + 10)
        window.blit(texts, rect)

        # ================
        # Skull
        # ================
        img = pygame.transform.scale(skull_sprite(), (30, 30))
        img_rect = img.get_rect(left=30, top=rect.bottom + 10)
        window.blit(img, img_rect)
        texts = text(15, "Decrease life without dying",
                     True, "#d7fcd4", )
        rect = texts.get_rect(
            left=img_rect.right + 10, centery=img_rect.centery)
        window.blit(texts, rect)

        # ================
        # Note
        # ================
        for msg in help_msgs.split("\n"):
            texts = text(15, msg, True, "#d7fcd4")
            rect = texts.get_rect(left=0, top=rect.bottom + 5)
            window.blit(texts, rect)

        # exit text
        window.blit(exit_text, exit_text_rect)

        pygame.display.update()
        clock.tick(FPS)


def home_screen(state: State):
    window = pygame.display.set_mode((350, 200))

    clock = pygame.time.Clock()

    bomberman_text = text(30, 'Bomberman', True, "#d7fcd4")
    waiting_text_rect = bomberman_text.get_rect(
        center=(window.get_width()//2, 20))

    host_text_pos = (10, waiting_text_rect.bottom + 30)
    host_text = text(15, 'Host: ', True, "#d7fcd4")
    host_input = InputBox(host_text.get_width(),
                          host_text_pos[1] - 5, 250, 25, 15, "localhost")

    port_text_pos = (10, host_text_pos[1] + 30)
    port_text = text(15, 'Port: ', True, "#d7fcd4")
    port_input = InputBox(port_text.get_width(),
                          port_text_pos[1] - 5, 250, 25, 15, "8888")

    connect_btn = Button(None, (window.get_width()//2, window.get_height() - 40),
                         " Connect ", font(20), "#d7fcd4", "White")
    connect_btn.border = True

    data = {
        "msg": None,
        "host": "localhost",
        "port": 8888
    }

    def connect():
        data["msg"] = "Failed to server"
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((data["host"], data["port"]))
            client_file = socket.SocketIO(client_socket, "rwb")

            state.file = client_file
            state.socket = client_socket
        except Exception as e:
            data["msg"] = "Failed to connect to server"

            def reset_msg():
                data["msg"] = None
            state.task_manager.add(3000, reset_msg)
            return

        # the server will sent the player index once we connect
        player_index = client_file.readline().rstrip()
        player_index = int.from_bytes(player_index, "big")
        state.player_index = player_index
        pygame.display.set_caption(f"BomberPy - Player {player_index}")

        threading.Thread(target=socket_thread, args=(
            state,), daemon=True).start()
        state.state = GameState.WAITING_PHASE

    def set_host(x):
        data["host"] = x

    def set_port(x):
        data["port"] = int(x)

    need_connect = False

    while True:
        mouse_position = pygame.mouse.get_pos()
        window.blit(get_background(), (0, 0))

        if state.state != GameState.HOME_SCREEN:
            break

        # Main screen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if connect_btn.checkForInput(mouse_position):
                    # force update message
                    # connecting to server is blocking the thread
                    # thats why we need to put it in end, so we can output msg
                    data["msg"] = "Connecting..."
                    need_connect = True

            host_input.handle_event(event, set_host)
            port_input.handle_event(event, set_port)

        window.blit(bomberman_text, waiting_text_rect)

        window.blit(host_text, host_text_pos)
        host_input.draw(window)

        window.blit(port_text, port_text_pos)
        port_input.draw(window)

        connect_btn.update(window, mouse_position)

        if data["msg"]:
            message = text(10, data["msg"], True, "#d7fcd4")
            message_rect = message.get_rect(bottomright=(
                window.get_width(), window.get_height()))
            window.blit(message, message_rect)

        pygame.display.update()
        state.task_manager.tick()
        clock.tick(FPS)

        if need_connect:
            connect()
            need_connect = False


def main():
    pygame.init()

    state = State()

    # start the app
    while True:
        if state.state == GameState.HOME_SCREEN:
            home_screen(state)
        elif state.state == GameState.WAITING_PHASE:
            waiting_phase(state)
        elif state.state == GameState.RANKING_PHASE:
            ranking_phase(state, True)
        elif state.state == GameState.GAME_PHASE:
            game_phase(state)
        elif state.state == GameState.WINNER_PHASE:
            ranking_phase(state, False)
        elif state.state == GameState.TUTORIAL:
            tutorial(state)


if __name__ == "__main__":
    main()
