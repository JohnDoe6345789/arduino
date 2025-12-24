# LED Effects and Games Examples

Welcome to the fun part of Arduino Lua Bot! This directory contains ready-to-use examples for creating amazing LED effects and playing interactive games over the serial port.

## 📁 Example Files

### 🎨 LED Effects (`examples_led_effects.txt`)

Contains 12 different LED animation effects that you can copy and paste into the Serial Monitor:

1. **Rainbow Cycle** - Smooth color transitions through the spectrum
2. **Breathing Effect** - Fades in and out like breathing
3. **Police Lights** - Red and blue alternating flashes
4. **Strobe Effect** - Fast white flashing
5. **Random Colors** - Uses the random() function
6. **Fire Effect** - Flickering flames simulation
7. **Ocean Wave** - Blue-cyan transitions
8. **Sunset Effect** - Yellow to deep red gradient
9. **Party Mode** - Fast random color changes
10. **Candle Flicker** - Realistic candle flame
11. **Lightning Effect** - Sudden bright flashes
12. **Heartbeat** - Double pulse pattern

### 🎮 Games (`examples_games.txt`)

Contains 8 interactive games you can play through the Serial Monitor:

1. **Number Guessing Game** - Guess the secret number
2. **Reaction Time Game** - How fast can you react?
3. **Simon Says Color Memory** - Remember the color sequence
4. **Button Mash Counter** - How many times can you press in 10 seconds?
5. **RGB Mixing Challenge** - Match the target color
6. **Timing Challenge** - Stop at exactly 5 seconds
7. **Rainbow Speed Run** - Type commands as fast as you can
8. **Binary Counter** - Learn binary with LED colors

## 🚀 How to Use

### Step 1: Upload the Lua Bot Sketch

1. Open `lua_bot.ino` in Arduino IDE
2. Select your Arduino board (Uno R4, Nano R4, etc.)
3. Select your COM port
4. Click Upload

### Step 2: Open Serial Monitor

1. Open Serial Monitor in Arduino IDE (or any serial terminal)
2. Set baud rate to **115200**
3. Set line ending to "Newline" or "Both NL & CR"

### Step 3: Run Examples

**For LED Effects:**
1. Open `examples_led_effects.txt` in a text editor
2. Choose an effect you want to try
3. Copy the commands for that effect (multiple lines)
4. Paste into Serial Monitor
5. Watch the magic happen! ✨

**For Games:**
1. Open `examples_games.txt` in a text editor
2. Choose a game you want to play
3. Follow the instructions in the file
4. Copy and paste commands as directed
5. Have fun! 🎮

## 💡 Tips for Best Results

### General Tips
- **Copy multiple lines**: You can copy and paste multiple commands at once
- **Be patient**: Serial communication has a small delay between commands
- **Use comments**: Lines starting with `#` are ignored (comments)
- **Check status**: Use the `status` command to see your variables
- **Reset when needed**: Use `reset` to clear variables and start fresh

### LED Effects Tips
- **Smooth animations**: The delay values control animation speed
- **Experiment**: Try changing RGB values to create your own colors
- **Combine effects**: Mix different patterns for unique results
- **Adjust brightness**: Scale all RGB values proportionally (e.g., divide by 2 for dimmer)
- **Save favorites**: Copy your favorite combinations to a new file

### Games Tips
- **Read instructions**: Each game has specific instructions at the start
- **Take your time**: No need to rush through the commands
- **Variables persist**: Your game state is saved in variables (use `status` to check)
- **Use the LED**: Many games use the LED to show feedback
- **Practice**: Games are more fun when you get familiar with the commands

## 🛠️ New Lua Functions

The enhanced Lua interpreter now supports these additional functions:

### LED Control
```
lua setRGB(255, 0, 0)          # Set RGB LED (easier than led command)
lua setRGB(r, g, b)            # Use variables for dynamic control
```

### Timing
```
lua t = millis()               # Get current time in milliseconds
lua delay(1000)                # Wait 1 second
```

### Random Numbers
```
lua r = random(256)            # Random from 0-255
lua r = random(10, 50)         # Random from 10-49
```

