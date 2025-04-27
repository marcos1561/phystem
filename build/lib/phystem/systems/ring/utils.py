from scipy.spatial import Voronoi
from scipy.optimize import fsolve
import numpy as np
import yaml
from math import atan, sin, cos, pi
from pathlib import Path
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection

from phystem.data_utils.grids import RegularGrid, RetangularGrid

def ring_radius(diameter, k_a, k_m, a0, spring_r, num_particles):
    '''
    Raio de equilíbrio do anel, indo do centro até a borda externa das partículas. 
    É calculado assumindo sua área de equilíbrio.
    '''
    # return p_diameter / (2 * (1 - cos(2*pi/(num_particles))))**.5
    area_eq = equilibrium_area(k_a, k_m, a0, spring_r, num_particles)
    particle_radius = (2 * area_eq / (num_particles * sin(2 * pi / num_particles)))**.5
    return particle_radius + diameter/2

def second_order_neighbors_dist(num_particles, lo):
    '''
    Dado um anel com `num_particles` partículas, cujas molas possuem
    comprimento `lo`, retorna a distância entre partículas que estão
    separadas por outra partícula. É assumido que o anel está no formato
    de um polígono regular.
    '''
    theta = np.pi * (1- 2/num_particles)
    return lo * (2*(1-np.cos(theta)))**.5    

def equilibrium_spring_l(num_particles, area0):
    '''
    Retorna o comprimento que as molas devem ter para que a área de equilíbrio
    de um anel com `num_particles`, apenas considerando as molas, seja a mesma
    de `area_o`. 
    '''
    theta = np.pi * 2 / num_particles
    return 2 * (area0 / num_particles * (1 - np.cos(theta)) / np.sin(theta))**.5

def equilibrium_p0(num_particles):
    '''
    Retorna o p0 em que `area0` é igual a área de equilíbrio
    apenas considerando as molas.
    '''
    theta = 2 * np.pi / num_particles
    return 2 * (num_particles * (1 - np.cos(theta))/np.sin(theta))**.5

def invasion_equilibrium_config(k_r, k_m, k_a, lo, ro, area0, relative_area_eq, vo, mu):
    '''
    Retorna a configuração de equilíbrio no pior cenário de invasão entre anéis. 
    
    Retorno:
    -------
    r: np.ndarray
        Array com a solução do equilíbrio:
        r[0]: Metade do ângulo que a partícula invasora faz com as partículas
            do anel sendo invadido.
        r[1]: Distância entre as partículas do anel sendo invadido.

    func(r): list
        Valor da função avaliada na solução encontrada. Se o módulo da soma
        desses valores não for perto de zero, significa que a solução não foi
        encontrada ou não existe.
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

def equilibrium_relative_area(k_a, k_m, a0, spring_r, num_particles):
    '''
    Retorna a área de equilíbrio em relação a `a0` (a_eq / a0).
    Essa área é apenas a área do polígono formado pelos centros das
    partículas do anel.
    '''
    p0_lim = equilibrium_p0(num_particles)
    a0_lim = (num_particles * spring_r / p0_lim)**2 

    if a0 < a0_lim:
        return 1

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

    return fsolve(func, 0.5)[0]

def equilibrium_area(k_a, k_m, a0, spring_r, num_particles):
    "Área de equilíbrio do polígono formado pelos centros das partículas do anel."
    return equilibrium_relative_area(k_a, k_m, a0, spring_r, num_particles) * a0

def particles_area(n, spring_r, diameter):
    '''
    Contribuição das partículas na área dos anéis.
    A área de um anel é a área do polígono formado pelos centros de suas partículas (A_p),
    mais a área das partículas que está fora desse polígono (A_c), essa
    função retorna A_c.
    '''
    root_term = (diameter**2 - spring_r**2)**.5
    t = np.pi/2 - atan(spring_r/root_term)
    area_intersect = 1/4 * (diameter**2 * t - spring_r * root_term)

    return n * np.pi / 4 * diameter**2 * (1 - (n-2)/(2*n)) - n * area_intersect

def max_k_adh(adh_size, dt, k_a, area0, lo, relative_area, mu, vo, x=1):
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

def same_rings(pos1, ids1, pos2, ids2, return_common_ids=False):
    '''
    Dados os array `pos1` e `pos2` cujos elementos possuem índices
    em `ids1` e `ids2`, respectivamente, retorna as posições 
    ordenadas pelos mesmos ids, ou seja, o i-ésimo elemento
    em ambos os arrays se referem ao mesmo id.

    Retorno:
    --------
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

