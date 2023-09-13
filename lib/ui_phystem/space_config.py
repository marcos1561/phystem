import matplotlib.pyplot as plt

from ui_phystem.widget import WidgetType

class StandardSpace:
    '''
    Configura a posição da UI que eu considero padrão.
    '''
    def __init__(self) -> None:
        self.fig = plt.figure()

        self.axes = {}
        self.space_mngs = {}

    def run(self):
        from ui_phystem import geometry
        fig = self.fig

        width = 0.2
        x_pad = 0.01
        y_pad = 0.01
        rel_y_pad = 0.01

        vertical_space = 1 - 2 * y_pad - rel_y_pad
        buttons_v_space = vertical_space/2
        info_v_space = vertical_space/2
        
        #==
        # Widgets
        #==
        bottom = y_pad
        left = x_pad
        buttons_ax = fig.add_axes([left, bottom, width, buttons_v_space], xticks=[], yticks=[])

        widget_space_mng = geometry.SpaceManager(buttons_ax.get_position().bounds, rel_pad=0.02)
        pause_button_ax = fig.add_axes(widget_space_mng.get_new_rect("pause", WidgetType.button))
        speed_slider_ax = fig.add_axes(widget_space_mng.get_new_rect("speed", WidgetType.slider))
        
        self.axes[WidgetType.button] = {
            "pause": pause_button_ax,
        }
        self.axes[WidgetType.slider] = {
            "speed": speed_slider_ax,
        }

        self.space_mngs["widgets"] = widget_space_mng

        #==
        # Info
        #==
        bottom = y_pad + buttons_v_space + rel_y_pad
        left = x_pad
        info_ax = fig.add_axes([left, bottom, width, info_v_space], xticks=[], yticks=[])
        self.axes["info"] = info_ax

        #==
        # Main
        #==
        bottom = 0.05

        info_rect = info_ax.get_position().bounds
        
        left = info_rect[0] + info_rect[2] + 0.05 
        h_space = 1 - left
        main_ax = fig.add_axes([
            left,
            bottom, 
            h_space/2,
            0.9
        ])

        self.axes["main"] = main_ax

        fig.set_size_inches(fig.get_size_inches()[0]*2.1, fig.get_size_inches()[1]*1.3)

        return fig, self.axes, self.space_mngs