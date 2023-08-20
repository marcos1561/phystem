from enum import Flag, Enum, auto

class CreateType(Enum):
    CIRCLE = auto()
    SQUARE = auto()

class RunType(Flag):
    COLLECT_DATA = auto()
    REAL_TIME = auto()
    SAVE_VIDEO = auto()

class SolverType(Enum):
    PYTHON = auto()
    CPP = auto()

class UpdateType(Enum):
    NORMAL = auto()
    WINDOWS = auto()

class SelfPropellingCfg:
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

class CreateCfg:
    def __init__(self, n: int, r: float, type: int) -> None:
        self.r = r
        self.n = n
        self.type = type

class SpaceCfg:
    def __init__(self, size:float) -> None:
        self.size = size

class RunCfg:
    id: RunType
    def __init__(self, dt: float, solver_type = SolverType.PYTHON, update_type = UpdateType.NORMAL) -> None:
        self.dt = dt
        self.solver_type = solver_type
        self.update_type = update_type

class CollectDataCfg(RunCfg):
    id = RunType.COLLECT_DATA
    def __init__(self, tf: float, dt: float, folder_path: str, solver_type: SolverType, 
        update_type = UpdateType.NORMAL, only_last=False) -> None:
        super().__init__(dt, solver_type, update_type)
        self.tf = tf
        self.folder_path = folder_path
        self.only_last = only_last

class RealTimeCfg(RunCfg):
    id = RunType.REAL_TIME
    def __init__(self, dt: float, num_steps_frame: int, fps: int, solver_type: SolverType,
        update_type = UpdateType.NORMAL) -> None:
        super().__init__(dt, solver_type, update_type)
        self.num_steps_frame = num_steps_frame
        self.fps = fps

class SaveCfg(RunCfg):
    id = RunType.SAVE_VIDEO
    def __init__(self, path:str, speed: float, fps: int, dt: float, 
        duration: float = None, tf: float = None, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:  
        super().__init__(dt, solver_type, update_type)
        if duration == None and tf == None:
            raise ValueError("Um dos parâmetros `duration` ou `tf` deve ser passado.")
        self.speed = speed
        self.path = path
        self.fps = fps
        self.dt = dt
    
        self.num_steps_frame = speed / fps / dt
        if self.num_steps_frame < 1:
            self.num_steps_frame = 1
            self.dt = self.speed/self.fps
        else:
            self.num_steps_frame = int(round(self.num_steps_frame))

        if duration != None:
            self.duration = duration
            self.num_frames = int(duration * fps)
            self.tf = self.num_frames * self.num_steps_frame * self.dt
        elif tf != None:
            self.tf = tf
            self.num_frames = int(self.tf / self.num_steps_frame / self.dt)
            self.duration = self.num_frames / self.fps
