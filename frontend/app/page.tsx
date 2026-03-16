"use client";

import type { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { COLORS, FONT } from "../types/theme";

type DeviceTemplate = {
  key: string;
  label: string;
  color: string;
};

type PlacedDevice = {
  id: string;
  label: string;
  color: string;
  x: number;
  y: number;
};

type Project = {
  id: string;
  name: string;
  expanded: boolean;
  devices: DeviceTemplate[];
  placed: PlacedDevice[];
};

const BASE_DEVICES: DeviceTemplate[] = [
  { key: "thermometer", label: "termometr", color: COLORS["device orange"] },
  { key: "humidity", label: "humidity", color: COLORS["device olive"] },
  { key: "light", label: "light sensor", color: COLORS["device teal"] },
  { key: "co2", label: "co2 sensor", color: COLORS["device red"] },
];

const NAMES = [
  "pervaya teplitsa",
  "vtoraya teplitsa",
  "tretya teplitsa",
  "chetvertaya teplitsa",
];

export default function Home() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [pending, setPending] = useState<DeviceTemplate | null>(null);

  const selected = useMemo(
    () => projects.find((p) => p.id === selectedId) ?? null,
    [projects, selectedId],
  );

  const createProject = () => {
    const n = projects.length;
    const id = `project-${Date.now()}`;
    const project: Project = {
      id,
      name: NAMES[n] ?? `teplitsa ${n + 1}`,
      expanded: true,
      devices: BASE_DEVICES.map((d, i) => ({
        ...d,
        key: `${d.key}-${id}-${i}`,
      })),
      placed: [],
    };
    setProjects((prev) => [...prev, project]);
    setSelectedId(id);
    setPending(null);
  };

  const placeDevice = (x: number, y: number) => {
    if (!selected || !pending) return;
    const placed: PlacedDevice = {
      id: `placed-${Date.now()}`,
      label: pending.label,
      color: pending.color,
      x,
      y,
    };
    setProjects((prev) =>
      prev.map((p) =>
        p.id === selected.id ? { ...p, placed: [...p.placed, placed] } : p,
      ),
    );
    setPending(null);
  };

  const toggleExpand = (id: string) =>
    setProjects((prev) =>
      prev.map((p) => (p.id === id ? { ...p, expanded: !p.expanded } : p)),
    );

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: COLORS["solid back"],
        fontFamily: FONT,
        overflow: "hidden",
      }}
    >
      {/* ── top bar ── */}
      <header
        style={{
          height: 44,
          flexShrink: 0,
          background: COLORS["little dark green"],
          borderBottom: "1px solid #1C241C",
          display: "flex",
          alignItems: "center",
          padding: "0 20px",
          gap: 12,
        }}
      >
        <span
          style={{
            flex: 1,
            color: COLORS["light green text"],
            fontSize: 20,
            letterSpacing: 2,
          }}
        >
          megalaba
        </span>
        <button
          type="button"
          onClick={() => router.push("/auth")}
          style={tealBtn}
        >
          exit
        </button>
      </header>

      {/* ── body ── */}
      <div
        style={{
          flex: 1,
          display: "grid",
          gridTemplateColumns: "200px 1fr",
          overflow: "hidden",
          minHeight: 0,
        }}
      >
        {/* ── sidebar ── */}
        <aside
          style={{
            background: COLORS["sidebar"],
            borderRight: "1px solid #1C241C",
            display: "flex",
            flexDirection: "column",
            overflowY: "auto",
          }}
        >
          <p
            style={{
              padding: "12px 16px 8px",
              color: COLORS["light green text"],
              fontSize: 20,
              borderBottom: "1px solid #1C241C",
            }}
          >
            teplitsi
          </p>

          <div style={{ flex: 1, padding: "6px 0" }}>
            {projects.length === 0 && (
              <p
                style={{
                  padding: "8px 16px",
                  color: COLORS["green text"],
                  fontSize: 13,
                }}
              >
                no greenhouses yet
              </p>
            )}

            {projects.map((project) => {
              const isActive = project.id === selectedId;
              return (
                <div key={project.id}>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedId(project.id);
                      setPending(null);
                      toggleExpand(project.id);
                    }}
                    style={{
                      ...projectRowStyle,
                      background: isActive ? "#243224" : "transparent",
                      color: isActive ? COLORS["light green text"] : COLORS["green text"],
                    }}
                  >
                    <span
                      style={{
                        display: "inline-block",
                        fontSize: 10,
                        transform: project.expanded ? "rotate(90deg)" : "none",
                        transition: "transform .15s",
                      }}
                    >
                      ▶
                    </span>
                    <span
                      style={{
                        flex: 1,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        textAlign: "left",
                      }}
                    >
                      {project.name}
                    </span>
                  </button>

                  {project.expanded && (
                    <div style={{ paddingLeft: 28, paddingBottom: 6 }}>
                      {project.devices.map((device) => (
                        <button
                          key={device.key}
                          type="button"
                          onClick={() =>
                            setPending(
                              pending?.key === device.key ? null : device,
                            )
                          }
                          style={{
                            ...deviceRowStyle,
                            outline:
                              pending?.key === device.key
                                ? `2px solid ${COLORS["light green text"]}`
                                : "none",
                          }}
                        >
                          <span
                            style={{
                              width: 8,
                              height: 8,
                              borderRadius: "50%",
                              background: device.color,
                              flexShrink: 0,
                              display: "block",
                            }}
                          />
                          <span
                            style={{
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {device.label}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ padding: "10px 14px", borderTop: "1px solid #1C241C" }}>
            <button
              type="button"
              onClick={createProject}
              style={{ ...tealBtn, width: "100%", padding: "6px 0" }}
            >
              + create
            </button>
          </div>
        </aside>

        {/* ── canvas ── */}
        <section
          style={{
            position: "relative",
            overflow: "hidden",
            background: COLORS["solid back"],
            cursor: pending ? "crosshair" : "default",
          }}
          onClick={(e) => {
            if (!pending || !selected) return;
            const rect = e.currentTarget.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            placeDevice(
              Math.max(3, Math.min(97, x)),
              Math.max(3, Math.min(97, y)),
            );
          }}
        >
          {/* wave + outline */}
          <GreenhousePattern visible={!!selected} />

          {/* empty state */}
          {!selected && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 10,
              }}
            >
              <span
                style={{
                  color: COLORS["green text"],
                  fontSize: "clamp(16px, 2vw, 24px)",
                }}
              >
                you don&apos;t have any teplitsa.
              </span>
              <button
                type="button"
                onClick={createProject}
                style={{
                  background: "none",
                  border: "none",
                  color: COLORS["light green text"],
                  fontFamily: FONT,
                  fontSize: "clamp(16px, 2vw, 24px)",
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
              >
                create it.
              </button>
            </div>
          )}

          {/* pending hint */}
          {pending && selected && (
            <div
              style={{
                position: "absolute",
                top: 12,
                right: 16,
                background: COLORS["panel"],
                color: COLORS["light green text"],
                borderRadius: 8,
                padding: "4px 12px",
                fontSize: 14,
                pointerEvents: "none",
                zIndex: 10,
              }}
            >
              place: {pending.label}
            </div>
          )}

          {/* placed devices */}
          {selected?.placed.map((device, idx) => (
            <div
              key={device.id}
              style={{
                position: "absolute",
                left: `${device.x}%`,
                top: `${device.y}%`,
                transform: "translate(-50%, -50%)",
                display: "flex",
                alignItems: "center",
                gap: 6,
                zIndex: 4,
                pointerEvents: "none",
              }}
            >
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: "50%",
                  background: device.color,
                  border: "2px solid #1D1D1D",
                  display: "grid",
                  placeItems: "center",
                  color: "#fff",
                  fontSize: 14,
                  flexShrink: 0,
                }}
              >
                {idx + 1}
              </div>
              <div
                style={{
                  background: COLORS["panel"],
                  color: COLORS["light green text"],
                  borderRadius: 6,
                  padding: "2px 8px",
                  fontSize: 13,
                  whiteSpace: "nowrap",
                }}
              >
                {device.label}
              </div>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}

function GreenhousePattern({ visible }: { visible: boolean }) {
  if (!visible) return null;
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {/* greenhouse outline */}
      <svg
        width="100%"
        height="100%"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        <path
          d="M 9 8 C 35 7, 65 8.5, 91 7.5 C 92 28, 91.5 60, 92 91 C 65 92, 35 91, 8.5 92 C 8 60, 8.5 28, 9 8 Z"
          stroke={COLORS["green text"]}
          strokeWidth="0.5"
          fill="none"
          opacity="0.6"
        />
        {/* corner marks */}
        {([
          [9, 8],
          [91, 8],
          [91, 91],
          [9, 91],
        ] as [number, number][]).map(([cx, cy], i) => (
          <rect
            key={i}
            x={cx - 1}
            y={cy - 1}
            width={2}
            height={2}
            fill={COLORS["green text"]}
            opacity="0.6"
          />
        ))}
      </svg>

      {/* wave rows */}
      {[16, 27, 38, 49, 60, 71, 82].map((top) => (
        <svg
          key={top}
          viewBox="0 0 1000 40"
          preserveAspectRatio="none"
          style={{
            position: "absolute",
            left: "9%",
            width: "82%",
            top: `${top}%`,
            height: 36,
            transform: "translateY(-50%)",
          }}
        >
          <path
            d="M0 20 C20 5,30 35,60 20 S90 5,120 20 S150 35,180 20 S210 5,240 20 S270 35,300 20 S330 5,360 20 S390 35,420 20 S450 5,480 20 S510 35,540 20 S570 5,600 20 S630 35,660 20 S690 5,720 20 S750 35,780 20 S810 5,840 20 S870 35,900 20 S930 5,960 20 S990 35,1000 20"
            fill="none"
            stroke={COLORS["green text"]}
            strokeWidth="5"
            strokeLinecap="round"
            opacity="0.3"
          />
        </svg>
      ))}
    </div>
  );
}

const tealBtn: CSSProperties = {
  border: "none",
  borderRadius: 6,
  padding: "4px 14px",
  background: COLORS["teal"],
  color: "#fff",
  fontFamily: FONT,
  fontSize: 14,
  cursor: "pointer",
};

const projectRowStyle: CSSProperties = {
  width: "100%",
  border: "none",
  borderRadius: 0,
  padding: "6px 10px",
  display: "flex",
  alignItems: "center",
  gap: 6,
  fontFamily: FONT,
  fontSize: 14,
  cursor: "pointer",
};

const deviceRowStyle: CSSProperties = {
  width: "100%",
  border: "none",
  background: "transparent",
  padding: "3px 6px 3px 0",
  display: "flex",
  alignItems: "center",
  gap: 6,
  color: COLORS["green text"],
  fontFamily: FONT,
  fontSize: 12,
  cursor: "pointer",
  borderRadius: 4,
};
