import { useMemo, useState } from 'react';
import {
  AppBar,
  Box,
  Button,
  Container,
  IconButton,
  Stack,
  Toolbar,
  Typography
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { PinGrid, DigitalPin, AnalogPin } from '../components/PinGrid';

const initialDigitalPins: DigitalPin[] = Array.from({ length: 8 }, (_, index) => ({
  index,
  label: `D${index}`,
  state: index % 2 === 0
}));

const initialAnalogPins: AnalogPin[] = Array.from({ length: 4 }, (_, index) => ({
  index,
  label: `A${index}`,
  value: Number((Math.sin(index) + 1.0).toFixed(2)) * 2.5
}));

export default function Home() {
  const [digitalPins, setDigitalPins] = useState<DigitalPin[]>(initialDigitalPins);
  const [analogPins, setAnalogPins] = useState<AnalogPin[]>(initialAnalogPins);
  const [ticks, setTicks] = useState(0);

  const boardSummary = useMemo(
    () => ({
      name: 'Uno-like virtual board',
      digitalCount: digitalPins.length,
      analogCount: analogPins.length
    }),
    [digitalPins.length, analogPins.length]
  );

  const handleDigitalChange = (index: number, next: boolean) => {
    setDigitalPins((pins) => pins.map((pin) => (pin.index === index ? { ...pin, state: next } : pin)));
  };

  const handleAnalogChange = (index: number, next: number) => {
    setAnalogPins((pins) => pins.map((pin) => (pin.index === index ? { ...pin, value: next } : pin)));
  };

  const tickSimulation = () => {
    setTicks((value) => value + 1);
    setAnalogPins((pins) => pins.map((pin) => ({ ...pin, value: Number((pin.value * 0.95).toFixed(2)) })));
  };

  const resetPins = () => {
    setDigitalPins(initialDigitalPins);
    setAnalogPins(initialAnalogPins);
    setTicks(0);
  };

  return (
    <Box>
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Arduino Simulator UI
          </Typography>
          <IconButton color="inherit" aria-label="reset" onClick={resetPins}>
            <RefreshIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container sx={{ py: 4 }}>
        <Stack spacing={3}>
          <Box>
            <Typography variant="h5" gutterBottom>
              {boardSummary.name}
            </Typography>
            <Typography color="text.secondary">
              Digital pins: {boardSummary.digitalCount} · Analog pins: {boardSummary.analogCount} ·
              Simulated ticks: {ticks}
            </Typography>
          </Box>

          <PinGrid
            digitalPins={digitalPins}
            analogPins={analogPins}
            onDigitalChange={handleDigitalChange}
            onAnalogChange={handleAnalogChange}
          />

          <Stack direction="row" spacing={2}>
            <Button variant="contained" onClick={tickSimulation} data-testid="tick-button">
              Simulate tick
            </Button>
            <Button variant="outlined" onClick={resetPins}>
              Reset board
            </Button>
          </Stack>

          <Box>
            <Typography variant="body2" color="text.secondary">
              Changes here can be wired to the C++ backend through a lightweight API service. The UI currently mirrors the
              backend&apos;s analog decay behaviour and provides clear control of digital pins for quick prototyping.
            </Typography>
          </Box>
        </Stack>
      </Container>
    </Box>
  );
}
