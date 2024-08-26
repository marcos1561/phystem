import numpy as np
from phystem.systems.ring.quantities import calculators, datas

name = "test_delta_2/delta" 
# name = "adh_1_bigger_force/delta" 
delta_data = datas.DeltaData(f"datas/{name}")
# delta_data = datas.DeltaData("datas/test_delta/delta")

# import matplotlib.pyplot as plt
# num_points = []
# for i in range(0, delta_data.num_points_completed):
#     pid = delta_data.ids_completed[i]
#     num_points.append(delta_data.init_selected_uids[pid].size)
# plt.scatter(range(len(num_points)), num_points)
# plt.show()

# print(delta_data.num_points_completed)
# print(delta_data.ids_completed[delta_data.num_points_completed-1])

for i in range(0, delta_data.num_points_completed):
    pid = delta_data.ids_completed[i]
    init_shape = np.array(delta_data.init_cms[pid]).shape
    final_shape = np.array(delta_data.final_cms[pid]).shape
    if init_shape != final_shape:
        print(i)

# print(delta_data.init_cms[5].shape)
# print(delta_data.final_cms[5].shape)

# name = "test_delta_2"
# delta_calc = calculators.DeltaCalculator(f"datas/{name}/delta", edge_k=1.4, root_path=f"results/{name}")
# delta_calc.crunch_numbers()

# delta_data = calculators.DeltaCalculator.load_data(f"results/{name}")

# import matplotlib.pyplot as plt

# plt.plot(delta_data.times, delta_data.deltas)
# plt.show()
