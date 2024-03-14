import numpy as np

from math import cos, pi

def get_ring_radius(diameter: float, num_particles: int):
    return diameter / (2 * (1 - cos(2*pi/(num_particles))))**.5

class RetangularGrid:
    def __init__(self, edges: tuple[np.ndarray]) -> None:
        '''
        Grade retangular dado as posições das bordas das células.

        Parâmetros:
            edges:
                Tupla com dois arrays:

                edges[0]: Posições das bordas das colunas, incluindo os extremos. 
                edges[1]: Posições das bordas das linhas, incluindo os extremos. 
        '''
        self.edges = edges

        self.num_dims = len(edges)

        # Quantidade de células em cada dimensão
        self.shape = (self.edges[0].size-1, self.edges[1].size-1) 
        
        # Quantidade de células em cada dimensão ordenados
        # na forma geralmente utilizada pelo matplotlib
        self.shape_mpl = (self.shape[1], self.shape[0])

        # Centro das células em cada dimensão
        self.dim_cell_center = []
        for dim in range(self.num_dims):
            self.dim_cell_center.append((self.edges[dim][1:] + self.edges[dim][:-1])/2)

        # Meshgrid do centro das células
        self.meshgrid = np.meshgrid(*self.dim_cell_center)

class RegularGrid(RetangularGrid):
    def __init__(self, length: float, height: float, num_cols: int, num_rows: int) -> None:
        '''
        Grade retangular para uma retângulo centrado na origem, com dimensões `length`x`height`. 
        '''
        edges = (
            np.linspace(-length/2, length/2, num_cols+1),
            np.linspace(-height/2, height/2, num_rows+1),
        )
        super().__init__(edges)

        # Tamanho das células em cada dimensão.
        self.size = (
            self.edges[0][1] - self.edges[0][0],
            self.edges[1][1] - self.edges[1][0],
        )

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    grid = RegularGrid(10, 5, 10, 5)

    plt.scatter(*grid.meshgrid)
    plt.show()
