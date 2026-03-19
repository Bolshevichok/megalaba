import { ReactNode } from "react";
import { BackgroundColor, COLORS } from "../types/theme";

type BackgroundProps = {
  color?: BackgroundColor;
  children: ReactNode;
};

export default function Background({ color = "solid back", children }: BackgroundProps) {
  return (
    <div style={{ background: COLORS[color], minHeight: "100vh" }}>
      {children}
    </div>
  );
}