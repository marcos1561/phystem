from pathlib import Path
from phystem.systems import ring
from phystem.systems.ring.run_config import CollectDataCfg
import numpy as np

from phystem.systems.ring.collectors import SnapshotsCol

def collect_pos(sim: ring.Simulation, cfg):
    # Extraindo objetos de interesse
    solver = sim.solver
    collect_cfg: CollectDataCfg = sim.run_cfg
    
    # Pasta onde os dados serão salvos
    save_path = collect_cfg.folder_path 

    count = 0
    collect_last_time = solver.time
    times = []
    while solver.time < collect_cfg.tf:
        solver.update()

        if solver.time - collect_last_time > cfg["collect_dt"]:
            # Ids dos anéis ativos:
            # Em bordas periódicos isso é desnecessário
            # e self.solver.rings_ids pode ser utilizado
            # diretamente.
            ring_ids = solver.rings_ids[:solver.num_active_rings]

            # Posições dos anéis
            pos = np.array(solver.pos)[ring_ids]
            
            # Guardando o tempo de coleta
            times.append(solver.time)

            # Salvando as posições
            file_path = save_path / f"pos_{count}.npy"
            np.save(file_path, pos)
            
            count += 1
            collect_last_time = solver.time
    
    # Salvando o tempo
    file_path = save_path / "times.npy"
    np.save(file_path, np.array(times))

    # Salvando as configurações da simulação
    sim.save_configs(save_path / "configs")