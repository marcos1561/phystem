class SpaceCfg:
    "Configurações do espaço na qual as partículas se encontram."
    def __init__(self, height: float, length: float) -> None:
        self.height = height
        self.length = length
    
    def set(self, other):
        self.height = other.height
        self.length = other.length
    
    def max_num_inside(self, ring_diameter):
        'Número ne anéis que cabem dentro do espaço'
        return int(self.height * self.length / ring_diameter**2)

    def particle_grid_shape(self, max_dist, frac=1.05):
        from math import floor
        box_size = max_dist * frac
        num_cols = int(floor(self.length/box_size))
        num_rows = int(floor(self.height/box_size))
        return (num_cols, num_rows)

    def rings_grid_shape(self, radius, frac=0.5):
        from math import ceil
        num_cols = int(ceil(self.length / ((2 + frac)*radius)))
        num_rows = int(ceil(self.height / ((2 + frac)*radius)))
        return (num_cols, num_rows)

