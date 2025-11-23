#include "HumanReadableApi.h"

#include <string.h>
#include <ctype.h>

// =========================
// Internal helpers
// =========================

int HumanReadableApi::stricmpLocal(const char *a, const char *b) {
    if (!a && !b) {
        return 0;
    }
    if (!a) {
        return -1;
    }
    if (!b) {
        return 1;
    }

    while (*a && *b) {
        unsigned char ca = static_cast<unsigned char>(*a);
        unsigned char cb = static_cast<unsigned char>(*b);
        int da = tolower(ca);
        int db = tolower(cb);
        if (da != db) {
            return da - db;
        }
        ++a;
        ++b;
    }

    return static_cast<unsigned char>(*a) -
           static_cast<unsigned char>(*b);
}

// =========================
// Constructors
// =========================

HumanReadableApi::HumanReadableApi(
    Stream &io,
    HraCommandDef *commands,
    uint8_t commandCount,
    char *lineBuffer,
    uint8_t lineBufferSize
)
    : _io(io),
      _commands(commands),
      _commandCount(commandCount),
      _buffer(lineBuffer),
      _bufferSize(lineBufferSize),
      _len(0),
      _caseInsensitive(false),
      _echoInput(false),
      _allowComments(true),
      _commentChar('#'),
      _unknownHandler(nullptr),
      _overflowOnCurrentLine(false),
      _lastLineOverflow(false)
{
}

HumanReadableApi::HumanReadableApi(
    Stream &io,
    HraCommandDef *commands,
    uint8_t commandCount,
    char *lineBuffer,
    uint8_t lineBufferSize,
    const HraConfig &config
)
    : _io(io),
      _commands(commands),
      _commandCount(commandCount),
      _buffer(lineBuffer),
      _bufferSize(lineBufferSize),
      _len(0),
      _caseInsensitive(config.caseInsensitive),
      _echoInput(config.echoInput),
      _allowComments(config.allowComments),
      _commentChar(config.commentChar),
      _unknownHandler(config.unknownHandler),
      _overflowOnCurrentLine(false),
      _lastLineOverflow(false)
{
}

// =========================
// Core polling
// =========================

void HumanReadableApi::poll() {
    while (_io.available()) {
        char c = static_cast<char>(_io.read());

        if (_echoInput) {
            _io.write(c);
        }

        if (c == '\n' || c == '\r') {
            if (_overflowOnCurrentLine) {
                // We had more characters than fit in the buffer.
                _lastLineOverflow    = true;
                _overflowOnCurrentLine = false;
                _len                 = 0;
                _io.println(F("ERR: Line too long"));
                continue;
            }

            if (_len > 0) {
                _buffer[_len] = '\0';
                _lastLineOverflow = false;
                handleLine(_buffer);
                _len = 0;
            }
        } else {
            if (_len < (_bufferSize - 1)) {
                _buffer[_len++] = c;
            } else {
                // Drop extra characters; remember that this line overflowed.
                _overflowOnCurrentLine = true;
            }
        }
    }
}

// =========================
// Tokenization / dispatch
// =========================

void HumanReadableApi::handleLine(char *line) {
    const char *argv[HRA_MAX_ARGS];
    uint8_t argc = 0;

    char *p = line;

    while (*p && argc < HRA_MAX_ARGS) {
        // Skip leading whitespace
        while (*p && isspace(static_cast<unsigned char>(*p))) {
            ++p;
        }
        if (!*p) {
            break;
        }

        // Comment support: if we hit the comment char at token start, stop.
        if (_allowComments && *p == _commentChar) {
            break;
        }

        char *start = nullptr;

        if (*p == '"') {
            // Quoted token: "foo bar", supports \" escape.
            ++p; // skip opening quote
            start = p;
            char *dst = start;

            while (*p) {
                if (*p == '\\' && p[1] != '\0') {
                    // Escape sequence: copy the next char verbatim.
                    ++p;
                    *dst++ = *p++;
                } else if (*p == '"') {
                    // Closing quote
                    ++p;
                    break;
                } else {
                    *dst++ = *p++;
                }
            }
            *dst = '\0';
        } else {
            // Normal token: stops at whitespace or commentChar
            start = p;
            while (*p &&
                   !isspace(static_cast<unsigned char>(*p))) {
                if (_allowComments && *p == _commentChar) {
                    // Comment character terminates token and the line.
                    break;
                }
                ++p;
            }
            if (*p) {
                *p = '\0';
                ++p;
            }
        }

        if (argc < HRA_MAX_ARGS && start && *start) {
            argv[argc++] = start;
        }

        // If we hit the comment character inside the token parsing,
        // the outer loop will see it as part of whitespace / null-termination
        // and break on the next iteration if it's at token start.
        if (!*p) {
            break;
        }
        if (_allowComments && *p == _commentChar) {
            break;
        }
    }

    if (argc > 0) {
        dispatchTokens(argc, argv);
    }
}

