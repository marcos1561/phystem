class UiSettings:
    def __init__(self, window_scale=0.83, dpi=190, left_pannel_size=0.3,
        InfoT=None, ControlT=None) -> None:
        self.window_scale = window_scale
        self.dpi = dpi
        self.left_pannel_size = left_pannel_size

        self.InfoT = InfoT
        self.ControlT = ControlT