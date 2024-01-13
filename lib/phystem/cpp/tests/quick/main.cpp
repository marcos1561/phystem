#include <iostream>
#include <vector>

using namespace std;

int main() {
    vector<int> a = {1, 2, 3};

    auto b = vector<int>(5, 1);

    int asd = 1;

    // cout << b.size() << endl;
    // b.assign(a.begin(), a.begin()+1);
    // cout << b.size() << endl;
    cout << b.at(100) << endl;
    for (auto el: b) {
        cout << el << ", ";
    }
    cout << endl;
}