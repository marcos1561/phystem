import numpy as np

from phystem.systems.ring.quantities.calculators import DeltaCalculator, CalcAutoSaveCfg
from phystem.systems.ring.quantities.datas import DeltaData

data = DeltaData("data/test1")

calc = DeltaCalculator(data, edge_k=1.7, root_path="results/test1")
calc.crunch_numbers()

calc2 = DeltaCalculator(data, edge_k=1.7, root_path="results/test2",
    autosave_cfg=CalcAutoSaveCfg(freq=3))
calc2.crunch_numbers(id_stop=7)

calc2 = DeltaCalculator.from_checkpoint("results/test2/autosave")
calc2.crunch_numbers()

print("deltas diff:", ((np.array(calc.deltas) - np.array(calc2.deltas))**2).sum())
print("times diff :", ((np.array(calc.times) - np.array(calc2.times))**2).sum())