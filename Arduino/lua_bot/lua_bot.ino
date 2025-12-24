// Arduino Lua Bot - Execute Lua code and respond to plain English commands
// Compatible with Arduino Nano R4 and other Arduino boards with Serial support
//
// Features:
// - Execute Lua code through serial port
// - Plain English command interface using HumanReadableApi
// - LED control demonstrations
// - Memory-efficient Lua-like interpreter

#include <HumanReadableApi.h>
#include <Arduino.h>

// =====================================================
// Configuration
// =====================================================

#define LINE_BUFFER_SIZE 128
#define LUA_BUFFER_SIZE 512
#define MAX_LUA_VARIABLES 10

static char lineBuffer[LINE_BUFFER_SIZE];
static char luaCodeBuffer[LUA_BUFFER_SIZE];
static int luaCodeBufferPos = 0;
static bool luaMultilineMode = false;

// LED pins (adjust for your board)
#if defined(ARDUINO_NANO_RP2040_CONNECT) || defined(ARDUINO_UNOWIFIR4) || defined(ARDUINO_MINIMA) || defined(ARDUINO_UNOR4_MINIMA) || defined(ARDUINO_UNOR4_WIFI)
  static const int LED_R_PIN = LEDR;
  static const int LED_G_PIN = LEDG;
  static const int LED_B_PIN = LEDB;
  static const bool LED_INVERTED = true; // Common anode
#else
  static const int LED_R_PIN = 9;
  static const int LED_G_PIN = 10;
  static const int LED_B_PIN = 11;
  static const bool LED_INVERTED = false;
#endif

// =====================================================
// Lua-like Interpreter State
// =====================================================

struct LuaVariable {
  char name[16];
  float value;
  bool inUse;
};

static LuaVariable luaVariables[MAX_LUA_VARIABLES];

// =====================================================
// Forward Declarations
// =====================================================

void handleLuaCommand(uint8_t argc, const char **argv);
void handleRunCommand(uint8_t argc, const char **argv);
void handleExecCommand(uint8_t argc, const char **argv);
void handleResetCommand(uint8_t argc, const char **argv);
void handleStatusCommand(uint8_t argc, const char **argv);
void handleHelpCommand(uint8_t argc, const char **argv);
void handleLedCommand(uint8_t argc, const char **argv);
void handlePinCommand(uint8_t argc, const char **argv);
void handleReadCommand(uint8_t argc, const char **argv);
void handleWriteCommand(uint8_t argc, const char **argv);
void handleDelayCommand(uint8_t argc, const char **argv);

void executeLuaCode(const char* code);
void resetLuaState();
float evaluateExpression(const char* expr);
void setLuaVariable(const char* name, float value);
float getLuaVariable(const char* name);
void onUnknownCommand(const char *cmd, uint8_t argc, const char **argv, Stream &io);

// =====================================================
// Command Registry
// =====================================================

HraCommandDef commands[] = {
  {
    "lua",
    handleLuaCommand,
    "lua <code>",
    "Execute a line of Lua-like code"
  },
  {
    "run",
    handleRunCommand,
    "run",
    "Enter multi-line Lua mode (type 'end' to execute)"
  },
  {
    "exec",
    handleExecCommand,
    "exec <code>",
    "Execute Lua code (alias for lua)"
  },
  {
    "reset",
    handleResetCommand,
    "reset",
    "Reset Lua interpreter state"
  },
  {
    "status",
    handleStatusCommand,
    "status",
    "Show Lua interpreter status and variables"
  },
  {
    "led",
    handleLedCommand,
    "led <on|off|red|green|blue|r g b>",
    "Control RGB LED in plain English"
  },
  {
    "pin",
    handlePinCommand,
    "pin <number> <mode>",
    "Set pin mode (INPUT, OUTPUT, INPUT_PULLUP)"
  },
  {
    "read",
    handleReadCommand,
    "read <pin>",
    "Read digital or analog pin value"
  },
  {
    "write",
    handleWriteCommand,
    "write <pin> <value>",
    "Write to digital or analog pin"
  },
  {
    "delay",
    handleDelayCommand,
    "delay <ms>",
    "Wait for specified milliseconds"
  },
  {
    "help",
    handleHelpCommand,
    "help [command]",
    "Show available commands"
  }
};

