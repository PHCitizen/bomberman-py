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


class State:
    def __init__(self):
        self.matrix = None
        self.players: list[Player] = []
        self.player_index = -1

        self.socket = None
        self.file: socket.SocketIO = None

        self.state = GameState.WAITING_PHASE
        self.round = 1
        self.countdown = 5


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
            data = data.split(b":", 1)[1]
            try:
                data = zlib.decompress(data)
                state.matrix = np.frombuffer(
                    data, dtype=np.uint8).reshape(MATRIX.shape)
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
    player_name = InputBox(185, 45, 250, 25, 15,
                           f"Player {state.player_index}")

    select_text = text(15, 'Choose your character', True, "#d7fcd4")
    select_text_rect = select_text.get_rect(
        center=(window.get_width()//2, player_name.rect.bottom + 30))

    def sumbit_name(name):
        pygame.display.set_caption(f"BomberPy - {name}")
        state.file.write(f"name:{name}\n".encode())

    selected_character = 1
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
                        if selected_character < CHARACTER_LENGTH:
                            selected_character += 1
                    elif back_btn.checkForInput(mouse_position):
                        if selected_character > 1:
                            selected_character -= 1
                    state.file.write(
                        f"character:{selected_character}\n".encode())
                except Exception as e:
                    pass

            if len(player_name.text) > 15 and event.type == pygame.KEYDOWN and event.key != pygame.K_BACKSPACE:
                continue
            player_name.handle_event(event, sumbit_name)

        window.blit(waiting_text, waiting_text_rect)
        window.blit(pname_text, (20, 50))
        player_name.draw(window)
        window.blit(select_text, select_text_rect)

        character = PlayerSprite(selected_character).get()
        character = pygame.transform.scale(character, (40, 40))
        character_rect = character.get_rect(
            top=select_text_rect.bottom + 10, left=50)
        window.blit(character, character_rect)

        if selected_character < CHARACTER_LENGTH:
            next_btn = Button(None, (character_rect.right + 10, character_rect.centery),
                              ">", font(20), "#d7fcd4", "White")
            next_btn.update(window, mouse_position)
        if selected_character > 1:
            back_btn = Button(None, (character_rect.left - 10, character_rect.centery),
                              "<", font(20), "#d7fcd4", "White")
            back_btn.update(window, mouse_position)

        pygame.display.update()
        clock.tick(FPS)


def game_phase(state: State):
    bgmusic().play(-1)

    clock = pygame.time.Clock()
    game_obj = Game(state.socket, state.file)
    stats_window = pygame.Surface((GAME_WIDTH, CELL_SIZE * 2))
    window = pygame.display.set_mode(
        (GAME_WIDTH, game_obj.surface.get_height() + stats_window.get_height()))

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

        countdown = text(20, f"{state.countdown}s", True, "#ff0000")
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
        if state.state != GameState.RANKING_PHASE:
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

        countdown = text(
            15, f"Round {state.round} will start in {state.countdown}", True, "#d7fcd4")
        countdown_rect = countdown.get_rect(center=(window.get_width()//2, 10))
        window.blit(countdown, countdown_rect)

        ranked_players = sorted(
            state.players, key=lambda x: x.points, reverse=True)
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


def main():
    pygame.init()

    try:
        host = sys.argv[1]
    except IndexError:
        host = "localhost"

    try:
        port = int(sys.argv[2])
    except IndexError:
        port = 8888

    state = State()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
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
    while True:
        if state.state == GameState.WAITING_PHASE:
            waiting_phase(state)
        elif state.state == GameState.RANKING_PHASE:
            ranking_phase(state, True)
        elif state.state == GameState.GAME_PHASE:
            game_phase(state)
        elif state.state == GameState.WINNER_PHASE:
            ranking_phase(state, False)


if __name__ == "__main__":
    main()
