'''
Configurações do sistema:

- Dinâmica
- Geometria do espaço
- Criação do estado inicial
- Outras (Stokes, Invaginação)
'''

from .dynamic_cfgs import RingCfg
from .space_cfgs import SpaceCfg
from .others_cfgs import StokesCfg, InvaginationCfg
from .creator_cfgs import *