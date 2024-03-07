'''
Configurações relacionadas ao sistema em questão.
'''

from phystem.systems.ring import creators

class RingCfg:
    '''
    Variáveis relacionadas a dinâmica do sistema.
    '''
    args_names = ("spring_k", "spring_r", "k_bend", "mobility", "relax_time",
        "vo", "trans_diff", "rot_diff", "exclusion_vol", "diameter", "p0")

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
      
    def adjust_area_pars(self, num_particles: int):
        print("adjust:", num_particles)
        if self.area_potencial in ["target_area", "target_area_and_format"]:
            perimeter = num_particles * self.diameter
            if self.area0 is None:
                self.area0 = (perimeter / self.p0)**2
            else:
                self.p0 = perimeter / self.area0**.5

    def set(self, other):
        raise Exception("Pensei que não tava usando isso >:( ")
        
        self.spring_k = other.spring_k
        self.spring_r = other.spring_r
        
        self.bend_k = other.k_bend
        self.p0 = other.p0

        self.mobility = other.mobility
        self.relax_time = other.relax_time
        self.vo = other.vo

        self.trans_diff = other.trans_diff
        self.rot_diff = other.rot_diff

        self.exclusion_vol = other.exclusion_vol
        self.diameter = other.diameter
    
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
    def __init__(self, upper_k: float, bottom_k: float):
        self.upper_k = upper_k
        self.bottom_k = bottom_k

class CreatorCfg:
    '''
    Configurações passada ao construtor de configuração inicial.
    '''
    CreatorType = creators.Creator
    def __init__(self, num_rings: int,  num_p: int, r: list[float], angle: list[float],
        center: list[list[float]]) -> None:
        self.num_rings = num_rings
        self.num_p = num_p
    
        self.r = self.process_scalar_input(r)
        self.angle = self.process_scalar_input(angle)
        
        self.center = center

    def process_scalar_input(self, input):
        if type(input) in (float, int):
            return [input] * self.num_rings
        else:
            return input
        

    def set(self, other):
        self.r = other.r
        self.num_rings = other.num_rings
        self.num_p = other.num_p
        self.vo = other.vo
        self.angle = other.angle
        self.center = other.center

    def get_pars(self):
        return {
            "num_rings": self.num_rings,
            "num_p": self.num_p,
            "r": self.r,
            "angle": self.angle,
            "center": self.center,
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
    '''
    Configurações do espaço na qual as partículas se encontram.
    '''    
    def __init__(self, height: float, length: float) -> None:
        self.height = height
        self.length = length
    
    def set(self, other):
        self.height = other.height
        self.length = other.length


