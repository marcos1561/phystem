#pragma once

#include <chrono>
#include <vector>

class TimeIt {
public:
    TimeIt(int num_samples);

    void start();
    void end();
    double mean_time();

private:
    int num_samples;
    int count;

    bool is_full;

    std::chrono::_V2::system_clock::time_point t1;

    std::vector<int64_t> times; 
};

