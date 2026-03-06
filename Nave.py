import pygame


class Nave:
    """
    Represents a ship. Handles:
      - Drag-and-drop movement
      - Rotation (R key while dragging): vertical <-> horizontal
      - Snap-to-grid placement with overlap/bounds checking
      - Scaled drawing both in the dock (pre-placement) and on the grid
    """

    def __init__(self, nome, path_img, dimensione=2):
        self.nome       = nome
        self.path_img   = path_img
        self.dimensione = dimensione

        # Drag state
        self.dragging   = False
        self.rect       = None

        # Placement state
        # rotation: 0 = vertical (default, matches ship images)
        #           90 = horizontal (after pressing R)
        self.rotation   = 0
        self.placed     = False
        self.grid_cells = []   # list of (col, row) once placed

    # ------------------------------------------------------------------
    # Image loading
    # ------------------------------------------------------------------

    def _load_image(self):
        """Load and rotate image according to current rotation."""
        img = pygame.image.load(self.path_img).convert_alpha()
        if self.rotation == 90:
            img = pygame.transform.rotate(img, 90)
        return img

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_nave(self, screen, pos_x=None, pos_y=None):
        """Draw ship freely (in dock / while dragging)."""
        img = self._load_image()

        if self.rect is None:
            if pos_x is None or pos_y is None:
                return
            self.rect = img.get_rect(topleft=(pos_x, pos_y))
        else:
            center    = self.rect.center
            self.rect = img.get_rect(center=center)

        screen.blit(img, self.rect.topleft)

    def draw_on_grid(self, screen, cell_size, offset_x, offset_y):
        """Draw ship scaled to fit its snapped grid cells."""
        if not self.grid_cells:
            return

        cols = [c for c, r in self.grid_cells]
        rows = [r for c, r in self.grid_cells]
        px = offset_x + min(cols) * cell_size
        py = offset_y + min(rows) * cell_size
        w  = (max(cols) - min(cols) + 1) * cell_size
        h  = (max(rows) - min(rows) + 1) * cell_size

        img = self._load_image()
        img = pygame.transform.scale(img, (w, h))
        screen.blit(img, (px, py))

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_event(self, event):
        """Handle drag, drop, and rotation. Ignores events if already placed."""
        if self.placed:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect and self.rect.collidepoint(event.pos):
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.rect.move_ip(event.rel)

        elif event.type == pygame.KEYDOWN and self.dragging:
            if event.key == pygame.K_r:
                self.rotation = 90 if self.rotation == 0 else 0
                # Re-centre rect after rotation changes image dimensions
                img           = self._load_image()
                center        = self.rect.center
                self.rect     = img.get_rect(center=center)

    # ------------------------------------------------------------------
    # Snap-to-grid placement
    # ------------------------------------------------------------------

    def get_snap_cells(self, col, row, cols, rows, occupied):
        """
        Calculate which grid cells this ship would occupy if placed at (col, row).
        Returns list of (col, row) tuples if valid, or None if out of bounds / overlapping.

        rotation == 0  → ship extends downward  (vertical)
        rotation == 90 → ship extends rightward (horizontal)
        """
        if self.rotation == 0:
            cells = [(col, row + i) for i in range(self.dimensione)]
        else:
            cells = [(col + i, row) for i in range(self.dimensione)]

        for c, r in cells:
            if not (0 <= c < cols and 0 <= r < rows):
                return None
            if (c, r) in occupied:
                return None

        return cells

    def snap(self, cells, cell_size, offset_x, offset_y):
        """Officially place the ship on the given grid cells."""
        self.grid_cells = cells
        self.placed     = True

        # Snap rect to the exact pixel position on the grid
        min_col = min(c for c, r in cells)
        min_row = min(r for c, r in cells)
        img       = self._load_image()
        self.rect = img.get_rect(
            topleft=(offset_x + min_col * cell_size,
                     offset_y + min_row * cell_size)
        )