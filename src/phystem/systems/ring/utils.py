from scipy.spatial import Voronoi
from scipy.optimize import fsolve
import numpy as np
import yaml
from math import cos, pi
from pathlib import Path
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection

def get_real_ring_radius(p_diameter: float, num_particles: int):
    'Raio do centro do anel até a ponta da partícula.'
    r = get_ring_radius(p_diameter, num_particles)
    return r + p_diameter/2

def get_ring_radius(p_diameter: float, num_particles: int):
    '''
    Raio de equilíbrio do anel dado o diâmetro das partículas (p_diameter)
    e quantas partículas compõem o anel (num_particles).
    Esse raio é do centro do anel até o centro da partícula.
    '''
    return p_diameter / (2 * (1 - cos(2*pi/(num_particles))))**.5

def get_second_order_neighbors_dist(num_particles, lo):
    '''
    Dado um anel com `num_particles` partículas, cujas molas possuem
    comprimento `lo`, retorna a distância entre partículas que estão
    separadas por outra partícula. É assumido que o anel está no formato
    de um polígono regular.
    '''
    theta = np.pi * (1- 2/num_particles)
    return lo * (2*(1-np.cos(theta)))**.5    

def get_equilibrium_spring_l(num_particles, area0):
    '''
    Retorna o comprimento que as molas devem ter para que a área de equilíbrio
    de um anel com `num_particles`, apenas considerando as molas, seja a mesma
    de `area_o`. 
    '''
    theta = np.pi * 2 / num_particles
    return 2 * (area0 / num_particles * (1 - np.cos(theta)) / np.sin(theta))**.5

def get_equilibrium_p0(num_particles):
    '''
    Retorna o p0 em que `area0` é igual a área de equilíbrio
    apenas considerando as molas.
    '''
    theta = 2 * np.pi / num_particles
    return 2 * (num_particles * (1 - np.cos(theta))/np.sin(theta))**.5

def get_invasion_equilibrium_config(k_r, k_m, k_a, lo, ro, area0, relative_area_eq, vo, mu):
    '''
    Considerando a situação de equilíbrio do pior cenário de invasão entre anéis, 
    retorna duas quantidades:
    * Metade do ângulo que a partícula invasora faz com as partículas
        do anel sendo invadido.
    * Distância entre as partículas do anel sendo invadido.
    '''
    def fp(theta, l):
        return k_r/ro * (ro - l / (2*np.sin(theta)))
    
    def fm(theta, l):
        return k_m * (l - lo)

    def get_l1(theta, l):
        return l / (2 * np.sin(theta))

    def get_cos_alpha(theta, l):
        l1 = get_l1(theta, l)
        return l1, (ro**2 - lo**2 - l1**2) / (-2 * l1 * lo)

    def sin_beta(theta, l):
        l1, cos_alpha = get_cos_alpha(theta, l)
        if cos_alpha > 1:
            print("Merda", cos_alpha)
            print(l, theta/np.pi*180)
            print(l1, ro, lo)
            print("============")
        return np.sin(theta) *  cos_alpha + np.cos(theta) * np.sqrt(1 - cos_alpha**2) 

    def fa(theta, l):
        # return k_a * area0 * (1 - relative_area_eq) * lo * sin_beta(theta, l)
        return k_a * area0 * (1 - relative_area_eq) * lo

    def eq1(theta, l):
        return mu * (2 * fp(theta, l) * np.cos(theta) - fa(theta, l)) - vo
        # return mu * (2 * fp(theta, l) * np.cos(theta)) - vo
    
    def eq2(theta, l):
        return mu * (fp(theta, l) * np.sin(theta) - fm(theta, l)) + vo

    def func(x):
        theta, l = x[0], x[1]
        return [
            eq1(theta, l),
            eq2(theta, l),
        ]

    r =  fsolve(func, [10/180 * np.pi, lo], maxfev=500)
    return r, func(r)

def get_equilibrium_relative_area(k_a, k_m, a0, spring_r, num_particles):
    "Retorna a área de equilíbrio em relação a `a0`."
    theta = 2 * np.pi / num_particles
    
    def get_r(f):
        return np.sqrt(f * 2 * a0 / (num_particles * np.sin(theta))) 

    def get_fm(f):
        return k_m * (get_r(f) * np.sqrt(2*(1 - np.cos(theta))) - spring_r)

    def get_fm_total(f):
        return 2 * get_fm(f) * np.sin(theta/2)

    def get_fa(f):
        r = get_r(f)
        return k_a * (a0 - 10/2 * r**2 * np.sin(theta)) * r * np.sin(theta)

    def func(f):
        return get_fa(f) - get_fm_total(f)

    return fsolve(func, 0.5)