def ring_spawn_pos(k_a, k_m, a0, spring_r, num_particles) -> np.ndarray:
    '''
    Posições de um anel centrado em x=(0, 0) com área igual
    a sua área de equilíbrio no formato de um polígono regular.

    Retorno:
    --------
    pos: ndarray com shape (num_particles, 2)
        Posições das partículas do anel.
    '''
    area = equilibrium_area(k_a, k_m, a0, spring_r, num_particles)
    theta = 2 * np.pi / num_particles
    p_radius = (2 * area / (num_particles * np.sin(theta)))**0.5
    
    angles = np.arange(0, np.pi*2, np.pi*2/num_particles)
    ring_pos = np.array([np.cos(angles), np.sin(angles)]) * p_radius
    return ring_pos.T

def time_to_num_dt(time, dt):
    '''
    Dado um intervalo de tempo `time`, retorna o menor `num_dt` tal que
    `num_dt * dt >= time` 
    '''
    num_dt = time // dt
    if dt * num_dt < time:
        num_dt += 1

    return int(num_dt)

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
    """
    Generate a list of neighbors for each node in a graph.
    Args:
        links (list of tuple): A list of tuples where each tuple represents a link between two nodes.
        n (int): The total number of nodes in the graph.
    Returns:
        list of list: A list where the i-th element is a list of neighbors for the i-th node.
    """
    neighs = [[] for _ in range(n)]
    for l in links:
        neighs[l[0]].append(l[1])
        neighs[l[1]].append(l[0])
    return neighs

def links_ids(links, n):
    """
    Generate a list of lists containing the indices of links connected to each node.
    Args:
        links (list of tuples): A list of tuples where each tuple represents a link between two nodes.
        n (int): The number of nodes.
    Returns:
        list of lists: A list where each element is a list of indices of links connected to the corresponding node.
    """
    ids = [[] for _ in range(n)]
    for i, l in enumerate(links):
        ids[l[0]].append(i)
        ids[l[1]].append(i)
    return ids

def neighbors_list(links, pos_list):
    """
    Generate a list of neighbors for each position in pos_list based on the given links.
    Parameters:
        links (numpy.ndarray): A 2D array where each row represents a link between two positions.
        pos_list (list): A list of positions for which neighbors need to be found.
    Returns:
        list: A list of numpy arrays, where each array contains the neighbors of the corresponding position in pos_list.
    """
    neighs = []
    for pid in pos_list:
        neighs_ids_1 = links[links[:, 0] == pid][:,1]
        neighs_ids_2 = links[links[:, 1] == pid][:,0]
        neighs_ids = np.concatenate([neighs_ids_1, neighs_ids_2])
        neighs.append(neighs_ids)
    return neighs

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

#
# Deprecated
# 
def particle_grid_shape(space_cfg, max_dist, frac=0.6):
    raise Exception("Use o método em SpaceCfg para isso.")

def rings_grid_shape(space_cfg, radius, frac=0.5):
    raise Exception("Use o método em SpaceCfg para isso.")

def num_rings_in_rect(ring_diameter: float, space_cfg):
    raise Exception("Use o método em SpaceCfg para isso.")


if __name__ == "__main__":
    print(time_to_num_dt(0.01 * 10.1, 0.01))
    
