#include <random>
#include <iostream>

int main()
{
    std::random_device dev;
    std::mt19937 rng(dev());
    std::uniform_int_distribution<std::mt19937::result_type> dist6(1,6); // distribution in range [1, 6]

    float a[] = {11, 21, 31, 41, 51, 61, 71, 81};

    std::cout << a[dist6(rng)] << std::endl;
}