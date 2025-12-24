# Arduino Lua Bot - Test Plan

## Test Environment

- **Board**: Arduino Uno R4 Minima / Nano R4 / Any compatible board
- **Baud Rate**: 115200
- **Serial Monitor**: Arduino IDE Serial Monitor or any terminal emulator

## Pre-upload Checklist

- [ ] HumanReadableApi library is installed
- [ ] Correct board selected in Arduino IDE
- [ ] Correct COM port selected
- [ ] Sketch compiles without errors

## Basic Functionality Tests

### Test 1: Serial Communication
**Expected**: Bot responds with welcome message
```
# Upload sketch
# Open Serial Monitor at 115200 baud
# Expected output:
==================================
  Arduino Lua Bot v1.0
==================================
[bot] Hello! I can execute Lua code and respond to plain English.
[bot] Type 'help' for commands or try:
[bot]   lua x = 5 + 3
[bot]   led red
[bot]   write 13 HIGH
```

**Status**: ⬜ Pass ⬜ Fail

### Test 2: Help Command
**Input**: `help`
**Expected**: List of all available commands

**Status**: ⬜ Pass ⬜ Fail

### Test 3: Status Command
**Input**: `status`
**Expected**: Shows Lua interpreter status
```
[bot] === Lua Interpreter Status ===
[bot] Variables defined: 0
[bot] Free memory: XXXX bytes
```

**Status**: ⬜ Pass ⬜ Fail

## LED Control Tests

### Test 4: LED Red
**Input**: `led red`
**Expected**: 
- RGB LED turns red
- Response: `[bot] LED is now red.`

**Status**: ⬜ Pass ⬜ Fail

### Test 5: LED Green
**Input**: `led green`
**Expected**: 
- RGB LED turns green
- Response: `[bot] LED is now green.`

**Status**: ⬜ Pass ⬜ Fail

### Test 6: LED Blue
**Input**: `led blue`
**Expected**: 
- RGB LED turns blue
- Response: `[bot] LED is now blue.`

**Status**: ⬜ Pass ⬜ Fail

### Test 7: LED Off
**Input**: `led off`
**Expected**: 
- RGB LED turns off
- Response: `[bot] LED is now off.`

**Status**: ⬜ Pass ⬜ Fail

### Test 8: Custom RGB
**Input**: `led 128 64 255`
**Expected**: 
- RGB LED shows custom color
- Response: `[bot] LED set to RGB(128, 64, 255)`

**Status**: ⬜ Pass ⬜ Fail

## Lua Variable Tests

### Test 9: Simple Assignment
**Input**: `lua x = 5`
**Expected**: `[bot] x = 5.00`

**Status**: ⬜ Pass ⬜ Fail

### Test 10: Arithmetic Expression
**Input**: 
```
lua a = 10
lua b = 20
lua c = a + b
```
**Expected**: 
```
[bot] a = 10.00
[bot] b = 20.00
[bot] c = 30.00
```

**Status**: ⬜ Pass ⬜ Fail

### Test 11: Status After Variables
**Input**: `status`
**Expected**: Shows all 3 variables (a, b, c)

**Status**: ⬜ Pass ⬜ Fail

### Test 12: Complex Expression
**Input**: `lua result = 5 + 3 * 2`
**Expected**: Expression evaluated (result = 11.00)

**Status**: ⬜ Pass ⬜ Fail

### Test 13: Division
**Input**: `lua ratio = 100 / 4`
**Expected**: `[bot] ratio = 25.00`

**Status**: ⬜ Pass ⬜ Fail

### Test 14: Reset Variables
**Input**: `reset`
**Expected**: `[bot] Lua interpreter reset. All variables cleared.`

**Input**: `status`
**Expected**: `[bot] Variables defined: 0`

**Status**: ⬜ Pass ⬜ Fail

## Lua Arduino Functions Tests

### Test 15: digitalWrite
**Setup**: Built-in LED on pin 13
**Input**: 
```
lua pinMode(13, OUTPUT)
lua digitalWrite(13, 1)
```
**Expected**: 
- Pin 13 LED turns on
- Response shows commands executed

**Status**: ⬜ Pass ⬜ Fail

### Test 16: analogWrite
**Setup**: LED on pin 9 (PWM capable)
**Input**: `lua analogWrite(9, 128)`
**Expected**: 
- LED on pin 9 at 50% brightness
- Response: `[bot] analogWrite(9, 128)`

**Status**: ⬜ Pass ⬜ Fail

### Test 17: digitalRead
**Setup**: Button on pin 2
**Input**: `lua digitalRead(2)`
**Expected**: Response shows pin value (0 or 1)

**Status**: ⬜ Pass ⬜ Fail

### Test 18: analogRead
**Setup**: Sensor on A0
**Input**: `lua analogRead(A0)`
**Expected**: Response shows analog value (0-1023)

**Status**: ⬜ Pass ⬜ Fail

### Test 19: delay
**Input**: `lua delay(2000)`
**Expected**: 
- 2 second pause
- Response: `[bot] delay(2000)`

**Status**: ⬜ Pass ⬜ Fail

### Test 20: print
**Input**: `lua print("Hello World")`
**Expected**: `[bot] Hello World`

**Status**: ⬜ Pass ⬜ Fail

## Plain English Command Tests

### Test 21: Pin Mode
**Input**: `pin 13 OUTPUT`
**Expected**: `[bot] Pin 13 set to OUTPUT.`

**Status**: ⬜ Pass ⬜ Fail

### Test 22: Digital Write
**Input**: `write 13 HIGH`
**Expected**: 
- Pin 13 turns on
- Response: `[bot] Pin 13 set to HIGH.`

