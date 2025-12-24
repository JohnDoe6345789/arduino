#include "simulator/board.hpp"
#include <fmt/format.h>
#include <cassert>

int main() {
    simulator::Board board{"Test", 4, 2};
    board.set_pin_mode(1, simulator::PinMode::Output);
    board.write_digital(1, true);
    board.tick();

    assert(board.read_digital(1) == true);
    fmt::print("Smoke test passed for {}\n", board.name());
    return 0;
}
