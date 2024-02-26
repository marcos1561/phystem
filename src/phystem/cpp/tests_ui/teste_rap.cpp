#include <iostream>
#include <array>

using namespace std;

class Cfg {
    int a;
};


template<class C>
class A {
public:
    C cfg;

    enum Item {item1, item2};

    void func_a() {
        func_b();
    }

    void func_b() {
        cout << "A" << endl;
    }
};

class B: public A<Cfg> {
public:
    void func_b() {
        cout << "B" << endl;
    }
};

using Vec2d = array<double, 2>;
using PosArray = array<Vec2d, 2>;

struct Abc {
    PosArray pos;
    Vec2d vel;
};

int main() {
    Abc abc;
        abc.pos = PosArray{
            Vec2d{1, 2},
            Vec2d{3, 4},
        };

        abc.vel = {0.0, 0.0};

    // array<double, 2> a{1, 2};
    // array<array<double, 2>, 2> a{
    // };

    cout << abc.pos[0][0] << ", " << abc.pos[1][1] << endl;
}