def get_max_k_adh(adh_size, dt, k_a, area0, lo, relative_area, mu, vo, x=1):
    '''
    Retorna o valor máximo de `k_adh` em relação a problemas numéricos. `x` deve
    ser um valor entre 0 e 1 utilizada para definir em qual ponto da região de
    adesão (que será `x * adh_size`) será feito o cálculo.
    '''
    x = adh_size * x
    area_prime = k_a * area0 * lo * (1 - relative_area)
    return adh_size/mu * (1/(2*dt) - vo/x) - adh_size/x * area_prime

def pos_to_mpl_scatter(pos):
    '''
    Posições das partículas para um formato aceito
    pelo `scatter` do matplotlib.
    '''
    return pos.reshape(pos.shape[0] * pos.shape[1], pos.shape[2]).T

def num_rings_in_rect(ring_diameter: float, space_cfg):
    raise Exception("Use o método em SpaceCfg para isso.")

def same_rings(pos1, ids1, pos2, ids2, return_common_ids=False):
    '''
    Dados os array `pos1` e `pos2` cujos elementos possuem índices
    em `ids1` e `ids2`, respectivamente, retorna as posições 
    ordenadas pelos mesmos ids, ou seja, o i-ésimo elemento
    em ambos os arrays se referem ao mesmo id.

    Return
    ------
    pos1, pos2:
        Array com as posições ordenadas pelos mesmos ids.
    
    common_ids:
        ids em comum entre `ids1` e `ids2`.
    '''
    argsort1 = np.argsort(ids1)
    argsort2 = np.argsort(ids2)
    
    ids1_sorted = np.sort(ids1)
    ids2_sorted = np.sort(ids2)

    common_ids = np.intersect1d(ids1_sorted, ids2_sorted)
    id_mask1 = np.where(np.in1d(ids1_sorted, common_ids))[0]
    id_mask2 = np.where(np.in1d(ids2_sorted, common_ids))[0]
    
    if return_common_ids:
        return pos1[argsort1[id_mask1]], pos2[argsort2[id_mask2]], common_ids
    else:
        return pos1[argsort1[id_mask1]], pos2[argsort2[id_mask2]]

