import unittest, os, shutil
from pathlib import Path

from phystem.systems.ring import Simulation, utils
from phystem.core.run_config import load_configs, CollectDataCfg, CheckpointCfg
from phystem.systems.ring.collectors import DeltaCol, ColAutoSaveCfg, DenVelCol, CreationRateCol, CheckpointCol, SnapshotsCol, SnapshotsColCfg, RingCol

current_folder = Path(os.path.dirname(__file__))
configs_path = current_folder / "data_test/ring/configs/collectors_configs"

class AsteroidError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class TestRingCols(unittest.TestCase):
    def test_autosave(self):
        stop_time = 50
        ColsT = {
            "delta": DeltaCol,
            "cr": CreationRateCol,
            "den_vel": DenVelCol,
            "checkpoint": CheckpointCol,
            "snaps": SnapshotsCol,
        }

        run_cfg, configs = self.exec_collect(stop_time, ColsT)

        run_cfg.checkpoint = CheckpointCfg(run_cfg.folder_path / "autosave")
        sim = Simulation(**configs)
        
        if sim.solver.time < 39:
            raise Exception("Tempo do solver está errado após o carregamento do auto-save.")
        
        sim.run()
        shutil.rmtree(run_cfg.folder_path)

        
    def test_autosave_backup(self):
        num_autosaves = 5
        class DeltaInfected(DeltaCol):
            count = 0
            def autosave(self):
                super().autosave()        
                DeltaInfected.count += 1

                if DeltaInfected.count == num_autosaves:
                    raise AsteroidError()

        stop_time = 50000000
        ColsT = {
            "cr": CreationRateCol,
            "den_vel": DenVelCol,
            "delta": DeltaInfected,
            "checkpoint": CheckpointCol,
            "snaps": SnapshotsCol,
        }

        run_cfg, configs = self.exec_collect(stop_time, ColsT)

        run_cfg.checkpoint = CheckpointCfg(run_cfg.folder_path / "autosave")
        sim = Simulation(**configs)


        autosave_dt = 5
        expected_time = autosave_dt * (num_autosaves - 1) 
        if sim.solver.time < expected_time - 1 or sim.solver.time > expected_time + 1:
            print("Solver time:", sim.solver.time)
            raise Exception("Tempo do solver incorreto após o carregamento.")    
        
        sim.run()
        shutil.rmtree(run_cfg.folder_path)

    @staticmethod
    def exec_collect(stop_time: float, ColsT: dict[str, RingCol]):
        configs = load_configs(configs_path)
        run_cfg: CollectDataCfg = configs["run_cfg"]
        dynamic_cfg = configs["dynamic_cfg"]
        radius = utils.ring_radius(
            p_diameter = dynamic_cfg.diameter,
            num_particles = configs["creator_cfg"].num_p,
        )

        # Configurações dos coletores
        func_cfg = {}

        center_region = -4 * 2*radius
        wait_dist = 4 * 2*radius
        xlims = [center_region - radius, center_region + radius]
        func_cfg["delta"] = {
            "min_num_rings": 1,
            "wait_dist": wait_dist,  
            "xlims": [center_region - radius, center_region + radius],
            "start_dt": (xlims[1] - xlims[0]) * dynamic_cfg.vo,
            "check_dt": 1/4 * (xlims[1] - xlims[0]) * dynamic_cfg.vo,
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
            ),
        }

        func_cfg["autosave_cfg"] = ColAutoSaveCfg(freq_dt=5)

        class DeltaInfected(DeltaCol):
            count = 0
            def autosave(self):
                super().autosave()        
                DeltaInfected.count += 1

                if DeltaInfected.count > 2:
                    raise AsteroidError()

        # Rodando a simulação
        run_cfg: CollectDataCfg = configs["run_cfg"]
        run_cfg.folder_path = current_folder / "tmp"
        run_cfg.func_cfg = func_cfg
        run_cfg.func = TestRingCols.get_pipeline(
            stop_time=stop_time,
            ColsT=ColsT,
        )

        try:
            Simulation(**configs).run()
        except AsteroidError as e:
            print("ASTEORIDE")
            pass

        return run_cfg, configs
    
    @staticmethod
    def get_pipeline(stop_time, ColsT: dict[str, RingCol]):
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

            for name, ColT in ColsT.items():
                col.add_collector(ColT, cfg.get(name, {}), name)

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