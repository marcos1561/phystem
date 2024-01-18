'''
Configurações relacionadas ao sistema em questão.
'''
class RingCfg:
    '''
    Variáveis relacionadas a dinâmica do sistema.
    '''
    args_names = ("spring_k", "spring_r", "k_bend", "mobility", "relax_time",
        "vo", "trans_diff", "rot_diff", "exclusion_vol", "diameter", "p0")

    def __init__(self,  spring_k, spring_r, area_potencial, k_bend, mobility, relax_time,
        vo, trans_diff, rot_diff, exclusion_vol, diameter, p0=None, area0=None) -> None:
        if p0 is None and area0 is None:
            raise Exception("Ao menos um dos parâmetros 'p0' e 'area0' devem ser setados.")

        self.spring_k = spring_k
        self.spring_r = spring_r
        
        self.area_potencial = area_potencial
        self.k_bend = k_bend
        self.p0 = p0
        self.area0 = area0

        self.mobility = mobility
        self.relax_time = relax_time
        self.vo = vo

        self.trans_diff = trans_diff
        self.rot_diff = rot_diff

        self.exclusion_vol = exclusion_vol
        self.diameter = diameter
      
    def adjust_area_pars(self, num_particles: int):
        if self.area_potencial == "target_area":
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
            "k_bend": self.k_bend,
            "area_potencial": self.area_potencial,
            "p0": self.p0,
            "area0": self.area0,
            "mobility": self.mobility,
            "relax_time": self.relax_time,
            "vo": self.vo,
            "trans_diff": self.trans_diff,
            "rot_diff": self.rot_diff,
            "exclusion_vol": self.exclusion_vol,
            "diameter": self.diameter,
        }

    def info(self):
        return (
            f"k_mola = {self.spring_k:.2f}  | p_0 = {self.p0:.2f}\n"
            f"k_area = {self.k_bend:.2f}   | area = {self.area0:.2f}\n"
            f"\n"
            f"D_T = {self.trans_diff:.2f}\n"
            f"D_R = {self.rot_diff:.2f}\n"
            f"\n"
        )

class StokesCfg:
    def __init__(self, obstacle_r: float, obstacle_x: float, obstacle_y: float,
        create_length: float, remove_length: float, num_max_rings: int
    ) -> None:
        self.obstacle_r = obstacle_r
        self.obstacle_x = obstacle_x
        self.obstacle_y = obstacle_y
        self.create_length = create_length
        self.remove_length = remove_length
        self.num_max_rings = num_max_rings

    def cpp_constructor_args(self):
        return {
            "obstacle_r": self.obstacle_r,
            "obstacle_x": self.obstacle_x,
            "obstacle_y": self.obstacle_y,
            "create_length": self.create_length,
            "remove_length": self.remove_length,
            "num_max_rings": self.num_max_rings,
        }

class CreatorCfg:
    '''
    Configurações passada ao construtor de configuração inicial.
    '''
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