class RetangularGrid:
    def __init__(self, edges: tuple[np.ndarray]) -> None:
        '''
        Grade retangular dado as posições das bordas das células.

        Parâmetros:
        -----------
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

        # Área das células.
        # self.cell_area[i, j] = Área da célula na linha i e coluna j
        w, h = np.meshgrid(*self.dim_cell_size)
        self.cell_area = w * h

    def adjust_shape(self, arr: np.ndarray, expected_order=2, arr_name="arr"):
        '''
        Se `arr` possui `expected_order` índices, ajusta seu shape para ter 
        `expected_order + 1` índices.
        Por exemplo, se `expected_order=2` e o shape de `arr` é (N, M), o ajuste 
        muda o shape para (1, N, M).
        '''
        num_indices = len(arr.shape) 
        if num_indices == expected_order:
            arr = arr.reshape(1, *arr.shape)
        elif num_indices != (expected_order + 1):
            order1, order2 = expected_order, expected_order + 1
            raise Exception(f"`len({arr_name}.shape)` é {len(arr.shape)}, mas deveria ser {order1} ou {order2}.")

        return arr

    def simplify_shape(self, arr: np.array):
        if arr.shape[0] == 1:
            arr = arr.reshape(*arr.shape[1:])
        return arr

    def get_out_mask(self, coords: np.array):
        "Retorna a máscara dos pontos em `coords` que estão fora da grade."
        coords = self.adjust_shape(coords, arr_name="coords")
        x = coords[:, :, 0]
        y = coords[:, :, 1]
        out_x = (x < 0) | (x > self.shape[0])
        out_y = (y < 0) | (y > self.shape[1])
        out = out_x | out_y
        return self.simplify_shape(out)

    def remove_out_of_bounds(self, coords: np.array):
        '''
        Retorna um array que somente contém as coordenadas em `coords`
        que estão dentro da grade.
        '''
        return coords[np.logical_not(self.get_out_mask(coords))]

    def count(self, coords: np.ndarray):
        '''
        Contagem da quantidade de pontos em cada célula da grade, dado as coordenadas dos pontos
        na grade `coords`.

        Retorno:
        --------
        count_grid: ndarray
            Array com a contagem dos pontos em cada célula. O elemento de índice (i, j)
            é a contagem da célula localizada na i-ésima linha e j-ésima coluna da grade.
            O índice (0, 0) é a célula no canto esquerdo inferior.
        '''
        coords = self.adjust_shape(coords, arr_name="coords")

        count_grid = np.zeros((coords.shape[0], *self.shape), dtype=int)
        for idx, coords_i in enumerate(coords):
            unique_coords, count = np.unique(coords_i, axis=0, return_counts=True)
            count_grid[idx, unique_coords[:, 0], unique_coords[:, 1]] = count 

        count_grid = np.transpose(count_grid, axes=(0, 2, 1))

        return self.simplify_shape(count_grid)

    def sum_by_cell(self, values: np.array, coords: np.array, zero_value=0):
        '''
        Soma dos valores que estão na mesma célula (possuem a mesma coordenada) da grade. 
        Cada elemento em `values` possui uma coordenada na grade associada em `coords`.

        Parâmetros:
        -----------
        values:
            Array com N (número de pontos) elementos, que são os valores associados a cada coordenada.
            O tipo dos elementos pode ser outro array, nesse caso values iria ser um array multidimensional,
            ou algum tipo definido pelo usuário, nesse caso o tipo precisa ter definido `__add__()` e
            é necessário passar o elemento nulo em `zero_value`,

        coords:
            Coordenadas na grade que cada elemento em `values` possui.
            
        Retorno:
        --------
        values_sum: ndarray
            Array com a soma dos valores que estão na mesma célula. 
            Seu shape é (N_l, N_c, [shape dos elementos em `values`]), em que N_l é o número de linhas 
            da grade e N_c o número de colunas.
        '''
        if len(coords.shape) == 2:
            coords = self.adjust_shape(coords, arr_name="coords")
            order = len(values.shape)
            values = self.adjust_shape(values, expected_order=order)

        v_shape = (values.shape[0], *reversed(self.shape[:2]), *self.shape[2:], *values.shape[2:])
        values_sum = np.full(v_shape, fill_value=zero_value, dtype=values.dtype)

        layer_ids = list(range(coords.shape[0]))
        for idx in range(coords.shape[1]):
            values_sum[layer_ids, coords[:, idx, 1], coords[:, idx, 0]] += values[:, idx]

        # values_sum = np.zeros((values.shape[1], *reversed(self.shape[:2]), *self.shape[2:]), dtype=float)
        # for idx, coord in enumerate(coords):
        #     values_sum[:, coord[1], coord[0]] += values[idx]

        return self.simplify_shape(values_sum)

    def mean_by_cell(self, values: np.array, coords: np.array, count: np.array=None):
        '''
        Mesma função de `self.sum_by_cell`, mas divide o resultado pela
        contagem de pontos em cada célula, assim realizando a média por célula.
        '''
        values_mean = self.sum_by_cell(values, coords)
        
        if count is None:
            count = self.count(coords)

        non_zero_mask = count > 0

        if len(coords.shape) == 3:
            num_new_axis = len(values.shape) - 2
        else:
            num_new_axis = len(values.shape) - 1

        values_mean[non_zero_mask] /= count[non_zero_mask].reshape(-1, *[1 for _ in range(num_new_axis)])
        return values_mean

    def intersect_circle_mask(self, radius, center=(0, 0)):
        '''
        Máscara das células que não intersectam o círculo de
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

    def plot_grid(self, ax: Axes, adjust_lims=True):
        x1 = self.dim_cell_center[0] - self.dim_cell_size[0]/2
        y1 = self.dim_cell_center[1] - self.dim_cell_size[1]/2

        max_x = x1[-1] + self.dim_cell_size[0][-1]
        max_y = y1[-1] + self.dim_cell_size[1][-1]

        lines = []
        for x in x1:
            lines.append([(x, y1[0]), (x, max_y)])
        lines.append([(max_x, y1[0]), (max_x, max_y)])
        for y in y1:
            lines.append([(x1[0], y), (max_x, y)])
        lines.append([(x1[0], max_y), (max_x, max_y)])
        
        if adjust_lims:
            offset = 0.3
            ax.set_xlim(
                self.dim_cell_center[0][0] - self.dim_cell_size[0][0]/2 * (1 + offset),
                self.dim_cell_center[0][-1] + self.dim_cell_size[0][-1]/2 * (1 + offset),
            )
            ax.set_ylim(
                self.dim_cell_center[1][0] - self.dim_cell_size[1][0]/2 * (1 + offset),
                self.dim_cell_center[1][-1] + self.dim_cell_size[1][-1]/2 * (1 + offset),
            )

        ax.add_collection(LineCollection(lines, color="black"))

    def plot_center(self, ax: Axes):
        ax.scatter(self.meshgrid[0], self.meshgrid[1], c="black")
    
    def plot_corners(self, ax: Axes):
        x1 = self.meshgrid[0] + self.dim_cell_size[0]/2
        x2 = self.meshgrid[0] - self.dim_cell_size[0]/2
        
        y1 = (self.meshgrid[1] + self.dim_cell_size[1].reshape(-1, 1)/2)
        y2 = (self.meshgrid[1] - self.dim_cell_size[1].reshape(-1, 1)/2)
        
        ax.scatter(x1, y1, c="black")
        ax.scatter(x1, y2, c="black")
        ax.scatter(x2, y1, c="black")
        ax.scatter(x2, y2, c="black")

