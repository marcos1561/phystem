from enum import Enum, auto

class ReplaySolverCfg:
    def __init__(self, vel_from_solver=False) -> None:
        self.vel_from_solver = vel_from_solver