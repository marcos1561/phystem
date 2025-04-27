import pickle, yaml
import numpy as np

from phystem.systems.ring.solvers import CppSolver
from phystem.cpp_lib.managers import ColInfo, InPolChecker 
from .base import RingCol, ColCfg
from .config_to_col import Configs2Collector

class InvasionColCfg(ColCfg):
    def __init__(self, freq_dt: int, autosave_cfg = None):
        super().__init__(autosave_cfg)
        self.freq_dt = freq_dt

class InvasionCol(RingCol):
    solver: CppSolver
    col_cfg: InvasionColCfg

    def setup(self):
        # State
        self.last_col_time = self.solver.num_time_steps
        self.relative_areas = []
        self.num_invasions = []
        self.invasions_pos = []
        self.unique_invasions = []
        self.times = []

    @property
    def vars_to_save(self):
        v = super().vars_to_save
        v.extend(["invasions_pos", "num_invasions", 
            "times", "last_col_time", "relative_areas", "unique_invasions"])
        return v

    def collect(self) -> None:
        t = self.solver.time
        t_dt = self.solver.num_time_steps
        if t_dt - self.last_col_time < self.col_cfg.freq_dt:
            return
        self.last_col_time = t_dt

        in_pol_checker: InPolChecker = self.solver.in_pol_checker

        num_inside = in_pol_checker.num_inside_points
        inside_points = in_pol_checker.inside_points

        self.num_invasions.append(num_inside)
        self.invasions_pos.append(np.array(inside_points[:num_inside]))
        self.unique_invasions.append(self.count_unique_invasions(in_pol_checker.collisions[:in_pol_checker.num_inside_points]))
        self.times.append(t)

        relative_areas = []
        for id, is_resolved in enumerate(self.solver.in_pol_checker.is_col_resolved):
            if not is_resolved:
                ring_id = self.solver.in_pol_checker.collisions[id].ring_id
                relative_areas.append(self.solver.area_debug.area[ring_id])
        self.relative_areas.append(relative_areas)
    
        if self.autosave_cfg:
            self.check_autosave()
    
    def count_unique_invasions(self, collisions: list[ColInfo]):
        unique_collisions = set()
        for collision in collisions:
            ids = tuple(sorted([collision.col_ring_id, collision.ring_id]))
            unique_collisions.add(ids)
        return len(unique_collisions)

    def save(self):
        with open(self.data_path / "data.pickle", "wb") as f:
            pickle.dump({
                "times": self.times, 
                "num_invasions": self.num_invasions,
                "invasions_pos": self.invasions_pos,
                "unique_invasions": self.unique_invasions,
                "relative_areas": self.relative_areas,
            }, f)

        with open(self.data_path / "metadata.yaml", "w") as f:
            yaml.dump({
                "num_points": len(self.num_invasions),
            }, f)

Configs2Collector.add(InvasionColCfg, InvasionCol)