class RegularGrid(RetangularGrid):
    def __init__(self, length: float, height: float, num_cols: int, num_rows: int, center=(0, 0)) -> None:
        "Grade retangular para uma retângulo centrado em `center`, com lados `length`x`height`."
        self.center = center
        self.length = length
        self.height = height
        self.num_cols = num_cols
        self.num_rows = num_rows
        self.center = center

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

    def coords(self, points: np.ndarray, check_out_of_bounds=True):
        '''
        Calcula as coordenadas dos pontos em `points` na grade.

        Parâmetros:
        -----------
        points:
            Array com os pontos, cujo shape pos ser:
                * (N, 2): 
                    N é o número de pontos e 2 vem das duas dimensões da grade 
                    (0 para o eixo x e 1 para o eixo y).

                * (M, N, 2):
                    Essencialmente uma lista de M arrays com N pontos.
        
        Retorno:
        --------
        coords: ndarray
            Array com o mesmo shape de `points` em que o i-ésimo elemento é a coordenada do 
            i-ésimo ponto na grade. O segundo índice do shape indica a dimensão da coordenada:
            
                coords[i, 0] -> Coordenada no eixo x (Coluna) \n
                coords[i, 1] -> Coordenada no eixo y (Linha)
            
            A célula da grade que está no canto esquerdo inferior possui coordenada (0, 0).
            Se `points` tem shape (M, N, 2), então o exemplo acima fica `coords[m, i, 0]`.
        '''
        num_indices = len(points.shape) 
        if num_indices == 2:
            points = points.reshape(1, *points.shape)
        elif num_indices != 3:
            raise Exception(f"`len(points.shape)` é {len(points.shape)}, mas deveria ser 2 ou 3.")

        x = points[:, :, 0] - self.center[0] + self.length/2
        y = points[:, :, 1] - self.center[1] + self.height/2

        col_pos = np.floor(x / self.cell_size[0]).astype(int)
        row_pos = np.floor(y / self.cell_size[1]).astype(int)

        if check_out_of_bounds:
            col_pos[col_pos >= self.shape[0]] = self.shape[0]
            row_pos[row_pos >= self.shape[1]] = self.shape[1]
            col_pos[col_pos < 0] = -1
            row_pos[row_pos < 0] = -1

        coords = np.empty(points.shape, int)

        coords[:, :, 0] = col_pos
        coords[:, :, 1] = row_pos

        if coords.shape[0] == 1:
            coords = coords.reshape(*coords.shape[1:])

        return coords

    def save_configs(self, path):
        with open(path, "w") as f:
            yaml.dump({
                "length": self.length, "height": self.height,
                "num_cols": self.num_cols, "num_rows": self.num_rows,
                "center": self.center,
            }, f)

    @classmethod
    def load(cls, path):
        with open(path, "r") as f:
            configs = yaml.unsafe_load(f)
        return cls(**configs)

