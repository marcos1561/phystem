#include "headers/application.h"

int main() {
    Application app;
    
    if (app.init() != 0) {
        return -1;
    }

    app.run();
    app.close();

    return 0;
}