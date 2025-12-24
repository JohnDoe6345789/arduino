# Arduino Projects

This repository contains Arduino sketches and libraries for various projects.

## Projects

### Lua Bot (`Arduino/lua_bot/`)
An Arduino sketch that executes Lua-like code through the serial port and responds to plain English commands.

**Features:**
- Execute Lua-like code via serial port
- Plain English command interface
- LED control with natural language
- Pin manipulation (read/write digital/analog)
- Variable storage and arithmetic
- Built on HumanReadableApi library

**Quick Start:**
```
led red
lua x = 5 + 3
write 13 HIGH
help
```

See [Arduino/lua_bot/README.md](Arduino/lua_bot/README.md) for full documentation.

### Starter Projects
- `Arduino/starter/` - Basic RGB LED rainbow animation
- `Arduino/starter2/` - RGB LED chatbot controller with patterns
- `Arduino/starter3/` - Advanced LED controller using HumanReadableApi

## Libraries

### HumanReadableApi (`Arduino/libraries/HumanReadableApi/`)
A command-line interface library for Arduino that makes it easy to create human-readable serial commands.

**Features:**
- Command registration and dispatch
- Argument parsing with quoted strings
- Help text generation
- Case-insensitive commands
- Comment support
- Custom unknown command handlers

## Getting Started

1. Clone this repository
2. Open Arduino IDE
3. Add the libraries to your Arduino libraries folder
4. Open any sketch from the `Arduino/` folder
5. Upload to your Arduino board
6. Open Serial Monitor at 115200 baud

## Requirements

- Arduino IDE 1.8.0 or later
- Compatible Arduino board (Uno, Nano, Mega, R4, etc.)
- USB cable for programming and serial communication

## License

See [LICENSE](LICENSE) file for details.
### Arduino Simulator (prototype)
A Conan/Ninja C++ simulation core with a Next.js + Material UI dashboard lives in `simulator/`. See `simulator/README.md` for setup instructions.