def pos_to_scatter(pos: np.ndarray):
    '''
    Dado um array que representa polígonos com shape (N, P, D) em que

    N: Número de polígonos
    P: Número de pontos dos polígonos
    D: Número de dimensões dos pontos

    Retorna todos os pontos organizados no shape (D, N*P). 
    '''
    return pos.reshape(pos.shape[0] * pos.shape[1], pos.shape[2]).T

def voro_edges(pos: np.ndarray):
    '''Ids que formam os links calculados a partir do diagrama de Voronoi.
    
    Parâmetros:
        pos:
            Array com as posições. Seu shape deve ser 
                (N, 2) 
            em que N é o número de pontos. Descrição:
                pos[i, 0] -> Posição x do i-ésimo ponto
                pos[i, 1] -> Posição y do i-ésimo ponto
    
    Retorno:
        ids_edges:
            Ids dos pontos que formam um link. Seu shape é (M, 2), em que M é o 
            número de links. Cada link é uma conexão entre dois
            pontos em `pos`

            ids_edges[i, 0] -> Id do ponto em `pos` que inicia o i-ésimo link 
            ids_edges[i, 1] -> Id do ponto em `pos` que finaliza o i-ésimo link 

            Logo o vetor que representa o i-ésimo link é

                id1, id2 = ids_edges[i]
                link_i = pos[id2] - pos[id1]
    '''
    vor = Voronoi(pos) # create Voronoi diagram
    points_adj = vor.ridge_points
    edges = np.sort(points_adj, axis=-1)
    ids_edges = np.array(sorted((a,b) for a,b in edges.astype(int)))
    return ids_edges

def calc_edges(cm, ring_diameter, k=1, return_dist=False):
    '''Ids que formam os links nos pontos em `cm`, de acordo
    com o diagrama de Voronoi, com a condição de que o comprimento do
    link seja menor do que `rin_diameter*k`.
    O shape de cm deve ser (N, 2), em que N é o número de pontos.
    '''
    edges = voro_edges(cm)
    edge_dist = cm[edges[:,0]] - cm[edges[:,1]]
    edge_dist = np.sqrt(np.square(edge_dist).sum(axis=1))
    
    mask = edge_dist<ring_diameter*k
    edges = edges[mask]
    if return_dist:
        return edges, edge_dist[mask]
    else:
        return edges

def neighbors_all(links, n):
    neighs = [[] for _ in range(n)]
    for l in links:
        neighs[l[0]].append(l[1])
        neighs[l[1]].append(l[0])
    return neighs

def links_ids(links, n):
    ids = [[] for _ in range(n)]
    for i, l in enumerate(links):
        ids[l[0]].append(i)
        ids[l[1]].append(i)
    return ids

def neighbors_list(links, pos_list):
    neighs = []
    for pid in pos_list:
        neighs_ids_1 = links[links[:, 0] == pid][:,1]
        neighs_ids_2 = links[links[:, 1] == pid][:,0]
        neighs_ids = np.concatenate([neighs_ids_1, neighs_ids_2])
        neighs.append(neighs_ids)
    return neighs

def particle_grid_shape(space_cfg, max_dist, frac=0.6):
    raise Exception("Use o método em SpaceCfg para isso.")

def rings_grid_shape(space_cfg, radius, frac=0.5):
    raise Exception("Use o método em SpaceCfg para isso.")


