#include <iostream>
#include <vector>

int main()
{
    std::vector<double> values;

    values.reserve(2);

    std::cout << "Sau reserve:\n";
    std::cout << "size = " << values.size() << '\n';
    std::cout << "capacity = " << values.capacity() << '\n';

    values.resize(2, 0.0);

    std::cout << "\nSau resize:\n";
    std::cout << "size = " << values.size() << '\n';
    std::cout << "values[0] = " << values.at(0) << '\n';
    std::cout << "values[1] = " << values.at(1) << '\n';
}