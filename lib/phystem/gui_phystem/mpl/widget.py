from enum import Enum, auto
from matplotlib.widgets import Button, Slider

from phystem.core.run_config import RealTimeCfg

class WidgetType(Enum):
    button = auto()
    slider = auto()

class StandardManager:
    '''
    Controla a funcionalidade dos widgets.
    '''
    def __init__(self, buttons_ax, slider_ax, run_cfg: RealTimeCfg) -> None:
        self.run_cfg = run_cfg
        self.graph_cfg = run_cfg.graph_cfg

        self.buttons = {}
        self.sliders: dict[str, Slider] = {}
        
        self.buttons["pause"] = Button(buttons_ax["pause"], "Pause")
        self.buttons["pause"].on_clicked(self.pause_callback)
        
        self.sliders["speed"] = Slider(
            ax=slider_ax["speed"],
            label="speed",
            valmin=1,
            valmax=100,
            valstep=1,
            valinit=run_cfg.num_steps_frame
        )
        self.sliders["speed"].label.set_position((0, 1)) 
        self.sliders["speed"].label.set_horizontalalignment("left")
        self.sliders["speed"].on_changed(self.speed_callback)
        
        self.is_paused = False

    def pause_callback(self, event):
        if self.is_paused:
            self.is_paused = False
        else:
            self.is_paused = True
   
    def speed_callback(self, val):
        self.run_cfg.num_steps_frame = int(val)
    