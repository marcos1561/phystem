'''
Configurações relacionadas ao sistema em questão.
'''
from phystem.systems.ring import creators, utils

class RingCfg:
    "Variáveis relacionadas a dinâmica do sistema."

    def __init__(self,  spring_k, spring_r, area_potencial, mobility, relax_time,
        vo, trans_diff, rot_diff, diameter, max_dist, rep_force, adh_force, k_invasion,
        p0=None, p0_format=None, area0=None, k_format=None, k_area=None) -> None:
        valid_potencials = ["target_area", "target_area_and_format", "format", "target_perimeter"]
        if area_potencial not in valid_potencials:
            raise ValueError(f"Potencial '{area_potencial}' não válido. Os valores permitidos são {valid_potencials}")

        if p0 is None and area0 is None:
            raise Exception("Ao menos um dos parâmetros 'p0' e 'area0' devem ser setados.")

        has_format = area_potencial in ["format", "target_area_and_format"]
        has_target_area = area_potencial in ["target_area", "target_area_and_format"]

        if has_format:
            if k_format is None:
                raise ValueError(f"'k_format' deve ser especificado para o potencial '{area_potencial}'.")
            if p0_format is None:
                raise ValueError(f"'p0_format' deve ser especificado para o potencial '{area_potencial}'.")
        
        if has_target_area and k_area is None:
            raise ValueError("'k_area' deve ser especificado para o potencial.")

        if area_potencial == "format":
            area0 = -1
            p0 = -1
            k_area = -1
        if not has_format:
            k_format = -1
            p0_format = -1

        self.spring_k = spring_k
        self.spring_r = spring_r
        
        self.area_potencial = area_potencial
        self.k_area = k_area
        self.k_format = k_format
        self.p0 = p0
        self.p0_format = p0_format
        self.area0 = area0

        self.k_invasion = k_invasion

        self.mobility = mobility
        self.relax_time = relax_time
        self.vo = vo

        self.trans_diff = trans_diff
        self.rot_diff = rot_diff

        self.diameter = diameter
        self.max_dist = max_dist
        self.rep_force = rep_force
        self.adh_force = adh_force

    def get_equilibrium_relative_area(self, num_particles):
        '''
        Retorna a área de equilíbrio relativa a `area0`. A área de
        equilíbrio ocorre quando a força da área se balança com a
        força das molas.
        '''
        area0 = self.area0
        if area0 is None:
            area0 = self.get_area0(num_particles)
        
        return utils.get_equilibrium_relative_area(
            k_a=self.k_area, k_m=self.spring_k, a0=area0,
            spring_r=self.spring_r, num_particles=num_particles,
        )
    
    def get_equilibrium_area(self, num_particles):
        '''
        Retorna a área de equilíbrio do anel. A área de
        equilíbrio ocorre quando a força da área se balança com a
        força das molas.
        '''
        area0 = self.area0
        if area0 is None:
            area0 = self.get_area0(num_particles)

        return self.get_equilibrium_relative_area(num_particles) * area0

    def get_max_k_adh(self, dt, relative_area, num_particles, x=1):
        area0 = self.area0
        if area0 is None:
            area0 = self.get_area0(num_particles)

        adh_size = self.max_dist - self.diameter

        return utils.get_max_k_adh(adh_size, dt, self.k_area, area0, self.spring_r, relative_area,
            self.mobility, self.vo, x)

    def get_area0(self, num_particles):
        '''
        Retorna a área de equilíbrio da força da área para
        o dado número de partículas, levando em consideração `p0`.
        '''
        return (num_particles * self.spring_r / self.p0)**2
    
    def get_p0(self, num_particles):
        '''
        Retorna o p0 para o dado número de partículas, levando em 
        consideração `area0`.
        '''
        return num_particles * self.spring_r / self.area0**.5
    
    def set_p0(self, value, num_particles):
        self.p0 = value
        self.area0 = self.get_area0(num_particles)

    def will_invade(self, num_particles, relative_area, tol=1e-3):
        area0 = self.get_area0(num_particles)
        _, est_value = utils.get_invasion_equilibrium_config(
            k_r=self.rep_force, k_m=self.spring_k, k_a=self.k_area,
            lo=self.spring_r, ro=self.diameter, area0=area0,
            relative_area_eq=relative_area, vo=self.vo, mu=self.mobility,
        )
        return abs(est_value[0]) + abs(est_value[1]) > tol

    def adjust_area_pars(self, num_particles: int):
        print("adjust:", num_particles)
        if self.area_potencial in ["target_area", "target_area_and_format"]:
            perimeter = num_particles * self.spring_r
            # perimeter = num_particles * self.diameter
            if self.area0 is None:
                self.area0 = (perimeter / self.p0)**2
            else:
                self.p0 = perimeter / self.area0**.5

    def cpp_constructor_args(self):
        return {
            "spring_k": self.spring_k,
            "spring_r": self.spring_r,
            "k_area": self.k_area,
            "k_format": self.k_format,
            "area_potencial": self.area_potencial,
            "p0": self.p0,
            "p0_format": self.p0_format,
            "area0": self.area0,
            "k_invasion": self.k_invasion,
            "mobility": self.mobility,
            "relax_time": self.relax_time,
            "vo": self.vo,
            "trans_diff": self.trans_diff,
            "rot_diff": self.rot_diff,
            "diameter": self.diameter,
            "max_dist": self.max_dist,
            "rep_force": self.rep_force,
            "adh_force": self.adh_force,
        }

    def info(self):
        return (
            f"k_mola = {self.spring_k:.2f}\n"
            f"k_area = {self.k_area:.2f} | k_format = {self.k_format:.2f}\n"
            f"p_0 = {self.p0:.2f} | area0 = {self.area0:.2f}\n"
            f"\n"
            f"D_T = {self.trans_diff:.2f}\n"
            f"D_R = {self.rot_diff:.2f}\n"
            f"\n"
        )

