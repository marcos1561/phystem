from typing import Any
import numpy as np

from phystem.core.creators import CreatorCore
from phystem.systems.ring import utils
from phystem.systems.ring.configs.space_cfgs import SpaceCfg
from phystem.systems.ring.configs.dynamic_cfgs import RingCfg

class InitData:
    def __init__(self, pos: np.ndarray, self_prop_angle: np.ndarray, uids: np.ndarray=None) -> None:
        '''
        Dados da configuração inicial.

        Parameters:
        -----------
            pos: ndarray (num_rings, num_particles, 2)
                    Posição inicial das partículas em cada anel.
                
            self_prop_angle: ndarray (num_rings)
                Ângulo inicial da direção da velocidade auto propulsora em cada anel.

            uids:
                Ids únicos de cada anel.
        '''
        self.pos = pos
        self.self_prop_angle = self_prop_angle
        self.uids = uids

    def get_data(self):
        return {
            "pos": self.pos,
            "self_prop_angle": self.self_prop_angle,
        }

def get_base_ring(num_particles, particle_diameter):
    ring_radius = utils.ring_radius(particle_diameter, num_particles)
    angles = np.arange(0, np.pi*2, np.pi*2/num_particles)
    ring_pos = np.array([np.cos(angles), np.sin(angles)]) * ring_radius
    return ring_pos.T


class CreatorCfg:
    def __init__(self, num_rings: int,  num_particles: int, r: list[float], angle: list[float],
        center: list[list[float]]) -> None:
        '''
        Cria anéis com `num_particles` partículas em formato circular com raio `r`, posições do 
        centro de massa em `center` e polarizações em `angle`. 

        Parameters:
        -----------
            num_rings:
                Número de anéis.
            
            num_particles:
                Número de partículas no anel.
        
            r:
                Raio do anel.
            
            angle:
                Ângulo inicial da velocidade auto propulsora.

            center:
                Centro da posição inicial do anel.
        '''
        self.num_rings = num_rings
        self.num_particles = num_particles
    
        self.r = self.process_scalar_input(r)
        self.angle = self.process_scalar_input(angle)
        
        self.center = center

    @classmethod
    def empty(cls):
        '''
        Configurações de uma condição inicial nula. Útil para o
        fluxo de stokes.
        '''
        return cls(
            num_rings=0, num_particles=None, 
            r=[], angle=[], center=[],
        )

    def process_scalar_input(self, input):
        try:
            _ = iter(input)
        except TypeError as e:
            return [input] * self.num_rings
        else:
            return input

    def set(self, other):
        raise Exception("Não deveria estar utilizando isso.")
        self.r = other.r
        self.num_rings = other.num_rings
        self.num_particles = other.num_particles
        self.vo = other.vo
        self.angle = other.angle
        self.center = other.center

class Creator(CreatorCore):
    def __init__(self, cfg: CreatorCfg, rng_seed: int=None) -> None:
        "Ver doc de `CreatorCfg`."
        super().__init__(rng_seed)

        self.num_rings = cfg.num_rings
        self.num_particles = cfg.num_particles
        self.r = cfg.r
        self.angle = cfg.angle
        self.center = cfg.center

    def create(self) -> InitData:
        '''
        Cria a configuração inicial.
        
        Return:
        -------
        InitData:
            Dados da configuração inicial
        '''
        pos = []
        self_prop_angle = []

        for ring_id in range(self.num_rings):
            ring_pos_angles = np.arange(0, np.pi*2, np.pi*2/self.num_particles)
            
            if ring_pos_angles.size != self.num_particles:
                raise Exception(f"'pos_angle' tem tamanho '{ring_pos_angles.size}', mas deveria ter '{self.num_particles}'")

            ring_pos = np.array([np.cos(ring_pos_angles), np.sin(ring_pos_angles)]) * self.r[ring_id]

            ring_pos[0] += self.center[ring_id][0]
            ring_pos[1] += self.center[ring_id][1]

            pos.append(ring_pos.T)
            self_prop_angle.append(self.angle[ring_id])

        return InitData(np.array(pos), np.array(self_prop_angle))


