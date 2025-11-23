#pragma once

#include <Arduino.h>

// =========================
// Configuration & types
// =========================

// Max number of arguments for a single command line.
// You can override this with -DHRA_MAX_ARGS=<N> at compile time.
#ifndef HRA_MAX_ARGS
#define HRA_MAX_ARGS 10
#endif

typedef void (*HraCommandHandler)(uint8_t argc, const char **argv);

// Called when no command matches, if supplied.
// You get the attempted command name (argv[0]), argc/argv and the Stream.
typedef void (*HraUnknownCommandHandler)(
    const char      *cmd,
    uint8_t          argc,
    const char     **argv,
    Stream          &io
);

// Optional configuration for the parser.
struct HraConfig {
    bool                     caseInsensitive;
    bool                     echoInput;
    bool                     allowComments;
    char                     commentChar;
    HraUnknownCommandHandler unknownHandler;

    HraConfig()
        : caseInsensitive(false),
          echoInput(false),
          allowComments(true),
          commentChar('#'),
          unknownHandler(nullptr)
    {}
};

// Each command can carry help metadata.
struct HraCommandDef {
    const char        *name;
    HraCommandHandler  handler;
    const char        *usage;       // optional, may be nullptr
    const char        *description; // optional, may be nullptr
};

class HumanReadableApi {
public:
    HumanReadableApi(
        Stream        &io,
        HraCommandDef *commands,
        uint8_t        commandCount,
        char          *lineBuffer,
        uint8_t        lineBufferSize
    );

    HumanReadableApi(
        Stream        &io,
        HraCommandDef *commands,
        uint8_t        commandCount,
        char          *lineBuffer,
        uint8_t        lineBufferSize,
        const HraConfig &config
    );

    // Call this regularly from loop(); it reads characters and fires handlers.
    void poll();

    // Optional: directly handle a full, null-terminated line.
    void handleLine(char *line);

    // Lower-level: directly invoke dispatch for a token array.
    void invoke(uint8_t argc, const char **argv);

    // Helper: parse "key=value" pairs in a line and call a callback.
    // Modifies the line in place. Pairs are separated by spaces, key and
    // value are separated by '='. Malformed tokens are skipped.
    typedef void (*KeyValueHandler)(const char *key, const char *value);

    // Original API (kept for compatibility, just ignores the count).
    static void parseKeyValuePairs(char *line, KeyValueHandler cb);

    // New API that returns the number of successfully parsed pairs.
    static size_t parseKeyValuePairsCount(char *line, KeyValueHandler cb);

    // Help generation based on HraCommandDef metadata.
    void printHelp() const;
    void printHelpFor(const char *commandName) const;

    // Line/overflow inspection.
    uint8_t bufferSize() const { return _bufferSize; }
    bool    lastLineOverflow() const { return _lastLineOverflow; }

private:
    Stream        &_io;
    HraCommandDef *_commands;
    uint8_t        _commandCount;

    char          *_buffer;
    uint8_t        _bufferSize;
    uint8_t        _len;

    bool           _caseInsensitive;
    bool           _echoInput;
    bool           _allowComments;
    char           _commentChar;
    HraUnknownCommandHandler _unknownHandler;

    bool           _overflowOnCurrentLine;
    bool           _lastLineOverflow;

    void dispatchTokens(uint8_t argc, const char **argv);

    static int  stricmpLocal(const char *a, const char *b);
};
