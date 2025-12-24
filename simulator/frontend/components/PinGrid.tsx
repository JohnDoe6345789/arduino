import { Card, CardContent, Grid, Slider, Stack, Switch, Typography } from '@mui/material';

export type DigitalPin = {
  index: number;
  label: string;
  state: boolean;
};

export type AnalogPin = {
  index: number;
  label: string;
  value: number;
};

type PinGridProps = {
  digitalPins: DigitalPin[];
  analogPins: AnalogPin[];
  onDigitalChange: (index: number, next: boolean) => void;
  onAnalogChange: (index: number, next: number) => void;
};

export function PinGrid({ digitalPins, analogPins, onDigitalChange, onAnalogChange }: PinGridProps) {
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Digital Pins</Typography>
            <Stack spacing={1}>
              {digitalPins.map((pin) => (
                <Stack
                  key={pin.index}
                  direction="row"
                  alignItems="center"
                  justifyContent="space-between"
                  data-testid={`digital-${pin.index}`}
                >
                  <Typography variant="body1">{pin.label}</Typography>
                  <Switch
                    checked={pin.state}
                    onChange={(_, checked) => onDigitalChange(pin.index, checked)}
                    color="primary"
                  />
                </Stack>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Analog Pins</Typography>
            <Stack spacing={2}>
              {analogPins.map((pin) => (
                <Stack key={pin.index} spacing={0.5} data-testid={`analog-${pin.index}`}>
                  <Stack direction="row" alignItems="center" justifyContent="space-between">
                    <Typography variant="body1">{pin.label}</Typography>
                    <Typography variant="body2" color="text.secondary">{pin.value.toFixed(2)} V</Typography>
                  </Stack>
                  <Slider
                    value={pin.value}
                    min={0}
                    max={5}
                    step={0.05}
                    marks={[{ value: 0, label: '0V' }, { value: 5, label: '5V' }]}
                    onChange={(_, value) => onAnalogChange(pin.index, value as number)}
                  />
                </Stack>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}
