import pickle, yaml

from phystem.systems.ring.solvers import CppSolver
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
        self.times = []

    @property
    def vars_to_save(self):
        v = super().vars_to_save
        v.extend(["invasions_pos", "num_invasions", "times", "last_col_time", "relative_areas"])
        return v

    def collect(self) -> None:
        t = self.solver.time
        t_dt = self.solver.num_time_steps
        if t_dt - self.last_col_time < self.col_cfg.freq_dt:
            return
        self.last_col_time = t_dt

        num_inside = self.solver.in_pol_checker.num_inside_points
        inside_points = self.solver.in_pol_checker.inside_points

        self.num_invasions.append(num_inside)
        self.invasions_pos.append(inside_points[:num_inside])
        self.times.append(t)

        relative_areas = []
        for id, is_resolved in enumerate(self.solver.in_pol_checker.is_col_resolved):
            if not is_resolved:
                ring_id = self.solver.in_pol_checker.collisions[id].ring_id
                relative_areas.append(self.solver.area_debug.area[ring_id])
        self.relative_areas.append(relative_areas)
    
        if self.autosave_cfg:
            self.check_autosave()
    
    def save(self):
        with open(self.data_path / "data.pickle", "wb") as f:
            pickle.dump({
                "times": self.times, "num_invasions": self.num_invasions,
                "invasions_pos": self.invasions_pos,
                "relative_areas": self.relative_areas,
            }, f)

        with open(self.data_path / "metadata.yaml", "w") as f:
            yaml.dump({
                "num_points": len(self.num_invasions),
            }, f)

Configs2Collector.add(InvasionColCfg, InvasionCol)