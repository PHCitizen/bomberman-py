import pygame

pygame.init()
win = pygame.display.set_mode((300, 300))

for index in range(1, 11):
    surface = pygame.Surface((128, 128), pygame.SRCALPHA)
    image = pygame.image.load(
        f"./others/10chars/spritesheets/{index} walk.png")
    image = pygame.transform.scale2x(image)
    flip = pygame.transform.flip(image, True, False)

    for y in range(4):
        for x in range(4):
            if y == 3:
                surface.blit(flip, (x * 32, y * 32),
                             (0, x * 32, 32, 32))
            else:
                surface.blit(image, (x * 32, y * 32),
                             (y * 32, x * 32, 32, 32))

    pygame.image.save(surface, f"./graphics/characters/{index}.png")


# while True:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             exit()

#     win.blit(surface, (0, 0))
#     pygame.display.update()
