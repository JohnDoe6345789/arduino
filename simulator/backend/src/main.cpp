#include "simulator/board.hpp"

#include <fmt/format.h>
#include <chrono>
#include <thread>

namespace {
void drive_led_pattern(simulator::Board &board) {
    board.set_pin_mode(0, simulator::PinMode::Output);
    for (int i = 0; i < 10; ++i) {
        const bool level = i % 2 == 0;
        board.write_digital(0, level);
        board.write_analog(0, level ? 1.0 : 0.2);
        board.tick();
        fmt::print("[tick {:02}] D0={} A0={:.2f}\n", i, board.read_digital(0), board.read_analog(0));
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
}
} // namespace

int main() {
    simulator::Board board{"Uno-like", 14, 6};
    fmt::print("Simulating board: {} with {} digital pins and {} analog pins.\n",
               board.name(), 14, 6);

    drive_led_pattern(board);

    auto states = board.snapshot();
    fmt::print("Captured {} pins in snapshot.\n", states.size());
    return 0;
}
