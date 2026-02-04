class Nave:
    def __init__(self, row, col, length, orientation):
        """
        row, col -> posizione iniziale (primo pezzo nave)
        length -> lunghezza nave
        orientation -> 'H' orizzontale | 'V' verticale
        """
        self.row = row
        self.col = col
        self.length = length
        self.orientation = orientation

        self.positions = self.calculate_positions()
        self.hits = set()  # celle colpite

    def calculate_positions(self):
        """Calcola tutte le celle occupate dalla nave"""
        positions = []
        for i in range(self.length):
            if self.orientation == 'H':
                positions.append((self.row, self.col + i))
            else:  # verticale
                positions.append((self.row + i, self.col))
        return positions

    def hit(self, row, col):
        """Registra un colpo se la nave è stata colpita"""
        if (row, col) in self.positions:
            self.hits.add((row, col))
            return True
        return False

    def is_sunk(self):
        """Controlla se la nave è affondata"""
        return len(self.hits) == self.length

    def occupies(self, row, col):
        """Controlla se la nave occupa una certa cella"""
        return (row, col) in self.positions
