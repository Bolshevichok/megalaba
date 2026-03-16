export const COLORS = {
  // backgrounds
  "solid back":        "#262726",
  "panel":             "#2D3A2D",
  "little dark green": "#303830",
  "sidebar":           "#2A322A",
  "input bg":          "#1C241C",
  "header":            "#2A2E2A",

  // text / accents
  "light green text":  "#6ADD5F",
  "green text":        "#748F72",

  // interactive
  "teal":              "#1A9090",
  "teal hover":        "#1FC8C8",

  // device type colors
  "device orange":     "#C47200",
  "device olive":      "#8A8A00",
  "device teal":       "#1A8080",
  "device red":        "#9A2020",
} as const;

export type ColorKey = keyof typeof COLORS;
export type BackgroundColor = "little dark green" | "solid back" | "panel" | "sidebar" | "input bg";

export const FONT = "var(--font-jersey-10)";

export const DEVICE_COLORS = [
  COLORS["device orange"],
  COLORS["device olive"],
  COLORS["device teal"],
  COLORS["device red"],
];