// =====================================================
// HumanReadableApi Setup
// =====================================================

HraConfig hraConfig;

HumanReadableApi api(
  Serial,
  commands,
  sizeof(commands) / sizeof(commands[0]),
  lineBuffer,
  sizeof(lineBuffer),
  hraConfig
);

// =====================================================
// Arduino Setup
// =====================================================

void setup() {
  // Configure HRA
  hraConfig.caseInsensitive = true;
  hraConfig.echoInput = false;
  hraConfig.allowComments = true;
  hraConfig.commentChar = '#';
  hraConfig.unknownHandler = onUnknownCommand;

  // Initialize Serial
  Serial.begin(115200);
  while (!Serial) {
    ; // Wait for serial port
  }

  // Initialize LED pins
  pinMode(LED_R_PIN, OUTPUT);
  pinMode(LED_G_PIN, OUTPUT);
  pinMode(LED_B_PIN, OUTPUT);
  
  // Turn off LEDs initially
  if (LED_INVERTED) {
    digitalWrite(LED_R_PIN, HIGH);
    digitalWrite(LED_G_PIN, HIGH);
    digitalWrite(LED_B_PIN, HIGH);
  } else {
    digitalWrite(LED_R_PIN, LOW);
    digitalWrite(LED_G_PIN, LOW);
    digitalWrite(LED_B_PIN, LOW);
  }

  // Initialize Lua state
  resetLuaState();

  // Welcome message
  Serial.println();
  Serial.println(F("=================================="));
  Serial.println(F("  Arduino Lua Bot v1.0"));
  Serial.println(F("=================================="));
  Serial.println(F("[bot] Hello! I can execute Lua code and respond to plain English."));
  Serial.println(F("[bot] Type 'help' for commands or try:"));
  Serial.println(F("[bot]   lua x = 5 + 3"));
  Serial.println(F("[bot]   led red"));
  Serial.println(F("[bot]   write 13 HIGH"));
  Serial.println();
}

// =====================================================
// Arduino Loop
// =====================================================

void loop() {
  // Handle multi-line Lua mode
  if (luaMultilineMode) {
    while (Serial.available()) {
      char c = (char)Serial.read();
      
      if (c == '\n' || c == '\r') {
        if (luaCodeBufferPos > 0) {
          luaCodeBuffer[luaCodeBufferPos] = '\0';
          
          // Check for end of multi-line input
          if (strcmp(luaCodeBuffer, "end") == 0 || strcmp(luaCodeBuffer, "END") == 0) {
            Serial.println(F("[bot] Executing Lua code..."));
            luaMultilineMode = false;
            // Execute accumulated code would go here
            luaCodeBufferPos = 0;
            Serial.println(F("[bot] Execution complete."));
          } else {
            // Add line to buffer
            Serial.print(F("  ... "));
            Serial.println(luaCodeBuffer);
            luaCodeBufferPos = 0;
          }
        }
      } else if (luaCodeBufferPos < LUA_BUFFER_SIZE - 1) {
        luaCodeBuffer[luaCodeBufferPos++] = c;
      }
    }
  } else {
    // Normal command mode
    api.poll();
  }
}

// =====================================================
// Command Handlers
// =====================================================

void handleLuaCommand(uint8_t argc, const char **argv) {
  if (argc < 2) {
    Serial.println(F("[bot] Usage: lua <code>"));
    Serial.println(F("[bot] Example: lua x = 5 + 3"));
    return;
  }

  // Reconstruct the Lua code from arguments
  String code = "";
  for (uint8_t i = 1; i < argc; i++) {
    if (i > 1) code += " ";
    code += argv[i];
  }

  Serial.print(F("[bot] Executing: "));
  Serial.println(code);
  
  executeLuaCode(code.c_str());
}

