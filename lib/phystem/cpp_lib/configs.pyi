class SelfPropellingCfg:
    def __init__(self, values: dict[str, float]) -> None: ...
    def info() -> None: ...

class RingCfg:
    def __init__(self, values: dict[str, float]) -> None: ...

class InPolCheckerCfg: 
    def __init__(self, num_cols_windows: int, update_freq: int) -> None: ...