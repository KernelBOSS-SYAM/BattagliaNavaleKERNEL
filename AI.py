import random


class AIOpponent:
    """
    Hunt & Target AI for Battaglia Navale.

    Supports multi-shot turns as per documentation:
    - Each turn the AI fires multiple shots (= its remaining un-hit ship cells)
    - HUNT mode: checkerboard pattern until a hit
    - TARGET mode: attacks adjacent cells after a hit to sink the ship
    """

    GRID_COLS = 13
    GRID_ROWS = 13

    SHIP_CONFIGS = [
        ("portaerei",           5),
        ("corazzata",           4),
        ("incrociatore1",       3),
        ("incrociatore2",       3),
        ("cacciatorpediniere",  2),
    ]

    def __init__(self):
        self.fired        = set()
        self.hits         = set()
        self.target_queue = []
        self.mode         = "HUNT"
        self.ship_cells   = set()
        self._place_ships_randomly()

    # ------------------------------------------------------------------
    # Ship placement
    # ------------------------------------------------------------------

    def _place_ships_randomly(self):
        occupied = set()
        for name, size in self.SHIP_CONFIGS:
            placed, attempts = False, 0
            while not placed and attempts < 1000:
                attempts += 1
                horizontal = random.choice([True, False])
                if horizontal:
                    col   = random.randint(0, self.GRID_COLS - size)
                    row   = random.randint(0, self.GRID_ROWS - 1)
                    cells = [(col + i, row) for i in range(size)]
                else:
                    col   = random.randint(0, self.GRID_COLS - 1)
                    row   = random.randint(0, self.GRID_ROWS - size)
                    cells = [(col, row + i) for i in range(size)]

                if not any(c in occupied for c in cells):
                    occupied.update(cells)
                    placed = True

        self.ship_cells = occupied

    def has_ship_at(self, col, row):
        return (col, row) in self.ship_cells

    # ------------------------------------------------------------------
    # Single shot (called in a loop for multi-shot turns)
    # ------------------------------------------------------------------

    def fire(self):
        """Return (col, row) for one shot. Call multiple times per turn."""
        if self.mode == "TARGET" and self.target_queue:
            cell = self.target_queue.pop(0)
            while cell in self.fired:
                if not self.target_queue:
                    self.mode = "HUNT"
                    cell = self._hunt()
                    break
                cell = self.target_queue.pop(0)
        else:
            self.mode = "HUNT"
            cell = self._hunt()

        self.fired.add(cell)
        return cell

    def report(self, cell, result):
        """
        Tell the AI the outcome of a shot.
        result: "miss", "hit", or "sunk"
        """
        if result == "hit":
            self.hits.add(cell)
            self.mode = "TARGET"
            self._enqueue_neighbors(cell)
        elif result == "sunk":
            self.hits.clear()
            self.target_queue.clear()
            self.mode = "HUNT"
        # "miss" needs no state change

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _hunt(self):
        # Checkerboard pattern first (ships can't fit in single-cell gaps)
        candidates = [
            (c, r)
            for c in range(self.GRID_COLS)
            for r in range(self.GRID_ROWS)
            if (c + r) % 2 == 0 and (c, r) not in self.fired
        ]
        if not candidates:
            candidates = [
                (c, r)
                for c in range(self.GRID_COLS)
                for r in range(self.GRID_ROWS)
                if (c, r) not in self.fired
            ]
        return random.choice(candidates)

    def _enqueue_neighbors(self, cell):
        col, row   = cell
        directions = self._aligned_directions() if len(self.hits) > 1 else [(-1,0),(1,0),(0,-1),(0,1)]
        for dc, dr in directions:
            nb = (col + dc, row + dr)
            if (
                0 <= nb[0] < self.GRID_COLS
                and 0 <= nb[1] < self.GRID_ROWS
                and nb not in self.fired
                and nb not in self.target_queue
            ):
                self.target_queue.append(nb)

    def _aligned_directions(self):
        cols = [c for c, r in self.hits]
        rows = [r for c, r in self.hits]
        if len(set(rows)) == 1:
            return [(1, 0), (-1, 0)]
        if len(set(cols)) == 1:
            return [(0, 1), (0, -1)]
        return [(-1,0),(1,0),(0,-1),(0,1)]