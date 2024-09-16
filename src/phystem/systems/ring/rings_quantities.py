import numpy as np
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
        count = self.grid.count(coords)
        return count

    def get_from_pos(self, pos):
        '''
        Calcula a densidade pelas posições dos anéis em `pos` (Veja a documentação
        de `get_cm` para informações do formato de `pos`).

        Retorno:
            Consulte a documentação de `.get_from_cm()`.
        '''
        self.get_from_cm(get_cm(pos))
