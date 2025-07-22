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
    def __init__(self, num_x, num_y, dynamic_cfg: RingCfg, space_x=0, space_y=0, ring_radius_k=1) -> None:
        '''
        Creates rings in a rectangular grid (centered at the origin) with `num_x` rings along the x-axis and `num_y` along the y-axis.
        The spacing between neighboring rings on the x-axis is `space_x` and on the y-axis is `space_y`.
        The direction of the polarizations is random with a uniform distribution between [0, 2*pi).
        
        Parameters
        -----------
        ring_radius_k:
            Constant that multiplies the ring radius. This allows the rings to be initialized compressed (< 0)
            or expanded (> 1).
        '''
        self.num_x = num_x 
        self.num_y = num_y 
        self.space_x = space_x 
        self.space_y = space_y 
        self.base_ring_pos = dynamic_cfg.ring_spawn_pos()
        self.ring_radius = dynamic_cfg.get_ring_radius()
        self.ring_radius_k = ring_radius_k
        self.particle_radius = dynamic_cfg.diameter / 2
        
        self.real_ring_radius = (self.ring_radius - self.particle_radius) * self.ring_radius_k + self.particle_radius

    @classmethod
    def from_density(cls, num_x, num_y, density, dynamic_cfg: RingCfg):
        '''
        Configurations with total density equal to `density`, using
        the same spacing on both axes, i.e., `space_x = space_y`.

        NOTE: If the required spacing is negative, the initial state of the rings will be
        rescaled so that the spacing is zero.
        '''
        r = dynamic_cfg.get_ring_radius()
        pr = dynamic_cfg.diameter / 2
        
        space = 1/density**.5 - 2*r

        ring_radius_k = 1
        if space < 0:
            space = 0
            ring_radius_k = (1/(2*density**.5) - pr) / (r - pr)

        return cls(num_x, num_y, dynamic_cfg, space, space, ring_radius_k)

    @classmethod
    def from_relative_density(cls, num_x, num_y, rel_density, dynamic_cfg: RingCfg):
        '''
        Configurations with relative density set to `rel_density`, using
        the same spacing on both axes, i.e., `space_x = space_y`.

        Let d be the density (number of rings per unit area), the relative density is

        d_r = d/d_eq - 1

        where d_eq is the equilibrium density (1/equilibrium area of the rings).
        '''
        den_eq = 1 / dynamic_cfg.get_equilibrium_area()
        density = (rel_density + 1) * den_eq
        return cls.from_density(num_x, num_y, density, dynamic_cfg)

    def get_space_cfg(self):
        "Returns a `SpaceCfg` that contains all rings."
        ring_d = 2 * self.real_ring_radius
        height = self.num_y * (ring_d + self.space_y)
        length = self.num_x * (ring_d + self.space_x)
        return SpaceCfg(height, length)

class RectangularGridCreator(CreatorCore):
    def __init__(self, cfg: RectangularGridCfg, rng_seed: int=None) -> None:
        super().__init__(rng_seed)
        self.cfg = cfg
        self.num_x = cfg.num_x
        self.num_y = cfg.num_y
        self.space_x = cfg.space_x
        self.space_y = cfg.space_y    
        self.base_ring_pos = cfg.base_ring_pos
        self.ring_radius = cfg.ring_radius
        self.ring_radius_k = cfg.ring_radius_k
        self.real_ring_d = cfg.real_ring_radius * 2
    
    def create(self) -> InitData:
        num_rings = self.num_x * self.num_y
        base_pos = self.base_ring_pos * self.ring_radius_k
        real_ring_d = self.real_ring_d
        
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




