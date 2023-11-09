
class DynamicCfg:
    def __init__(self, vo: float, noise_strength: float):
        self.vo = vo
        self.noise_strength = noise_strength
    
class CreatorCfg:
    def __init__(self, speed: float,  size: int) -> None:
        self.speed = speed
        self.size = size
    
    def get_pars(self):
        return {
            "speed": self.speed,
            "size": self.size,
        }

class SpaceCfg:
    def __init__(self, size: float) -> None:
        self.size = size