import pygame
import Grid
import Nave


pygame.init()

screen = pygame.display.set_mode((1400, 900))

#Sfondo griglia giocatore
main = pygame.image.load('./img/main.png').convert()
main = pygame.transform.scale(main, (700, 900))

#Sfondo gliglia avversario
radar = pygame.image.load('./img/radar.jpg').convert()
radar = pygame.transform.scale(radar, (700, 900))

#creo la griglia
my_grid = Grid.Grid(40, 13, 13)
enemy_grid = Grid.Grid(40, 13, 13)

# Inserimento navi
corazzata = Nave.Nave("corazzata", "./img/corazzata.png", 4)
incrociatore = Nave.Nave("incrociatore", "./img/incrociatore.png", 4)
cacciatorpediniere = Nave.Nave("cacciatorpediniere", "./img/cacciatorpediniere.png", 4)
portaerei = Nave.Nave("portaerei", "./img/portaAerei.png", 4)

runnig = True
while runnig:
    for event in pygame.event.get():

        pygame.display.flip()
        screen.blit(main, (0, 0))
        screen.blit(radar, (700, 0))
        my_grid.draw_grid(screen, (0,0,255), offset_x = 90, offset_y = 170)
        enemy_grid.draw_grid(screen, (0, 255, 0), offset_x = 790, offset_y = 170)
        
        portaerei.draw_nave(screen, offset_x = 50, offset_y = 700)
        corazzata.draw_nave(screen, offset_x = 150, offset_y = 700)
        incrociatore.draw_nave(screen, offset_x = 250, offset_y = 700)
        incrociatore.draw_nave(screen, offset_x = 350, offset_y = 700)
        cacciatorpediniere.draw_nave(screen, offset_x = 450, offset_y = 700)


        if event.type == pygame.QUIT:
            runnig = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            print(my_grid.get_pos_OnClick(event.pos[0], event.pos[1], offset_x = 90, offset_y = 170))

  
