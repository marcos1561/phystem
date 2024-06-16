import pickle
from pathlib import Path

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
    def __init__(self, root_path: Path, autosave_root_name="autosave", 
        state_name="state") -> None:
        '''
        Parâmetros:
            root_dir:
                Pasta raiz que contém a pasta raiz do auto-salvamento.
            
            automatic_load:
                Carregar o auto-save nesse inicializador quando
                configurado.
        '''
        root_path = Path(root_path)
        self.autosave_root_path = root_path / autosave_root_name
        self.autosave_state_path = root_path / autosave_root_name / (state_name + ".pickle")

        self.autosave_root_path.mkdir(parents=True, exist_ok=True)
    
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

    def load_autosave(self):
        with open(self.autosave_state_path, "rb") as f:
            saved_vars = pickle.load(f)
            self.set_vars_to_save(saved_vars)
