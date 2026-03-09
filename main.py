import pygame
import Grid
import Nave
import game_handler as gh

pygame.init()

green = (0,255,0) 
blue = (59,68,255)
cell_dimension = 40
Ncell = 13
game_state = "PLACEMENT"

ships_placed = 0
confirmed = False

screen = pygame.display.set_mode((1400,900))

#BACKGROUND LOADING
main_img, radar_img = gh.load_backgrounds()

#GRID CREATION
my_grid = Grid.Grid(40,13,13,(59,68,255))
enemy_grid = Grid.Grid(40,13,13,(0,255,0))

#SHIP LOADING 
ships = gh.create_ships()
portaerei = ships[0]
corazzata = ships[1]
incrociatore1 = ships[2]
incrociatore2 = ships[3]
cacciatorpediniere = ships[4]

#BUTTON LOCK SHIP
button_rect = pygame.Rect(1100, 800, 200, 60)
button_color = (0, 200, 0)
font = pygame.font.SysFont(None, 40)

running = True

while running:

    #DRAW BACKGROUND AND GRIDS
    screen.blit(main_img, (0,0))
    screen.blit(radar_img, (700,0))
    my_grid.draw_grid(screen, offset_x=90, offset_y=170)
    enemy_grid.draw_grid(screen, offset_x=790, offset_y=170)

    #DRAW SHIPS
    gh.draw_ships(screen, ships)
    
    # Pulsante CONFERMA
    if ships_placed == 5 and not confirmed:
        pygame.draw.rect(screen, button_color, button_rect)
        text = font.render("CONFERMA", True, (255,255,255))
        screen.blit(text, (button_rect.x + 25, button_rect.y + 15))


    for event in pygame.event.get():
        pygame.display.flip()

        if event.type == pygame.QUIT:
            running = False

        if game_state == "PLACEMENT":
            game_state = gh.handle_placement(event, ships, my_grid, ships_placed, confirmed, button_rect)

        #elif game_state == "PLAYER_TURN":
            #max_shots = gh.calcola_colpi_disponibili(ships)
            #game_state = gh.handle_player_turn(event, enemy_grid, max_shots)

        #elif game_state == "ENEMY_TURN":
            #game_state = gh.handle_enemy_turn()

        #elif game_state == "VALUTAZIONE_FASE":
            #game_state = gh.handle_evaluation(enemy_grid)

        # Click sul bottone
        

        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     if ships_placed == 5 and confirmed:
        #         coordinates = enemy_grid.get_pos_OnClick(event.pos[0], event.pos[1], 790, 170)
        #         if coordinates is not None:
        #             enemy_grid.spara(coordinates[0], coordinates[1])

pygame.quit()
