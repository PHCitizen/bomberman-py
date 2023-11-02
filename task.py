import pygame


class Task:
    def __init__(self):
        self.task_list = []

    def add(self, amount, cb):
        current = pygame.time.get_ticks()
        self.task_list.append((current + amount, cb))

    def tick(self):
        current = pygame.time.get_ticks()
        for i, task in enumerate(self.task_list):
            if current >= task[0]:
                task[1]()
                del self.task_list[i]
