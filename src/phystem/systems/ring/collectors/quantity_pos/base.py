from enum import Enum, auto
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import pickle
import yaml

from phystem.core.collectors import ColAutoSaveCfg
from phystem.data_utils.data_types import ArraySizeAware
from phystem.systems.ring.solvers import CppSolver

@dataclass
class QuantityPosState:
    "Variáveis que caracterizam o estado do coletor raiz."
    
    # Tempo da última coleta em unidades do passo temporal.
    col_last_time: int
    
    # Tempos em que foi coletado dados, em unidades de tempo da simulação.
    times: list[float] = field(default_factory=list)

@dataclass
class QuantityState:
    "Variáveis que caracterizam o estado dos coletores gerenciados."
    
    # Container dos dados coletados.
    data: ArraySizeAware
    
    # Id do arquivo atualmente sendo preenchido de dados.
    file_id:int = 0

class QuantityCfg(ABC):
    "Base das configurações dos coletores gerenciados por `QuantityPosCol`."
    @property
    @abstractmethod
    def num_dims(self) -> int:
        "Número de dimensões dos pontos salvos a cada coleta."
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        "Nome raiz dos arquivos de dados salvos."
        pass

class QuantityPosCfg:
    class CheckType:
        only_x = auto()
        only_y = auto()
        both = auto()
        none = auto()

    def __init__(self, collect_dt: int, xlims: list[float]="all", ylims: list[float]="all", 
        quantities_cfg: list[QuantityCfg]=None, transient_time: float=0,
        autosave_cfg: ColAutoSaveCfg=None, memory_per_file=10*1e6):
        '''
        Configurações do gerenciador de coletores com quantidades associadas às posições
        do centro dos anéis. Para escolher quais coletores serão utilizados, basta
        adicionar a sua configuração no parâmetro `quantities_cfg`. Por padrão,
        sempre é adicionado um coletor de posições dos anéis.

        Em cada coletor, os dados são guardados em um array com dimensão (N, n_p, d) em que:
        
        N   : Número de pontos coletados
        n_p : Número de anéis em um ponto coletado
        d   : Dimensão dos elementos que constituem o ponto

        OBS: Se a coleta for muito longa, os dados coletados vão ser salvos em arquivos separados, mas que em
        conjunto representam uma única lista de pontos de dados.

        Parâmetros:
        -----------
        transient_time:
            Tempo esperado para iniciar a coleta de dados.
        
        collect_dt:
            Intervalo de tempo entre coletas. Dado em unidades do passo temporal
            do esquema de integração.
        
        xlims, ylims:
            Limites nos eixos x e y da região onde a coleta é feita. Seus valores
            podem ser `"all"`, que é equivalente a color os limites no infinito.
        
        quantities_cfg:
            Lista com as configurações dos coletores.

        autosave_cfg:
            Configurações do auto-salvamento.

        memory_per_file:
            Tamanho do arquivo de dados dos coletores em bytes.
        '''
        if quantities_cfg is None:
            quantities_cfg = []

        self.check_type = self.CheckType.both
        
        self._xlims = xlims
        self._ylims = ylims

        self.transient_time = transient_time
        self.collect_dt = collect_dt
        self.xlims = xlims
        self.ylims = ylims
        self.memory_per_file = memory_per_file
        self.quantities_cfg = quantities_cfg
        self.autosave_cfg = autosave_cfg

    def get_check_type(self):
        check_x = self.xlims != 0
        check_y = self.ylims != 0

        if check_x and check_y:
            return self.CheckType.both
        if check_x and not check_y:
            return self.CheckType.only_x
        if not check_x and check_y:
            return self.CheckType.only_y
        if not check_x and not check_y:
            return self.CheckType.none

    @property
    def xlims(self):
        return self._xlims
    
    @property
    def ylims(self):
        return self._ylims

    @xlims.setter
    def xlims(self, value):
        if value == "all":
            value = [-float('inf'), float('inf')]
            self.check_x = False
        else:
            self.check_x = True
        self._xlims = value
        self.check_type = self.get_check_type()

    @ylims.setter
    def ylims(self, value):
        if value == "all":
            value = [-float('inf'), float('inf')]
            self.check_y = False
        else:
            self.check_y = True
        self._ylims = value
        self.check_type = self.get_check_type()
        

class QuantityCol(ABC):
    StateT = QuantityState
    
    def __init__(self, configs: QuantityCfg, root_state: QuantityPosState, root_configs: QuantityPosCfg, 
        solver: CppSolver, num_max_rings, num_data_points_per_file, data_path):
        "Base dos coletores gerenciados por `QuantityPos`."
        self.solver = solver
        self.configs = configs
        self.root_state = root_state
        self.root_configs = root_configs
        self.data_path = data_path
        # self.num_data_points_per_file = int(self.root_configs.memory_per_file / (num_max_rings * configs.num_dims * 4))

        self.metadata = {}

        self.data = self.create_data(num_data_points_per_file, num_max_rings)
        self.state = self.StateT(self.data)

        self.init_metadata(self.metadata)

    def init_metadata(self, metadata: dict):
        pass

    def before_save_metadata(self, metadata: dict):
        pass

    def create_data(self, num_data_points_per_file, num_max_rings):
        return ArraySizeAware(num_data_points_per_file, num_max_rings, self.configs.num_dims)

    def to_collect(self, time_dt: int, is_time: bool) -> bool:
        '''
        Retorna `True` se for para realizar a coleta
        
        Parâmetros:
        -----------
        time_dt:
            Número de passos temporais dados até o momento.
        
        is_time:
            `True` se o tempo desde a última coleta é maior do que
            o intervalo de tempo entre coletas.
        '''
        return is_time

    @abstractmethod
    def collect(self, ids_in_region, cms_in_region):
        pass

    def save_data(self):
        filename = f"{self.configs.name}_{self.state.file_id}"
        file_path = self.data_path / (filename + ".pickle")
        with open(file_path, "wb") as f:
            pickle.dump(self.state.data, f)
    
    def save(self):
        self.save_data()

        self.before_save_metadata(self.metadata)
        with open(self.data_path / f"{self.configs.name}_metadata.yaml", "w") as f:
            yaml.dump(self.metadata, f)
