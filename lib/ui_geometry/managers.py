class Buttons:
    def __init__(self, main_ax_rect: list, width=None, height=None, x_pad=0.01, y_pad=0.01, rel_pad=0.01) -> None:
        self.main_rect = main_ax_rect

        self.width = width
        if width is None:
            self.width = main_ax_rect[2] * 0.6
        
        self.height = height
        if height is None:
            self.height = main_ax_rect[3] * 0.1

        self.pads = {"x": x_pad, "y": y_pad, "rel": rel_pad}
        
        self.next_rect = [
            main_ax_rect[0] + x_pad, 
            main_ax_rect[1] + main_ax_rect[3] - y_pad - self.height,
            self.width, 
            self.height,
        ]

    def get_new_rect(self):
        rect = self.next_rect.copy()
        self.next_rect[1] -= self.height + self.pads["rel"] 
        return rect
