#include <random>
#include <iostream>
#include <forward_list>
#include <algorithm>

template <typename T>
void remove_by_indices(std::forward_list<T>& flist, std::vector<size_t>& indices) {
    // Sort indices in descending order
    std::sort(indices.begin(), indices.end());

    for (auto idx : indices) {
        if (idx >= flist.max_size()) {
            throw std::out_of_range("Index out of range");
        }
    }

    auto prev = flist.before_begin();
    for (auto idx = indices.rbegin(); idx != indices.rend(); ++idx) {
        prev = flist.before_begin();
        for (size_t i = 0; i < *idx; ++i) {
            ++prev;
        }
        flist.erase_after(prev);
    }
}

struct ColInfo {
    int ring_id;
    int particle_id;
};

class ResolvedInv {
public:
    struct Invasion {
        ColInfo col;
        int num_steps_elapsed;
    };

    std::forward_list<Invasion> invasions;
    void add_collision(ColInfo col_info) {
        invasions.push_front(Invasion{col_info, 0});
    }
};

class Simulation {
public:
    ResolvedInv invasions;

    Simulation() {};
};

int main()
{
    Simulation sim;
    // sim.invasions.add_collision(ColInfo{1, 2});
    // sim.invasions.add_collision(ColInfo{2, -1});
    // sim.invasions.add_collision(ColInfo{3, -1});
    // sim.invasions.add_collision(ColInfo{4, -1});
    // sim.invasions.add_collision(ColInfo{5, -1});

    std::vector<size_t> ids;
    ids.push_back(10);
    for (auto i: ids) {
        std::cout << i << std::endl;
    }

    // for (const auto& i : sim.invasions.invasions) {
    //     std::cout << i.col.ring_id << std::endl;
    // }

    // std::vector<size_t> indices = {1,3};
    // remove_by_indices(sim.invasions.invasions, indices);
    
    // std::cout << "=======" << std::endl;
    // for (const auto& i : sim.invasions.invasions) {
    //     std::cout << i.col.ring_id << std::endl;
    // }
}