class StokesCfg:
    def __init__(self, obstacle_r: float, obstacle_x: float, obstacle_y: float,
        create_length: float, remove_length: float, flux_force: float, 
        obs_force: float, num_max_rings: int
    ) -> None:
        self.obstacle_r = obstacle_r
        self.obstacle_x = obstacle_x
        self.obstacle_y = obstacle_y
        self.create_length = create_length
        self.remove_length = remove_length
        self.flux_force = flux_force
        self.obs_force = obs_force
        self.num_max_rings = num_max_rings

    @staticmethod
    def get_null_cpp_cfg():
        return {
            "obstacle_r": 0,
            "obstacle_x": 0,
            "obstacle_y": 0,
            "create_length": 0,
            "remove_length": 0,
            "flux_force": 0,
            "obs_force": 0,
            "num_max_rings": -1,
        }

    def cpp_constructor_args(self):
        return {
            "obstacle_r": self.obstacle_r,
            "obstacle_x": self.obstacle_x,
            "obstacle_y": self.obstacle_y,
            "create_length": self.create_length,
            "remove_length": self.remove_length,
            "flux_force": self.flux_force,
            "obs_force": self.obs_force,
            "num_max_rings": self.num_max_rings,
        }

class InvaginationCfg:
    def __init__(self, upper_k: float, bottom_k: float, num_affected: int):
        self.upper_k = upper_k
        self.bottom_k = bottom_k
        self.num_affected = num_affected 

class CreatorCfg:
    "Configurações passadas ao construtor da configuração inicial."
    CreatorType = creators.Creator
    def __init__(self, num_rings: int,  num_particles: int, r: list[float], angle: list[float],
        center: list[list[float]]) -> None:
        '''
        Cria anéis com `num_particles` partículas em formato de circular com raio `r`, posições do 
        centro de massa `center` e polarizações `angle`. 
        '''
        self.num_rings = num_rings
        self.num_particles = num_particles
    
        self.r = self.process_scalar_input(r)
        self.angle = self.process_scalar_input(angle)
        
        self.center = center

    @classmethod
    def empty(cls, num_particle):
        '''
        Configurações de uma condição inicial nula. Útil para o
        fluxo de stokes.
        '''
        return cls(
            num_rings=0, num_particles=num_particle, 
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
        self.r = other.r
        self.num_rings = other.num_rings
        self.num_particles = other.num_particles
        self.vo = other.vo
        self.angle = other.angle
        self.center = other.center

    def get_pars(self):
        return {
            "num_rings": self.num_rings,
            "num_particles": self.num_particles,
            "r": self.r,
            "angle": self.angle,
            "center": self.center,
        }

class RectangularGridCfg:
    CreatorType = creators.RectangularGridCreator
    def __init__(self, num_x, num_y, space_x, space_y, num_particles, particle_diameter, ring_radius_k=1) -> None:
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
        self.num_particles = num_particles 
        self.particle_diameter = particle_diameter
        self.ring_radius_k = ring_radius_k

    @classmethod
    def from_relative_density(cls, num_x, num_y, rel_density, num_particles, particle_diameter, ring_radius_k):
        '''
        Configurações que possuem a densidade relativa setada em `rel_density` utilizando
        o mesmo espaçamento em ambos os eixos, ou seja, `space_x = space_y`.

        Sendo d a densidade (Nº de anéis por un. de área), temos que a densidade relativa é

        d_r = d/d_eq - 1

        Em que d_eq é a densidade de equilíbrio, que acontece quando setamos `space_x = space_y = 0`.
        '''
        real_ring_d = 2 * utils.get_real_ring_radius(particle_diameter, num_particles)
        space = real_ring_d * (1/(rel_density +1)**.5 - 1)
        return cls(num_x, num_y, space, space, num_particles, particle_diameter, ring_radius_k)

    def get_space_cfg(self):
        real_ring_d = 2 * utils.get_real_ring_radius(self.particle_diameter, self.num_particles)
        height = self.num_y * (real_ring_d + self.space_y)
        length = self.num_x * (real_ring_d + self.space_x)

        return SpaceCfg(height, length)

    def get_pars(self):
        return {
            "num_rings_x": self.num_x,
            "num_rings_y": self.num_y,
            "space_x": self.space_x,
            "space_y": self.space_y,
            "num_particles": self.num_particles,
            "particle_diameter": self.particle_diameter,
            "ring_radius_k": self.ring_radius_k,
        }

class InvaginationCreatorCfg:
    CreatorType = creators.InvaginationCreator

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

    def get_pars(self):
        return {
            "num_rings": self.num_rings,
            "num_p": self.num_p,
            "height": self.height,
            "length": self.length,
            "diameter": self.diameter,
        }

class SpaceCfg:
    "Configurações do espaço na qual as partículas se encontram."
    def __init__(self, height: float, length: float) -> None:
        self.height = height
        self.length = length
    
    def set(self, other):
        self.height = other.height
        self.length = other.length
    
    def max_num_inside(self, ring_diameter):
        'Número ne anéis que cabem dentro do espaço'
        return int(self.height * self.length / ring_diameter**2)

    def particle_grid_shape(self, max_dist, frac=1.05):
        from math import floor
        box_size = max_dist * frac
        num_cols = int(floor(self.length/box_size))
        num_rows = int(floor(self.height/box_size))
        return (num_cols, num_rows)

    def rings_grid_shape(self, radius, frac=0.5):
        from math import ceil
        num_cols = int(ceil(self.length / ((2 + frac)*radius)))
        num_rows = int(ceil(self.height / ((2 + frac)*radius)))
        return (num_cols, num_rows)




