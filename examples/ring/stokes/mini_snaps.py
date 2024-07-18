from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.run_config import CheckpointCfg, CollectDataCfg
from phystem.systems.ring.collectors import SnapshotsCol, SnapshotsColCfg

collect_data_cfg = CollectDataCfg(
    int_cfg=None,
    folder_path="data/teste",
    tf=2,
    func=SnapshotsCol.pipeline,
    func_cfg=SnapshotsColCfg(
        snaps_dt=0.2,
    ),
    checkpoint=CheckpointCfg(
        root_path="data/init_state_flux-0_5/checkpoint"
    )
)

configs = Simulation.configs_from_checkpoint(collect_data_cfg)
Simulation(**configs).run()
