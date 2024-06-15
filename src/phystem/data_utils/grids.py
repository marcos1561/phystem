import numpy as np

class RetangularGrid:
    def __init__(self, edges: tuple[np.ndarray]) -> None:
        '''Grade retangular dado as posições das bordas das células.

        Parâmetros:
            edges:
                Tupla com dois arrays:

                edges[0]: Posições das bordas das colunas, incluindo os extremos. 
                edges[1]: Posições das bordas das linhas, incluindo os extremos. 
        '''
        self.edges = edges

        self.num_dims = len(edges)

        # Comprimento da grade em cada dimensão
        self.size = []
        
        # Centro das células em cada dimensão
        self.dim_cell_center = []
        
        # Comprimento das células em cada dimensão
        self.dim_cell_size = []
       
        for dim in range(self.num_dims):
            self.size.append(self.edges[dim][-1] - self.edges[dim][0])
            self.dim_cell_center.append((self.edges[dim][1:] + self.edges[dim][:-1])/2)
            self.dim_cell_size.append(self.edges[dim][1:] - self.edges[dim][:-1])

        # Quantidade de células em cada dimensão
        self.shape = (self.edges[0].size-1, self.edges[1].size-1) 
        
        # Quantidade de células em cada dimensão, ordenados
        # na forma geralmente utilizada pelo matplotlib
        self.shape_mpl = (self.shape[1], self.shape[0])

        # Centro das células em cada dimensão
        self.dim_cell_center = []
        for dim in range(self.num_dims):
            self.dim_cell_center.append((self.edges[dim][1:] + self.edges[dim][:-1])/2)

        # Meshgrid do centro das células
        self.meshgrid = np.meshgrid(*self.dim_cell_center)

    def filter_coords(self, coords: np.ndarray):
        '''Remove as coordenadas fora da grade'''

        mask = np.full(coords.shape[0], False)
        for i in range(2):
            mask_i = np.logical_or(coords[:, i] < 0, coords[:, i] >= self.shape[i])
            mask = np.logical_or(mask, mask_i)

        return coords[np.logical_not(mask)]

    def count(self, coords: np.ndarray):
        '''Contagem da quantidade de pontos em cada célula da grade, dado as coordenadas dos pontos
        na grade (coords).

        Retorno:
            count_grid: ndarray
                Array com a contagem dos pontos em cada célula. O elemento de índice (i, j)
                é a contagem da célula localizada na i-ésima linha e j-ésima coluna da grade.
        '''
        coords, count = np.unique(coords, axis=0, return_counts=True)
        count_grid = np.zeros(self.shape, dtype=int)
        count_grid[coords[:, 0], coords[:, 1]] = count 
        return count_grid.T

    def sum_by_cell(self, values: np.array, coords: np.array):
        '''Soma dos valores dos pontos que estão na mesma célula da grade. Cada
        ponto possui um valor associando em `values` e sua coordenada na grade está 
        em `coords`.

        Parâmetros:
            values:
                Array com os valores dos pontos a serem somados. 

                values[i] -> valor do i-ésimo ponto.

            grid_coords:
                Coordenadas dos pontos na grade ao qual `values` se refere.
            
        Retorno:
            values_sum: ndarray
                Array com a soma dos valores dos pontos que estão na mesma célula. 
                Seu shape é (N_l, N_c, *values.shape[1:]), em que N_l é o número de linhas da grade
                e N_c o número de colunas.

                vel_grid[i, j] -> Soma dos valores da célula localiza
                    na linha i e coluna j da grade.
        '''
        values_sum = np.zeros((*reversed(self.shape[:2]), *self.shape[2:], *values.shape[1:]),  dtype=float)
        for idx, coord in enumerate(coords):
            values_sum[coord[1], coord[0]] += values[idx]

        # values_sum = np.zeros((values.shape[1], *reversed(self.shape[:2]), *self.shape[2:]), dtype=float)
        # for idx, coord in enumerate(coords):
        #     values_sum[:, coord[1], coord[0]] += values[idx]
        
        return values_sum

    def mean_by_cell(self, values: np.array, coords: np.array, count: np.array=None):
        '''Mesma função de `self.sum_by_cell`, mas divide o resultado pela
        contagem de pontos em cada célula, assim realizando a média por célula.
        '''
        values_mean = self.sum_by_cell(values, coords)
        
        if count is None:
            count = self.count(coords)

        non_zero_mask = count > 0
        extend_shape = np.ones(len(values[0].shape), dtype=int)

        print(values_mean[non_zero_mask])

        values_mean[non_zero_mask] /= count.reshape(*count.shape, *extend_shape)[non_zero_mask]
        # values_mean[non_zero_mask] /= count[non_zero_mask]
        return values_mean

    def intersect_circle_mask(self, radius, center=(0, 0)):
        '''Máscara das células que não intersectam o círculo de
        centro `center` e raio `radius`;
        '''
        x_max = self.meshgrid[0] + self.dim_cell_size[0]/2
        x_min = self.meshgrid[0] - self.dim_cell_size[0]/2
        
        y_max = (self.meshgrid[1].T + self.dim_cell_size[1]/2).T
        y_min = (self.meshgrid[1].T - self.dim_cell_size[1]/2).T
        
        x_max_sqr = np.square(x_max - center[0]) 
        x_min_sqr = np.square(x_min - center[0]) 
        
        y_max_sqr = np.square(y_max - center[1]) 
        y_min_sqr = np.square(y_min - center[1]) 

        d1 = np.sqrt(x_max_sqr + y_max_sqr)
        d2 = np.sqrt(x_max_sqr + y_min_sqr)
        d3 = np.sqrt(x_min_sqr + y_max_sqr)
        d4 = np.sqrt(x_min_sqr + y_min_sqr)

        return np.logical_not((d1 < radius) | (d2 < radius) | (d3 < radius) | (d4 < radius))

