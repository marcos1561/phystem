import unittest, os, shutil
from pathlib import Path

from phystem.systems.ring import Simulation, utils
from phystem.core.run_config import load_configs, CollectDataCfg, CheckpointCfg
from phystem.systems.ring.collectors import DeltaCol, ColAutoSaveCfg, DenVelCol, CreationRateCol, CheckpointCol, SnapshotsCol, SnapshotsColCfg

current_folder = Path(os.path.dirname(__file__))
configs_path = current_folder / "data_test/ring/configs/collectors_configs"

class AsteroidError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class TestRingCols(unittest.TestCase):
    def test_autosave(self):
        configs = load_configs(configs_path)
        run_cfg: CollectDataCfg = configs["run_cfg"]
        dynamic_cfg = configs["dynamic_cfg"]
        radius = utils.get_ring_radius(
            p_diameter = dynamic_cfg.diameter,
            num_particles = configs["creator_cfg"].num_p,
        )

        # Configurações dos coletores
        func_cfg = {}

        center_region = -4 * 2*radius
        wait_dist = 4 * 2*radius
        xlims = [center_region - radius, center_region + radius]
        func_cfg["delta"] = {
            "wait_dist": wait_dist,  
            "xlims": [center_region - radius, center_region + radius],
            "start_dt": (xlims[1] - xlims[0]) * dynamic_cfg.vo,
            "check_dt": 1/4 * (xlims[1] - xlims[0]) * dynamic_cfg.vo,
            "autosave_cfg": ColAutoSaveCfg(freq_dt=5),
        }

        func_cfg["den_vel"] = {
            "xlims": [center_region - radius, center_region + radius],
            "vel_dt": 2,
            "density_dt": 2,
            "vel_frame_dt": 0.5,
        }

        func_cfg["cr"] = {
            "wait_time": 0,
            "collect_time": run_cfg.tf, 
            "collect_dt": 1,
        }

        func_cfg["snaps"] = {
            "col_cfg": SnapshotsColCfg(
                snaps_dt=2,
                wait_time=1,
            )
        }

        func_cfg["autosave_cfg"] = ColAutoSaveCfg(freq_dt=5)

        # Rodando a simulação
        run_cfg: CollectDataCfg = configs["run_cfg"]
        run_cfg.folder_path = current_folder / "tmp"
        run_cfg.func_cfg = func_cfg
        run_cfg.func = TestRingCols.get_pipeline(stop_time=50)

        try:
            Simulation(**configs).run()
        except AsteroidError as e:
            pass

        run_cfg.checkpoint = CheckpointCfg(run_cfg.folder_path / "autosave")
        sim = Simulation(**configs)
        
        if sim.solver.time < 39:
            raise Exception("Tempo do solver está errado após o carregamento do auto-save.")
        
        sim.run()
        shutil.rmtree(run_cfg.folder_path)

    @staticmethod
    def get_pipeline(stop_time):
        def pipeline(sim: Simulation, cfg: dict=None):
            from phystem.core.run_config import CollectDataCfg
            from phystem.systems.ring.collectors import ColManager
            from phystem.utils import progress
            
            collect_cfg: CollectDataCfg = sim.run_cfg
            solver = sim.solver

            col = ColManager(
                root_path=collect_cfg.folder_path, solver=sim.solver, configs=sim.configs, 
                to_load_autosave=collect_cfg.is_autosave,
                autosave_cfg=cfg["autosave_cfg"],
            )

            col.add_collector(DeltaCol, cfg["delta"], "delta")
            col.add_collector(CreationRateCol, cfg["cr"], "cr")
            col.add_collector(DenVelCol, cfg["den_vel"], "den_vel")
            col.add_collector(CheckpointCol, {}, "checkpoint")
            col.add_collector(SnapshotsCol, cfg["snaps"], "snaps")

            is_autosave = collect_cfg.is_autosave

            prog = progress.Continuos(collect_cfg.tf)
            while solver.time < collect_cfg.tf:
                if solver.time > stop_time and not is_autosave:
                    raise AsteroidError((
                        "Um asteroide atingiu o computador, assim "
                        "parando a execução deste código de forma inesperada."
                    ))

                solver.update()
                col.collect()
                prog.update(solver.time)
            col.save()
            prog.update(solver.time)
        
        return pipeline

if __name__ == '__main__':
    unittest.main()