class RectangularGridCfg:
    def __init__(self, num_x, num_y, space_x, space_y, dynamic_cfg: RingCfg, ring_radius_k=1) -> None:
        '''
        Cria anéis em grade retangular (centrada na origem) com `num_x` anéis no eixo x e `num_y` no eixo y.
        O espaçamento entre anéis vizinhos no eixo x é `space_x` e no eixo y `space_y`.
        A direção das polarizações é aleatória com distribuição uniforme entre [0, 2*pi).
        
        Parameters
        -----------
        ring_radius_k:
            Constante que multiplica o raio do anel. Dessa forma, é possível iniciar os anéis comprimidos (< 0)
            ou expandidos (> 1).
        '''
        self.num_x = num_x 
        self.num_y = num_y 
        self.space_x = space_x 
        self.space_y = space_y 
        self.base_ring_pos = dynamic_cfg.ring_spawn_pos()
        self.ring_radius = dynamic_cfg.get_ring_radius()
        self.ring_radius_k = ring_radius_k

    @classmethod
    def from_relative_density(cls, num_x, num_y, rel_density, dynamic_cfg: RingCfg, ring_radius_k=1):
        '''
        Configurações que possuem a densidade relativa setada em `rel_density` utilizando
        o mesmo espaçamento em ambos os eixos, ou seja, `space_x = space_y`.

        Sendo d a densidade (Nº de anéis por un. de área), temos que a densidade relativa é

        d_r = d/d_eq - 1

        Em que d_eq é a densidade de equilíbrio (1/área de equilíbrio dos anéis).
        '''
        rho_eq = 1 / dynamic_cfg.get_equilibrium_area()
        ring_d = 2 * dynamic_cfg.get_ring_radius()
        rho = (rel_density + 1) * rho_eq
        space = (1/rho)**.5 - ring_d
        return cls(num_x, num_y, space, space, dynamic_cfg, ring_radius_k)

    def get_space_cfg(self):
        ring_d = 2 * self.ring_radius
        height = self.num_y * (ring_d + self.space_y)
        length = self.num_x * (ring_d + self.space_x)
        return SpaceCfg(height, length)

class RectangularGridCreator(CreatorCore):
    def __init__(self, cfg: RectangularGridCfg, rng_seed: int=None) -> None:
        super().__init__(rng_seed)
        self.num_x = cfg.num_x
        self.num_y = cfg.num_y
        self.space_x = cfg.space_x
        self.space_y = cfg.space_y    
        self.base_ring_pos = cfg.base_ring_pos
        self.ring_radius = cfg.ring_radius
        self.ring_radius_k = cfg.ring_radius_k
    
    def create(self) -> InitData:
        real_ring_d = 2 * self.ring_radius
        num_rings = self.num_x * self.num_y

        base_pos = self.base_ring_pos * self.ring_radius_k
        pos = []
        for i in range(self.num_x):
            x = (i + 1/2) * (self.space_x + real_ring_d)
            for j in range(self.num_y):
                y = (j + 1/2) * (self.space_y + real_ring_d)
                pos.append(base_pos + [x, y])
        
        height = self.num_y * (real_ring_d + self.space_y)
        width = self.num_x * (real_ring_d + self.space_x)
        central_point = [width/2, height/2]

        pos = np.array(pos) - central_point
        random_angles = np.random.random(num_rings) * 2*np.pi 

        return InitData(pos, random_angles)

class InvaginationCreatorCfg:
    def __init__(self, num_rings: int, height: int, length: int, diameter: float) -> None:
        self.num_rings = num_rings

        self.height = height
        self.length = length
        self.diameter = diameter
        
        self.num_p = None

    @property
    def ring_radius(self):
        from math import pi, sin
        theta = 2*pi/self.num_rings
        return self.diameter*self.length / (2 * sin(theta/2))

