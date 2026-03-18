// Shared types for dashboard
export type Device = {
  id: number;
  name: string;
  colorIndex: number; // index into DEVICE_COLORS array
  x: number; // 0-100 percentage relative to canvas
  y: number;
};

export type Greenhouse = {
  id: number;
  name: string;
  expanded: boolean;
  devices: Device[];
};
