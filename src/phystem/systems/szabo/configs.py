'''
Configurações relacionadas ao sistema em questão.
'''
from enum import Enum, auto

class CreateType(Enum):
    '''
    Tipos de formato de espaço utilizados na criação da configuração inicial. 
    '''
    CIRCLE = auto()
    SQUARE = auto()

class SelfPropellingCfg:
    '''
    Variáveis relacionadas a dinâmica do sistema.
    '''
    args_names = ("relaxation_time", "mobility", "max_repulsive_force", "max_attractive_force",
        "r_eq",  "max_r", "vo", "nabla")

    def __init__(self, relaxation_time, mobility, max_repulsive_force, max_attractive_force,
        r_eq,  max_r, vo, nabla) -> None:
        self.mobility = mobility
        
        self.vo = vo
        self.nabla = nabla
        self.relaxation_time = relaxation_time

        self.max_repulsive_force = max_repulsive_force
        self.max_attractive_force = max_attractive_force
        self.r_eq = r_eq
        self.max_r = max_r
      
    def set(self, other):
        self.mobility = other.mobility
        
        self.vo = other.vo
        self.nabla = other.nabla
        self.relaxation_time = other.relaxation_time

        self.max_repulsive_force = other.max_repulsive_force
        self.max_attractive_force = other.max_attractive_force
        self.r_eq = other.r_eq
        self.max_r = other.max_r
    
    def cpp_constructor_args(self):
        return {
            "relaxation_time": self.relaxation_time,
            "mobility": self.mobility,
            "max_repulsive_force": self.max_repulsive_force,
            "max_attractive_force": self.max_attractive_force,
            "r_eq": self.r_eq,
            "max_r": self.max_r,
            "vo": self.vo,
            "nabla": self.nabla,
        }
    
    def info(self):
        return (
            f"$\\eta$ = {self.nabla:.2f}\n"
            f"$v_0$ = {self.vo:.2f}\n"
            f"$\\tau$ = {self.relaxation_time:.2f}\n"
            f"$\\mu$ = {self.mobility:.2f}\n"
        )

class CreatorCfg:
    '''
    Configurações passada ao construtor de configuração inicial.
    '''
    def __init__(self, n: int, r: float, type: CreateType) -> None:
        self.r = r
        self.n = n
        self.type = type

    def set(self, other):
        self.r = other.r
        self.n = other.n
        self.type = other.type

    def get_pars(self):
        return {
            "n": self.n,
            "r": self.r,
            "space_type": self.type,
        }

class SpaceCfg:
    '''
    Configurações do espaço na qual as partículas se encontram.
    '''    
    def __init__(self, size:float) -> None:
        self.size = size
    
    def set(self, other):
        self.size = other.size
