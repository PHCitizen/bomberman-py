import pygame
from assets import *
from settings import *


class Button:
    def __init__(self, image, pos, text_input, font, base_color, hovering_color):
        self.image = image
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.font = font
        self.padding = 5
        self.border = False

        self.base_color, self.hovering_color = base_color, hovering_color
        self.text_input = text_input
        self.text = self.font.render(self.text_input, True, self.base_color)
        if self.image is None:
            self.image = self.text
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

    def update(self, screen, position):
        self.changeColor(position)
        if self.image is not None:
            screen.blit(self.image, self.rect)

        if self.border:
            a, b, c, d = self.text_rect
            pad, pad2 = self.padding, self.padding * 2
            pos = (a-pad, b-pad, c+pad2, d+pad2)
            pygame.draw.rect(screen, "#d7fcd4", pos, 2)
        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            return True
        return False

    def changeColor(self, position):
        if position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom):
            self.text = self.font.render(
                self.text_input, True, self.hovering_color)
        else:
            self.text = self.font.render(
                self.text_input, True, self.base_color)


class InputBox:
    def __init__(self, x, y, w, h, font_size=15, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = C_INACTIVE
        self.text = text
        self.font_size = font_size
        self.txt_surface = font(font_size).render(text, True, self.color)
        self.active = False

    def handle_event(self, event, callback):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = C_ACTIVE if self.active else C_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                    self.color = C_INACTIVE
                    callback(self.text)
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = font(self.font_size).render(
                    self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pygame.draw.rect(screen, self.color, self.rect, 2)
