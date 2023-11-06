'''
Configurações relacionadas ao sistema em questão.
'''
class RingCfg:
    '''
    Variáveis relacionadas a dinâmica do sistema.
    '''
    args_names = ("spring_k", "spring_r", "k_bend", "mobility", "relax_time",
        "vo", "trans_diff", "rot_diff", "exclusion_vol", "diameter", "p0")

    def __init__(self,  spring_k, spring_r, area_potencial, k_bend, p0, area0, mobility, relax_time,
        vo, trans_diff, rot_diff, exclusion_vol, diameter) -> None:
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
            f"$D_T$ = {self.trans_diff:.2f}\n"
            f"$D_R$ = {self.rot_diff:.2f}\n"
            f"$p0$ = {self.p0:.2f}\n"
        )

class CreateCfg:
    '''
    Configurações passada ao construtor de configuração inicial.
    '''
    def __init__(self, num_rings: int,  num_p: int, r: list[float], vo: list[float], angle: list[float],
        center: list[list[float]]) -> None:
        self.num_rings = num_rings
        self.num_p = num_p
    
        self.r = self.process_scalar_input(r)
        self.vo = self.process_scalar_input(vo)
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
            "vo": self.vo,
            "angle": self.angle,
            "center": self.center,
        }

class SpaceCfg:
    '''
    Configurações do espaço na qual as partículas se encontram.
    '''    
    def __init__(self, size:float) -> None:
        self.size = size
    
    def set(self, other):
        self.size = other.size

