"use client";

import { useRef, useState } from "react";
import { COLORS, DEVICE_COLORS, FONT } from "../../types/theme";
import { Device } from "../../types/dashboard";

// Wave rows inside the greenhouse (y positions as % of viewBox height)
const WAVE_ROWS = [18, 28, 38, 48, 58, 68, 78];

// Greenhouse bounds in SVG viewBox (0-100 units)
const GH = { x1: 8, y1: 8, x2: 92, y2: 90 };

function buildWavePath(y: number): string {
  const step = 6;
  const amp = 2.5;
  let d = `M ${GH.x1} ${y}`;
  for (let x = GH.x1 + step; x <= GH.x2; x += step) {
    const cy = y + (((x - GH.x1) / step) % 2 === 0 ? amp : -amp);
    d += ` Q ${x - step / 2} ${cy} ${x} ${y}`;
  }
  return d;
}

// Slightly wobbly greenhouse outline path
const OUTLINE_PATH = `
  M ${GH.x1 + 1} ${GH.y1 - 0.5}
  C ${GH.x1 + 20} ${GH.y1 - 1}, ${GH.x1 + 55} ${GH.y1 + 0.5}, ${GH.x2 - 1} ${GH.y1 + 0.5}
  C ${GH.x2 + 0.5} ${GH.y1 + 15}, ${GH.x2 - 0.5} ${GH.y1 + 50}, ${GH.x2 + 1} ${GH.y2 - 1}
  C ${GH.x2 - 20} ${GH.y2 + 0.5}, ${GH.x1 + 40} ${GH.y2 - 0.5}, ${GH.x1 - 0.5} ${GH.y2 + 0.5}
  C ${GH.x1 - 0.5} ${GH.y2 - 25}, ${GH.x1 + 0.5} ${GH.y1 + 25}, ${GH.x1 + 1} ${GH.y1 - 0.5}
  Z
`.trim();

type CanvasProps = {
  devices: Device[];
  hasGreenhouse: boolean;
  selectedName: string;
  onMoveDevice: (id: number, x: number, y: number) => void;
  onCreateGreenhouse: () => void;
};

export default function Canvas({
  devices,
  hasGreenhouse,
  selectedName,
  onMoveDevice,
  onCreateGreenhouse,
}: CanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const draggingRef = useRef<{ id: number; offsetX: number; offsetY: number } | null>(null);
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  const handleMarkerMouseDown = (e: React.MouseEvent, device: Device) => {
    e.preventDefault();
    e.stopPropagation();
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const px = (device.x / 100) * rect.width;
    const py = (device.y / 100) * rect.height;
    draggingRef.current = {
      id: device.id,
      offsetX: e.clientX - rect.left - px,
      offsetY: e.clientY - rect.top - py,
    };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!draggingRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(2, Math.min(96, ((e.clientX - rect.left - draggingRef.current.offsetX) / rect.width) * 100));
    const y = Math.max(2, Math.min(96, ((e.clientY - rect.top - draggingRef.current.offsetY) / rect.height) * 100));
    onMoveDevice(draggingRef.current.id, x, y);
  };

  const handleMouseUp = () => {
    draggingRef.current = null;
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{
        flex: 1,
        background: COLORS["solid back"],
        position: "relative",
        overflow: "hidden",
        cursor: draggingRef.current ? "grabbing" : "default",
      }}
    >
      {!hasGreenhouse ? (
        /* ── empty state ── */
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 12,
            fontFamily: FONT,
          }}
        >
          <span style={{ color: COLORS["green text"], fontSize: 18 }}>
            you don&apos;t have any teplitsa.
          </span>
          <button
            onClick={onCreateGreenhouse}
            style={{
              background: "none",
              border: "none",
              color: COLORS["light green text"],
              fontFamily: FONT,
              fontSize: 18,
              cursor: "pointer",
              textDecoration: "underline",
            }}
          >
            create it.
          </button>
        </div>
      ) : (
        <>
          {/* ── SVG: greenhouse outline + wave rows ── */}
          <svg
            width="100%"
            height="100%"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            style={{ position: "absolute", top: 0, left: 0 }}
          >
            {/* wave rows */}
            {WAVE_ROWS.map((y) => (
              <path
                key={y}
                d={buildWavePath(y)}
                stroke={COLORS["green text"]}
                strokeWidth="0.4"
                fill="none"
                opacity="0.35"
              />
            ))}

            {/* greenhouse outline */}
            <path
              d={OUTLINE_PATH}
              stroke={COLORS["green text"]}
              strokeWidth="0.6"
              fill="none"
              opacity="0.7"
            />

            {/* corner ticks */}
            {[
              [GH.x1, GH.y1],
              [GH.x2, GH.y1],
              [GH.x2, GH.y2],
              [GH.x1, GH.y2],
            ].map(([cx, cy], i) => (
              <rect
                key={i}
                x={cx - 1}
                y={cy - 1}
                width={2}
                height={2}
                fill={COLORS["green text"]}
                opacity="0.7"
              />
            ))}
          </svg>

          {/* ── greenhouse name label ── */}
          {selectedName && (
            <div
              style={{
                position: "absolute",
                top: 8,
                left: "50%",
                transform: "translateX(-50%)",
                color: COLORS["green text"],
                fontFamily: FONT,
                fontSize: 13,
                pointerEvents: "none",
                opacity: 0.6,
              }}
            >
              {selectedName}
            </div>
          )}

          {/* ── device markers ── */}
          {devices.map((device, idx) => {
            const color = DEVICE_COLORS[device.colorIndex % DEVICE_COLORS.length];
            const isHovered = hoveredId === device.id;
            return (
              <div
                key={device.id}
                onMouseDown={(e) => handleMarkerMouseDown(e, device)}
                onMouseEnter={() => setHoveredId(device.id)}
                onMouseLeave={() => setHoveredId(null)}
                style={{
                  position: "absolute",
                  left: `${device.x}%`,
                  top: `${device.y}%`,
                  transform: "translate(-50%, -50%)",
                  cursor: "grab",
                  zIndex: isHovered ? 10 : 5,
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                {/* circle with number */}
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: "50%",
                    background: color,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#fff",
                    fontFamily: FONT,
                    fontSize: 14,
                    boxShadow: isHovered ? `0 0 0 2px ${color}55` : "none",
                    flexShrink: 0,
                  }}
                >
                  {idx + 1}
                </div>

                {/* tooltip */}
                {isHovered && (
                  <div
                    style={{
                      background: COLORS["panel"],
                      border: `1px solid ${color}`,
                      borderRadius: 5,
                      padding: "3px 8px",
                      color: COLORS["light green text"],
                      fontFamily: FONT,
                      fontSize: 12,
                      whiteSpace: "nowrap",
                      pointerEvents: "none",
                    }}
                  >
                    {device.name}
                  </div>
                )}
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}
