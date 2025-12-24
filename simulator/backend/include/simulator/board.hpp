#pragma once

#include <cstddef>
#include <string>
#include <unordered_map>
#include <vector>

namespace simulator {

enum class PinMode {
    Input,
    Output,
    AnalogIn,
    AnalogOut
};

struct PinState {
    PinMode mode{PinMode::Input};
    bool digital_level{false};
    double analog_level{0.0};
};

class Board {
public:
    Board(std::string name, std::size_t digital_pins, std::size_t analog_pins);

    const std::string &name() const;

    void set_pin_mode(std::size_t index, PinMode mode);
    void write_digital(std::size_t index, bool level);
    bool read_digital(std::size_t index) const;
    void write_analog(std::size_t index, double level);
    double read_analog(std::size_t index) const;

    void tick();
    std::vector<PinState> snapshot() const;

private:
    void validate_digital_index(std::size_t index) const;
    void validate_analog_index(std::size_t index) const;

    std::string name_;
    std::vector<PinState> digital_pins_;
    std::vector<PinState> analog_pins_;
    std::unordered_map<std::size_t, double> scheduled_ramps_;
};

} // namespace simulator
