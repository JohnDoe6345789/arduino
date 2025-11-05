// Non-blocking smooth rainbow on Nano R4 Minima
static inline void setRGB(uint8_t r, uint8_t g, uint8_t b) {
  analogWrite(LEDR, 255 - r);
  analogWrite(LEDG, 255 - g);
  analogWrite(LEDB, 255 - b);
}

static void hsv2rgb(uint16_t h, uint8_t s, uint8_t v,
                    uint8_t &r, uint8_t &g, uint8_t &b) {
  uint8_t c = (uint16_t)v * s / 255;
  uint8_t x = (uint16_t)c * (60 - abs((h % 120) - 60)) / 60;
  uint8_t m = v - c;
  uint8_t rp=0, gp=0, bp=0;
  if (h < 60)       { rp=c; gp=x; bp=0; }
  else if (h < 120) { rp=x; gp=c; bp=0; }
  else if (h < 180) { rp=0; gp=c; bp=x; }
  else if (h < 240) { rp=0; gp=x; bp=c; }
  else if (h < 300) { rp=x; gp=0; bp=c; }
  else              { rp=c; gp=0; bp=x; }
  r = rp + m; g = gp + m; b = bp + m;
}

void setup() {
  pinMode(LEDR, OUTPUT);
  pinMode(LEDG, OUTPUT);
  pinMode(LEDB, OUTPUT);
}

void loop() {
  static uint32_t lastMillis = 0;
  static uint16_t hue = 0;            // 0–359
  const uint32_t interval = 10;       // ms per hue-step

  if (millis() - lastMillis >= interval) {
    lastMillis += interval;
    hue = (hue + 1) % 360;

    uint8_t r, g, b;
    hsv2rgb(hue, 255, 64, r, g, b);
    setRGB(r, g, b);
  }

  // — your custom tasks here —
  // e.g., check sensors, update display, handle USB commands
}
