import sys
import pygame

LOGICAL_W, LOGICAL_H = 320, 170
SCALE = 3

pygame.init()
window = pygame.display.set_mode((LOGICAL_W * SCALE, LOGICAL_H * SCALE))
canvas = pygame.Surface((LOGICAL_W, LOGICAL_H))
pygame.display.set_caption("Z-Pet (PC Preview)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 16, bold=True)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    canvas.fill((28, 22, 42))
    pygame.draw.rect(canvas, (175, 130, 255), (10, 10, 300, 150), 2)
    text = font.render("Z-PET READY (320x170)", True, (240, 235, 255))
    canvas.blit(text, (56, 76))

    pygame.transform.scale(canvas, window.get_size(), window)
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()