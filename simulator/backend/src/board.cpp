#include "simulator/board.hpp"

#include <stdexcept>

namespace simulator {

Board::Board(std::string name, std::size_t digital_pins, std::size_t analog_pins)
    : name_(std::move(name)), digital_pins_(digital_pins), analog_pins_(analog_pins) {}

const std::string &Board::name() const { return name_; }

void Board::set_pin_mode(std::size_t index, PinMode mode) {
    if (index < digital_pins_.size()) {
        digital_pins_[index].mode = mode;
        return;
    }
    if (index < analog_pins_.size()) {
        analog_pins_[index].mode = mode;
        return;
    }
    throw std::out_of_range{"Invalid pin index"};
}

void Board::write_digital(std::size_t index, bool level) {
    validate_digital_index(index);
    digital_pins_[index].mode = PinMode::Output;
    digital_pins_[index].digital_level = level;
}

bool Board::read_digital(std::size_t index) const {
    validate_digital_index(index);
    return digital_pins_[index].digital_level;
}

void Board::write_analog(std::size_t index, double level) {
    validate_analog_index(index);
    analog_pins_[index].mode = PinMode::AnalogOut;
    analog_pins_[index].analog_level = level;
    scheduled_ramps_[index] = level;
}

double Board::read_analog(std::size_t index) const {
    validate_analog_index(index);
    return analog_pins_[index].analog_level;
}

void Board::tick() {
    // Apply a simple decay to analog outputs to mimic RC circuits and energy loss.
    constexpr double decay_factor = 0.95;
    for (std::size_t i = 0; i < analog_pins_.size(); ++i) {
        if (analog_pins_[i].mode == PinMode::AnalogOut) {
            analog_pins_[i].analog_level *= decay_factor;
        }
    }

    // Restore scheduled ramps to their target value so UI polling shows activity.
    for (const auto &entry : scheduled_ramps_) {
        const auto index = entry.first;
        if (index < analog_pins_.size()) {
            analog_pins_[index].analog_level = entry.second;
        }
    }
}

std::vector<PinState> Board::snapshot() const {
    std::vector<PinState> states;
    states.reserve(digital_pins_.size() + analog_pins_.size());
    states.insert(states.end(), digital_pins_.begin(), digital_pins_.end());
    states.insert(states.end(), analog_pins_.begin(), analog_pins_.end());
    return states;
}

void Board::validate_digital_index(std::size_t index) const {
    if (index >= digital_pins_.size()) {
        throw std::out_of_range{"Digital pin index out of range"};
    }
}

void Board::validate_analog_index(std::size_t index) const {
    if (index >= analog_pins_.size()) {
        throw std::out_of_range{"Analog pin index out of range"};
    }
}

} // namespace simulator
