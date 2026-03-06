import random


class AIOpponent:
    """
    Hunt & Target AI — adattato alla grid_matrix del gruppo.

    La grid_matrix usa:
        -1  acqua libera
         0  cella occupata da nave (non ancora colpita)
         1  cella nave colpita
        -2  acqua già sparata (mancato)

    Regole colpi:
        shots = somma degli hp rimasti di tutte le navi non affondate
        (calcolata da calcola_colpi_disponibili in game_handler.py)
    """

    GRID_COLS = 13
    GRID_ROWS = 13

    SHIP_SIZES = [5, 4, 3, 3, 2]   # portaerei, corazzata, 2×incrociatore, caccia

    def __init__(self):
        self.fired        = set()    # (col, row) già sparati
        self.hits         = set()    # (col, row) colpiti ma non ancora affondati
        self.target_queue = []       # celle prioritarie in modalità TARGET
        self.mode         = "HUNT"
        self.grid_matrix  = self._build_grid()
        self._place_ships_randomly()

    # ──────────────────────────────────────────────────────────────────
    # Setup
    # ──────────────────────────────────────────────────────────────────

    def _build_grid(self):
        """Griglia interna AI — stessa struttura di Grid.grid_matrix."""
        return [[-1] * self.GRID_ROWS for _ in range(self.GRID_COLS)]

    def _place_ships_randomly(self):
        """Piazza le navi AI nella griglia interna in modo casuale."""
        for size in self.SHIP_SIZES:
            placed, attempts = False, 0
            while not placed and attempts < 2000:
                attempts += 1
                horizontal = random.choice([True, False])
                if horizontal:
                    col = random.randint(0, self.GRID_COLS - size)
                    row = random.randint(0, self.GRID_ROWS - 1)
                    cells = [(col + i, row) for i in range(size)]
                else:
                    col = random.randint(0, self.GRID_COLS - 1)
                    row = random.randint(0, self.GRID_ROWS - size)
                    cells = [(col, row + i) for i in range(size)]

                if all(self.grid_matrix[c][r] == -1 for c, r in cells):
                    for c, r in cells:
                        self.grid_matrix[c][r] = 0   # 0 = nave presente
                    placed = True

    # ──────────────────────────────────────────────────────────────────
    # Interfaccia pubblica
    # ──────────────────────────────────────────────────────────────────

    def has_ship_at(self, col, row):
        """Ritorna True se l'AI ha una nave nella cella (col, row)."""
        return self.grid_matrix[col][row] == 0

    def receive_shot(self, col, row):
        """
        Il giocatore spara sulla griglia AI.
        Aggiorna grid_matrix e ritorna "hit", "sunk" o "miss".
        """
        val = self.grid_matrix[col][row]
        if val == 0:
            self.grid_matrix[col][row] = 1   # colpito
            # Controlla se la nave è affondata cercando 0 adiacenti connessi
            if self._is_ship_sunk(col, row):
                return "sunk"
            return "hit"
        elif val == -1:
            self.grid_matrix[col][row] = -2  # acqua sparata
            return "miss"
        else:
            return "already_fired"

    def fire(self):
        """
        Restituisce (col, row) per uno sparo AI sul giocatore.
        Chiamare più volte per turni multi-colpo.
        """
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
        Comunica all'AI il risultato di uno sparo sulla griglia giocatore.
        result: "miss" | "hit" | "sunk"
        """
        if result == "hit":
            self.hits.add(cell)
            self.mode = "TARGET"
            self._enqueue_neighbors(cell)
        elif result == "sunk":
            self.hits.clear()
            self.target_queue.clear()
            self.mode = "HUNT"

    def all_sunk(self):
        """True se tutte le navi AI sono state affondate."""
        return all(
            self.grid_matrix[c][r] != 0
            for c in range(self.GRID_COLS)
            for r in range(self.GRID_ROWS)
        )

    # ──────────────────────────────────────────────────────────────────
    # Interni
    # ──────────────────────────────────────────────────────────────────

    def _hunt(self):
        """Modalità caccia: pattern a scacchiera, poi celle rimanenti."""
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
        col, row = cell
        directions = (
            self._aligned_directions()
            if len(self.hits) > 1
            else [(-1, 0), (1, 0), (0, -1), (0, 1)]
        )
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
        return [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def _is_ship_sunk(self, col, row):
        """
        BFS dalla cella colpita: la nave è affondata se nessuna cella
        connessa (orizzontale/verticale) ha ancora valore 0.
        """
        visited = set()
        queue   = [(col, row)]
        while queue:
            c, r = queue.pop()
            if (c, r) in visited:
                continue
            visited.add((c, r))
            if self.grid_matrix[c][r] == 0:
                return False   # almeno una cella ancora integra
            for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
                nc, nr = c+dc, r+dr
                if (
                    0 <= nc < self.GRID_COLS
                    and 0 <= nr < self.GRID_ROWS
                    and (nc, nr) not in visited
                    and self.grid_matrix[nc][nr] in (0, 1)
                ):
                    queue.append((nc, nr))
        return True
