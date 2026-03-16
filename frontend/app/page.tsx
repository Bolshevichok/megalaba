"use client";

import type { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { COLORS, FONT } from "../types/theme";

type DeviceType = "sensors" | "actuators" | "automation";

type DeviceTemplate = {
  key: string;
  label: string;
  color: string;
  type: DeviceType;
};

type PlacedDevice = {
  id: string;
  label: string;
  color: string;
  type: DeviceType;
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

const DEVICE_TYPE_TITLES: Record<DeviceType, string> = {
  sensors: "датчики",
  actuators: "актуаторы",
  automation: "автоматизация",
};

const DEVICE_TYPE_ORDER: DeviceType[] = ["sensors", "actuators", "automation"];

const DEVICE_TYPE_COLORS: Record<DeviceType, string> = {
  sensors: COLORS["device teal"],
  actuators: COLORS["device orange"],
  automation: COLORS["device olive"],
};

const KNOWN_DEVICES: Array<Omit<DeviceTemplate, "key">> = [
  { label: "освещенность", color: COLORS["device teal"], type: "sensors" },
  { label: "влажность", color: COLORS["device olive"], type: "sensors" },
  { label: "температура", color: COLORS["device orange"], type: "sensors" },
  { label: "полив", color: COLORS["device teal"], type: "actuators" },
  { label: "подогрев", color: COLORS["device orange"], type: "actuators" },
  { label: "проветривание", color: COLORS["device olive"], type: "actuators" },
  { label: "освещение", color: COLORS["device red"], type: "actuators" },
  { label: "поддержка скриптов", color: COLORS["device teal"], type: "automation" },
];

export default function Home() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [pending, setPending] = useState<DeviceTemplate | null>(null);
  const [activePlacedId, setActivePlacedId] = useState<string | null>(null);
  const [canvasFilter, setCanvasFilter] = useState<DeviceType | "all">("all");

  const canvasRef = useRef<HTMLElement | null>(null);
  const draggingRef = useRef<{ projectId: string; deviceId: string } | null>(null);
  const dragMovedRef = useRef(false);
  const skipPlacementClickRef = useRef(false);
  const [draggingDeviceId, setDraggingDeviceId] = useState<string | null>(null);

  const selected = useMemo(
    () => projects.find((project) => project.id === selectedId) ?? null,
    [projects, selectedId],
  );

  const createProject = () => {
    const typedName = window.prompt("project name", `teplitsa ${projects.length + 1}`);
    if (typedName === null) {
      return;
    }

    const name = typedName.trim();
    if (!name) {
      return;
    }

    const projectId = `project-${Date.now()}`;
    const project: Project = {
      id: projectId,
      name,
      expanded: true,
      devices: KNOWN_DEVICES.map((device, index) => ({
        ...device,
        key: `known-${projectId}-${index}`,
      })),
      placed: [],
    };

    setProjects((prev) => [...prev, project]);
    setSelectedId(projectId);
    setPending(null);
    setActivePlacedId(null);
  };

  const toggleExpand = (projectId: string) => {
    setProjects((prev) =>
      prev.map((project) =>
        project.id === projectId ? { ...project, expanded: !project.expanded } : project,
      ),
    );
  };

  const placeDevice = (x: number, y: number) => {
    if (!selected || !pending) {
      return;
    }

    const placed: PlacedDevice = {
      id: `placed-${Date.now()}`,
      label: pending.label,
      color: pending.color,
      type: pending.type,
      x,
      y,
    };

    setProjects((prev) =>
      prev.map((project) =>
        project.id === selected.id
          ? { ...project, placed: [...project.placed, placed] }
          : project,
      ),
    );

    setActivePlacedId(placed.id);
    setPending(null);
  };

  const movePlacedDevice = (projectId: string, deviceId: string, x: number, y: number) => {
    setProjects((prev) =>
      prev.map((project) =>
        project.id === projectId
          ? {
              ...project,
              placed: project.placed.map((device) =>
                device.id === deviceId ? { ...device, x, y } : device,
              ),
            }
          : project,
      ),
    );
  };

  const removePlacedDevice = (projectId: string, placedId: string) => {
    setProjects((prev) =>
      prev.map((project) =>
        project.id === projectId
          ? { ...project, placed: project.placed.filter((device) => device.id !== placedId) }
          : project,
      ),
    );
    setActivePlacedId(null);
  };

  const beginDragging = (
    event: React.PointerEvent<HTMLDivElement>,
    projectId: string,
    deviceId: string,
  ) => {
    event.preventDefault();
    event.stopPropagation();

    dragMovedRef.current = false;
    skipPlacementClickRef.current = true;
    draggingRef.current = { projectId, deviceId };
    setDraggingDeviceId(deviceId);
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const handleCanvasPointerMove = (event: React.PointerEvent<HTMLElement>) => {
    const dragging = draggingRef.current;
    const canvas = canvasRef.current;
    if (!dragging || !canvas) {
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width) * 100;
    const y = ((event.clientY - rect.top) / rect.height) * 100;

    dragMovedRef.current = true;
    movePlacedDevice(
      dragging.projectId,
      dragging.deviceId,
      Math.max(3, Math.min(97, x)),
      Math.max(3, Math.min(97, y)),
    );
  };

  const handleCanvasPointerUp = () => {
    if (!draggingRef.current) {
      return;
    }

    draggingRef.current = null;
    dragMovedRef.current = false;
    setDraggingDeviceId(null);

    window.setTimeout(() => {
      skipPlacementClickRef.current = false;
    }, 0);
  };

  const activePlacedDevice = useMemo(() => {
    if (!selected || !activePlacedId) {
      return null;
    }

    return selected.placed.find((device) => device.id === activePlacedId) ?? null;
  }, [selected, activePlacedId]);

  const visiblePlacedDevices = useMemo(() => {
    if (!selected) {
      return [];
    }

    if (canvasFilter === "all") {
      return selected.placed;
    }

    return selected.placed.filter((device) => device.type === canvasFilter);
  }, [selected, canvasFilter]);

  useEffect(() => {
    if (!activePlacedId) {
      return;
    }

    const stillVisible = visiblePlacedDevices.some((device) => device.id === activePlacedId);
    if (!stillVisible) {
      setActivePlacedId(null);
    }
  }, [activePlacedId, visiblePlacedDevices]);

  return (
    <div
      style={{
        minHeight: "100vh",
        overflow: "auto",
        background: COLORS["solid back"],
      }}
    >
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          fontFamily: FONT,
          overflow: "hidden",
        }}
      >
        <header
          style={{
            height: 56,
            flexShrink: 0,
            background: COLORS["little dark green"],
            boxShadow: "0 13px 4px rgba(0, 0, 0, 0.25)",
            display: "flex",
            alignItems: "center",
            padding: "0 16px",
            gap: 12,
            zIndex: 2,
          }}
        >
          <span
            style={{
              flex: 1,
              color: COLORS["green text"],
              fontSize: 12,
              letterSpacing: 0.3,
            }}
          >
            megalaba
          </span>
          <button type="button" onClick={() => router.push("/auth")} style={tealBtn}>
            exit
          </button>
        </header>

        <div
          style={{
            flex: 1,
            display: "grid",
            gridTemplateColumns: "260px 1fr",
            columnGap: 42,
            overflow: "hidden",
            minHeight: 0,
            padding: "28px 18px 18px",
          }}
        >
          <aside
            style={{
              background: COLORS["panel"],
              borderRadius: 15,
              boxShadow: "13px 13px 4px rgba(0, 0, 0, 0.25)",
              display: "flex",
              flexDirection: "column",
              overflowY: "auto",
            }}
          >
            <p
              style={{
                padding: "8px 16px 14px",
                color: COLORS["green text"],
                fontSize: 22,
                textAlign: "center",
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
                    <div
                      style={{
                        ...projectRowStyle,
                        background: "rgba(116, 143, 114, 0.19)",
                        color: isActive ? COLORS["light green text"] : COLORS["green text"],
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => toggleExpand(project.id)}
                        style={{
                          ...inlineIconButton,
                          color: isActive ? COLORS["light green text"] : COLORS["green text"],
                          transform: project.expanded ? "rotate(90deg)" : "none",
                          transition: "transform .15s",
                        }}
                      >
                        ▶
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedId(project.id);
                          setPending(null);
                          setActivePlacedId(null);
                        }}
                        style={{
                          ...inlineNameButton,
                          color: isActive ? COLORS["light green text"] : COLORS["green text"],
                        }}
                      >
                        {project.name}
                      </button>
                    </div>

                    {project.expanded && (
                      <div style={{ paddingLeft: 28, paddingBottom: 8 }}>
                        {DEVICE_TYPE_ORDER.map((type) => {
                          const typedDevices = project.devices.filter((device) => device.type === type);
                          if (!typedDevices.length) {
                            return null;
                          }

                          return (
                            <div key={`${project.id}-${type}`} style={{ marginBottom: 8 }}>
                              <span
                                style={{
                                  color: COLORS["green text"],
                                  fontSize: 11,
                                  textTransform: "lowercase",
                                  display: "block",
                                  marginBottom: 4,
                                }}
                              >
                                {DEVICE_TYPE_TITLES[type]} ({typedDevices.length})
                              </span>

                              {typedDevices.map((device) => (
                                <button
                                  key={device.key}
                                  type="button"
                                  onClick={() => setPending(pending?.key === device.key ? null : device)}
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
                          );
                        })}
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
                style={{ ...tealBtn, width: "100%", height: 26, fontSize: 14 }}
              >
                create
              </button>
            </div>
          </aside>

          <section
            ref={canvasRef}
            style={{
              position: "relative",
              overflow: "hidden",
              background: COLORS["solid back"],
              cursor: draggingDeviceId ? "grabbing" : pending ? "crosshair" : "default",
              paddingTop: 12,
            }}
            onPointerMove={handleCanvasPointerMove}
            onPointerUp={handleCanvasPointerUp}
            onPointerCancel={handleCanvasPointerUp}
            onClick={(event) => {
              setActivePlacedId(null);

              if (skipPlacementClickRef.current) {
                return;
              }

              if (!pending || !selected) {
                return;
              }

              const rect = event.currentTarget.getBoundingClientRect();
              const x = ((event.clientX - rect.left) / rect.width) * 100;
              const y = ((event.clientY - rect.top) / rect.height) * 100;
              placeDevice(Math.max(3, Math.min(97, x)), Math.max(3, Math.min(97, y)));
            }}
          >
            <GreenhousePattern visible={!!selected} />

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

            {pending && selected && (
              <div
                style={{
                  position: "absolute",
                  top: 58,
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

            <div
              style={{
                position: "absolute",
                top: 10,
                right: 16,
                zIndex: 11,
                background: COLORS["panel"],
                border: `1px solid ${COLORS["green text"]}`,
                borderRadius: 12,
                padding: "4px 6px",
                display: "flex",
                gap: 6,
              }}
              onPointerDown={(event) => event.stopPropagation()}
              onClick={(event) => event.stopPropagation()}
            >
              <button
                type="button"
                style={{
                  ...filterButtonStyle,
                  background: canvasFilter === "all" ? COLORS.teal : "rgba(4,86,109,0.28)",
                }}
                onClick={() => setCanvasFilter("all")}
                title="показать все"
              >
                все
              </button>
              {DEVICE_TYPE_ORDER.map((type) => (
                <button
                  key={type}
                  type="button"
                  style={{
                    ...filterButtonStyle,
                    background: canvasFilter === type ? DEVICE_TYPE_COLORS[type] : `${DEVICE_TYPE_COLORS[type]}66`,
                  }}
                  onClick={() => setCanvasFilter(type)}
                  title={DEVICE_TYPE_TITLES[type]}
                >
                  {DEVICE_TYPE_TITLES[type][0]}
                </button>
              ))}
            </div>

            {visiblePlacedDevices.map((device, idx) => (
              <div
                key={device.id}
                onPointerDown={(event) => {
                  if (!selected) {
                    return;
                  }
                  beginDragging(event, selected.id, device.id);
                }}
                onPointerUp={(event) => {
                  handleCanvasPointerUp();
                  event.stopPropagation();
                  if (!dragMovedRef.current) {
                    setActivePlacedId(device.id);
                  }
                }}
                onPointerCancel={() => {
                  handleCanvasPointerUp();
                }}
                style={{
                  position: "absolute",
                  left: `${device.x}%`,
                  top: `${device.y}%`,
                  transform: "translate(-50%, -50%)",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  zIndex: draggingDeviceId === device.id ? 8 : 4,
                  pointerEvents: "auto",
                  cursor: "grab",
                  touchAction: "none",
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

            {selected && activePlacedDevice && (
              <div
                style={{
                  position: "absolute",
                  left: `${Math.min(activePlacedDevice.x + 7, 88)}%`,
                  top: `${Math.max(activePlacedDevice.y - 4, 8)}%`,
                  transform: "translate(-50%, -50%)",
                  zIndex: 12,
                  background: COLORS["panel"],
                  border: `1px solid ${COLORS["green text"]}`,
                  borderRadius: 10,
                  padding: 8,
                  display: "grid",
                  gap: 6,
                  minWidth: 120,
                  boxShadow: "0 8px 18px rgba(0, 0, 0, 0.35)",
                }}
                onPointerDown={(event) => event.stopPropagation()}
                onClick={(event) => event.stopPropagation()}
              >
                <button
                  type="button"
                  style={deviceMenuButtonStyle}
                  onClick={() => {
                    window.alert("Редактирование устройства пока в разработке");
                  }}
                >
                  редактировать
                </button>
                <button
                  type="button"
                  style={{ ...deviceMenuButtonStyle, background: COLORS["device red"] }}
                  onClick={() => removePlacedDevice(selected.id, activePlacedDevice.id)}
                >
                  удалить
                </button>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

function GreenhousePattern({ visible }: { visible: boolean }) {
  if (!visible) return null;

  return (
    <div style={{ position: "absolute", inset: 0 }}>
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
        {([
          [9, 8],
          [91, 8],
          [91, 91],
          [9, 91],
        ] as [number, number][]).map(([cx, cy], index) => (
          <rect
            key={index}
            x={cx - 1}
            y={cy - 1}
            width={2}
            height={2}
            fill={COLORS["green text"]}
            opacity="0.6"
          />
        ))}
      </svg>

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
  borderRadius: 12,
  width: 108,
  height: 32,
  background: COLORS["teal"],
  color: COLORS["light green text"],
  fontFamily: FONT,
  fontSize: 18,
  lineHeight: 1,
  cursor: "pointer",
};

const projectRowStyle: CSSProperties = {
  width: "100%",
  border: "none",
  borderRadius: 0,
  padding: "0 10px",
  display: "flex",
  alignItems: "center",
  gap: 6,
  fontFamily: FONT,
  fontSize: 18,
  height: 30,
  cursor: "pointer",
};

const deviceRowStyle: CSSProperties = {
  width: 174,
  height: 20,
  border: "none",
  background: COLORS["device orange"],
  padding: "0 8px",
  display: "flex",
  alignItems: "center",
  gap: 6,
  color: COLORS["light green text"],
  fontFamily: FONT,
  fontSize: 12,
  cursor: "pointer",
  borderRadius: 10,
  marginBottom: 6,
};

const inlineIconButton: CSSProperties = {
  border: "none",
  background: "transparent",
  padding: 0,
  width: 16,
  cursor: "pointer",
  lineHeight: 1,
  fontSize: 15,
};

const inlineNameButton: CSSProperties = {
  border: "none",
  background: "transparent",
  padding: 0,
  textAlign: "left",
  width: "100%",
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  fontFamily: FONT,
  fontSize: 18,
  cursor: "pointer",
};

const deviceMenuButtonStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  height: 26,
  padding: "0 8px",
  color: COLORS["light green text"],
  background: COLORS.teal,
  fontFamily: FONT,
  fontSize: 14,
  textAlign: "left",
  cursor: "pointer",
};

const filterButtonStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  minWidth: 34,
  height: 28,
  padding: "0 8px",
  color: COLORS["light green text"],
  fontFamily: FONT,
  fontSize: 14,
  lineHeight: 1,
  cursor: "pointer",
};
