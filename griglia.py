class Griglia:
    def __init__(self, size=13):
        self.size = size
        self.grid = [[-1 for _ in range(size)] for _ in range(size)]
        self.navi = []

    def is_inside(self, row, col):
        """Controlla se una cella è dentro la griglia"""
        return 0 <= row < self.size and 0 <= col < self.size

    def can_place_ship(self, nave):
        """Controlla se la nave può essere posizionata"""
        for (row, col) in nave.positions:
            if not self.is_inside(row, col):
                return False
            if self.grid[row][col] != -1:  # già occupata
                return False
        return True

    def place_ship(self, nave):
        """Inserisce la nave nella griglia"""
        if self.can_place_ship(nave):
            self.navi.append(nave)
            for (row, col) in nave.positions:
                self.grid[row][col] = 0
            return True
        return False

    def shoot(self, row, col):
        """Gestisce un colpo"""
        if not self.is_inside(row, col):
            return "Fuori griglia"

        # già colpito
        if self.grid[row][col] == 1:
            return "Già colpito"

        for nave in self.navi:
            if nave.hit(row, col):
                self.grid[row][col] = 1
                if nave.is_sunk():
                    return "Colpito e affondato"
                return "Colpito"

        # acqua
        self.grid[row][col] = 1
        return "Acqua"