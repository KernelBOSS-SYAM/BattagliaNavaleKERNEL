import pygame
#COSTANTI
CELL_SIZE = 30
WIDTH = 13 * CELL_SIZE
HEIGHT = 13 * CELL_SIZE


# Inizializzazione
pygame.init()
screen = pygame.display.set_mode((1500, 800))

# 1. Caricare l'immagine di sfondo
img_sfondo = pygame.image.load('./img/main.png').convert()
img_sfondo = pygame.transform.scale(img_sfondo,(500,700))
screen.blit(img_sfondo, (0, 0))
grid = [[-1 for _ in range(13)] for _ in range(13)]
pygame.display.set_caption("Battaglia Navale")
print(grid)



def draw_grid():
    for row in range(13):
        for col in range(13):
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (0, 0, 255), rect, 1)  # bordo blu

draw_grid()
imgC = pygame.image.load('./img/Corazzata.png')
imgC = pygame.transform.scale(imgC, (150, 150))

rectC = pygame.Rect(30, 30, 100, 100)
rectC.bottomleft = (30, 200)
screen.blit(imgC, rectC)




# Game loop
running = True
while running:

    


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            col = x // CELL_SIZE
            row = y // CELL_SIZE
            
            print("Cella:", row, col)
        


    # Aggiornare lo schermo
    pygame.display.flip()

pygame.quit()