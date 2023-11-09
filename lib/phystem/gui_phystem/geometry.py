from phystem.gui_phystem.widget import WidgetType

class VerticalGeometry:
    def __init__(self, main_ax_rect: list, width=None, height=None, x_pad=0.01, y_pad=0.01, rel_pad=0.01) -> None:
        '''
        Coloca rect's de axes em ordem vertical dentro do rect do axe principal.

        Parameters:
        -----------
            main_ax_rect:
                rect do axe principal.
            
            width:
                Comprimento dos axes (em porcentagem da tela)
            
            width:
                Altura dos axes (em porcentagem da tela)
            
            x_pad:
                Pad em relação as bordas verticais do axe principal.
            
            y_pad:
                Pad em relação as bordas horizontais do axe principal.
            
            rel_pad:
                Pad em relação as axes entre si.

        Attributes:
        -----------
            widget_order: [str]
                Ordem dos axes colocados.
        '''
        self.main_rect = main_ax_rect
        
        self.widget_order = []

        if width is None:
            self.width = main_ax_rect[2] * 0.6
        else:
            self.width = main_ax_rect[2] * width

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

    def get_new_rect(self, name: str, type: WidgetType) -> list:
        '''
        Retorna o próximo rect da coluna.

        Parameters:
        -----------
            name:
                Nome do novo axe.
            
            type:
                Qual o tipo do widget que esse axe representa.
            
        Return:
        -------
            rect:
        '''
        self.widget_order.append((name, type)) 

        rect = self.next_rect.copy()
        self.next_rect[1] -= self.height + self.pads["rel"] 
        return rect