void HumanReadableApi::invoke(uint8_t argc, const char **argv) {
    dispatchTokens(argc, argv);
}

void HumanReadableApi::dispatchTokens(uint8_t argc, const char **argv) {
    if (argc == 0) {
        return;
    }

    const char *cmd = argv[0];

    for (uint8_t i = 0; i < _commandCount; ++i) {
        const HraCommandDef &def = _commands[i];
        if (!def.name) {
            continue;
        }

        bool match = false;
        if (_caseInsensitive) {
            match = (stricmpLocal(cmd, def.name) == 0);
        } else {
            match = (strcmp(cmd, def.name) == 0);
        }

        if (match) {
            if (def.handler) {
                def.handler(argc, argv);
            }
            return;
        }
    }

    if (_unknownHandler) {
        _unknownHandler(cmd, argc, argv, _io);
    } else {
        _io.println(F("ERR: Unknown command"));
    }
}

// =========================
// Key/value parsing
// =========================

void HumanReadableApi::parseKeyValuePairs(char *line,
                                          KeyValueHandler cb) {
    (void)parseKeyValuePairsCount(line, cb);
}

size_t HumanReadableApi::parseKeyValuePairsCount(char *line,
                                                 KeyValueHandler cb) {
    if (!line || !cb) {
        return 0;
    }

    size_t count = 0;
    char  *p     = line;

    while (*p) {
        // Skip leading whitespace
        while (*p && isspace(static_cast<unsigned char>(*p))) {
            ++p;
        }
        if (!*p) {
            break;
        }

        char *key = p;

        // Find '=' or whitespace
        while (*p && *p != '=' &&
               !isspace(static_cast<unsigned char>(*p))) {
            ++p;
        }

        if (*p != '=') {
            // Malformed token, skip to next whitespace
            while (*p && !isspace(static_cast<unsigned char>(*p))) {
                ++p;
            }
            continue;
        }

        // Terminate key
        *p++ = '\0';

        // Value starts here
        char *value = p;

        // Value runs until whitespace
        while (*p &&
               !isspace(static_cast<unsigned char>(*p))) {
            ++p;
        }

        if (*p) {
            *p++ = '\0';
        }

        cb(key, value);
        ++count;
    }

    return count;
}

// =========================
// Help
// =========================

void HumanReadableApi::printHelp() const {
    for (uint8_t i = 0; i < _commandCount; ++i) {
        const HraCommandDef &def = _commands[i];
        if (!def.name) {
            continue;
        }

        _io.print(F("  "));
        if (def.usage && def.usage[0] != '\0') {
            _io.print(def.usage);
        } else {
            _io.print(def.name);
        }

        if (def.description && def.description[0] != '\0') {
            _io.print(F("  - "));
            _io.print(def.description);
        }

        _io.println();
    }
}

void HumanReadableApi::printHelpFor(const char *commandName) const {
    if (!commandName || !*commandName) {
        printHelp();
        return;
    }

    for (uint8_t i = 0; i < _commandCount; ++i) {
        const HraCommandDef &def = _commands[i];
        if (!def.name) {
            continue;
        }

        bool match = false;
        if (_caseInsensitive) {
            match = (stricmpLocal(commandName, def.name) == 0);
        } else {
            match = (strcmp(commandName, def.name) == 0);
        }

        if (match) {
            _io.print(F("  "));
            if (def.usage && def.usage[0] != '\0') {
                _io.print(def.usage);
            } else {
                _io.print(def.name);
            }

            if (def.description && def.description[0] != '\0') {
                _io.print(F("  - "));
                _io.print(def.description);
            }

            _io.println();
            return;
        }
    }

    _io.print(F("ERR: No help for command '"));
    _io.print(commandName);
    _io.println(F("'"));
}