class RegularGrid(RetangularGrid):
    def __init__(self, length: float, height: float, num_cols: int, num_rows: int, center=(0, 0)) -> None:
        '''Grade retangular para uma retângulo centrado em `center`, com lados `length`x`height`.'''
        self.center = center
        self.length = length
        self.height = height

        edges = (
            np.linspace(-length/2 + center[0], length/2 + center[0], num_cols+1),
            np.linspace(-height/2 + center[1], height/2 + center[1], num_rows+1),
        )
        super().__init__(edges)

        # Tamanho da célula em cada dimensão.
        self.cell_size = (
            self.edges[0][1] - self.edges[0][0],
            self.edges[1][1] - self.edges[1][0],
        )

    def coords(self, points: np.ndarray, skip_out_of_bounds=False, remove_out_of_bounds=False):
        '''Calcula as coordenadas dos pontos em `points` na grade.

        Parâmetros:
            points:
                Array com os pontos, cujo shape é (N, 2), onde
                N é o número de pontos e 2 vem das duas dimensões da grade 
                (0 para o eixo x e 1 para o eixo y).
        
        Retorno:
            coords: ndarray
                Array com shape (N, 2) em que o i-ésimo elemento é a coordenada do 
                i-ésimo ponto na grade. O segundo índice do shape indica a dimensão da coordenada:
                    
                    coords[i, 0] -> Coordenada no eixo x (Coluna) \n
                    coords[i, 1] -> Coordenada no eixo y (Linha)
                
                A célula da grade que está no canto esquerdo inferior possui coordenada (0, 0).
        '''
        x = points[:, 0] - self.center[0] + self.length/2
        y = points[:, 1] - self.center[1] + self.height/2

        col_pos = (x / self.cell_size[0]).astype(int)
        row_pos = (y / self.cell_size[1]).astype(int)

        if not skip_out_of_bounds:
            col_pos[col_pos > self.shape[0]] = self.shape[0]
            row_pos[row_pos > self.shape[1]] = self.shape[1]
            row_pos[row_pos < 0] = -1
            col_pos[col_pos < 0] = -1


        coords = np.array([col_pos, row_pos]).T
        
        if remove_out_of_bounds:
            coords = self.filter_coords(coords)
        
        return coords

if __name__ == "__main__":
    l, h = 10, 5
    grid = RegularGrid(l, h, 7, 5)

    n = 10
    xs = (np.random.random(n) - 0.5) * l
    ys = (np.random.random(n) - 0.5) * h
    ps = np.array([xs, ys]).T

    coords = grid.coords(ps)

    coords = np.array([
        [0, 0],
        [0, 0],
        [1, 2],
        [1, 2],
        [1, 2],
    ])

    values = np.array([
        [1 , 1 ],
        [-3, 4 ],
        [3 , -3],
        [6 , 2 ],
        [-1, 11],
    ])

    r_all = grid.mean_by_cell(values, coords) 

    check_x = grid.mean_by_cell(values[:, 0], coords) == r_all[:, :, 0]
    check_y = grid.mean_by_cell(values[:, 1], coords) == r_all[:, :, 1]
    print("Mean by cell Test:", check_x.all(), check_y.all())

    # import matplotlib.pyplot as plt
    # plt.scatter(xs, ys, c="black")
    # plt.show()