**Status**: ⬜ Pass ⬜ Fail

### Test 23: Digital Read
**Input**: `read 2`
**Expected**: Shows pin value

**Status**: ⬜ Pass ⬜ Fail

### Test 24: Delay Command
**Input**: `delay 1000`
**Expected**: 
- 1 second pause
- Response: `[bot] Done.`

**Status**: ⬜ Pass ⬜ Fail

## Natural Language Tests

### Test 25: Greeting
**Input**: `hello`
**Expected**: `[bot] Hello! How can I help you today?`

**Status**: ⬜ Pass ⬜ Fail

### Test 26: Natural LED Control
**Input**: `turn led red`
**Expected**: LED turns red

**Status**: ⬜ Pass ⬜ Fail

### Test 27: Unknown Command
**Input**: `xyz123`
**Expected**: Error message suggesting help

**Status**: ⬜ Pass ⬜ Fail

## Edge Cases and Error Handling

### Test 28: Empty Command
**Input**: (press Enter)
**Expected**: No error, ready for next command

**Status**: ⬜ Pass ⬜ Fail

### Test 29: Long Command
**Input**: Very long string (>128 chars)
**Expected**: `ERR: Line too long`

**Status**: ⬜ Pass ⬜ Fail

### Test 30: Case Insensitivity
**Input**: `LED RED` (uppercase)
**Expected**: LED turns red (same as `led red`)

**Status**: ⬜ Pass ⬜ Fail

### Test 31: Comments
**Input**: `led blue # This is a comment`
**Expected**: LED turns blue, comment ignored

**Status**: ⬜ Pass ⬜ Fail

### Test 32: Maximum Variables
**Input**: Define 11 variables
**Expected**: Error after 10th variable

**Status**: ⬜ Pass ⬜ Fail

### Test 33: Undefined Variable
**Input**: `lua y = undefined_var + 5`
**Expected**: Uses 0 for undefined variables

**Status**: ⬜ Pass ⬜ Fail

### Test 34: Division by Zero
**Input**: `lua result = 10 / 0`
**Expected**: Returns 0 or handles gracefully

**Status**: ⬜ Pass ⬜ Fail

## Memory Tests

### Test 35: Memory Status
**Input**: `status`
**Expected**: Shows free memory (AVR boards only)

**Status**: ⬜ Pass ⬜ Fail

### Test 36: Repeated Commands
**Action**: Send 100 commands rapidly
**Expected**: All commands processed, no crashes

**Status**: ⬜ Pass ⬜ Fail

## Integration Tests

### Test 37: LED Blink Sequence
**Input**:
```
pin 13 OUTPUT
write 13 HIGH
delay 500
write 13 LOW
delay 500
write 13 HIGH
delay 500
write 13 LOW
```
**Expected**: LED blinks 2 times

**Status**: ⬜ Pass ⬜ Fail

### Test 38: Variable-based Control
**Input**:
```
lua x = 128
lua analogWrite(9, x)
lua x = 255
lua analogWrite(9, x)
```
**Expected**: LED brightness changes

**Status**: ⬜ Pass ⬜ Fail

### Test 39: Mixed Commands
**Input**:
```
led red
delay 1000
lua digitalWrite(13, 1)
delay 1000
write 13 LOW
led off
```
**Expected**: All commands execute correctly

**Status**: ⬜ Pass ⬜ Fail

## Performance Tests

### Test 40: Response Time
**Action**: Send command and measure response time
**Expected**: Response within 100ms

**Status**: ⬜ Pass ⬜ Fail

### Test 41: Command Throughput
**Action**: Send 10 commands in rapid succession
**Expected**: All processed correctly

**Status**: ⬜ Pass ⬜ Fail

## Documentation Tests

### Test 42: Help for Specific Command
**Input**: `help led`
**Expected**: Shows detailed help for led command

**Status**: ⬜ Pass ⬜ Fail

### Test 43: Examples in EXAMPLES.md
**Action**: Try at least 10 examples from EXAMPLES.md
**Expected**: All work as documented

**Status**: ⬜ Pass ⬜ Fail

## Board Compatibility Tests

### Test 44: Arduino Uno R4
**Expected**: Works with inverted LED logic

**Status**: ⬜ Pass ⬜ Fail ⬜ N/A

### Test 45: Arduino Nano R4
**Expected**: Works with inverted LED logic

**Status**: ⬜ Pass ⬜ Fail ⬜ N/A

### Test 46: Arduino Mega
**Expected**: Works with standard LED pins

**Status**: ⬜ Pass ⬜ Fail ⬜ N/A

### Test 47: Arduino Uno
**Expected**: Works with standard LED pins

**Status**: ⬜ Pass ⬜ Fail ⬜ N/A

## Compilation Tests

### Test 48: Compile for Arduino Uno
**Action**: Set board to Uno and compile
**Expected**: Compiles without errors

**Status**: ⬜ Pass ⬜ Fail

### Test 49: Compile for Arduino Mega
**Action**: Set board to Mega and compile
**Expected**: Compiles without errors

**Status**: ⬜ Pass ⬜ Fail

### Test 50: Compile for Arduino Nano R4
**Action**: Set board to Nano R4 and compile
**Expected**: Compiles without errors

**Status**: ⬜ Pass ⬜ Fail

## Test Summary

- Total Tests: 50
- Passed: ___
- Failed: ___
- N/A: ___

## Notes

- All tests should be performed with Serial Monitor set to 115200 baud
- Some tests require physical hardware (LEDs, buttons, sensors)
- Memory tests are board-specific
- Board compatibility tests depend on available hardware

## Known Issues

_(Document any known issues discovered during testing)_

## Recommendations

_(Document any improvements or fixes needed based on test results)_
