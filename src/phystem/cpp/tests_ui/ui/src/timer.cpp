#include "headers/timer.h"

using namespace std::chrono;

TimeIt::TimeIt(int in_num_samples) {
    times = std::vector<int64_t>(in_num_samples, 0);
    count = 0;
    is_full = false;
    num_samples = in_num_samples;
}

void TimeIt::start() {
    t1 = high_resolution_clock::now();
}

void TimeIt::end() {
    auto t2 = high_resolution_clock::now();

    auto duration = duration_cast<microseconds>(t2 - t1).count();
    times[count] = duration;
    count += 1;
    if (count == num_samples) {
        is_full = true;
        count = 0;
    }
}

double TimeIt::mean_time() {
    int n = count;
    if (is_full) {
        n = num_samples;
    } 
    
    int64_t sum = 0;
    for (int i = 0; i < n; i++)
    {
        sum += times[i];
    }
    
    return ((double)sum / 1000.0) / (double)n;
    // return sum;
} 
