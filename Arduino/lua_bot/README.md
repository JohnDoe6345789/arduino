# Arduino Lua Bot

An Arduino sketch that executes Lua-like code through the serial port and responds to plain English commands.

## Features

- **Lua-like Code Execution**: Execute simple Lua code with variables and expressions
- **Plain English Commands**: Control Arduino with natural language
- **Serial Port Interface**: Communicate through USB serial (115200 baud)
- **LED Control**: Control RGB LEDs with simple commands
- **Pin Manipulation**: Read and write digital/analog pins
- **Variable Storage**: Store and use variables in Lua code
- **Built on HumanReadableApi**: Uses the existing command framework

## Hardware Requirements

- Arduino board with Serial support (Nano R4, Uno R4, Nano RP2040, Mega, etc.)
- RGB LED (optional, can use built-in LED on Nano R4)
- USB cable for serial communication

## Installation

1. Copy the `lua_bot` folder to your Arduino sketchbook
2. Install the `HumanReadableApi` library (included in this repository)
3. Open `lua_bot.ino` in Arduino IDE
4. Select your board and port
5. Upload the sketch
6. Open Serial Monitor at 115200 baud

## Usage

### Plain English Commands

```
led red             # Turn LED red
led blue            # Turn LED blue  
led off             # Turn LED off
led 255 128 0       # Set LED to RGB(255, 128, 0)

write 13 HIGH       # Turn on pin 13
read 2              # Read pin 2
pin 13 OUTPUT       # Set pin 13 to OUTPUT mode

delay 1000          # Wait 1 second

help                # Show all commands
status              # Show interpreter status
```

### Natural Language (experimental)

The bot can understand some natural language:

```
turn led red
turn led off
hello
what can you do
```

### Lua Code Execution

Execute Lua-like code for more advanced control:

```
lua x = 5
lua y = 10
lua z = x + y
lua digitalWrite(13, 1)
lua analogWrite(9, 128)
lua delay(1000)
lua print("Hello from Lua!")
```

### Supported Lua Functions

- `digitalWrite(pin, value)` - Set digital pin HIGH (1) or LOW (0)
- `analogWrite(pin, value)` - Set PWM value (0-255)
- `digitalRead(pin)` - Read digital pin state
- `analogRead(pin)` - Read analog pin value (0-1023)
- `pinMode(pin, mode)` - Set pin mode (INPUT, OUTPUT, INPUT_PULLUP)
- `delay(ms)` - Wait for milliseconds
- `print(message)` - Print message to serial

### Variable Storage

Store and use variables in your Lua code:

```
lua x = 5
lua y = 3
lua result = x + y
status              # Shows: result = 8
```

Variables persist between commands until `reset` is called.

### Multi-line Mode (Future)

```
run
# Enter multiple lines of Lua code
x = 10
y = 20
digitalWrite(13, 1)
end
```

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `lua <code>` | Execute Lua code | `lua x = 5 + 3` |
| `exec <code>` | Alias for lua | `exec y = 10` |
| `run` | Multi-line mode | `run` (then type code) |
| `reset` | Clear all variables | `reset` |
| `status` | Show variables & memory | `status` |
| `led <color>` | Control RGB LED | `led red` |
| `led <r> <g> <b>` | Set LED RGB values | `led 255 128 0` |
| `pin <n> <mode>` | Set pin mode | `pin 13 OUTPUT` |
| `read <pin>` | Read pin value | `read 2` |
| `write <pin> <val>` | Write to pin | `write 13 HIGH` |
| `delay <ms>` | Wait milliseconds | `delay 1000` |
| `help [cmd]` | Show help | `help led` |

## Examples

### Blink an LED

```
pin 13 OUTPUT
write 13 HIGH
delay 1000
write 13 LOW
delay 1000
```

Or with Lua:

```
lua pinMode(13, OUTPUT)
lua digitalWrite(13, 1)
lua delay(1000)
lua digitalWrite(13, 0)
```

### Control RGB LED

```
led red
delay 1000
led green
delay 1000
led blue
delay 1000
led off
```

### Use Variables

```
lua brightness = 128
lua analogWrite(9, brightness)
lua brightness = brightness + 50
lua analogWrite(9, brightness)
```

### Read Sensor

```
pin 2 INPUT
read 2
lua sensor = analogRead(A0)
```

## Limitations

- **Simple Lua Implementation**: This is a lightweight Lua-like interpreter, not full Lua
- **Limited Memory**: Variables are limited to 10 slots
- **Basic Expressions**: Supports +, -, *, / operations
- **No Functions**: Cannot define custom Lua functions
- **No Loops/Conditionals**: No if/while/for statements in current version

## Technical Details

- **Baud Rate**: 115200
- **Command Buffer**: 128 bytes
- **Lua Buffer**: 512 bytes  
- **Max Variables**: 10
- **Variable Name Length**: 15 characters
- **Case Insensitive**: Commands are case-insensitive
- **Comment Support**: Use `#` for comments

## Architecture

The sketch uses:
- **HumanReadableApi**: For command parsing and handling
- **Simple Expression Evaluator**: For Lua-like arithmetic
- **Variable Store**: Array-based variable storage
- **Function Parser**: Basic function call parsing

## Future Enhancements

- Full Lua interpreter integration (using eLua or similar)
- Conditional statements (if/else)
- Loop support (while, for)
- User-defined functions
- More Arduino functions exposed to Lua
- EEPROM variable persistence
- Script storage and playback

## License

See repository LICENSE file.

## Author

Created for the Arduino community.