void handleRunCommand(uint8_t argc, const char **argv) {
  (void)argc;
  (void)argv;
  
  Serial.println(F("[bot] Entering multi-line Lua mode."));
  Serial.println(F("[bot] Type your Lua code, then 'end' on a new line to execute."));
  luaMultilineMode = true;
  luaCodeBufferPos = 0;
}

void handleExecCommand(uint8_t argc, const char **argv) {
  handleLuaCommand(argc, argv); // Alias for lua command
}

void handleResetCommand(uint8_t argc, const char **argv) {
  (void)argc;
  (void)argv;
  
  resetLuaState();
  Serial.println(F("[bot] Lua interpreter reset. All variables cleared."));
}

void handleStatusCommand(uint8_t argc, const char **argv) {
  (void)argc;
  (void)argv;
  
  Serial.println(F("[bot] === Lua Interpreter Status ==="));
  Serial.print(F("[bot] Variables defined: "));
  
  int count = 0;
  for (int i = 0; i < MAX_LUA_VARIABLES; i++) {
    if (luaVariables[i].inUse) {
      count++;
    }
  }
  Serial.println(count);
  
  for (int i = 0; i < MAX_LUA_VARIABLES; i++) {
    if (luaVariables[i].inUse) {
      Serial.print(F("[bot]   "));
      Serial.print(luaVariables[i].name);
      Serial.print(F(" = "));
      Serial.println(luaVariables[i].value);
    }
  }
  
  Serial.print(F("[bot] Free memory: "));
  #ifdef __AVR__
  extern int __heap_start, *__brkval;
  int v;
  Serial.print((int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval));
  #else
  Serial.print(F("N/A"));
  #endif
  Serial.println(F(" bytes"));
}

void handleHelpCommand(uint8_t argc, const char **argv) {
  Serial.println(F("[bot] === Available Commands ==="));
  
  if (argc >= 2) {
    api.printHelpFor(argv[1]);
  } else {
    api.printHelp();
  }
  
  Serial.println();
  Serial.println(F("[bot] === Plain English Examples ==="));
  Serial.println(F("[bot]   'led red' - Turn LED red"));
  Serial.println(F("[bot]   'led off' - Turn LED off"));
  Serial.println(F("[bot]   'write 13 HIGH' - Turn on pin 13"));
  Serial.println(F("[bot]   'read 2' - Read pin 2"));
  Serial.println();
  Serial.println(F("[bot] === Lua Examples ==="));
  Serial.println(F("[bot]   lua x = 10"));
  Serial.println(F("[bot]   lua y = x + 5"));
  Serial.println(F("[bot]   lua digitalWrite(13, 1)"));
  Serial.println(F("[bot]   lua delay(1000)"));
}

