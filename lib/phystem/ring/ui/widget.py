from typing import Callable
from matplotlib.axes._axes import Axes
from matplotlib.widgets import Button, Slider, CheckButtons
from matplotlib.axes import Axes

from phystem.core.run_config import RealTimeCfg, RunType
from phystem.ring.ui.graph import GraphCfg
from ui_phystem import widget

class CheckButtonsV:
    def __init__(self, ax: Axes, labels: dict[str, str], actives: dict[str, bool], callback: dict[str, Callable],
        colors: dict[str, str]={}, rel_pad=0) -> None:
        self.buttons = {}

        label_props = {name: {} for name in labels.keys()}
        frame_props = {name: {} for name in labels.keys()}
        check_props = {name: {} for name in labels.keys()}
        
        for name, c in colors.items():
            label_props[name]["color"] = [c]
            frame_props[name]["edgecolor"] = [c]
            check_props[name]["facecolor"] = [c]

        n = len(labels)
        width = (1 - (n-1) * rel_pad) / n
        cb_x = 0
        for internal_name in labels.keys(): 
            l = labels[internal_name]
            is_active = actives[internal_name]

            cb_ax = ax.inset_axes([cb_x, 0, width, 1], xticks=[], yticks=[])
            
            cb_x += width + rel_pad

            cb = CheckButtons(cb_ax, [l], [is_active], label_props=label_props[internal_name],
                frame_props=frame_props[internal_name], check_props=check_props[internal_name])
            cb.on_clicked(callback[internal_name])
            self.buttons[internal_name] = cb

        ax.set_xticks([])
        ax.set_yticks([])

        
class WidgetManager(widget.StandardManager):
    def __init__(self, buttons_ax, slider_ax, run_cfg: RealTimeCfg) -> None:
        super().__init__(buttons_ax, slider_ax, run_cfg)
        self.graph_cfg: GraphCfg = run_cfg.graph_cfg

        self.buttons["circles"] = Button(buttons_ax["circles"], "Show Circles")
        self.buttons["circles"].on_clicked(self.circles_callback)

        internal_name_to_label = {
            "spring": "F_spring",
            "vol": "F_vol",
            "area": "F_area",
            "total": "F_total",
        }
        self.force_label_to_internal = dict(zip(internal_name_to_label.values(), internal_name_to_label.keys()))
        self.buttons["check_buttons"] = CheckButtonsV(
            ax=buttons_ax["check_buttons"],
            labels=internal_name_to_label,
            actives=self.graph_cfg.f_name_to_show,
            callback=dict(zip(internal_name_to_label.keys(), [self.forces_callback]*len(internal_name_to_label.keys()))),
            rel_pad=0,
            colors=self.graph_cfg.force_to_color,
        )
       
        internal_name_to_label = {"pos_cont": "Show pos_cont" }
        self.pos_cont_label_to_internal = dict(zip(internal_name_to_label.values(), internal_name_to_label.keys()))
        self.buttons["cb_pos_cont"] = CheckButtonsV(
            ax=buttons_ax["cb_pos_cont"],
            labels=internal_name_to_label,
            actives={"pos_cont": self.graph_cfg.show_pos_cont},
            callback={"pos_cont": self.pos_cont_callback},
        )
        
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

    def pos_cont_callback(self, label):
        self.graph_cfg.show_pos_cont = not self.graph_cfg.show_pos_cont

    def forces_callback(self, label):
        internal_l = self.force_label_to_internal[label]
        self.graph_cfg.f_name_to_show[internal_l] = not self.graph_cfg.f_name_to_show[internal_l] 

    def circles_callback(self, event):
        if self.graph_cfg.show_circles:
            self.graph_cfg.show_circles = False
        else:
            self.graph_cfg.show_circles = True
    
    def freq_callback(self, val):
        self.run_cfg.frequency = int(val)

# class CheckButtonsV(CheckButtons):
#     def __init__(self, ax: Axes, labels: Sequence[str], actives: Sequence[bool] = ..., x_pad=0.03, box_pad=0.02) -> None:
#         super().__init__(ax, labels, actives)

#         cb = self

#         box_w = cb.rectangles[0].get_width()
#         box_x = cb.rectangles[0].get_x()
#         cb.labels[0].set_x(box_x + box_w + box_pad)
#         # cb.labels[0].set_fontsize(5)

#         num_cb = len(cb.labels)
#         for cb_id in range(1, num_cb):
#             x2 = x_pad + ax.transData.inverted().transform(cb.labels[cb_id-1].get_tightbbox(ax.get_figure().canvas.get_renderer()))[1][0]

#             cb.rectangles[cb_id].set_x(x2)
#             cb.rectangles[cb_id].set_y(cb.rectangles[cb_id-1].get_y())

#             y2 = cb.lines[cb_id-1][0].get_ydata()[0]
#             h = cb.lines[cb_id-1][0].get_ydata()[1] - y2
#             dy = 1. / (num_cb + 1)
#             for i in range(2):
#                 p1, p2 = cb.lines[cb_id][i].get_data()
#                 p1[0] = x2, x2 + dy/2
#                 p1[0] = x2, x2 + dy/2
                
#                 if i == 0:
#                     p2 = [y2 + h, y2]
#                 else:
#                     p2 = [y2, h + y2]

#                 cb.lines[cb_id][i].set_data(p1[0], p2)

#             box_w = cb.rectangles[cb_id].get_width()
#             cb.labels[cb_id].set_x(x2+box_w + box_pad)
#             cb.labels[cb_id].set_y(cb.labels[cb_id-1].get_position()[1])