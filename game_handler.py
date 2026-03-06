import pygame
import Nave

player_shots = []


#
def load_backgrounds():

    main_img = pygame.image.load('./img/main.png').convert()
    main_img = pygame.transform.scale(main_img, (700,900))

    radar_img = pygame.image.load('./img/radar.jpg').convert()
    radar_img = pygame.transform.scale(radar_img, (700,900))

    return main_img, radar_img

#
def create_ships():

    portaerei = Nave.Nave("portaerei", "./img/portaAerei.png", 5)
    corazzata = Nave.Nave("corazzata", "./img/corazzata.png", 4)
    incrociatore1 = Nave.Nave("incrociatore1", "./img/incrociatore.png", 3)
    incrociatore2 = Nave.Nave("incrociatore2", "./img/incrociatore.png", 3)
    cacciatorpediniere = Nave.Nave("cacciatorpediniere", "./img/cacciatorpediniere.png", 2)

    ships = [
        portaerei,
        corazzata,
        incrociatore1,
        incrociatore2,
        cacciatorpediniere
    ]

    return ships

#
def draw_ships(screen, ships, start_x=50, start_y=700, spacing=100):

    for i, ship in enumerate(ships):

        x = start_x + i * spacing
        y = start_y

        ship.draw_nave(screen, x, y)

def handle_placement(event, ships, my_grid, ships_placed, confirmed, button_rect):
    if event.type == pygame.MOUSEBUTTONDOWN:
            if ships_placed == 5 and button_rect.collidepoint(event.pos):
                confirmed = True
        
                print("Posizionamento confermato!")

        # Gestione navi solo se non confermato
    if not confirmed:
        for ship in ships:
            if not ship.placed:
                if ship.handle_event(event):
                    if my_grid.place_ship(ship, 90, 170):
                        ships_placed += 1
    return "PLAYER_TURN"

def handle_player_turn(event, enemy_grid, player_shots, max_shots):

    if event.type == pygame.MOUSEBUTTONDOWN:

        pos = enemy_grid.get_pos_OnClick(
            event.pos[0],
            event.pos[1],
            790,
            170
        )

        if pos is not None:

            if len(player_shots) < max_shots:

                x, y = pos

                if (x, y) not in player_shots:

                    player_shots.append((x, y))

                    print("Colpo registrato:", x, y)
                    print("Colpi:", len(player_shots), "/", max_shots)

            if len(player_shots) == max_shots:
                return "EVALUATION"

    return "PLAYER_TURN"

def handle_evaluation(enemy_grid, player_shots):

    while player_shots:

        x, y = player_shots.pop(0)

        cell = enemy_grid.grid_matrix[x][y]

        # nave colpita
        if cell != -1 and cell != -2:

            ship = cell

            result = ship.take_hit()

            enemy_grid.grid_matrix[x][y] = 1

            print("COLPITO")

            if result == "affondata":
                print("Nave affondata!")

        # acqua
        elif cell == -1:

            enemy_grid.grid_matrix[x][y] = -2

            print("ACQUA")

    return "ENEMY_TURN"


def handle_enemy_turn():
    return None

def calcola_colpi_disponibili(ships):

    totale = 0

    for ship in ships:
        if not ship.affondata:
            totale += ship.hp

    return totale