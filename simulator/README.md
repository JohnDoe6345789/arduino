# Arduino Simulator (Design Prototype)

This folder contains a proof-of-concept Arduino simulator composed of two layers:

- **Backend (C++/Conan/Ninja):** a minimal simulation core that models pin state, analog decay, and provides a CLI driver for quick iteration.
- **Frontend (Next.js/Material UI):** a React-based UI for visualising pins, toggling digital levels, and previewing analog ramps.

## Backend

The backend lives in [`backend/`](backend/) and uses Conan to fetch dependencies and CMake with the Ninja generator for fast builds.

### Requirements
- Python 3 with `conan`
- CMake 3.21+
- Ninja build system

### Build & test
```bash
cd simulator/backend
conan profile detect --force
conan install . --output-folder=build --build=missing
cmake --preset default
cmake --build --preset default
ctest --preset default
```

Running `sim_driver` demonstrates a simple LED toggle pattern with analog decay: `./build/sim_driver`.

## Frontend

The frontend lives in [`frontend/`](frontend/) and is built with Next.js and Material UI.

### Requirements
- Node.js 20+

### Install & run
```bash
cd simulator/frontend
npm ci
npm run dev
```

The landing page shows a mock board summary, digital pin toggles, and analog sliders that mirror how the backend pin state could be polled.

## Continuous Integration

GitHub Actions workflow [`simulator.yml`](../.github/workflows/simulator.yml) wires the backend and frontend together by building the C++ simulation core and linting/building the Next.js application.
