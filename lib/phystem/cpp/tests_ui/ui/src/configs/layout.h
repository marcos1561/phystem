#pragma once

namespace ui {
namespace configs
{

struct GuiLayout {
    float info_width;
};

class LayoutCfg {
public:
    float windows_scale;
    GuiLayout gui_layout;

    LayoutCfg(float windows_scale=1.3, GuiLayout gui_layout=GuiLayout{0.4}) : windows_scale(windows_scale), gui_layout(gui_layout) { }
};

} } 
