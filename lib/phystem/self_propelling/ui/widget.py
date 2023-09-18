from matplotlib.widgets import Button, Slider

from phystem.self_propelling.run_config import RealTimeCfg
from phystem.self_propelling.run_config import RealTimeCfg
from phystem.core.run_config import RealTimeCfg, RunType
from ui_phystem import widget

class WidgetManager(widget.StandardManager):
    def __init__(self, buttons_ax, slider_ax, run_cfg: RealTimeCfg) -> None:
        super().__init__(buttons_ax, slider_ax, run_cfg)
        
        self.buttons["circles"] = Button(buttons_ax["circles"], "Show Circles")
        self.buttons["circles"].on_clicked(self.circles_callback)
        
        if run_cfg.id is RunType.REPLAY_DATA:
            self.sliders["freq"] = Slider(
                ax=slider_ax["freq"],
                label="freq",
                valmin=0,
                valmax=10,
                valstep=1,
                valinit=run_cfg.frequency
            )
            self.sliders["freq"].label.set_position((0, 1)) 
            self.sliders["freq"].label.set_horizontalalignment("left")
            self.sliders["freq"].on_changed(self.freq_callback)

    def circles_callback(self, event):
        if self.run_cfg.graph_cfg.show_circles:
            self.run_cfg.graph_cfg.show_circles = False
        else:
            self.run_cfg.graph_cfg.show_circles = True
    
    def freq_callback(self, val):
        self.run_cfg.frequency = int(val)