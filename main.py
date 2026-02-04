import pygame

# Inizializzazione
pygame.init()
screen = pygame.display.set_mode((900, 600))

# 1. Caricare l'immagine di sfondo
auto = pygame.image.load('image/main.png').convert()
auto = pygame.transform.scale(auto,(450,600))

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 2. Disegnare lo sfondo (alle coordinate 0,0)
    screen.blit(auto, (0, 0))

    # Aggiornare lo schermo
    pygame.display.flip()

pygame.quit()