'''
Coletores de quantidades que estão associadas às posições dos centros
dos anéis. 
Existe um coletor raiz (`QuantityPosCol`) responsável por gerenciar todos
os outros coletores. `QuantityPosCol` garante que todos os coletores coletem
no mesmo tempo e que os centros dos anéis sejam salvos uma única vez.
'''
from .root_collector import QuantityPosCol, QuantityPosCfg
from .collectors import *