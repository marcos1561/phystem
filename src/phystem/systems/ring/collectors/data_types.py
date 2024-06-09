import numpy as np

class ArraySizeAware:
    def __init__(self, num_data_points: int, max_num_els: int, num_dims: int, dtype=np.float32) -> None:
        self.data = np.zeros((num_data_points, max_num_els, num_dims), dtype=dtype)
        self.point_num_elements = np.zeros(num_data_points, dtype=int)
        self.current_id = 0

    def add(self, data: np.array):
        self.update(self.current_id, data)
        self.current_id += 1

    def update(self, id, data: np.array):
        num_elements = data.shape[0]
        self.data[id,:num_elements] = data
        self.point_num_elements[id] = num_elements

    def reset(self):
        self.current_id = 0
        self.point_num_elements[:] = 0
        self.data[:] = 0

    def strip(self):
        self.data = self.data[:self.num_points]
        self.point_num_elements = self.point_num_elements[:self.num_points]

    def __getitem__(self, key):
        return self.data[key][:self.point_num_elements[key]]

    @property
    def num_points(self):
        return self.current_id

    @property
    def is_full(self):
        return self.current_id >= self.data.shape[0]
