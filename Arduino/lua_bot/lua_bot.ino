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
#define LUA_BUFFER_SIZE 2048
#define MAX_LUA_VARIABLES 10
#define COMPRESSED_CODE_SIZE 8192  // Much larger now with compression

static char lineBuffer[LINE_BUFFER_SIZE];
static char luaCodeBuffer[LUA_BUFFER_SIZE];
static int luaCodeBufferPos = 0;
static bool luaMultilineMode = false;
static bool luaPasteMode = false;

// Compressed storage for pasted Lua code (uses token codes)
static uint8_t compressedCode[COMPRESSED_CODE_SIZE];
static int compressedCodeSize = 0;

// Token codes for compression (0x80-0xFF range to avoid conflicts with ASCII)
#define TOKEN_BASE 0x80
enum LuaTokens {
  TOK_SETRGB = TOKEN_BASE,      // 0x80
  TOK_DIGITALWRITE,              // 0x81
  TOK_ANALOGWRITE,               // 0x82
  TOK_DIGITALREAD,               // 0x83
  TOK_ANALOGREAD,                // 0x84
  TOK_PINMODE,                   // 0x85
  TOK_DELAY,                     // 0x86
  TOK_MILLIS,                    // 0x87
  TOK_RANDOM,                    // 0x88
  TOK_PRINT,                     // 0x89
  TOK_SERIALAVAILABLE,           // 0x8A
  TOK_SERIALREAD,                // 0x8B
  TOK_IF,                        // 0x8C
  TOK_THEN,                      // 0x8D
  TOK_ELSE,                      // 0x8E
  TOK_ELSEIF,                    // 0x8F
  TOK_END,                       // 0x90
  TOK_WHILE,                     // 0x91
  TOK_DO,                        // 0x92
  TOK_FOR,                       // 0x93
  TOK_IN,                        // 0x94
  TOK_REPEAT,                    // 0x95
  TOK_UNTIL,                     // 0x96
  TOK_FUNCTION,                  // 0x97
  TOK_RETURN,                    // 0x98
  TOK_LOCAL,                     // 0x99
  TOK_AND,                       // 0x9A
  TOK_OR,                        // 0x9B
  TOK_NOT,                       // 0x9C
  TOK_TRUE,                      // 0x9D
  TOK_FALSE,                     // 0x9E
  TOK_NIL,                       // 0x9F
  TOK_BREAK,                     // 0xA0
  TOK_GOTO,                      // 0xA1
};

// Token lookup table (must match enum order)
const char* TOKEN_STRINGS[] = {
  "setRGB", "digitalWrite", "analogWrite", "digitalRead", "analogRead",
  "pinMode", "delay", "millis", "random", "print",
  "serialAvailable", "serialRead",
  "if", "then", "else", "elseif", "end",
  "while", "do", "for", "in", "repeat", "until",
  "function", "return", "local", "and", "or", "not",
  "true", "false", "nil", "break", "goto"
};
#define TOKEN_COUNT (sizeof(TOKEN_STRINGS) / sizeof(TOKEN_STRINGS[0]))

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
void handleStartPasteCommand(uint8_t argc, const char **argv);
void handleEndPasteCommand(uint8_t argc, const char **argv);

