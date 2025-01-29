'''
Utilidades para calcular quantidades do sistema de anéis.
'''
import numpy as np

from scipy import interpolate
from scipy.ndimage import gaussian_filter

from phystem.systems.ring.configs import *
from . import utils
from .utils import RegularGrid

def get_cm(rings: np.ndarray):
    '''
    Retorna os centros de massa dos anéis em `rings`.

    Parâmetros:
        rings:
            Array com as posições das partículas que compõem os anéis.
            Seu shape dever ser :
                
                (N_a, N_p, 2)
            
            Onde:
              
                N_a: número de anéis
                N_p: número de partículas
                
            O último elemento do shape é a dimensão, 0 para o eixo x e 1 para o eixo y. 
            Então, rings[i, j, 1] é a coordenada no eixo y da j-ésima partícula do i-ésimo anel.     
    
    Retorno:
        Array com shape (N_a, 2). Por exemplo, o elemento com índice [i, 0] é a coordenada x
        do centro de massa do i-ésimo anel.
    '''
    return rings.sum(axis=1)/rings.shape[1]

def get_vel_cm(vel: np.ndarray):
    '''
    Velocidade do centro de massa dos anéis dados a velocidade das partículas `vel`.
    
    Parâmetros:
        vel:
            Array com shape ([número de anéis], [numero de partículas], 2)
            contendo as velocidades.
    
    Retorno:
        Array com shape ([número de anéis, 2]).
    '''
    return vel.sum(axis=1)/vel.shape[1]

def get_vel_cm_from_pos(pos1, uid1, pos2, uid2, dt):
    '''
    Velocidade do centro de massa dado as posições das partículas
    no tempo t (`pos1`) e no tempo t+dt (`pos2`).

    Return
    ------
    vel_cm: np.array
        Velocidades do centro de massa.
    pos1, pos2: np.array
        Posições organizadas para coincidirem entre os frames, ou seja,
        pos1[i] e pos2[i] se referem ao mesmo anel.
    '''
    pos1, pos2 = utils.same_rings(pos1, uid1, pos2, uid2)
    vel = (pos2 - pos1) / dt
    vel_cm = get_vel_cm(vel)
    return vel_cm, pos1, pos2

def get_vel_angle(vel):
    '''
    Direção das velocidades em `vel`. `vel` é um array
    (N, 2).
    '''
    return np.arctan2(vel[:, 1], vel[:, 0])

def get_speed(vel_grid: np.array):
    return np.sqrt((np.square(vel_grid)).sum(axis=0))

def get_dist_pb(pos1: np.array, pos2: np.array, height, length):
    '''
    Diferença entre `pos1` e `pos2` considerando bordas periódicas.
    Os arrays devem ter o shape ([número de pontos] , 2)
    '''
    diff = pos2 - pos1

    x_filter = np.abs(diff[:,0]) > length/2 
    y_filter = np.abs(diff[:,1]) > height/2 
    
    diff[x_filter, 0] -= np.copysign(length, diff[x_filter, 0]) 
    diff[y_filter, 1] -= np.copysign(height, diff[y_filter, 1]) 
    return diff

def get_area(rings: np.array):
    '''
    Retorna as áreas dos anéis em `rings`.
    Ver a doc de `get_cm` para informações sobre o tipo de `rings`.
    '''
    num_rings = rings.shape[0]
    areas = np.empty(num_rings, dtype=float)

    for ring_i in range(num_rings):
        ring_pos = rings[ring_i]
        cross_prod = np.cross(ring_pos[:-1], ring_pos[1:])
        areas[ring_i] = cross_prod.sum()
        
        areas[ring_i] += np.cross(ring_pos[-1], ring_pos[0])
    
    areas /= 2
    return areas

def get_in_obstacle_mask(grid: utils.RegularGrid, stokes_cfg: StokesCfg):
    "Determines whether points in a grid are within a circular obstacle."
    x, y = grid.meshgrid[0] - stokes_cfg.obstacle_x, grid.meshgrid[1] - stokes_cfg.obstacle_y
    return x**2 + y**2 < stokes_cfg.obstacle_r**2