def roll_segmented_cmap(cmap, amount):
    '''
    Translada o `cmap`  por `amount` unidades, considerando 
    que as bordas são periódicas.
    '''
    channel_to_id = {
        "red": 0, "green": 1, "blue": 2,
    }

    segmentdata = {}
    for channel in ["red", "green", "blue"]:
        segmentdata[channel] = [list(row) for row in cmap._segmentdata[channel]]

    for channel in ["red", "green", "blue"]:
        color_data = segmentdata[channel] 
        for row in color_data:
            row[0] += amount
        
        add_idx = None
        for idx, value in enumerate(color_data):
            if value[0] > 1:
                add_idx = idx
                break

        color_value = cmap(amount)[channel_to_id[channel]]
        color_data.insert(add_idx, [1, color_value, color_value])
        color_data.insert(add_idx+1, [0, color_value, color_value])

        for value in color_data:
            if value[0] > 1:
                value[0] -= 1
        
        color_values = [row[0] for row in color_data]
        segmentdata[channel] = [row for _, row in sorted(zip(color_values, color_data))]

    from matplotlib.colors import LinearSegmentedColormap        
    return LinearSegmentedColormap("rolled", segmentdata)


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    # print(np.floor(np.array([[-0.1,2,3]])))
    # exit()

    grid = RegularGrid(1, 1, 5, 4)

    points = (np.random.random((5, 2)) - 0.5)
    # values = (np.random.random((2, 5, 2, 3)) - 0.5)
    values = (np.random.random((5, 2)) - 0.5)
    
    class CustomValue:
        def __init__(self, x) -> None:
            self.x = x

        # def __iadd__(self, other):
        #     self.x += other.x
        #     return self

        def __add__(self, other):
            return CustomValue(self.x + other.x)

        def __str__(self):
            return str(self.x)
        
        def __repr__(self):
            return f"{self.x}"

    # values = np.empty(points.shape[:2], dtype=CustomValue)
    # letters = "abcdefghijklmnopqrtuvwxyz"
    # for i in range(points.shape[1]):
    #     values[0][i] = CustomValue(letters[i])
    #     values[1][i] = CustomValue(letters[i])

    c = grid.coords(points)

    layer = 0
    c[2] = [0, 3]
    c[4] = [0, 3]


    mean_values = grid.mean_by_cell(values, c)

    a1 = mean_values[3, 0]
    a2 = (values[2] + values[4])/2

    print(c)

    print(a1 == a2)
    print(a1)
    print(a2)


    # ax = plt.gca()
    # ax.set_xlim(-0.7, 0.7)
    # ax.set_ylim(-0.7, 0.7)
    # grid.plot_grid(ax)
    # ax.scatter(*points[0].T, c="red")
    # ax.scatter(*points[1].T, c="green")
    # plt.show()

    exit()

    # print(points)
    # print(c)
    # print(grid.remove_out_of_bounds(c))

    print(grid.count(c))
    a = grid.sum_by_cell(points, c, zero_value=CustomValue(0))
    print(a.shape)

    # ax = plt.gca()
    # ax.set_xlim(-0.7, 0.7)
    # ax.set_ylim(-0.7, 0.7)
    # grid.plot_grid(ax)
    # ax.scatter(*points.T)

    # plt.show()

    # points1 = np.array([
    #     [-0.45, -0.3],
    #     [-0.35, -0.3],
    #     [-0.45, -0.2],
    # ])
    # points2 = points1 + 0.5
    # points_t = np.array([points1, points2])
    
    # plt.scatter(*points1.T, marker="x")
    # plt.scatter(*points2.T, marker="x")

    # ct = grid.coords(points_t)
    # c1, c2 = grid.coords(points1), grid.coords(points2)

    # print(np.all(c1 == ct[0]))
    # print(np.all(c2 == ct[1]))

    # # cell_size_mg = np.meshgrid

    # x1 = grid.meshgrid[0] + grid.dim_cell_size[0]/2
    # x2 = grid.meshgrid[0] - grid.dim_cell_size[0]/2
    
    # y1 = (grid.meshgrid[1] + grid.dim_cell_size[1].reshape(-1, 1)/2)
    # y2 = (grid.meshgrid[1] - grid.dim_cell_size[1].reshape(-1, 1)/2)

    # center = (0, 0)
    # r = 0.2

    # ax = plt.gca()
    # ax.add_patch(Circle(center, r, fill=False))
    
    # mask = grid.intersect_circle_mask(r, center)
    # x1 = x1[mask]
    # x2 = x2[mask]
    # y1 = y1[mask]
    # y2 = y2[mask]
    
    # print(mask.shape)
    
    # # plt.scatter(x1, y1, c="red")
    # # plt.scatter(x1, y2, c="blue")
    # # plt.scatter(x2, y1, c="green")
    # # plt.scatter(x2, y2, c="orange")
    # grid.plot_grid(ax)
    # grid.plot_corners(ax)

    # plt.scatter(grid.meshgrid[0][mask], grid.meshgrid[1][mask], c="black")
    
    # plt.show()
