import numpy as np
import time

class TimeIt:
    def __init__(self, num_samples: int = 100) -> None:
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