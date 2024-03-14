from enum import Enum, auto

class ReplaySolverCfg:
    class Mode(Enum):
        normal = auto()
        same_ids = auto()
        same_ids_pre_calc = auto()

    def __init__(self, vel_from_solver=False, mode=Mode.normal,
        ring_per_grid=2) -> None:
        self.mode = mode
        self.vel_from_solver = vel_from_solver
        self.ring_per_grid = ring_per_grid