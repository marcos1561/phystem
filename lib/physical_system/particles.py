import numpy as np

from physical_system.configs import CreateType, CreateCfg

class Particles:
    def __init__(self, create_cfg: CreateCfg, rng_seed=None) -> None:
        self.create_cfg = create_cfg

        self.pos: np.ndarray
        self.vel: np.ndarray

        self.rng = np.random.default_rng(rng_seed)

        self.create_type_to_func = {
            CreateType.CIRCLE: self.circle,
            CreateType.SQUARE: self.square,
        }

    def create(self):
        self.create_type_to_func[self.create_cfg.type]()

    def square(self):
        r = self.create_cfg.r

        x, y = r * (self.rng.random((2, self.create_cfg.n)) * 2 - 1)
        self.pos = np.array([x, y], dtype=np.float64)

        theta = self.rng.random(self.create_cfg.n) * 2 *np.pi
        self.vel = np.array([np.cos(theta), np.sin(theta)], dtype=np.float64)

    def circle(self):
        r = self.create_cfg.r

        x, y = r* (self.rng.random((2, self.create_cfg.n*30)) * 2 - 1)
        filter = x**2 + y**2 < r
        self.pos = np.array([x[filter], y[filter]], dtype=np.float64)[:,:self.create_cfg.n]

        theta = self.rng.random(self.create_cfg.n) * 2 *np.pi
        self.vel = np.array([np.cos(theta), np.sin(theta)], dtype=np.float64)

    def plot(self):
        return self.pos
