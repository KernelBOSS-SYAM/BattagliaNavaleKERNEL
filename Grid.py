import pygame

pygame.font.init()
font = pygame.font.SysFont("arial", 20)


class Grid:
    """
    Represents a game grid. Handles:
      - Drawing the grid lines and coordinate labels
      - Tracking cell states: None, "hit", "miss"
      - Drawing hit (red X) and miss (blue dot) markers
      - Converting mouse clicks to grid coordinates
    """

    def __init__(self, cell_dimension=40, num_width_cells=13,
                 num_height_cells=13, color_grid=(255, 255, 255)):
        self.cell_dimension    = cell_dimension
        self.num_width_cells   = num_width_cells
        self.num_height_cells  = num_height_cells
        self.color_grid        = color_grid
        self._cell_states      = {}   # (col, row) -> "hit" | "miss"

    # ------------------------------------------------------------------
    # Cell state management
    # ------------------------------------------------------------------

    def set_cell_state(self, col, row, state):
        """Set a cell state: 'hit' or 'miss'."""
        self._cell_states[(col, row)] = state

    def get_cell_state(self, col, row):
        """Return the state of a cell, or None if untouched."""
        return self._cell_states.get((col, row))

    def reset(self):
        """Clear all cell states (useful for new game)."""
        self._cell_states.clear()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_grid(self, screen, offset_x=20, offset_y=20):
        """Draw grid lines, coordinate labels, and hit/miss markers."""

        # Draw hit/miss markers first (below grid lines)
        for (col, row), state in self._cell_states.items():
            self._draw_marker(screen, col, row, state, offset_x, offset_y)

        # Grid lines
        for i in range(self.num_width_cells):
            for j in range(self.num_height_cells):
                pygame.draw.rect(
                    screen, self.color_grid,
                    (offset_x + i * self.cell_dimension,
                     offset_y + j * self.cell_dimension,
                     self.cell_dimension, self.cell_dimension),
                    1
                )

        # Column letters (A, B, C …)
        for i in range(self.num_width_cells):
            letter = chr(65 + i)
            text   = font.render(letter, True, self.color_grid)
            x = offset_x + i * self.cell_dimension + self.cell_dimension // 2 - text.get_width() // 2
            y = offset_y - int(self.cell_dimension // 1.5)
            screen.blit(text, (x, y))

        # Row numbers (1, 2, 3 …)
        for j in range(self.num_height_cells):
            number = str(j + 1)
            text   = font.render(number, True, self.color_grid)
            x = offset_x - int(self.cell_dimension // 1.5)
            y = offset_y + j * self.cell_dimension + self.cell_dimension // 2 - text.get_height() // 2
            screen.blit(text, (x, y))

    def _draw_marker(self, screen, col, row, state, offset_x, offset_y):
        """Draw a hit (red X) or miss (blue dot) marker on a cell."""
        rx  = offset_x + col * self.cell_dimension
        ry  = offset_y + row * self.cell_dimension
        cd  = self.cell_dimension
        pad = 6

        if state == "hit":
            pygame.draw.rect(screen, (200, 40, 40), (rx, ry, cd, cd))
            pygame.draw.line(screen, (255, 255, 255), (rx + pad, ry + pad),      (rx + cd - pad, ry + cd - pad), 3)
            pygame.draw.line(screen, (255, 255, 255), (rx + cd - pad, ry + pad), (rx + pad,      ry + cd - pad), 3)
        elif state == "miss":
            pygame.draw.rect(screen, (40, 80, 160), (rx, ry, cd, cd))
            pygame.draw.circle(screen, (255, 255, 255), (rx + cd // 2, ry + cd // 2), 6)

    def draw_pending(self, screen, cells, offset_x, offset_y):
        """
        Highlight a list of (col, row) cells in yellow.
        Used to show targets selected by the player before firing.
        """
        for col, row in cells:
            rx = offset_x + col * self.cell_dimension
            ry = offset_y + row * self.cell_dimension
            cd = self.cell_dimension
            pygame.draw.rect(screen, (255, 220, 0),   (rx, ry, cd, cd))
            pygame.draw.rect(screen, (255, 255, 255), (rx, ry, cd, cd), 2)

    # ------------------------------------------------------------------
    # Mouse interaction
    # ------------------------------------------------------------------

    def get_cell_dimension(self):
        return self.cell_dimension

    def get_pos_OnClick(self, mouse_x, mouse_y, offset_x=20, offset_y=20):
        """Convert a mouse position to (col, row) grid coordinates, or None."""
        cell_x = (mouse_x - offset_x) // self.cell_dimension
        cell_y = (mouse_y - offset_y) // self.cell_dimension

        if 0 <= cell_x < self.num_width_cells and 0 <= cell_y < self.num_height_cells:
            return (cell_x, cell_y)
        return None