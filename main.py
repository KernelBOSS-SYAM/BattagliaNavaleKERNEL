import pygame
import Grid

pygame.init()

screen = pygame.display.set_mode((1400, 800))

#Sfondo griglia giocatore
main = pygame.image.load('./img/main.png').convert()
main = pygame.transform.scale(main, (700, 800))

#Sfondo gliglia avversario
radar = pygame.image.load('./img/radar.jpg').convert()
radar = pygame.transform.scale(radar, (700, 800))

#creo la griglia
my_grid = Grid.Grid()
enemy_grid = Grid.Grid()




runnig = True
while runnig:
    for event in pygame.event.get():

        pygame.display.flip()
        screen.blit(main, (0, 0))
        screen.blit(radar, (700, 0))
        my_grid.draw_grid(screen, (0,0,255), offset_x = 155, offset_y = 100)
        enemy_grid.draw_grid(screen, (0, 255, 0), offset_x = 855, offset_y = 100)




        if event.type == pygame.QUIT:
            runnig = False