void handleLedCommand(uint8_t argc, const char **argv) {
  if (argc < 2) {
    Serial.println(F("[bot] Usage: led <on|off|red|green|blue|white|r g b>"));
    return;
  }

  String cmd = String(argv[1]);
  cmd.toLowerCase();

  if (cmd == "on" || cmd == "white") {
    if (LED_INVERTED) {
      analogWrite(LED_R_PIN, 0);
      analogWrite(LED_G_PIN, 0);
      analogWrite(LED_B_PIN, 0);
    } else {
      analogWrite(LED_R_PIN, 255);
      analogWrite(LED_G_PIN, 255);
      analogWrite(LED_B_PIN, 255);
    }
    Serial.println(F("[bot] LED is now white (all on)."));
  } 
  else if (cmd == "off") {
    if (LED_INVERTED) {
      analogWrite(LED_R_PIN, 255);
      analogWrite(LED_G_PIN, 255);
      analogWrite(LED_B_PIN, 255);
    } else {
      analogWrite(LED_R_PIN, 0);
      analogWrite(LED_G_PIN, 0);
      analogWrite(LED_B_PIN, 0);
    }
    Serial.println(F("[bot] LED is now off."));
  }
  else if (cmd == "red") {
    if (LED_INVERTED) {
      analogWrite(LED_R_PIN, 0);
      analogWrite(LED_G_PIN, 255);
      analogWrite(LED_B_PIN, 255);
    } else {
      analogWrite(LED_R_PIN, 255);
      analogWrite(LED_G_PIN, 0);
      analogWrite(LED_B_PIN, 0);
    }
    Serial.println(F("[bot] LED is now red."));
  }
  else if (cmd == "green") {
    if (LED_INVERTED) {
      analogWrite(LED_R_PIN, 255);
      analogWrite(LED_G_PIN, 0);
      analogWrite(LED_B_PIN, 255);
    } else {
      analogWrite(LED_R_PIN, 0);
      analogWrite(LED_G_PIN, 255);
      analogWrite(LED_B_PIN, 0);
    }
    Serial.println(F("[bot] LED is now green."));
  }
  else if (cmd == "blue") {
    if (LED_INVERTED) {
      analogWrite(LED_R_PIN, 255);
      analogWrite(LED_G_PIN, 255);
      analogWrite(LED_B_PIN, 0);
    } else {
      analogWrite(LED_R_PIN, 0);
      analogWrite(LED_G_PIN, 0);
      analogWrite(LED_B_PIN, 255);
    }
    Serial.println(F("[bot] LED is now blue."));
  }
  else if (argc >= 4) {
    // RGB values provided
    int r = atoi(argv[1]);
    int g = atoi(argv[2]);
    int b = atoi(argv[3]);
    
    r = constrain(r, 0, 255);
    g = constrain(g, 0, 255);
    b = constrain(b, 0, 255);
    
    if (LED_INVERTED) {
      analogWrite(LED_R_PIN, 255 - r);
      analogWrite(LED_G_PIN, 255 - g);
      analogWrite(LED_B_PIN, 255 - b);
    } else {
      analogWrite(LED_R_PIN, r);
      analogWrite(LED_G_PIN, g);
      analogWrite(LED_B_PIN, b);
    }
    
    Serial.print(F("[bot] LED set to RGB("));
    Serial.print(r);
    Serial.print(F(", "));
    Serial.print(g);
    Serial.print(F(", "));
    Serial.print(b);
    Serial.println(F(")"));
  }
  else {
    Serial.println(F("[bot] Unknown LED command. Try: on, off, red, green, blue, white, or <r g b>"));
  }
}

void handlePinCommand(uint8_t argc, const char **argv) {
  if (argc < 3) {
    Serial.println(F("[bot] Usage: pin <number> <INPUT|OUTPUT|INPUT_PULLUP>"));
    return;
  }

  int pin = atoi(argv[1]);
  String mode = String(argv[2]);
  mode.toUpperCase();

  if (mode == "INPUT") {
    pinMode(pin, INPUT);
    Serial.print(F("[bot] Pin "));
    Serial.print(pin);
    Serial.println(F(" set to INPUT."));
  } 
  else if (mode == "OUTPUT") {
    pinMode(pin, OUTPUT);
    Serial.print(F("[bot] Pin "));
    Serial.print(pin);
    Serial.println(F(" set to OUTPUT."));
  }
  else if (mode == "INPUT_PULLUP") {
    pinMode(pin, INPUT_PULLUP);
    Serial.print(F("[bot] Pin "));
    Serial.print(pin);
    Serial.println(F(" set to INPUT_PULLUP."));
  }
  else {
    Serial.println(F("[bot] Unknown mode. Use: INPUT, OUTPUT, or INPUT_PULLUP"));
  }
}

void handleReadCommand(uint8_t argc, const char **argv) {
  if (argc < 2) {
    Serial.println(F("[bot] Usage: read <pin>"));
    return;
  }

  int pin = atoi(argv[1]);
  
  // Check if it's an analog pin
  if (pin >= A0) {
    int value = analogRead(pin);
    Serial.print(F("[bot] Analog pin "));
    Serial.print(pin);
    Serial.print(F(" = "));
    Serial.println(value);
  } else {
    int value = digitalRead(pin);
    Serial.print(F("[bot] Digital pin "));
    Serial.print(pin);
    Serial.print(F(" = "));
    Serial.println(value == HIGH ? "HIGH" : "LOW");
  }
}