void executeLuaCode(const char* code);
void executeMultiLineLuaCode();
void executeLuaBlock(int startLine, int endLine);
int compressLuaCode(const char* code, uint8_t* output, int maxSize);
String decompressLuaCode(const uint8_t* input, int size);
void compressAndStoreLine(const char* line);
bool evaluateCondition(const char* condition);
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
    "startpaste",
    handleStartPasteCommand,
    "startpaste",
    "Start paste mode for multi-line Lua code"
  },
  {
    "endpaste",
    handleEndPasteCommand,
    "endpaste",
    "End paste mode and execute Lua code"
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
  // Handle paste mode
  if (luaPasteMode) {
    while (Serial.available()) {
      char c = (char)Serial.read();
      
      if (c == '\n' || c == '\r') {
        if (luaCodeBufferPos > 0) {
          luaCodeBuffer[luaCodeBufferPos] = '\0';
          
          // Check for end of paste mode
          if (strcmp(luaCodeBuffer, "endpaste") == 0 || strcmp(luaCodeBuffer, "ENDPASTE") == 0) {
            Serial.print(F("[bot] Compressed "));
            Serial.print(compressedCodeSize);
            Serial.println(F(" bytes of Lua code."));
            Serial.println(F("[bot] Executing..."));
            luaPasteMode = false;
            executeMultiLineLuaCode();
            luaCodeBufferPos = 0;
            Serial.println(F("[bot] Execution complete."));
          } else {
            // Compress and store the line
            compressAndStoreLine(luaCodeBuffer);
            luaCodeBufferPos = 0;
          }
        }
      } else if (luaCodeBufferPos < LUA_BUFFER_SIZE - 1) {
        luaCodeBuffer[luaCodeBufferPos++] = c;
      }
    }
  }
  // Handle multi-line Lua mode
  else if (luaMultilineMode) {
    while (Serial.available()) {
      char c = (char)Serial.read();
      
      if (c == '\n' || c == '\r') {
        if (luaCodeBufferPos > 0) {
          luaCodeBuffer[luaCodeBufferPos] = '\0';
          
          // Check for end of multi-line input
          if (strcmp(luaCodeBuffer, "end") == 0 || strcmp(luaCodeBuffer, "END") == 0) {
            Serial.println(F("[bot] Executing Lua code..."));
            luaMultilineMode = false;
            executeMultiLineLuaCode();
            luaCodeBufferPos = 0;
            Serial.println(F("[bot] Execution complete."));
          } else {
            // Compress and store the line
            compressAndStoreLine(luaCodeBuffer);
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
  Serial.println(F("[bot] Supports: if/then/else, while/do, for loops!"));
  luaMultilineMode = true;
  compressedCodeSize = 0;
  luaCodeBufferPos = 0;
}

void handleStartPasteCommand(uint8_t argc, const char **argv) {
  (void)argc;
  (void)argv;
  
  Serial.println(F("[bot] === PASTE MODE ACTIVATED ==="));
  Serial.println(F("[bot] Paste your Lua code now."));
  Serial.println(F("[bot] Type 'endpaste' on a new line when done."));
  Serial.println(F("[bot] Supports: if/then/else, while/do, for loops!"));
  Serial.print(F("[bot] Code compression: "));
  Serial.print(COMPRESSED_CODE_SIZE);
  Serial.println(F(" bytes available"));
  luaPasteMode = true;
  compressedCodeSize = 0;
  luaCodeBufferPos = 0;
}

void handleEndPasteCommand(uint8_t argc, const char **argv) {
  (void)argc;
  (void)argv;
  
  if (luaPasteMode) {
    Serial.println(F("[bot] Ending paste mode and executing..."));
    luaPasteMode = false;
    executeMultiLineLuaCode();
    Serial.println(F("[bot] Execution complete."));
  } else {
    Serial.println(F("[bot] Not in paste mode. Use 'startpaste' first."));
  }
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
  Serial.println(F("[bot]   lua setRGB(255, 0, 0)"));
  Serial.println(F("[bot]   lua digitalWrite(13, 1)"));
  Serial.println(F("[bot]   lua delay(1000)"));
  Serial.println();
  Serial.println(F("[bot] === Multi-line Code ==="));
  Serial.println(F("[bot]   'startpaste' - Begin paste mode with compression"));
  Serial.println(F("[bot]   Paste your code with if/while/for loops"));
  Serial.println(F("[bot]   'endpaste' - Execute compressed code"));
  Serial.println();
  Serial.println(F("[bot] === Example Files ==="));
  Serial.println(F("[bot]   See examples_led_effects.txt for LED animations"));
  Serial.println(F("[bot]   See examples_games.txt for interactive games"));
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
  int exprLen = exprStr.length();
  if (exprLen == 0) {
    return 0.0f;
  }
  
  // First pass: look for + or - (lowest precedence)
  for (int i = exprLen - 1; i >= 0; i--) {
    char c = exprStr.charAt(i);
    if (c == '+' || c == '-') {
      opPos = i;
      op = c;
      break;
    }
  }
  
  // Second pass: if no + or -, look for * or / (higher precedence)
  if (opPos == -1) {
    for (int i = exprLen - 1; i >= 0; i--) {
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

// Helper function to parse three integer arguments from function call
bool parseThreeIntArgs(const String& funcCall, int& arg1, int& arg2, int& arg3) {
  int startIdx = funcCall.indexOf('(') + 1;
  int endIdx = funcCall.indexOf(')');
  if (endIdx > startIdx) {
    String args = funcCall.substring(startIdx, endIdx);
    int firstComma = args.indexOf(',');
    if (firstComma > 0) {
      int secondComma = args.indexOf(',', firstComma + 1);
      if (secondComma > firstComma) {
        String arg1Str = args.substring(0, firstComma);
        String arg2Str = args.substring(firstComma + 1, secondComma);
        String arg3Str = args.substring(secondComma + 1);
        arg1Str.trim();
        arg2Str.trim();
        arg3Str.trim();
        arg1 = arg1Str.toInt();
        arg2 = arg2Str.toInt();
        arg3 = arg3Str.toInt();
        return true;
      }
    }
  }
  return false;
}

// Helper function to set RGB LED with proper inversion handling
void setRGBLed(int r, int g, int b) {
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
  
  if (codeStr.startsWith("setRGB(")) {
    int r, g, b;
    if (parseThreeIntArgs(codeStr, r, g, b)) {
      setRGBLed(r, g, b);
      Serial.print(F("[bot] setRGB("));
      Serial.print(r);
      Serial.print(F(", "));
      Serial.print(g);
      Serial.print(F(", "));
      Serial.print(b);
      Serial.println(F(")"));
      return;
    }
  }
  
  if (codeStr.startsWith("millis()")) {
    unsigned long ms = millis();
    Serial.print(F("[bot] millis() = "));
    Serial.println(ms);
    return;
  }
  
  if (codeStr.startsWith("random(")) {
    int startIdx = codeStr.indexOf('(') + 1;
    int endIdx = codeStr.indexOf(')');
    if (endIdx > startIdx) {
      String args = codeStr.substring(startIdx, endIdx);
      int commaPos = args.indexOf(',');
      long randVal;
      if (commaPos > 0) {
        // Two arguments: random(min, max)
        String minStr = args.substring(0, commaPos);
        String maxStr = args.substring(commaPos + 1);
        minStr.trim();
        maxStr.trim();
        int minVal = minStr.toInt();
        int maxVal = maxStr.toInt();
        randVal = random(minVal, maxVal);
      } else {
        // One argument: random(max)
        args.trim();
        int maxVal = args.toInt();
        randVal = random(maxVal);
      }
      Serial.print(F("[bot] random() = "));
      Serial.println(randVal);
      return;
    }
  }
  
  if (codeStr.startsWith("serialAvailable()")) {
    int available = Serial.available();
    Serial.print(F("[bot] serialAvailable() = "));
    Serial.println(available);
    return;
  }
  
  if (codeStr.startsWith("serialRead()")) {
    if (Serial.available() > 0) {
      int value = Serial.read();
      Serial.print(F("[bot] serialRead() = "));
      Serial.println(value);
    } else {
      Serial.println(F("[bot] serialRead() = -1 (no data)"));
    }
    return;
  }
  
  // If nothing matched, try to evaluate as expression and print result
  float result = evaluateExpression(code);
  Serial.print(F("[bot] Result: "));
  Serial.println(result);
}

// =====================================================
// Compression Functions
// =====================================================

// Compress Lua code by replacing keywords with token codes
int compressLuaCode(const char* code, uint8_t* output, int maxSize) {
  int outPos = 0;
  int inPos = 0;
  int len = strlen(code);
  
  while (inPos < len && outPos < maxSize) {
    bool tokenFound = false;
    
    // Try to match tokens (longest match first)
    for (int i = 0; i < TOKEN_COUNT; i++) {
      int tokenLen = strlen(TOKEN_STRINGS[i]);
      if (inPos + tokenLen <= len && 
          strncmp(code + inPos, TOKEN_STRINGS[i], tokenLen) == 0) {
        // Check that it's a complete word (not part of a variable name)
        if ((inPos + tokenLen >= len) || 
            !isalnum(code[inPos + tokenLen]) && code[inPos + tokenLen] != '_') {
          output[outPos++] = TOKEN_BASE + i;
          inPos += tokenLen;
          tokenFound = true;
          break;
        }
      }
    }
    
    if (!tokenFound) {
      // Copy character as-is
      output[outPos++] = (uint8_t)code[inPos++];
    }
  }
  
  return outPos;
}

// Decompress Lua code by expanding token codes back to keywords
String decompressLuaCode(const uint8_t* input, int size) {
  String result = "";
  result.reserve(size * 2);  // Reserve some space
  
  for (int i = 0; i < size; i++) {
    uint8_t byte = input[i];
    
    if (byte >= TOKEN_BASE && byte < TOKEN_BASE + TOKEN_COUNT) {
      // It's a token - expand it
      int tokenIndex = byte - TOKEN_BASE;
      result += TOKEN_STRINGS[tokenIndex];
    } else {
      // Regular character
      result += (char)byte;
    }
  }
  
  return result;
}

// Compress and add a line to the compressed storage
void compressAndStoreLine(const char* line) {
  uint8_t tempBuffer[LINE_BUFFER_SIZE * 2];
  int compressedLen = compressLuaCode(line, tempBuffer, sizeof(tempBuffer));
  
  if (compressedCodeSize + compressedLen + 1 < COMPRESSED_CODE_SIZE) {
    // Store length byte followed by compressed data
    compressedCode[compressedCodeSize++] = (uint8_t)compressedLen;
    memcpy(compressedCode + compressedCodeSize, tempBuffer, compressedLen);
    compressedCodeSize += compressedLen;
  } else {
    Serial.println(F("[bot] Warning: Compressed code buffer full!"));
  }
}

// =====================================================
// Multi-line Execution with Control Structures
// =====================================================

// Evaluate a condition (returns true/false)
bool evaluateCondition(const char* condition) {
  String condStr = String(condition);
  condStr.trim();
  
  // Handle comparison operators
  if (condStr.indexOf("==") > 0) {
    int pos = condStr.indexOf("==");
    String left = condStr.substring(0, pos);
    String right = condStr.substring(pos + 2);
    left.trim();
    right.trim();
    float leftVal = evaluateExpression(left.c_str());
    float rightVal = evaluateExpression(right.c_str());
    return abs(leftVal - rightVal) < 0.0001;
  }
  
  if (condStr.indexOf("!=") > 0) {
    int pos = condStr.indexOf("!=");
    String left = condStr.substring(0, pos);
    String right = condStr.substring(pos + 2);
    left.trim();
    right.trim();
    float leftVal = evaluateExpression(left.c_str());
    float rightVal = evaluateExpression(right.c_str());
    return abs(leftVal - rightVal) >= 0.0001;
  }
  
  if (condStr.indexOf("<=") > 0) {
    int pos = condStr.indexOf("<=");
    String left = condStr.substring(0, pos);
    String right = condStr.substring(pos + 2);
    left.trim();
    right.trim();
    float leftVal = evaluateExpression(left.c_str());
    float rightVal = evaluateExpression(right.c_str());
    return leftVal <= rightVal;
  }
  
  if (condStr.indexOf(">=") > 0) {
    int pos = condStr.indexOf(">=");
    String left = condStr.substring(0, pos);
    String right = condStr.substring(pos + 2);
    left.trim();
    right.trim();
    float leftVal = evaluateExpression(left.c_str());
    float rightVal = evaluateExpression(right.c_str());
    return leftVal >= rightVal;
  }
  
  if (condStr.indexOf("<") > 0) {
    int pos = condStr.indexOf("<");
    String left = condStr.substring(0, pos);
    String right = condStr.substring(pos + 1);
    left.trim();
    right.trim();
    float leftVal = evaluateExpression(left.c_str());
    float rightVal = evaluateExpression(right.c_str());
    return leftVal < rightVal;
  }
  
  if (condStr.indexOf(">") > 0) {
    int pos = condStr.indexOf(">");
    String left = condStr.substring(0, pos);
    String right = condStr.substring(pos + 1);
    left.trim();
    right.trim();
    float leftVal = evaluateExpression(left.c_str());
    float rightVal = evaluateExpression(right.c_str());
    return leftVal > rightVal;
  }
  
  // Just evaluate as expression (non-zero is true)
  return evaluateExpression(condition) != 0.0f;
}

// Execute a block of Lua code (decompressed)
void executeLuaBlock(String* lines, int startLine, int endLine) {
  int i = startLine;
  
  while (i <= endLine) {
    String line = lines[i];
    line.trim();
    
    // Skip empty lines and comments
    if (line.length() == 0 || line.startsWith("--")) {
      i++;
      continue;
    }
    
    // Handle if statements
    if (line.startsWith("if ")) {
      int thenPos = line.indexOf(" then");
      if (thenPos > 0) {
        String condition = line.substring(3, thenPos);
        condition.trim();
        
        // Find matching end
        int depth = 1;
        int elsePos = -1;
        int endPos = -1;
        
        for (int j = i + 1; j <= endLine; j++) {
          String checkLine = lines[j];
          checkLine.trim();
          if (checkLine.startsWith("if ")) depth++;
          if (checkLine == "end") {
            depth--;
            if (depth == 0) {
              endPos = j;
              break;
            }
          }
          if (depth == 1 && checkLine == "else") {
            elsePos = j;
          }
        }
        
        if (endPos > 0) {
          if (evaluateCondition(condition.c_str())) {
            // Execute then block
            int blockEnd = (elsePos > 0) ? elsePos - 1 : endPos - 1;
            executeLuaBlock(lines, i + 1, blockEnd);
          } else if (elsePos > 0) {
            // Execute else block
            executeLuaBlock(lines, elsePos + 1, endPos - 1);
          }
          i = endPos + 1;
          continue;
        }
      }
    }
    
    // Handle while loops
    if (line.startsWith("while ")) {
      int doPos = line.indexOf(" do");
      if (doPos > 0) {
        String condition = line.substring(6, doPos);
        condition.trim();
        
        // Find matching end
        int depth = 1;
        int endPos = -1;
        
        for (int j = i + 1; j <= endLine; j++) {
          String checkLine = lines[j];
          checkLine.trim();
          if (checkLine.startsWith("while ")) depth++;
          if (checkLine == "end") {
            depth--;
            if (depth == 0) {
              endPos = j;
              break;
            }
          }
        }
        
        if (endPos > 0) {
          // Execute loop
          int loopCount = 0;
          while (evaluateCondition(condition.c_str()) && loopCount < 1000) {
            executeLuaBlock(lines, i + 1, endPos - 1);
            loopCount++;
          }
          i = endPos + 1;
          continue;
        }
      }
    }
    
    // Handle for loops (simple numeric for)
    if (line.startsWith("for ")) {
      int doPos = line.indexOf(" do");
      if (doPos > 0) {
        String forHeader = line.substring(4, doPos);
        forHeader.trim();
        
        // Parse: varname = start, end [, step]
        int eqPos = forHeader.indexOf("=");
        if (eqPos > 0) {
          String varName = forHeader.substring(0, eqPos);
          varName.trim();
          
          String range = forHeader.substring(eqPos + 1);
          int firstComma = range.indexOf(",");
          if (firstComma > 0) {
            int secondComma = range.indexOf(",", firstComma + 1);
            
            String startStr = range.substring(0, firstComma);
            String endStr;
            String stepStr = "1";
            
            if (secondComma > 0) {
              endStr = range.substring(firstComma + 1, secondComma);
              stepStr = range.substring(secondComma + 1);
            } else {
              endStr = range.substring(firstComma + 1);
            }
            
            startStr.trim();
            endStr.trim();
            stepStr.trim();
            
            float startVal = evaluateExpression(startStr.c_str());
            float endVal = evaluateExpression(endStr.c_str());
            float stepVal = evaluateExpression(stepStr.c_str());
            
            // Find matching end
            int depth = 1;
            int endPos = -1;
            
            for (int j = i + 1; j <= endLine; j++) {
              String checkLine = lines[j];
              checkLine.trim();
              if (checkLine.startsWith("for ")) depth++;
              if (checkLine == "end") {
                depth--;
                if (depth == 0) {
                  endPos = j;
                  break;
                }
              }
            }
            
            if (endPos > 0) {
              // Execute loop
              int loopCount = 0;
              if (stepVal > 0) {
                for (float v = startVal; v <= endVal && loopCount < 1000; v += stepVal) {
                  setLuaVariable(varName.c_str(), v);
                  executeLuaBlock(lines, i + 1, endPos - 1);
                  loopCount++;
                }
              } else if (stepVal < 0) {
                for (float v = startVal; v >= endVal && loopCount < 1000; v += stepVal) {
                  setLuaVariable(varName.c_str(), v);
                  executeLuaBlock(lines, i + 1, endPos - 1);
                  loopCount++;
                }
              }
              i = endPos + 1;
              continue;
            }
          }
        }
      }
    }
    
    // Regular Lua statement
    executeLuaCode(line.c_str());
    i++;
  }
}

// Execute all stored multi-line code
void executeMultiLineLuaCode() {
  if (compressedCodeSize == 0) {
    Serial.println(F("[bot] No code to execute."));
    return;
  }
  
  // Decompress all lines
  String lines[MAX_LUA_LINES];
  int lineCount = 0;
  int pos = 0;
  
  while (pos < compressedCodeSize && lineCount < MAX_LUA_LINES) {
    int lineLen = compressedCode[pos++];
    if (pos + lineLen > compressedCodeSize) break;
    
    lines[lineCount++] = decompressLuaCode(compressedCode + pos, lineLen);
    pos += lineLen;
  }
  
  // Execute the decompressed code
  if (lineCount > 0) {
    executeLuaBlock(lines, 0, lineCount - 1);
  }
  
  // Clear compressed storage
  compressedCodeSize = 0;
}
