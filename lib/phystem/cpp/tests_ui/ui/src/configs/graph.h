#pragma once

namespace ui {
namespace configs {

class PointsCfg {
public:
    float color[3];

    PointsCfg(float color_in[3] = nullptr) {
        if (color_in == nullptr) {
            color[0] = 1.0;
            color[1] = 1.0;
            color[2] = 0.0;
        } else {
            for (int i = 0; i < 3; i++) {
                color[i] = color_in[i];
            }
        }
    };
};

} }