import pygame
import Grid
import Nave

pygame.init()

green = (0,255,0) 
blue = (59,68,255)
cell_dimension = 40
Ncell = 13


screen = pygame.display.set_mode((1400,900))

# sfondi
main_img = pygame.image.load('./img/main.png').convert()
main_img = pygame.transform.scale(main_img, (700,900))

radar_img = pygame.image.load('./img/radar.jpg').convert()
radar_img = pygame.transform.scale(radar_img, (700,900))


# griglie
my_grid = Grid.Grid(cell_dimension,Ncell,Ncell,blue)
enemy_grid = Grid.Grid(cell_dimension,Ncell,Ncell,green)


# navi

portaerei = Nave.Nave("portaerei", "./img/portaAerei.png", 5)
corazzata = Nave.Nave("corazzata", "./img/corazzata.png", 4)
incrociatore1 = Nave.Nave("incrociatore1", "./img/incrociatore.png", 3)
incrociatore2 = Nave.Nave("incrociatore2", "./img/incrociatore.png", 3)
cacciatorpediniere = Nave.Nave("cacciatorpediniere", "./img/cacciatorpediniere.png", 2)


running = True

while running:

    screen.blit(main_img, (0,0))
    screen.blit(radar_img, (700,0))

    my_grid.draw_grid(screen, offset_x=90, offset_y=170)
    enemy_grid.draw_grid(screen, offset_x=790, offset_y=170)


    # disegno navi
    portaerei.draw_nave(screen, 50, 670)
    corazzata.draw_nave(screen, 150, 700)
    incrociatore1.draw_nave(screen, 250, 700)
    incrociatore2.draw_nave(screen, 350, 700)
    cacciatorpediniere.draw_nave(screen, 450, 700)


    for event in pygame.event.get():
        pygame.display.flip()

        if event.type == pygame.QUIT:
            running = False


        # gestione eventi navi
            if portaerei.handle_event(event):
                my_grid.place_ship(portaerei, 90, 170)

            if corazzata.handle_event(event):
                my_grid.place_ship(corazzata, 90, 170)


            if incrociatore1.handle_event(event):
                my_grid.place_ship(incrociatore1, 90, 170)

            if incrociatore2.handle_event(event):
                my_grid.place_ship(incrociatore2, 90, 170)              

            if cacciatorpediniere.handle_event(event):
                my_grid.place_ship(cacciatorpediniere, 90, 170)
                print(my_grid.grid_matrix)

pygame.quit()

  
