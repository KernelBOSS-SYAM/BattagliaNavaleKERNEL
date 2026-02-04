import pygame
# Inizializzazione
pygame.init()
screen = pygame.display.set_mode((900, 600))

# 1. Caricare l'immagine di sfondo
auto = pygame.image.load('./img/main.png').convert()
auto = pygame.transform.scale(auto,(450,600))

grid = [[-1 for _ in range(13)] for _ in range(13)]
print(grid)

CELL_SIZE = 30
ROWS = 13
COLS = 13

WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE

def draw_grid():
    for row in range(ROWS):
        for col in range(COLS):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (0, 0, 255), rect, 1)  # bordo blu

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    screen.blit(auto, (0, 0))
    draw_grid()


    # Aggiornare lo schermo
    pygame.display.flip()

pygame.quit()