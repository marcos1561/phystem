class UiSettings:
    def __init__(self, window_scale=0.83, dpi=130, left_pannel_size=0.3,
        always_update=False, InfoT=None, ControlT=None) -> None:
        self.window_scale = window_scale
        self.dpi = dpi
        self.left_pannel_size = left_pannel_size
        self.always_update = always_update

        self.InfoT = InfoT
        self.ControlT = ControlT