### Serial Communication (for games)
```
lua available = serialAvailable()  # Check if data available
lua byte = serialRead()            # Read one byte
```

## 🎨 Creating Your Own Effects

Here's a template for creating custom LED effects:

```
# My Custom Effect
lua print("Starting custom effect...")

# Your animation loop
lua setRGB(255, 0, 0)  # Red
delay 500
lua setRGB(0, 255, 0)  # Green  
delay 500
lua setRGB(0, 0, 255)  # Blue
delay 500

lua print("Effect complete!")
led off
```

## 🎮 Creating Your Own Games

Here's a template for creating simple games:

```
# My Custom Game
lua print("=== MY GAME ===")
lua print("Game instructions here...")

# Setup
lua score = 0
lua level = 1

# Game logic
lua print("Type your command...")
# Player does something
lua score = score + 10

# Show results
lua print("Your score:")
status

# Victory!
lua setRGB(0, 255, 0)
lua print("You win!")
```

## 📝 Command Reference

### Quick Command List
- `led <color>` - Control LED (red, green, blue, off, etc.)
- `lua <code>` - Execute Lua code
- `delay <ms>` - Wait specified milliseconds
- `status` - Show all variables
- `reset` - Clear all variables
- `help` - Show all commands

### Variable Management
```
lua x = 10              # Create variable
lua y = x + 5           # Use variable
status                  # See all variables
reset                   # Clear all variables
```

## 🔧 Troubleshooting

### Effect/Game Not Working?
1. Check baud rate is 115200
2. Make sure you uploaded the latest lua_bot sketch
3. Try running commands one at a time first
4. Use `status` to check if variables are set correctly
5. Use `reset` if things get stuck

### LED Not Responding?
1. Check if your board has the built-in RGB LED (R4 boards do)
2. Verify LED pins are correct for your board
3. Try simple commands first: `led red` then `led off`
4. Check LED brightness (try full brightness: `led 255 255 255`)

### Serial Monitor Issues?
1. Close and reopen Serial Monitor
2. Check correct COM port is selected
3. Verify baud rate is 115200
4. Try unplugging and replugging USB cable

## 🎓 Learning Path

### Beginner
1. Start with simple LED commands: `led red`, `led off`
2. Try the basic LED effects (breathing, police lights)
3. Play the simpler games (timing challenge, binary counter)

### Intermediate
1. Experiment with custom RGB colors: `lua setRGB(r, g, b)`
2. Try effects with variables and timing
3. Play memory and reaction games

### Advanced
1. Create your own LED effect combinations
2. Modify game parameters to make them harder
3. Design completely new effects and games
4. Combine multiple effects into sequences

## 🌟 Featured Examples

### Quick Start - Rainbow Effect (30 seconds)
```
led 255 0 0
delay 500
led 255 128 0
delay 500
led 255 255 0
delay 500
led 0 255 0
delay 500
led 0 255 255
delay 500
led 0 0 255
delay 500
led 255 0 255
delay 500
led off
```

### Quick Start - Reaction Game (1 minute)
```
lua print("Get ready...")
lua setRGB(255, 0, 0)
delay 2000
lua setRGB(0, 255, 0)
lua start = millis()
lua print("Press Enter NOW!")
# Press Enter, then:
lua end = millis()
lua time = end - start
lua print("Your time (ms):")
status
```

## 📚 Additional Resources

- **README.md** - Full Lua Bot documentation
- **EXAMPLES.md** - Basic command examples  
- **TEST_PLAN.md** - Testing guide
- **IMPLEMENTATION_SUMMARY.md** - Technical details

## 🤝 Contributing

Have a cool effect or game to share? Great! You can:
1. Modify the example files with your creation
2. Share with the Arduino community
3. Help others learn by explaining your code

## 📄 License

These examples are provided as-is for educational and fun purposes. Feel free to modify and share!

## 🎉 Have Fun!

Remember, the goal is to have fun while learning! Don't be afraid to experiment, break things (they're easy to fix with `reset`), and create something unique.

Happy coding! 🚀✨

---
*For Arduino R4 with RGB LED - Compatible with other Arduino boards with modifications*
