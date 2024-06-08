import time
from datetime import timedelta
import numpy as np
from abc import ABC, abstractmethod
import logging

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ProgressType:
    mid = 0
    end = 1
    nothing = 2

class Progress(ABC):
    def __init__(self, end: float, start=0) -> None:
        self.start = start
        self.total = end - start
        self.start_time = time.time()

        self.has_inform_first_estimate = False
        self.has_ended = False

    @abstractmethod
    def get_progress_type(self, t: float) -> int:
        pass

    def to_inform_first_progress(self):
        if not self.has_inform_first_estimate:
            elapsed_time = time.time() - self.start_time
            if elapsed_time > 10:
                logger.debug("Call em informar primeiro progresso")

                self.has_inform_first_estimate = True
                return True
            else:
                return False
        else:
            return False

    def update(self, t: float):
        t -= self.start
        p_type = self.get_progress_type(t)

        if p_type == ProgressType.mid:
            p = t/self.total * 100

            slope = 0
            if p > 0:
                slope = (time.time() - self.start_time)/p
            remained_time = (100 - p) * slope

            print(
                f"Progresso: {p:.2f} % | {str(timedelta(seconds=remained_time))}")
        elif p_type == ProgressType.end and not self.has_ended:
            self.has_ended = True
            total_time = time.time() - self.start_time
            print(
                f"Progresso: {100.00:.2f} %\nTempo total: {str(timedelta(seconds=total_time))}")

class Discrete(Progress):
    def __init__(self, end: int, step: int) -> None:
        super().__init__(end)
        self.count_step = int(end * step/100)
        if self.count_step == 0:
            self.count_step = 1

    def get_progress_type(self, t: float) -> int:
        to_inform_first_estimate = self.to_inform_first_progress()
        if t % self.count_step == 0 or to_inform_first_estimate:
            if t > 0:
                self.has_inform_first_estimate = True

            return ProgressType.mid
        elif t >= self.total:
            return ProgressType.end
        else:
            return ProgressType.nothing

class Continuos(Progress):
    def __init__(self, end: float, start=0, step: int = 10) -> None:
        super().__init__(end, start)

        self.interval_lims: np.ndarray = np.linspace(0, end-start, step)
        self.interval_mask = np.zeros(self.interval_lims.size-1)

    def where_interval(self, t: float) -> int:
        interval_id = 0
        for id, lim in enumerate(self.interval_lims):
            if t < lim:
                interval_id = id - 1
                break
        else:
            return self.interval_lims.size

        return interval_id

    def get_progress_type(self, t: float) -> int:
        interval_id = self.where_interval(t)
        if interval_id >= self.interval_mask.size:
            return ProgressType.end

        to_inform_first_estimate = self.to_inform_first_progress()

        if not self.interval_mask[interval_id] or to_inform_first_estimate:
            if t > 0:
                self.has_inform_first_estimate = True

            self.interval_mask[interval_id] = True
            return ProgressType.mid
        else:
            return ProgressType.nothing

class MplAnim(Discrete):
    def update(self, t: int, _: int):
        super().update(t)

if __name__ == "__main__":
    n = 100 + 50
    dt = 1

    prog = Continuos(100, 10)

    t = 0
    while t < n:
        t += dt

        if t == 88:
            print()

        print(t)
        prog.update(t)