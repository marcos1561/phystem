from pathlib import Path
from .autosave import AutoSavable, AutoSaveCfg
from abc import ABC, abstractmethod

class Calculator(ABC, AutoSavable):
    def __init__(self, root_dir: str | Path, autosave_cfg: AutoSaveCfg = None) -> None:
        super().__init__(root_dir, autosave_cfg)

    @abstractmethod
    def calculate(self):
        '''Calcula a quantidade relativa a esse calculador.
        Esse método deve ser capaz de continuar de um ponto salvo.
        '''
        pass