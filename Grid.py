import pygame
pygame.font.init()
font = pygame.font.SysFont("arial", 20)

class Grid:

    def __init__(self, cell_dimension=30, num_width_cells=13, num_height_cells=13, color_grid=(255,255,255)):
        self.cell_dimension = cell_dimension
        self.num_width_cells = num_width_cells
        self.num_height_cells = num_height_cells
        self.color_grid = color_grid

        self.grid_matrix = [
            [-1 for _ in range(num_height_cells)]
            for _ in range(num_width_cells)
        ]

    def draw_grid(self, screen, offset_x=20, offset_y=20):

        for i in range(self.num_width_cells):
            for j in range(self.num_height_cells):
                pygame.draw.rect(
                    screen,
                    self.color_grid,
                    (
                        offset_x + i * self.cell_dimension,
                        offset_y + j * self.cell_dimension,
                        self.cell_dimension,
                        self.cell_dimension
                    ),
                    1
                )

        for i in range(self.num_width_cells):
            letter = chr(65 + i)
            text = font.render(letter, True, self.color_grid)
            x = offset_x + i * self.cell_dimension + self.cell_dimension//2 - text.get_width()//2
            y = offset_y - 25
            screen.blit(text, (x, y))

        for j in range(self.num_height_cells):
            number = str(j+1)
            text = font.render(number, True, self.color_grid)
            x = offset_x - 25
            y = offset_y + j * self.cell_dimension + self.cell_dimension//2 - text.get_height()//2
            screen.blit(text, (x, y))

    def place_ship(self, ship, offset_x=20, offset_y=20):

        cell_x = (ship.rect.x - offset_x) // self.cell_dimension
        cell_y = (ship.rect.y - offset_y) // self.cell_dimension

        valid = True
        positions = []

        for i in range(ship.dimensione):

            if ship.rotation == 0:
                x = cell_x + i
                y = cell_y
            else:
                x = cell_x
                y = cell_y + i

            if not (0 <= x < self.num_width_cells and 0 <= y < self.num_height_cells):
                valid = False
                break

            if self.grid_matrix[x][y] != -1:
                valid = False
                break

            positions.append((x, y))

        if not valid:
            return False

        ship.rect.x = offset_x + cell_x * self.cell_dimension
        ship.rect.y = offset_y + cell_y * self.cell_dimension

        for (x, y) in positions:
            self.grid_matrix[x][y] = 1

        ship.grid_position = (cell_x, cell_y)
        ship.placed = True

        return True