class InvaginationCreator(CreatorCore):
    def __init__(self, cfg: InvaginationCreatorCfg, rng_seed: int = None) -> None:
        super().__init__(rng_seed)

        self.num_rings = cfg.num_rings
        self.height = cfg.height
        self.length = cfg.length
        self.diameter = cfg.diameter
        self.num_p = cfg.num_p

    def create(self):
        return self.loop()

        pos = np.zeros((self.num_rings, self.num_p, 2))
        # self_prop_angle = np.zeros((self.num_rings, self.num_p))
        self_prop_angle = np.random.random((self.num_rings, self.num_p)) * 2 * np.pi

        base_pos = np.zeros((self.num_p, 2))
        
        start_id = 0
        end_id = start_id + self.height
        base_pos[start_id:end_id, 0] = 0
        base_pos[start_id:end_id, 1] = np.linspace(1, 0, self.height)
        
        start_id = end_id-1
        end_id = start_id + self.length
        base_pos[start_id:end_id, 0] = np.linspace(0, 1, self.length)
        base_pos[start_id:end_id, 1] = 0
        
        start_id = end_id-1
        end_id = start_id + self.height
        base_pos[start_id:end_id, 0] = 1
        base_pos[start_id:end_id, 1] = np.linspace(0, 1, self.height)
        
        start_id = end_id-1
        end_id = start_id + self.length -1
        base_pos[start_id:end_id, 0] = np.linspace(1, 0, self.length)[:-1]
        base_pos[start_id:end_id, 1] = 1
        
        ring_length = (self.length - 1) * self.diameter
        ring_height = (self.height - 1) * self.diameter
        
        scale_matrix = np.array([[ring_length, 0], [0, ring_height]]) 
        base_pos = scale_matrix.dot(base_pos.T).T

        for i in range(self.num_rings):
            displacement = np.array([
                (ring_length + self.diameter) * i, 
                0, 
            ])

            pos[i] = base_pos + displacement

        center = np.array([self.num_rings * (ring_length + self.diameter) / 2 - self.diameter / 2 ,ring_height/2])
        pos -= center

        return InitData(pos, self_prop_angle)

    def loop(self):
        from scipy import optimize
        from math import cos, sin, floor

        num_rings = self.num_rings
        num_p_int= self.length
        num_p_height = self.height
        d = self.diameter
        
        theta = 2*np.pi/num_rings
        r0 = d*num_p_int / (2 * sin(theta/2))

        def func(r):
            t1 = (r * (cos(theta) - 1) + sin(theta) * d/2)**2
            t2 = (r * sin(theta) - (cos(theta) + 1) * d/2)**2
            c = (num_p_int-1)**2 * d**2 
            return t1 + t2 - c

        r = optimize.fsolve(func, r0)[0]

        rot_matrix = np.array([
            [cos(theta), -sin(theta)],
            [sin(theta), cos(theta)],
        ])

        p1 = np.array([r, d/2])
        p2 = rot_matrix.dot(np.array([r, -d/2]))

        pos_base = []
        for i in range(num_p_int):
            center_i = (p1 - p2)/np.linalg.norm((p1 - p2)) * d/2 * (i*2) + p2
            pos_base.append(center_i)
        
        for i in range(1, num_p_height):
            center_i = p1 + np.array([1, 0]) * i*d
            pos_base.append(center_i)

        left_r_dir = rot_matrix.dot(np.array([1, 0]))
        
        p3 = pos_base[-1]
        p4 = p2 + left_r_dir * (num_p_height -1 ) * d

        outer_l = np.linalg.norm(p3 - p4) - d

        num_p_outer = floor(outer_l/d - 1)

        outer_dir = (p4-p3) / np.linalg.norm(p4-p3)
        for i in range(num_p_outer):
            center_i = p3 + outer_dir * (d/2 + (2*i + 1)*outer_l/num_p_outer/2)
            pos_base.append(center_i)

        for i in range(num_p_height-1):
            center_i = p4 - left_r_dir * i * d
            pos_base.append(center_i)

        pos_base = np.array(pos_base)
        pos = [pos_base]
        for i in range(1, num_rings):
            pos.append(rot_matrix.dot(pos[-1].T).T)

        pos = np.array(pos)
        self_prop_angle = np.random.random((num_rings, pos.shape[1])) * 2 * np.pi

        # import matplotlib.pyplot as plt
        # plt.scatter(*pos.T)
        # plt.show()

        print(pos.shape)
        return InitData(pos, self_prop_angle)


class CreatorRD(CreatorCore):
    def create(self) -> None:
        pass


config_to_creator: dict[Any ,CreatorCore] = {
    CreatorCfg: Creator,
    RectangularGridCfg: RectangularGridCreator,
    InvaginationCreatorCfg: InvaginationCreator,
}    

if __name__ == "__main__":
    num_rings = 1
    num_p = 1
    height = 1
    length = 1
    diameter = 1

    print(Creator(0, 30, [3], [0], [0, 0]).create().pos.shape[0])
    # creator = InvaginationCreator(num_rings, num_p, height, length, diameter)
    # creator.loop()




