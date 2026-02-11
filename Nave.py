from cmath import rect
import pygame
import Grid

my_grid = Grid.Grid(40, 13, 13)
GRID_OFFSET_X = 90
GRID_OFFSET_Y = 170

class Nave:
    nome = "Nave"
    dimesione = 0
    path_img = ""

    def __init__(self, nome, path_img, dimensione=2):
        self.nome = nome
        self.path_img = path_img
        self.dimesione = dimensione
        self.dragging = False
        self.rect = None
        self.rotation = 0

    def draw_nave(self, screen, offset_x, offset_y, rotation = 0):
        global img
        img = pygame.image.load(self.path_img).convert_alpha()
        img = pygame.transform.rotate(img, self.rotation)

        if self.rect is None:
            self.rect = img.get_rect(topleft=(offset_x, offset_y))
        else:
            center = self.rect.center
            self.rect = img.get_rect(center=center)

        screen.blit(img, self.rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if event.button == 1: # Tasto sinistro
                    self.dragging = True

                elif event.button == 4: #Scorrimento in alto
                    self.rotation = min(self.rotation + 90, 0)
                elif event.button == 5: #Scorrimento in basso
                    self.rotation = max(self.rotation - 90, - 90)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False

            cell_pos = None

            if my_grid is not None:
                mouse_x, mouse_y = event.pos

                cell_pos = my_grid.get_pos_OnClick(
                mouse_x, mouse_y,
                offset_x=GRID_OFFSET_X,
                offset_y=GRID_OFFSET_Y
                )

            if cell_pos is not None:
                cell_x, cell_y = cell_pos

                x = GRID_OFFSET_X + cell_x * my_grid.get_cell_dimension()
                y = GRID_OFFSET_Y + cell_y * my_grid.get_cell_dimension()

                self.rect.topleft = (x, y)

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                # Muove il rettangolo seguendo il mouse
                self.rect.move_ip(event.rel)
