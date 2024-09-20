import numpy as np

from phystem.core.creators import CreatorCore
from phystem.systems.ring import utils

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
    ring_radius = utils.get_ring_radius(particle_diameter, num_particles)
    angles = np.arange(0, np.pi*2, np.pi*2/num_particles)
    ring_pos = np.array([np.cos(angles), np.sin(angles)]) * ring_radius
    return ring_pos.T

class Creator(CreatorCore):
    def __init__(self, num_rings: int, num_particles: int, r: list[float], angle: list[float], center: list, 
        rng_seed: int = None) -> None:
        '''
        Cria anéis com `num_particles` partículas em formato de circular com raio `r`, posições do 
        centro de massa em `center` e polarizações em `angle`. 

        OBS: A função `create` é responsável por gerar a configuração inicial. 
        
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
            
            rng_seed:
                Seed utilizada na geração de números aleatórios. Se for `None` é
                utilizado uma seed aleatória.
        '''
        super().__init__(rng_seed)

        self.num_rings = num_rings
        self.num_particles = num_particles
        self.r = r
        self.angle = angle
        self.center = center

    def create(self) -> InitData:
        '''
        Cria a configuração inicial.
        
        Return:
        -------
            : InitData
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

class RectangularGridCreator(CreatorCore):
    def __init__(self, num_rings_x, num_rings_y, space_x, space_y, num_particles, particle_diameter, 
        ring_radius_k=1, rng_seed: int = None) -> None:
        super().__init__(rng_seed)

        self.num_rings_x = num_rings_x
        self.num_rings_y = num_rings_y
        self.space_x = space_x
        self.space_y = space_y    
        self.num_particles = num_particles
        self.particle_diameter = particle_diameter
        self.ring_radius_k = ring_radius_k
    
    def create(self) -> InitData:
        ring_radius = utils.get_ring_radius(self.particle_diameter, self.num_particles)
        real_ring_d = 2 * (ring_radius + self.particle_diameter/2)
        num_rings = self.num_rings_x * self.num_rings_y

        base_pos = get_base_ring(self.num_particles, self.particle_diameter) * self.ring_radius_k
        pos = []
        for i in range(self.num_rings_x):
            x = (i + 1/2) * (self.space_x + real_ring_d)
            for j in range(self.num_rings_y):
                y = (j + 1/2) * (self.space_y + real_ring_d)
                pos.append(base_pos + [x, y])
        
        height = self.num_rings_y * (real_ring_d + self.space_y)
        width = self.num_rings_x * (real_ring_d + self.space_x)
        central_point = [width/2, height/2]

        pos = np.array(pos) - central_point
        random_angles = np.random.random(num_rings) * 2*np.pi 

        return InitData(pos, random_angles)

class InvaginationCreator(CreatorCore):
    def __init__(self, num_rings: int, num_p: int, height: int, length: int, diameter: float,
        rng_seed: int = None) -> None:
        super().__init__(rng_seed)

        self.num_rings = num_rings
        self.height = height
        self.length = length
        self.diameter = diameter

        self.num_p = num_p
        

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
    

if __name__ == "__main__":
    num_rings = 1
    num_p = 1
    height = 1
    length = 1
    diameter = 1

    print(Creator(0, 30, [3], [0], [0, 0]).create().pos.shape[0])
    # creator = InvaginationCreator(num_rings, num_p, height, length, diameter)
    # creator.loop()