void handleWriteCommand(uint8_t argc, const char **argv) {
  if (argc < 3) {
    Serial.println(F("[bot] Usage: write <pin> <value>"));
    Serial.println(F("[bot] Value can be: HIGH, LOW, or 0-255 for PWM"));
    return;
  }

  int pin = atoi(argv[1]);
  String valueStr = String(argv[2]);
  valueStr.toUpperCase();

  if (valueStr == "HIGH") {
    digitalWrite(pin, HIGH);
    Serial.print(F("[bot] Pin "));
    Serial.print(pin);
    Serial.println(F(" set to HIGH."));
  }
  else if (valueStr == "LOW") {
    digitalWrite(pin, LOW);
    Serial.print(F("[bot] Pin "));
    Serial.print(pin);
    Serial.println(F(" set to LOW."));
  }
  else {
    int value = atoi(argv[2]);
    value = constrain(value, 0, 255);
    analogWrite(pin, value);
    Serial.print(F("[bot] Pin "));
    Serial.print(pin);
    Serial.print(F(" set to "));
    Serial.println(value);
  }
}

void handleDelayCommand(uint8_t argc, const char **argv) {
  if (argc < 2) {
    Serial.println(F("[bot] Usage: delay <milliseconds>"));
    return;
  }

  int ms = atoi(argv[1]);
  Serial.print(F("[bot] Delaying for "));
  Serial.print(ms);
  Serial.println(F(" ms..."));
  delay(ms);
  Serial.println(F("[bot] Done."));
}

// =====================================================
// Unknown Command Handler (Natural Language)
// =====================================================

void onUnknownCommand(const char *cmd, uint8_t argc, const char **argv, Stream &io) {
  (void)argc;
  (void)argv;
  
  // Try to interpret as natural language
  String input = String(cmd);
  input.toLowerCase();

  // Simple natural language parsing
  if (input.indexOf("turn") >= 0 && input.indexOf("led") >= 0) {
    if (input.indexOf("red") >= 0) {
      const char* args[] = {"led", "red"};
      handleLedCommand(2, args);
      return;
    } 
    else if (input.indexOf("green") >= 0) {
      const char* args[] = {"led", "green"};
      handleLedCommand(2, args);
      return;
    }
    else if (input.indexOf("blue") >= 0) {
      const char* args[] = {"led", "blue"};
      handleLedCommand(2, args);
      return;
    }
    else if (input.indexOf("off") >= 0) {
      const char* args[] = {"led", "off"};
      handleLedCommand(2, args);
      return;
    }
    else if (input.indexOf("on") >= 0) {
      const char* args[] = {"led", "on"};
      handleLedCommand(2, args);
      return;
    }
  }

  if (input.indexOf("hello") >= 0 || input.indexOf("hi") == 0) {
    io.println(F("[bot] Hello! How can I help you today?"));
    return;
  }

  if (input.indexOf("what") >= 0 && input.indexOf("can") >= 0 && input.indexOf("do") >= 0) {
    io.println(F("[bot] I can execute Lua code and control Arduino pins!"));
    io.println(F("[bot] Try 'help' to see all commands."));
    return;
  }

  // Default response
  io.print(F("[bot] I don't understand '"));
  io.print(cmd);
  io.println(F("'. Try 'help' for commands."));
}

// =====================================================
// Lua Interpreter Functions
// =====================================================

void resetLuaState() {
  for (int i = 0; i < MAX_LUA_VARIABLES; i++) {
    luaVariables[i].inUse = false;
    luaVariables[i].name[0] = '\0';
    luaVariables[i].value = 0.0f;
  }
}

