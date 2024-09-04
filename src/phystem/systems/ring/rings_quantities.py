import numpy as np
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
    def __init__(self, length, height, num_cols, num_rows, center=(0, 0)):
        '''
        Calculador de densidade dividindo o espaço (definido por `length`, `height` e `center`) em
        uma grade retangular `num_rows` x `num_cols`.
        A densidade é calculada em cada célula da grade, e a medida é a contagem
        de anéis na célula em questão.
        '''
        self.grid = RegularGrid(length, height, num_cols, num_rows, center)

    def get_from_cm(self, cms):
        '''
        Calcula a densidade dado o centro de massa dos anéis.
        
        Retorno:
            Array com shape (num_cols, num_rows), em que cada elemento
            representa uma célula da grade. O índice [0, 0] representa o canto
            superior esquerdo. 
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
