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
my_grid = Grid.Grid(40, 13, 13, (59, 68, 255))
enemy_grid = Grid.Grid(40, 13, 13, (0,255,0))

# Inserimento navi
corazzata = Nave.Nave("corazzata", "./img/corazzata.png", 4)
incrociatore1 = Nave.Nave("incrociatore1", "./img/incrociatore.png", 4)
incrociatore2 = Nave.Nave("incrociatore2", "./img/incrociatore.png", 4)
cacciatorpediniere = Nave.Nave("cacciatorpediniere", "./img/cacciatorpediniere.png", 4)
portaerei = Nave.Nave("portaerei", "./img/portaAerei.png", 4)

runnig = True
while runnig:
    for event in pygame.event.get():
        pygame.display.flip()
        
        screen.blit(main, (0, 0))
        screen.blit(radar, (700, 0))
        my_grid.draw_grid(screen, offset_x = 90, offset_y = 170)
        enemy_grid.draw_grid(screen, offset_x = 790, offset_y = 170)
        
        portaerei.draw_nave(screen, pos_x = 50, pos_y = 670)
        corazzata.draw_nave(screen, pos_x = 150, pos_y = 700)
        incrociatore1.draw_nave(screen, pos_x = 250, pos_y = 700)
        incrociatore2.draw_nave(screen, pos_x = 350, pos_y = 700)
        cacciatorpediniere.draw_nave(screen, pos_x = 450, pos_y = 700)

        corazzata.handle_event(event)
        incrociatore1.handle_event(event)
        incrociatore2.handle_event(event)
        cacciatorpediniere.handle_event(event)
        portaerei.handle_event(event)

        if event.type == pygame.QUIT:
            runnig = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = my_grid.get_pos_OnClick(event.pos[0], event.pos[1], offset_x = 90, offset_y = 170)
            if pos is not None:
                print(f"Cliccato sulla cella: {pos}")

  
