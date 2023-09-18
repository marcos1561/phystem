'''
Configurações relacionadas ao sistema em questão.
'''
class RingCfg:
    '''
    Variáveis relacionadas a dinâmica do sistema.
    '''
    args_names = ("spring_k", "spring_r", "bend_k", "mobility", "relax_time",
        "vo", "trans_diff", "rot_diff", "exclusion_vol", "diameter")

    def __init__(self,  spring_k, spring_r, bend_k, mobility, relax_time,
        vo, trans_diff, rot_diff, exclusion_vol, diameter) -> None:
        self.spring_k = spring_k
        self.spring_r = spring_r
        
        self.bend_k = bend_k

        self.mobility = mobility
        self.relax_time = relax_time
        self.vo = vo

        self.trans_diff = trans_diff
        self.rot_diff = rot_diff

        self.exclusion_vol = exclusion_vol
        self.diameter = diameter
      
    def set(self, other):
        self.spring_k = other.spring_k
        self.spring_r = other.spring_r
        
        self.bend_k = other.bend_k

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
            "bend_k": self.bend_k,
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
        )

class CreateCfg:
    '''
    Configurações passada ao construtor de configuração inicial.
    '''
    def __init__(self, n: int, r: float, vo: float, angle: float) -> None:
        self.r = r
        self.n = n
        self.vo = vo
        self.angle = angle

    def set(self, other):
        self.r = other.r
        self.n = other.n
        self.vo = other.vo
        self.angle = other.angle

    def get_pars(self):
        return {
            "n": self.n,
            "r": self.r,
            "vo": self.vo,
            "angle": self.angle,
        }

class SpaceCfg:
    '''
    Configurações do espaço na qual as partículas se encontram.
    '''    
    def __init__(self, size:float) -> None:
        self.size = size
    
    def set(self, other):
        self.size = other.size

