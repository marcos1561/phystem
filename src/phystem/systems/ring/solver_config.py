from enum import Enum, auto

class ReplaySolverCfg:
    def __init__(self, calc_vel_dframes=1, vel_from_solver=False) -> None:
        self.vel_from_solver = vel_from_solver
        self.calc_vel_dframes = calc_vel_dframes