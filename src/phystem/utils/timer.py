import numpy as np
import time

class FuncTimes:
    def __init__(self, num_samples) -> None:
        self.num_samples = num_samples
        self.times = np.zeros(num_samples)
        self.count = 0
        self.is_full = False

    def decorator(self, func: callable):
        t1 = time.time()
        func()
        t2 = time.time()

        self.times[self.count] = (t2 - t1)*1000
        self.count += 1
        if self.count == self.num_samples:
            self.is_full = True
            self.count = 0
    
    def mean_time(self):
        if self.is_full:
            return self.times.mean()
        else:
            if self.count == 0:
                return 0
            else:
                return self.times.sum() / self.count

class TimeIt:
    def __init__(self, funcs_names: list[str] = None, num_samples: int = 100) -> None:
        if funcs_names is None:
            funcs_names = []

        # self.times = np.zeros(num_samples)
        self.times: dict[str, FuncTimes] = {}
        for name in funcs_names:
            self.add_timer(name, num_samples)

    def add_timer(self, name: str, num_samples: int=100):
        if name in self.times.keys():
            raise Exception(f"Nome '{name}' já existe")
        self.times[name] = FuncTimes(num_samples)

    def decorator(self, name: str, func: callable):
        self.times[name].decorator(func)

    def mean_time(self, name: str):
        return self.times[name].mean_time()