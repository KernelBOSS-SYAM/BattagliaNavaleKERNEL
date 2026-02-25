import pygame
pygame.font.init()
font = pygame.font.SysFont("arial", 20)


class Grid:
    cell_dimension = 30
    num_width_cells = 0
    num_height_cells = 0
    color_grid = 0
    grid_matrix = []




    # Inizializza la griglia con le dimensioni specificate
    # cell_dimension: dimensione di ogni cella
    # num_width_cells: numero di celle in larghezza
    # num_height_cells: numero di celle in altezza
    def __init__(self, cell_dimension = 30, num_width_cells = 13, num_height_cells = 13, color_grid = (255,255,255)):
        self.cell_dimension = cell_dimension
        self.num_width_cells = num_width_cells
        self.num_height_cells = num_height_cells
        self.color_grid = color_grid
        self.grid_matrix = [[-1 for _ in range(num_height_cells)] for _ in range(num_width_cells)]

    # Disegna la griglia sullo schermo
    # screen: superficie di pygame su cui disegnare
    # color: colore delle linee della griglia
    # offset_x, offset_y: posizione di partenza della griglia
    def draw_grid(self, screen, offset_x = 20, offset_y = 20):
        for i in range(self.num_width_cells):
            for j in range(self.num_height_cells):
                pygame.draw.rect(screen, self.color_grid, (offset_x + i * self.cell_dimension, offset_y + j * self.cell_dimension, self.cell_dimension, self.cell_dimension), 1)

        for i in range(self.num_width_cells):
            letter = chr(65 + i)  # 65 = 'A'
            text = font.render(letter, True, self.color_grid)

            x = offset_x + i * self.cell_dimension + self.cell_dimension // 2 - text.get_width() // 2
            y = offset_y - self.cell_dimension // 1.5

            screen.blit(text, (x, y))

        for j in range(self.num_height_cells):
            number = str(j + 1)
            text = font.render(number, True, self.color_grid)

            x = offset_x - self.cell_dimension // 1.5
            y = offset_y + j * self.cell_dimension + self.cell_dimension // 2 - text.get_height() // 2

            screen.blit(text, (x, y))

    def get_cell_dimension(self):
        return self.cell_dimension
    
    def get_pos_OnClick (self, mouse_x, mouse_y, offset_x = 20, offset_y = 20):
        cell_x = (mouse_x - offset_x) // self.cell_dimension
        cell_y = (mouse_y - offset_y) // self.cell_dimension

        if 0 <= cell_x < self.num_width_cells and 0 <= cell_y < self.num_height_cells:
            return (cell_x, cell_y)

    

        