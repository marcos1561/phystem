import pickle
from pathlib import Path
import os
from . import settings

class AutoSavePaths:
    def __init__(self, root_dirname="autosave", state_filename="state") -> None:
        '''
        Parâmetros:
            root_dir:
                Nome da pasta raiz dos dados salvos.
            
            state_filename:
                Nome do arquivo que contém o estado da classe.
            
        '''
        self.root_dirname = root_dirname
        self.state_path = Path(root_dirname, state_filename + ".pickle")

class AutoSavable():
    IS_COMPLETED_FLAG = settings.autosave_completion_flag_name
    ROOT_NAME = settings.autosave_root_name
    BACKUP_NAME = settings.autosave_root_backup_name

    def __init__(self, root_path: Path, autosave_container_name=settings.autosave_container_name, 
        state_name=settings.autosave_state_name) -> None:
        '''
        Parâmetros:
            root_dir:
                Pasta raiz que contém a pasta raiz do auto-salvamento.
            
            automatic_load:
                Carregar o auto-save nesse inicializador quando
                configurado.
        '''
        root_path = Path(root_path)
        
        self.autosave_container_name = autosave_container_name
        self.autosave_state_name = state_name
        
        self.autosave_container_path = root_path / autosave_container_name
        self.autosave_root_path = self.autosave_container_path / self.ROOT_NAME
        self.autosave_state_path = self.autosave_root_path / (state_name + ".pickle")
        
        self.autosave_paths = []
        for dir_name in [self.ROOT_NAME, self.BACKUP_NAME]:
            autosave_path = self.autosave_container_path / dir_name
            autosave_path.mkdir(parents=True, exist_ok=True)
            self.autosave_paths.append(autosave_path)

    @property
    def vars_to_save(self) -> list[str]:
        '''Nome dos atributos para serem salvos no auto-salvamento'''
        raise Exception("'vars_to_save' não foi implementado.")
    
    def get_vars_to_save(self):
        return {name: getattr(self, name) for name in self.vars_to_save}
    
    def set_vars_to_save(self, values: dict):
        for name, value in values.items():
            setattr(self, name, value)

    def autosave(self):
        '''Salva o estado atual.'''
        if self.vars_to_save is not None:
            with open(self.autosave_state_path, "wb") as f:
                pickle.dump(self.get_vars_to_save(), f)

    def exec_autosave(self, *args, **kwargs):
        '''Executa o auto-salvamento setando uma flag que informa a completude da operação.'''
        os.rename(self.autosave_container_path / self.BACKUP_NAME, self.autosave_container_path / "temp")
        os.rename(self.autosave_container_path / self.ROOT_NAME, self.autosave_container_path / self.BACKUP_NAME)
        os.rename(self.autosave_container_path / "temp", self.autosave_container_path / self.ROOT_NAME)
        
        is_completed_path = self.autosave_root_path / (self.IS_COMPLETED_FLAG + ".pickle")
        with open(is_completed_path, "wb") as f:
            pickle.dump(False, f)
        
        r = self.autosave(*args, **kwargs)

        with open(is_completed_path, "wb") as f:
            pickle.dump(True, f)

        return r
    
    @staticmethod
    def get_autosave_path(autosave_container_path: Path):
        '''Retorno o caminho de uma pasta que contém um
        auto-salvamento válido, dodo o caminho que contém
        todos os auto-salvamentos.
        '''
        autosave_container_path = Path(autosave_container_path)
        
        # Check if root path has only one autosave
        has_backup, has_autosave = False, False
        for item in autosave_container_path.iterdir():
            if item.is_dir() and item.stem == AutoSavable.BACKUP_NAME:
                has_backup = True
            if item.is_dir() and item.stem == AutoSavable.ROOT_NAME:
                has_autosave = True

        if not (has_autosave and has_backup):
            return autosave_container_path

        autosave_path = autosave_container_path / AutoSavable.ROOT_NAME        
        is_completed_name = AutoSavable.IS_COMPLETED_FLAG + ".pickle"
        for _ in range(2):
            settings.autosave_completion_flag_name
            with open(autosave_path / is_completed_name, "rb") as f:
                is_completed = pickle.load(f)

            if is_completed:
               break
            
            autosave_path = autosave_container_path / AutoSavable.BACKUP_NAME        
        else:
            raise Exception("Todos os auto-salvamentos estão corrompidos!.")

        return autosave_path

    def load_autosave(self, use_backup=False):
        '''Carrega o estado salvo e retorna o caminho raiz do auto-salvamento.'''
        if use_backup:
            autosave_path = self.autosave_container_path / AutoSavable.BACKUP_NAME
        else:
            autosave_path = self.get_autosave_path(self.autosave_container_path)
        
        with open(autosave_path / (self.autosave_state_name + ".pickle"), "rb") as f:
            saved_vars = pickle.load(f)
            self.set_vars_to_save(saved_vars)

        return autosave_path