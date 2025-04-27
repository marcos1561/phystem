class UiSettings:
    def __init__(self, window_scale=0.83, dpi=None, left_pannel_size=0.3,
        always_update=False, InfoT=None, ControlT=None, fig_size_scale=1.4) -> None:
        self.window_scale = window_scale
        self.dpi = dpi
        self.left_pannel_size = left_pannel_size
        self.always_update = always_update
        self.fig_size_scale = fig_size_scale

        self.InfoT = InfoT
        self.ControlT = ControlT