def interpolate_obstacle(data, grid: utils.RegularGrid, stokes_cfg: StokesCfg):
    '''Interpola os dados do campo escalar `data` na região do obstáculo.'''
    in_obstacle_mask = get_in_obstacle_mask(grid, stokes_cfg)
    # in_obstacle_mask = grid.circle_mask(
    #     stokes_cfg.obstacle_r, 
    #     (stokes_cfg.obstacle_x, stokes_cfg.obstacle_y), 
    #     mode="inside"
    # )

    valid_points = np.array([
        grid.meshgrid[0][~in_obstacle_mask],
        grid.meshgrid[1][~in_obstacle_mask],
    ]).T
    
    inter_points = np.array([
        grid.meshgrid[0][in_obstacle_mask],
        grid.meshgrid[1][in_obstacle_mask],
    ]).T

    values = data[~in_obstacle_mask]

    new_values = interpolate.griddata(valid_points, values, inter_points, method="cubic")

    data[in_obstacle_mask] = new_values

def smooth_data(data, grid:utils.RegularGrid, new_cell_size, filter_sigma, stokes_cfg: StokesCfg, skip_start_cols=0, skip_end_cols=0):
    '''
    Dado o campo escalar `data` na grade `grid`, faz o seguinte:

    - Interpola o campo para as células dentro do obstáculo.
    - Aplica um filtro gaussiano com sigma igual a `filter_sigma`.
    - Interpola os dados para uma nova grade com células de lado `new_cell_size`.
    
    Retorno:
    --------
    smooth_data:
        Campo suavizado e interpolado para uma grade mais detalhada.
    
    bigger_grid:
        Grade na qual os dados foram interpolados.
    '''
    start_id = skip_start_cols
    end_id = skip_end_cols
    data = np.copy(data)

    edge_end_id = end_id
    if end_id == 0:
        edge_end_id = grid.shape[0] + 1
        end_id = grid.shape[0]

    data = data[:, start_id:end_id]
    grid = utils.RegularGrid.from_edges((
        grid.edges[0][start_id:edge_end_id], grid.edges[1]
    ))

    interpolate_obstacle(data, grid, stokes_cfg)

    num_cols = round(grid.length / new_cell_size)
    num_rows = round(grid.height / new_cell_size)

    bigger_grid = utils.RegularGrid(
        grid.length, grid.height, num_cols, num_rows, grid.center
    )

    dx, dy = grid.cell_size

    sigma_x = filter_sigma / dx
    sigma_y = filter_sigma / dy

    data_smooth = gaussian_filter(data, sigma=(sigma_y, sigma_x)) 

    grid_points = np.vstack([grid.meshgrid[0].ravel(), grid.meshgrid[1].ravel()]).T
    data_smooth = interpolate.griddata(grid_points, data_smooth.ravel(), (bigger_grid.meshgrid[0], bigger_grid.meshgrid[1]), method="cubic")

    # Remove NaN
    nan_mask = np.isnan(data_smooth)
    bigger_grid_points = np.vstack([bigger_grid.meshgrid[0][~nan_mask].ravel(), bigger_grid.meshgrid[1][~nan_mask].ravel()]).T
    data_nearest = interpolate.griddata(bigger_grid_points, data_smooth[~nan_mask].ravel(), (bigger_grid.meshgrid[0], bigger_grid.meshgrid[1]), method="nearest")
    data_smooth = np.where(nan_mask, data_nearest, data_smooth)

    return data_smooth, bigger_grid

class Density:
    def __init__(self, grid: RegularGrid):
        '''
        Calculador de densidade em cada célula da grade `grid`.
        A densidade é a contagem de anéis na célula em questão.
        '''
        self.grid = grid

    def get_from_cm(self, cms):
        '''
        Calcula a densidade dado o centro de massa dos anéis.
        
        Retorno:
            Array com shape (num_cols, num_rows), em que cada elemento
            representa uma célula da grade. O índice [0, 0] representa o canto
            inferior esquerdo. 
        '''
        coords = self.grid.coords(cms)
        count = self.grid.count(coords, remove_out_of_bounds=True, simplify_shape=True)
        return count / self.grid.cell_area

    def get_from_pos(self, pos):
        '''
        Calcula a densidade pelas posições dos anéis em `pos` (Veja a documentação
        de `get_cm` para informações do formato de `pos`).

        Retorno:
            Consulte a documentação de `.get_from_cm()`.
        '''
        self.get_from_cm(get_cm(pos))