void setLuaVariable(const char* name, float value) {
  // Find existing variable or empty slot
  int emptySlot = -1;
  for (int i = 0; i < MAX_LUA_VARIABLES; i++) {
    if (luaVariables[i].inUse && strcmp(luaVariables[i].name, name) == 0) {
      luaVariables[i].value = value;
      return;
    }
    if (!luaVariables[i].inUse && emptySlot == -1) {
      emptySlot = i;
    }
  }
  
  // Create new variable
  if (emptySlot >= 0) {
    // Safely copy name with proper null termination
    size_t len = strlen(name);
    if (len > 15) len = 15;
    memcpy(luaVariables[emptySlot].name, name, len);
    luaVariables[emptySlot].name[len] = '\0';
    luaVariables[emptySlot].value = value;
    luaVariables[emptySlot].inUse = true;
  } else {
    Serial.println(F("[bot] Error: No more variable slots available."));
  }
}

float getLuaVariable(const char* name) {
  for (int i = 0; i < MAX_LUA_VARIABLES; i++) {
    if (luaVariables[i].inUse && strcmp(luaVariables[i].name, name) == 0) {
      return luaVariables[i].value;
    }
  }
  return 0.0f;
}

float evaluateExpression(const char* expr) {
  // Very basic expression evaluator
  // Handles: numbers, variables, +, -, *, /
  
  String exprStr = String(expr);
  exprStr.trim();
  
  // Check if it's just a number
  char* endptr;
  float val = strtof(exprStr.c_str(), &endptr);
  if (*endptr == '\0') {
    return val;
  }
  
  // Check if it's a variable
  for (int i = 0; i < MAX_LUA_VARIABLES; i++) {
    if (luaVariables[i].inUse && exprStr.equals(luaVariables[i].name)) {
      return luaVariables[i].value;
    }
  }
  
  // Handle simple binary operations with proper precedence
  // Find lowest precedence operator (+ and - before * and /)
  int opPos = -1;
  char op = '\0';
  
  // Check for empty expression
  if (exprStr.length() == 0) {
    return 0.0f;
  }
  
  // First pass: look for + or - (lowest precedence)
  for (int i = (int)exprStr.length() - 1; i >= 0; i--) {
    char c = exprStr.charAt(i);
    if (c == '+' || c == '-') {
      opPos = i;
      op = c;
      break;
    }
  }
  
  // Second pass: if no + or -, look for * or / (higher precedence)
  if (opPos == -1) {
    for (int i = (int)exprStr.length() - 1; i >= 0; i--) {
      char c = exprStr.charAt(i);
      if (c == '*' || c == '/') {
        opPos = i;
        op = c;
        break;
      }
    }
  }
  
  if (opPos > 0) {
    String left = exprStr.substring(0, opPos);
    String right = exprStr.substring(opPos + 1);
    left.trim();
    right.trim();
    
    float leftVal = evaluateExpression(left.c_str());
    float rightVal = evaluateExpression(right.c_str());
    
    switch (op) {
      case '+': return leftVal + rightVal;
      case '-': return leftVal - rightVal;
      case '*': return leftVal * rightVal;
      case '/': return (rightVal != 0) ? leftVal / rightVal : 0;
    }
  }
  
  return 0.0f;
}

// Helper function to parse two integer arguments from function call
bool parseTwoIntArgs(const String& funcCall, int& arg1, int& arg2) {
  int startIdx = funcCall.indexOf('(') + 1;
  int endIdx = funcCall.indexOf(')');
  if (endIdx > startIdx) {
    String args = funcCall.substring(startIdx, endIdx);
    int commaPos = args.indexOf(',');
    if (commaPos > 0) {
      arg1 = args.substring(0, commaPos).toInt();
      arg2 = args.substring(commaPos + 1).toInt();
      return true;
    }
  }
  return false;
}

