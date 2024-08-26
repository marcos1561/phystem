from phystem.systems.ring.quantities.calculators import DenVelCalculator,  DeltaCalculator, CalcAutoSaveCfg
from pathlib import Path
import time, shutil

name = "test_save_data"
data_path = Path(f"datas/{name}")
root_path = Path(f"results/{name}")

t1 = time.time()
delta = DeltaCalculator(data_path / "delta", edge_k=1.4, root_path=root_path / "delta")
den_vel = DenVelCalculator(data_path / "den_vel", root_path=root_path / "den_vel")

delta.crunch_numbers(to_save=True)
den_vel.crunch_numbers(to_save=True)

cr_dest_path = root_path / "cr"
if cr_dest_path.exists():
    shutil.rmtree(cr_dest_path)
shutil.copytree(data_path / "cr", cr_dest_path)

t2 = time.time()

print(f"Elapsed Time: {t2 -t1}")
