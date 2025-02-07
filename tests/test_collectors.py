import unittest, os, shutil
from pathlib import Path

from phystem.systems.ring import Simulation, utils
from phystem.systems.ring.configs import RingCfg
from phystem.core.run_config import load_configs, CollectDataCfg, CheckpointCfg
from phystem.systems.ring.collectors import *
from phystem.systems.ring.quantities.datas import *

CURRENT_FOLDER = Path(os.path.dirname(__file__))
CONFIGS_PATH = CURRENT_FOLDER / "data_test/ring/configs/collectors_configs"

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
        configs = load_configs(CONFIGS_PATH)
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
        run_cfg.folder_path = CURRENT_FOLDER / "tmp"
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

@dataclass
class InfectedCfg(quantity_pos.base.QuantityCfg):
    name = "infected"
    num_dims = 1
    to_crash = True
    stop_time: float = None

class InfectedCol(quantity_pos.base.QuantityCol):
    configs: InfectedCfg

    def to_collect(self, time_dt, is_time):
        return True
    
    def collect(self, ids_in_region, cms_in_region):
        if self.configs.to_crash and self.solver.time > self.configs.stop_time:
            self.state.has_crashed = True
            raise AsteroidError
        
quantity_pos.quantity_cfg_to_col[InfectedCfg] = InfectedCol


class TestQuantityPos(unittest.TestCase):
    def test_autosave(self):
        '''
        Check if QuantityPos collectors have an equal number of collected data points
        and saved time points, with the collection process crashing and resuming
        using an autosave.
        '''
        configs = load_configs(CONFIGS_PATH)
        run_cfg: CollectDataCfg = configs["run_cfg"]
        dynamic_cfg: RingCfg = configs["dynamic_cfg"]
        radius = dynamic_cfg.get_ring_radius()
        
        #== Parameters ==#
        tf = 120
        stop_times = [50, 80]
        collect_time = 1
        autosave_freq_time = 5

        quantities_cfg=[
            quantity_pos.VelocityCfg(frame_dt=utils.time_to_num_dt(0.3, run_cfg.int_cfg.dt)),
            quantity_pos.PolarityCfg(),
            quantity_pos.AreaCfg(),
            InfectedCfg(),
        ]

        datas_list = {
            "cms": CmsData,
            "vel": VelData,
            "pol": PolData,
            "area": AreaData,
        }
        #================#
        
        # Collectors configuration
        center_region = -4 * 2*radius
        func_cfg = ColManagerCfg(
            cols_cfgs={
            "q": QuantityPosCfg(
                collect_dt=utils.time_to_num_dt(collect_time, run_cfg.int_cfg.dt),
                xlims=[center_region - radius, center_region + radius],
                quantities_cfg=quantities_cfg,
            ),
            "cr": CreationRateColCfg(
                wait_time=4, collect_time=stop_times[0] - 4, collect_dt=2,
            ),
            },
            autosave_cfg=ColAutoSaveCfg(freq_dt=autosave_freq_time),
        ) 
        

        # Running simulation
        run_cfg.folder_path = CURRENT_FOLDER / "tmp"
        run_cfg.tf = tf
        run_cfg.func_cfg = func_cfg

        for idx, stop_time in enumerate(stop_times + [-1]):
            if idx == 0:
                col_cfg: InfectedCfg
                for col_cfg in func_cfg.cols_cfgs["q"].quantities_cfg:
                    if type(col_cfg) is InfectedCfg:
                        break
                col_cfg.stop_time = stop_time
            else:
                # Reloading simulation
                configs = Simulation.configs_from_autosave(run_cfg.folder_path / "autosave")
                
                if stop_time != -1:
                    cr_cfg: CreationRateColCfg = configs["run_cfg"].func_cfg.cols_cfgs["cr"]
                    cr_cfg.collect_time = stop_time - cr_cfg.wait_time 

                for col_cfg in configs["run_cfg"].func_cfg.cols_cfgs["q"].quantities_cfg:
                    if type(col_cfg) is InfectedCfg:
                        break
                col_cfg.stop_time = stop_time
                if stop_time == -1:
                    col_cfg.to_crash = False

            sim = Simulation(**configs)

            if idx > 0:
                if sim.solver.time < stop_times[idx-1] - autosave_freq_time:
                    raise Exception((
                        f"Tempo do solver ({sim.solver.time}) está errado após o carregamento do auto-save. "
                        f"Deveria ser >= {stop_times[idx-1] - autosave_freq_time}"
                    ))
                
            if stop_time != -1:
                try:
                    sim.run()
                except AsteroidError as e:
                    print("Asteroid!")
            else:
                sim.run()

        datas: dict[str, BaseData] = {name: DataT(run_cfg.folder_path / "q") for name, DataT in datas_list.items()}

        all_times = []
        for name, d in datas.items():
            time_length = d.times.size
            data_length = len(d.__getattribute__(name))
            
            all_times.append(time_length)

            if name == "vel" and not d.last_point_completed:
                data_length += 1

            self.assertEqual(time_length, data_length, f"{name}: data.times.size != len(data.{name})")
            self.assertEqual(time_length, len(d.cms), f"{name}: data.times.size != len(data.cms)")

        self.assertEqual(np.array(all_times).all(), True, "times")

        cr_data = CreationRateData(run_cfg.folder_path / "cr")

        self.assertEqual(cr_data.times.size, cr_data.num_active.size)
        self.assertEqual(cr_data.times.size, cr_data.num_created.size)

        shutil.rmtree(run_cfg.folder_path)

if __name__ == '__main__':
    unittest.main()