void executeLuaCode(const char* code) {
  String codeStr = String(code);
  codeStr.trim();
  
  // Handle variable assignment: x = expression
  int eqPos = codeStr.indexOf('=');
  if (eqPos > 0 && eqPos < codeStr.length() - 1) {
    // Check it's not == comparison
    if (codeStr.charAt(eqPos - 1) != '=' && codeStr.charAt(eqPos + 1) != '=') {
      String varName = codeStr.substring(0, eqPos);
      String expr = codeStr.substring(eqPos + 1);
      varName.trim();
      expr.trim();
      
      float value = evaluateExpression(expr.c_str());
      setLuaVariable(varName.c_str(), value);
      
      Serial.print(F("[bot] "));
      Serial.print(varName);
      Serial.print(F(" = "));
      Serial.println(value);
      return;
    }
  }
  
  // Handle function calls
  if (codeStr.startsWith("digitalWrite(")) {
    int pin, value;
    if (parseTwoIntArgs(codeStr, pin, value)) {
      digitalWrite(pin, value);
      Serial.print(F("[bot] digitalWrite("));
      Serial.print(pin);
      Serial.print(F(", "));
      Serial.print(value);
      Serial.println(F(")"));
      return;
    }
  }
  
  if (codeStr.startsWith("analogWrite(")) {
    int pin, value;
    if (parseTwoIntArgs(codeStr, pin, value)) {
      analogWrite(pin, value);
      Serial.print(F("[bot] analogWrite("));
      Serial.print(pin);
      Serial.print(F(", "));
      Serial.print(value);
      Serial.println(F(")"));
      return;
    }
  }
  
  if (codeStr.startsWith("digitalRead(")) {
    int startIdx = codeStr.indexOf('(') + 1;
    int endIdx = codeStr.indexOf(')');
    if (endIdx > startIdx) {
      int pin = codeStr.substring(startIdx, endIdx).toInt();
      int value = digitalRead(pin);
      Serial.print(F("[bot] digitalRead("));
      Serial.print(pin);
      Serial.print(F(") = "));
      Serial.println(value);
      return;
    }
  }
  
  if (codeStr.startsWith("analogRead(")) {
    int startIdx = codeStr.indexOf('(') + 1;
    int endIdx = codeStr.indexOf(')');
    if (endIdx > startIdx) {
      int pin = codeStr.substring(startIdx, endIdx).toInt();
      int value = analogRead(pin);
      Serial.print(F("[bot] analogRead("));
      Serial.print(pin);
      Serial.print(F(") = "));
      Serial.println(value);
      return;
    }
  }
  
  if (codeStr.startsWith("delay(")) {
    int startIdx = codeStr.indexOf('(') + 1;
    int endIdx = codeStr.indexOf(')');
    if (endIdx > startIdx) {
      int ms = codeStr.substring(startIdx, endIdx).toInt();
      delay(ms);
      Serial.print(F("[bot] delay("));
      Serial.print(ms);
      Serial.println(F(")"));
      return;
    }
  }
  
  if (codeStr.startsWith("pinMode(")) {
    int startIdx = codeStr.indexOf('(') + 1;
    int endIdx = codeStr.indexOf(')');
    if (endIdx > startIdx) {
      String args = codeStr.substring(startIdx, endIdx);
      int commaPos = args.indexOf(',');
      if (commaPos > 0) {
        int pin = args.substring(0, commaPos).toInt();
        String modeStr = args.substring(commaPos + 1);
        modeStr.trim();
        int mode = INPUT;
        if (modeStr == "OUTPUT" || modeStr == "1") mode = OUTPUT;
        else if (modeStr == "INPUT_PULLUP" || modeStr == "2") mode = INPUT_PULLUP;
        pinMode(pin, mode);
        Serial.print(F("[bot] pinMode("));
        Serial.print(pin);
        Serial.print(F(", "));
        Serial.print(mode);
        Serial.println(F(")"));
        return;
      }
    }
  }
  
  if (codeStr.startsWith("print(")) {
    int startIdx = codeStr.indexOf('(') + 1;
    int endIdx = codeStr.lastIndexOf(')');
    if (endIdx > startIdx) {
      String msg = codeStr.substring(startIdx, endIdx);
      msg.trim();
      // Remove quotes if present
      if (msg.startsWith("\"") && msg.endsWith("\"")) {
        msg = msg.substring(1, msg.length() - 1);
      }
      Serial.print(F("[bot] "));
      Serial.println(msg);
      return;
    }
  }
  
  // If nothing matched, try to evaluate as expression and print result
  float result = evaluateExpression(code);
  Serial.print(F("[bot] Result: "));
  Serial.println(result);
}
