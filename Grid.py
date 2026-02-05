import pygame

class Grid:
    cell_dimension = 30
    num_width_cells = 0
    num_height_cells = 0


    # Inizializza la griglia con le dimensioni specificate
    # cell_dimension: dimensione di ogni cella
    # num_width_cells: numero di celle in larghezza
    # num_height_cells: numero di celle in altezza
    def __init__(self, cell_dimension = 30, num_width_cells = 13, num_height_cells = 13):
        self.cell_dimension = cell_dimension
        self.num_width_cells = num_width_cells
        self.num_height_cells = num_height_cells


    # Disegna la griglia sullo schermo
    # screen: superficie di pygame su cui disegnare
    # color: colore delle linee della griglia
    # offset_x, offset_y: posizione di partenza della griglia
    def draw_grid(self, screen, color= (0,0,255), offset_x = 20, offset_y = 20):
        for i in range(self.num_width_cells):
            for j in range(self.num_height_cells):
                pygame.draw.rect(screen, color, (offset_x + i * self.cell_dimension, offset_y + j * self.cell_dimension, self.cell_dimension, self.cell_dimension), 1)

    def get_cell_dimension(self):
        return self.cell_dimension
    