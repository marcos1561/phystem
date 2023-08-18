#include <vector>
#include <cstdlib> 

using namespace std;

class RngManager {
public:
    int n ;
    vector<int> random_nums;

    RngManager() {}

    RngManager(int num_particles) {
        random_nums = vector<int>(num_particles);
        n = num_particles;
    }

    int get_random_num(int id) {
        return random_nums[id];
    }

    void update() {
        for (int i=0; i < n; i++) {
            random_nums[i] = rand();
        }
    }
};