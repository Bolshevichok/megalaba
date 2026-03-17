"use client";

import type { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { COLORS, FONT } from "../types/theme";
import { 
  getGreenhouses, 
  createGreenhouse as apiCreateGreenhouse,
  deleteGreenhouse as apiDeleteGreenhouse,
  updateGreenhouseCanvas,
  getUnassignedDevices,
  assignDevice,
  saveScript
} from "../lib/api";

type DeviceType = "sensors" | "actuators";

type DeviceTemplate = {
  key: string;
  label: string;
  color: string;
  type: DeviceType;
  sourceId?: number;
};

type PlacedDevice = {
  id: string;
  label: string;
  color: string;
  type: DeviceType;
  order: number;
  x: number;
  y: number;
  currentReading?: string | number;
  sourceId?: number;
};

const SENSOR_UNITS: Record<string, string> = {
  "освещенность": "lx",
  "влажность": "%",
  "температура": "°C",
};

type Project = {
  id: string;
  name: string;
  expanded: boolean;
  devices: DeviceTemplate[];
  placed: PlacedDevice[];
};

type RuleJoin = "AND" | "OR";
type RuleOperator = ">" | ">=" | "=" | "<=" | "<";
type RuleCommand = "on" | "off";
type RuleScopeMode = "all" | "custom";

type RuleCondition = {
  id: string;
  sensorKeys: string[];
  operator: RuleOperator;
  value: string;
  joinWithPrevious: RuleJoin;
};

type RuleDeviceOption = {
  id: string;
  label: string;
};

type RuleDeviceTypeOption = {
  label: string;
  ids: string[];
};

type AutomationRule = {
  id: string;
  name: string;
  enabled: boolean;
  scopeMode: RuleScopeMode;
  allowedSensorKeys: string[];
  allowedActuatorKeys: string[];
  conditions: RuleCondition[];
  actuatorKeys: string[];
  command: RuleCommand;
};

const DEVICE_TYPE_TITLES: Record<DeviceType, string> = {
  sensors: "датчики",
  actuators: "актуаторы",
};

const DEVICE_TYPE_ORDER: DeviceType[] = ["sensors", "actuators"];

const DEVICE_TYPE_COLORS: Record<DeviceType, string> = {
  sensors: COLORS["device teal"],
  actuators: COLORS["device orange"],
};



export default function Home() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [availableDevices, setAvailableDevices] = useState<DeviceTemplate[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [pending, setPending] = useState<DeviceTemplate | null>(null);
  const [activePlacedId, setActivePlacedId] = useState<string | null>(null);
  const [canvasFilter, setCanvasFilter] = useState<DeviceType | "all">("all");
  const [isAutomationOpen, setIsAutomationOpen] = useState(false);
  const [rulesByProject, setRulesByProject] = useState<Record<string, AutomationRule[]>>({});
  const [activeRuleIdByProject, setActiveRuleIdByProject] = useState<Record<string, string | null>>({});

  const canvasRef = useRef<HTMLElement | null>(null);
  const draggingRef = useRef<{ projectId: string; deviceId: string } | null>(null);
  const dragMovedRef = useRef(false);
  const skipPlacementClickRef = useRef(false);
  const [draggingDeviceId, setDraggingDeviceId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [fetchedGreenhousesResp, unassignedResp] = await Promise.all([
        getGreenhouses(),
        getUnassignedDevices(),
      ]);

      const fetchedGreenhouses = fetchedGreenhousesResp.greenhouses || [];
      const unassigned = unassignedResp.devices || [];

      const newProjects = fetchedGreenhouses.map((gh: any) => {
        let placed: any[] = [];
        if (gh.canvas_state) {
          try {
            placed = JSON.parse(gh.canvas_state);
          } catch (e) {
            console.error("Failed to parse canvas_state", e);
          }
        }

        const normalizedPlaced: PlacedDevice[] = placed
          .filter((item) => item && typeof item === "object")
          .map((item) => {
            const legacyType = String(item.type || "");
            const normalizedType: DeviceType = legacyType === "actuators" ? "actuators" : "sensors";
            return {
              ...item,
              type: normalizedType,
            };
          });

        return {
          id: String(gh.id),
          name: gh.name,
          expanded: true,
          devices: [],
          placed: normalizedPlaced,
        };
      });
      setProjects(newProjects);
      
      setAvailableDevices(
        unassigned.map((d: any) => {
          let type: DeviceType = "sensors";
          let color: string = COLORS["device teal"];

         const actuatorCount = Number(d?.actuator_count ?? 0);

          if (actuatorCount > 0 || d?.device_type?.includes("actuator")) {
            type = "actuators";
            color = COLORS["device orange"];
          }

          return {
            key: String(d.id),
            label: d.name,
            color,
            type,
            sourceId: d.id,
          };
        }),
      );

      setSelectedId((prev) => {
        if (!prev && newProjects.length > 0) {
          return newProjects[0].id;
        }
        return prev;
      });

    } catch (e) {
      console.error("Failed to load data", e);
      if (e instanceof Error && (e.message.includes("403") || e.message.includes("401"))) {
        router.push("/auth");
      }
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const selected = useMemo(
    () => projects.find((project) => project.id === selectedId) ?? null,
    [projects, selectedId],
  );

  const selectedSensors = useMemo<RuleDeviceOption[]>(() => {
    if (!selected) {
      return [];
    }

    const counters: Record<string, number> = {};
    return selected.placed
      .filter((device) => device.type === "sensors")
      .map((device) => {
        counters[device.label] = (counters[device.label] ?? 0) + 1;
        return {
          id: String(device.sourceId ?? device.id),
          label: `${device.label} ${counters[device.label]}`,
        };
      });
  }, [selected]);

  const selectedActuators = useMemo<RuleDeviceOption[]>(() => {
    if (!selected) {
      return [];
    }

    const counters: Record<string, number> = {};
    return selected.placed
      .filter((device) => device.type === "actuators")
      .map((device) => {
        counters[device.label] = (counters[device.label] ?? 0) + 1;
        return {
          id: String(device.sourceId ?? device.id),
          label: `${device.label} ${counters[device.label]}`,
        };
      });
  }, [selected]);

  const selectedSensorTypes = useMemo<RuleDeviceTypeOption[]>(() => {
    const grouped = new Map<string, string[]>();
    selectedSensors.forEach((sensor) => {
      const baseLabel = sensor.label.replace(/\s\d+$/, "");
      grouped.set(baseLabel, [...(grouped.get(baseLabel) ?? []), sensor.id]);
    });

    return Array.from(grouped.entries()).map(([label, ids]) => ({ label, ids }));
  }, [selectedSensors]);

  const selectedActuatorTypes = useMemo<RuleDeviceTypeOption[]>(() => {
    const grouped = new Map<string, string[]>();
    selectedActuators.forEach((actuator) => {
      const baseLabel = actuator.label.replace(/\s\d+$/, "");
      grouped.set(baseLabel, [...(grouped.get(baseLabel) ?? []), actuator.id]);
    });

    return Array.from(grouped.entries()).map(([label, ids]) => ({ label, ids }));
  }, [selectedActuators]);

  const selectedRules = useMemo(
    () => (selected ? rulesByProject[selected.id] ?? [] : []),
    [rulesByProject, selected],
  );

  const activeRule = useMemo(() => {
    if (!selected) {
      return null;
    }
    const ruleId = activeRuleIdByProject[selected.id];
    if (!ruleId) {
      return null;
    }
    return selectedRules.find((rule) => rule.id === ruleId) ?? null;
  }, [activeRuleIdByProject, selected, selectedRules]);

  const availableSensorsForRule = useMemo(() => {
    if (!activeRule) {
      return [];
    }
    if (activeRule.scopeMode === "all") {
      return selectedSensors;
    }
    return selectedSensors.filter((device) => activeRule.allowedSensorKeys.includes(device.id));
  }, [activeRule, selectedSensors]);

  const availableActuatorsForRule = useMemo(() => {
    if (!activeRule) {
      return [];
    }
    if (activeRule.scopeMode === "all") {
      return selectedActuators;
    }
    return selectedActuators.filter((device) => activeRule.allowedActuatorKeys.includes(device.id));
  }, [activeRule, selectedActuators]);

  const createDefaultCondition = (): RuleCondition => ({
    id: `condition-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    sensorKeys: selectedSensors[0]?.id ? [selectedSensors[0].id] : [],
    operator: ">",
    value: "",
    joinWithPrevious: "OR",
  });

  const createRule = () => {
    if (!selected) {
      return;
    }

    const newRule: AutomationRule = {
      id: `rule-${Date.now()}`,
      name: `Правило ${selectedRules.length + 1}`,
      enabled: true,
      scopeMode: "all",
      allowedSensorKeys: selectedSensors.map((device) => device.id),
      allowedActuatorKeys: selectedActuators.map((device) => device.id),
      conditions: [createDefaultCondition()],
      actuatorKeys: selectedActuators[0]?.id ? [selectedActuators[0].id] : [],
      command: "on",
    };

    setRulesByProject((prev) => ({
      ...prev,
      [selected.id]: [...(prev[selected.id] ?? []), newRule],
    }));

    setActiveRuleIdByProject((prev) => ({
      ...prev,
      [selected.id]: newRule.id,
    }));
  };

  const updateRule = (ruleId: string, updater: (rule: AutomationRule) => AutomationRule) => {
    if (!selected) {
      return;
    }
    setRulesByProject((prev) => ({
      ...prev,
      [selected.id]: (prev[selected.id] ?? []).map((rule) => (rule.id === ruleId ? updater(rule) : rule)),
    }));
  };

  const deleteRule = (ruleId: string) => {
    if (!selected) {
      return;
    }

    const nextRules = (rulesByProject[selected.id] ?? []).filter((rule) => rule.id !== ruleId);
    setRulesByProject((prev) => ({
      ...prev,
      [selected.id]: nextRules,
    }));

    setActiveRuleIdByProject((prev) => ({
      ...prev,
      [selected.id]: nextRules[0]?.id ?? null,
    }));
  };


  const saveRuleToServer = async (rule: AutomationRule) => {
    if (!selected) return;
    try {
      await saveScript(Number(selected.id), {
        name: rule.name,
        script_code: JSON.stringify(rule),
        enabled: rule.enabled
      });
      alert("Правило сохранено на сервере!");
    } catch (e) {
      console.error("Failed to save rule", e);
      alert("Ошибка при сохранении правила");
    }
  };

  const createProject = async () => {

    const typedName = window.prompt("project name", `teplitsa ${projects.length + 1}`);
    if (typedName === null) {
      return;
    }

    const name = typedName.trim();
    if (!name) {
      return;
    }

    try {
      const newGh = await apiCreateGreenhouse({ name });
      const projectId = String(newGh.id);
      const project: Project = {
        id: projectId,
        name,
        expanded: true,
        devices: [],
        placed: [],
      };

      setProjects((prev) => [...prev, project]);
      setSelectedId(projectId);
      setPending(null);
      setActivePlacedId(null);
    } catch (e) {
      console.error("Failed to create greenhouse", e);
      alert("Failed to create greenhouse");
    }
  };

  const toggleExpand = (projectId: string) => {
    setProjects((prev) =>
      prev.map((project) =>
        project.id === projectId ? { ...project, expanded: !project.expanded } : project,
      ),
    );
  };

  const deleteProject = async (projectId: string, projectName: string) => {
    const shouldDelete = window.confirm(`Удалить теплицу \"${projectName}\"?`);
    if (!shouldDelete) {
      return;
    }

    try {
      await apiDeleteGreenhouse(Number(projectId));

      setProjects((prev) => prev.filter((project) => project.id !== projectId));
      setSelectedId((prev) => (prev === projectId ? null : prev));
      setActivePlacedId(null);
      setPending(null);

      await loadData();
    } catch (e) {
      console.error("Failed to delete greenhouse", e);
      alert("Не удалось удалить теплицу");
    }
  };

  const persistCanvasState = async (projectId: string, newPlaced: PlacedDevice[]) => {
    try {
      await updateGreenhouseCanvas(Number(projectId), JSON.stringify(newPlaced));
    } catch (e) {
      console.error("Failed to persist canvas", e);
    }
  };

  const placeDevice = async (x: number, y: number) => {
    if (!selected || !pending || !pending.sourceId) {
      return;
    }

    const placed: PlacedDevice = {
      id: String(Date.now()) + Math.random().toString().slice(2, 6),
      label: pending.label,
      color: pending.color,
      type: pending.type,
      order: selected.placed.length + 1,
      x,
      y,
      sourceId: pending.sourceId,
    };

    const newPlaced = [...selected.placed, placed];

    try {
      await assignDevice(pending.sourceId, Number(selected.id));

      const nextProjects = projects.map((project) => {
        if (project.id === selected.id) {
          return { ...project, placed: newPlaced };
        }

        const filteredPlaced = project.placed.filter((device) => device.sourceId !== pending.sourceId);
        return filteredPlaced.length === project.placed.length ? project : { ...project, placed: filteredPlaced };
      });

      setProjects(nextProjects);

      setAvailableDevices((prev) => prev.filter((d) => d.sourceId !== pending.sourceId));
      
      setActivePlacedId(placed.id);
      setPending(null);

      await Promise.all(
        nextProjects
          .filter((project) =>
            project.id === selected.id || project.placed.length !== projects.find((p) => p.id === project.id)?.placed.length,
          )
          .map((project) => persistCanvasState(project.id, project.placed)),
      );
    } catch (e) {
      console.error("Failed to assign and place device", e);
      alert("Failed to place device on server");
    }
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

  const removePlacedDevice = async (projectId: string, placedId: string) => {
    const project = projects.find((p) => p.id === projectId);
    if (!project) return;
    const deviceToRemove = project.placed.find((d) => d.id === placedId);
    if (!deviceToRemove || !deviceToRemove.sourceId) return;

    const newPlaced = project.placed.filter((device) => device.id !== placedId);

    try {
      await assignDevice(deviceToRemove.sourceId, null);

      const nextProjects = projects.map((project) => {
        const filteredPlaced = project.placed.filter((device) => device.sourceId !== deviceToRemove.sourceId);
        if (project.id === projectId) {
          return { ...project, placed: newPlaced };
        }
        return filteredPlaced.length === project.placed.length ? project : { ...project, placed: filteredPlaced };
      });

      setProjects(nextProjects);
      setAvailableDevices((prev) => [
        ...prev.filter((device) => device.sourceId !== deviceToRemove.sourceId),
        {
          key: String(deviceToRemove.sourceId),
          label: deviceToRemove.label,
          color: deviceToRemove.color,
          type: deviceToRemove.type,
          sourceId: deviceToRemove.sourceId,
        },
      ]);
      setActivePlacedId(null);

      await Promise.all(
        nextProjects
          .filter((project) =>
            project.id === projectId || project.placed.length !== projects.find((p) => p.id === project.id)?.placed.length,
          )
          .map((project) => persistCanvasState(project.id, project.placed)),
      );
      await loadData();
    } catch (e) {
      console.error("Failed to remove placed device", e);
      alert("Failed to remove placed device");
    }
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
    const dragging = draggingRef.current;
    if (!dragging) return;

    if (dragMovedRef.current) {
      const pId = dragging.projectId;
      const proj = projects.find((p) => p.id === pId);
      if (proj) {
         persistCanvasState(pId, proj.placed);
      }
    }

    draggingRef.current = null;
    dragMovedRef.current = false;
    setDraggingDeviceId(null);

    window.setTimeout(() => {
      skipPlacementClickRef.current = false;
    }, 0);
  };

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
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          setSelectedId(project.id);
                          setIsAutomationOpen(true);
                        }}
                        style={scriptsBtnStyle}
                        title="Скрипты"
                      >
                        scripts
                      </button>
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          deleteProject(project.id, project.name);
                        }}
                        style={deleteProjectBtnStyle}
                        title="Удалить теплицу"
                      >
                        ×
                      </button>
                    </div>

                    
                  </div>
                );
              })}

            {availableDevices.length > 0 && (
              <div style={{ marginTop: 24, borderTop: "1px solid #1C241C", paddingTop: 10 }}>
                <p style={{ padding: "8px 16px", color: COLORS["light green text"], fontSize: 16 }}>
                  непривязанные
                </p>
                <div style={{ paddingLeft: 16, paddingBottom: 8 }}>
                  {DEVICE_TYPE_ORDER.map((type) => {
                    const typedDevices = availableDevices.filter((device) => device.type === type);
                    if (!typedDevices.length) return null;
                    return (
                      <div key={`unassigned-${type}`} style={{ marginBottom: 8 }}>
                        <span style={{ color: COLORS["green text"], fontSize: 11, textTransform: "lowercase", display: "block", marginBottom: 4 }}>
                          {DEVICE_TYPE_TITLES[type]} ({typedDevices.length})
                        </span>
                        {typedDevices.map((device) => (
                          <button key={device.key} type="button" onClick={() => setPending(pending?.key === device.key ? null : device)} style={{ ...deviceRowStyle, outline: pending?.key === device.key ? `2px solid ${COLORS["light green text"]}` : "none" }}>
                            <span style={{ width: 8, height: 8, borderRadius: "50%", background: device.color, flexShrink: 0, display: "block" }} />
                            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{device.label}</span>
                          </button>
                        ))}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
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

            {!isLoading && !selected && (
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

            {visiblePlacedDevices.map((device) => (
              <div
                key={device.id}
                onPointerDown={(event) => {
                  if (event.button !== 0) {
                    return;
                  }
                  if (!selected) {
                    return;
                  }
                  beginDragging(event, selected.id, device.id);
                }}
                onPointerUp={(event) => {
                  if (event.button !== 0) {
                    return;
                  }
                  handleCanvasPointerUp();
                  event.stopPropagation();
                }}
                onClick={(event) => {
                  event.stopPropagation();
                  if (!dragMovedRef.current) {
                    setActivePlacedId(device.id);
                  }
                }}
                onPointerCancel={() => {
                  handleCanvasPointerUp();
                }}
                onContextMenu={(event) => event.preventDefault()}
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
                  overflow: "visible",
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
                  {device.order}
                </div>
                <div
                  style={{
                    background: COLORS["panel"],
                    color: COLORS["light green text"],
                    borderRadius: 6,
                    padding: "2px 8px",
                    fontSize: 13,
                    whiteSpace: "nowrap",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <span>{device.label}</span>
                  {device.type === "sensors" && (
                    <span
                      style={{
                        background: "rgba(255, 255, 255, 0.1)",
                        padding: "1px 6px",
                        borderRadius: 4,
                        color: "#fff",
                        fontSize: 12,
                        fontWeight: 500,
                      }}
                    >
                      {device.currentReading ?? "--"} {SENSOR_UNITS[device.label.replace(/\s\d+$/, "")] ?? ""}
                    </span>
                  )}
                </div>
                {activePlacedId === device.id && selected && (
                  <button
                    type="button"
                    style={deviceDeleteButtonStyle}
                    onPointerDown={(event) => event.stopPropagation()}
                    onClick={(event) => {
                      event.stopPropagation();
                      removePlacedDevice(selected.id, device.id);
                    }}
                    title="Удалить устройство"
                  >
                    −
                  </button>
                )}
              </div>
            ))}
          </section>
        </div>
      </div>

      {isAutomationOpen && (
        <div style={modalOverlayStyle} onClick={() => setIsAutomationOpen(false)}>
          <div style={modalStyle} onClick={(event) => event.stopPropagation()}>
            <div style={modalHeaderStyle}>
              <span>Автоматизация</span>
              <button type="button" style={modalCloseBtnStyle} onClick={() => setIsAutomationOpen(false)}>
                close
              </button>
            </div>

            {!selected ? (
              <div style={emptyModalStateStyle}>Сначала создайте и выберите теплицу</div>
            ) : (
              <div style={modalContentStyle}>
                <aside style={rulesListStyle}>
                  <button type="button" style={newRuleBtnStyle} onClick={createRule}>
                    + новое правило
                  </button>

                  {selectedRules.map((rule) => (
                    <button
                      key={rule.id}
                      type="button"
                      onClick={() =>
                        setActiveRuleIdByProject((prev) => ({
                          ...prev,
                          [selected.id]: rule.id,
                        }))
                      }
                      style={{
                        ...ruleItemStyle,
                        borderColor: activeRule?.id === rule.id ? COLORS["light green text"] : "transparent",
                      }}
                    >
                      <span>{rule.name}</span>
                      <span style={{ opacity: 0.75 }}>{rule.enabled ? "on" : "off"}</span>
                    </button>
                  ))}
                </aside>

                <section style={editorStyle}>
                  {!activeRule ? (
                    <div style={emptyModalStateStyle}>Создайте или выберите правило</div>
                  ) : (
                    <>
                      <div style={editorRowStyle}>
                        <input
                          value={activeRule.name}
                          onChange={(event) =>
                            updateRule(activeRule.id, (rule) => ({ ...rule, name: event.target.value }))
                          }
                          style={textInputStyle}
                        />
                        <label style={toggleLabelStyle}>
                          <input
                            type="checkbox"
                            checked={activeRule.enabled}
                            onChange={(event) =>
                              updateRule(activeRule.id, (rule) => ({ ...rule, enabled: event.target.checked }))
                            }
                          />
                          enabled
                        </label>
                        <button type="button" style={dangerBtnStyle} onClick={() => deleteRule(activeRule.id)}>
                          удалить
                        </button>
                      </div>

                      <div style={sectionTitleStyle}>Если</div>

                      <div style={scopePanelStyle}>
                        <div style={scopeHeaderStyle}>Устройства в правиле</div>
                        <div style={conditionRowStyle}>
                          <select
                            value={activeRule.scopeMode}
                            onChange={(event) => {
                              const nextMode = event.target.value as RuleScopeMode;
                              updateRule(activeRule.id, (rule) => {
                                const baseRule: AutomationRule =
                                  nextMode === "all"
                                    ? {
                                        ...rule,
                                        scopeMode: "all",
                                        allowedSensorKeys: selectedSensors.map((device) => device.id),
                                        allowedActuatorKeys: selectedActuators.map((device) => device.id),
                                      }
                                    : {
                                        ...rule,
                                        scopeMode: "custom",
                                        allowedSensorKeys:
                                          rule.allowedSensorKeys.length > 0
                                            ? rule.allowedSensorKeys
                                            : selectedSensors.map((device) => device.id),
                                        allowedActuatorKeys:
                                          rule.allowedActuatorKeys.length > 0
                                            ? rule.allowedActuatorKeys
                                            : selectedActuators.map((device) => device.id),
                                      };

                                const sensorPool =
                                  baseRule.scopeMode === "all"
                                    ? selectedSensors
                                    : selectedSensors.filter((device) =>
                                        baseRule.allowedSensorKeys.includes(device.id),
                                      );
                                const actuatorPool =
                                  baseRule.scopeMode === "all"
                                    ? selectedActuators
                                    : selectedActuators.filter((device) =>
                                        baseRule.allowedActuatorKeys.includes(device.id),
                                      );

                                return {
                                  ...baseRule,
                                  conditions: baseRule.conditions.map((condition) => ({
                                      ...condition,
                                      sensorKeys: condition.sensorKeys.filter((sensorId) =>
                                        sensorPool.some((sensor) => sensor.id === sensorId),
                                      ),
                                    })),
                                  actuatorKeys: baseRule.actuatorKeys.filter((actuatorId) =>
                                    actuatorPool.some((actuator) => actuator.id === actuatorId),
                                  ),
                                };
                              });
                            }}
                            style={smallSelectStyle}
                          >
                            <option value="all">все устройства</option>
                            <option value="custom">конкретные</option>
                          </select>
                        </div>

                        {activeRule.scopeMode === "custom" && (
                          <>
                            <div style={scopeGroupTitleStyle}>Датчики для условий</div>
                            <div style={scopeCheckboxGridStyle}>
                              {selectedSensorTypes.map((sensorType) => (
                                <label key={sensorType.label} style={scopeCheckboxLabelStyle}>
                                  <input
                                    type="checkbox"
                                    checked={sensorType.ids.every((id) => activeRule.allowedSensorKeys.includes(id))}
                                    onChange={(event) => {
                                      updateRule(activeRule.id, (rule) => {
                                        const nextKeys = event.target.checked
                                          ? [...rule.allowedSensorKeys, ...sensorType.ids]
                                          : rule.allowedSensorKeys.filter(
                                              (key) => !sensorType.ids.includes(key),
                                            );
                                        const uniqueKeys = Array.from(new Set(nextKeys));
                                        const filteredSensors = selectedSensors.filter((device) =>
                                          uniqueKeys.includes(device.id),
                                        );

                                        return {
                                          ...rule,
                                          allowedSensorKeys: uniqueKeys,
                                          conditions: rule.conditions.map((condition) => ({
                                              ...condition,
                                              sensorKeys: condition.sensorKeys.filter((sensorId) =>
                                                filteredSensors.some((device) => device.id === sensorId),
                                              ),
                                            })),
                                        };
                                      });
                                    }}
                                  />
                                  {sensorType.label}
                                </label>
                              ))}
                            </div>

                            <div style={scopeGroupTitleStyle}>Актуаторы для действий</div>
                            <div style={scopeCheckboxGridStyle}>
                              {selectedActuatorTypes.map((actuatorType) => (
                                <label key={actuatorType.label} style={scopeCheckboxLabelStyle}>
                                  <input
                                    type="checkbox"
                                    checked={actuatorType.ids.every((id) => activeRule.allowedActuatorKeys.includes(id))}
                                    onChange={(event) => {
                                      updateRule(activeRule.id, (rule) => {
                                        const nextKeys = event.target.checked
                                          ? [...rule.allowedActuatorKeys, ...actuatorType.ids]
                                          : rule.allowedActuatorKeys.filter(
                                              (key) => !actuatorType.ids.includes(key),
                                            );
                                        const uniqueKeys = Array.from(new Set(nextKeys));
                                        const filteredActuators = selectedActuators.filter((device) =>
                                          uniqueKeys.includes(device.id),
                                        );

                                        return {
                                          ...rule,
                                          allowedActuatorKeys: uniqueKeys,
                                          actuatorKeys: rule.actuatorKeys.filter((actuatorId) =>
                                            filteredActuators.some((device) => device.id === actuatorId),
                                          ),
                                        };
                                      });
                                    }}
                                  />
                                  {actuatorType.label}
                                </label>
                              ))}
                            </div>
                          </>
                        )}
                      </div>

                      {activeRule.conditions.map((condition, index) => (
                        <div key={condition.id} style={conditionRowStyle}>
                          {index > 0 && (
                            <select
                              value={condition.joinWithPrevious}
                              onChange={(event) =>
                                updateRule(activeRule.id, (rule) => ({
                                  ...rule,
                                  conditions: rule.conditions.map((item) =>
                                    item.id === condition.id
                                      ? { ...item, joinWithPrevious: event.target.value as RuleJoin }
                                      : item,
                                  ),
                                }))
                              }
                              style={smallSelectStyle}
                            >
                              <option value="AND">И</option>
                              <option value="OR">ИЛИ</option>
                            </select>
                          )}

                          <MultiSelectDropdown
                            options={availableSensorsForRule}
                            selectedIds={condition.sensorKeys}
                            placeholder="выберите датчики"
                            onChange={(selectedIds) =>
                              updateRule(activeRule.id, (rule) => ({
                                ...rule,
                                conditions: rule.conditions.map((item) =>
                                  item.id === condition.id ? { ...item, sensorKeys: selectedIds } : item,
                                ),
                              }))
                            }
                          />

                          <select
                            value={condition.operator}
                            onChange={(event) =>
                              updateRule(activeRule.id, (rule) => ({
                                ...rule,
                                conditions: rule.conditions.map((item) =>
                                  item.id === condition.id
                                    ? { ...item, operator: event.target.value as RuleOperator }
                                    : item,
                                ),
                              }))
                            }
                            style={smallSelectStyle}
                          >
                            <option value=">">{">"}</option>
                            <option value=">=">{">="}</option>
                            <option value="=">{"="}</option>
                            <option value="<=">{"<="}</option>
                            <option value="<">{"<"}</option>
                          </select>

                          <input
                            value={condition.value}
                            onChange={(event) =>
                              updateRule(activeRule.id, (rule) => ({
                                ...rule,
                                conditions: rule.conditions.map((item) =>
                                  item.id === condition.id ? { ...item, value: event.target.value } : item,
                                ),
                              }))
                            }
                            placeholder="значение"
                            style={valueInputStyle}
                          />

                          <button
                            type="button"
                            style={miniBtnStyle}
                            disabled={activeRule.conditions.length <= 1}
                            onClick={() =>
                              updateRule(activeRule.id, (rule) => ({
                                ...rule,
                                conditions: rule.conditions.filter((item) => item.id !== condition.id),
                              }))
                            }
                          >
                            -
                          </button>
                        </div>
                      ))}

                      <button
                        type="button"
                        style={miniBtnStyle}
                        onClick={() =>
                          updateRule(activeRule.id, (rule) => ({
                            ...rule,
                            conditions: [...rule.conditions, createDefaultCondition()],
                          }))
                        }
                      >
                        + добавить условие
                      </button>

                      <div style={sectionTitleStyle}>Тогда</div>

                      <div style={conditionRowStyle}>
                        <MultiSelectDropdown
                          options={availableActuatorsForRule}
                          selectedIds={activeRule.actuatorKeys}
                          placeholder="выберите актуаторы"
                          onChange={(selectedIds) =>
                            updateRule(activeRule.id, (rule) => ({ ...rule, actuatorKeys: selectedIds }))
                          }
                        />

                        <select
                          value={activeRule.command}
                          onChange={(event) =>
                            updateRule(activeRule.id, (rule) => ({
                              ...rule,
                              command: event.target.value as RuleCommand,
                            }))
                          }
                          style={smallSelectStyle}
                        >
                          <option value="on">включить</option>
                          <option value="off">выключить</option>
                        </select>
                      </div>
                    </>
                  )}
                </section>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function MultiSelectDropdown({
  options,
  selectedIds,
  onChange,
  placeholder,
}: {
  options: RuleDeviceOption[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  placeholder: string;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const selectedLabels = options
    .filter((option) => selectedIds.includes(option.id))
    .map((option) => option.label);

  const previewText =
    selectedLabels.length === 0
      ? placeholder
      : selectedLabels.length <= 2
        ? selectedLabels.join(", ")
        : `${selectedLabels.slice(0, 2).join(", ")} +${selectedLabels.length - 2}`;

  const toggleOption = (optionId: string) => {
    if (selectedIds.includes(optionId)) {
      onChange(selectedIds.filter((id) => id !== optionId));
      return;
    }
    onChange([...selectedIds, optionId]);
  };

  return (
    <div
      style={multiSelectWrapperStyle}
      tabIndex={0}
      onBlur={(event) => {
        const nextFocused = event.relatedTarget as Node | null;
        if (!nextFocused || !event.currentTarget.contains(nextFocused)) {
          setIsOpen(false);
        }
      }}
    >
      <button
        type="button"
        style={multiSelectControlButtonStyle}
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <span style={multiSelectPreviewStyle}>{previewText}</span>
        <span style={multiSelectChevronStyle}>{isOpen ? "^" : "v"}</span>
      </button>

      {isOpen && (
        <div style={multiSelectMenuStyle}>
          {options.length === 0 ? (
            <div style={multiSelectEmptyStyle}>нет устройств</div>
          ) : (
            options.map((option) => {
              const checked = selectedIds.includes(option.id);
              return (
                <button
                  key={option.id}
                  type="button"
                  style={{
                    ...multiSelectOptionStyle,
                    background: checked ? "rgba(116, 143, 114, 0.26)" : "transparent",
                  }}
                  onClick={() => toggleOption(option.id)}
                >
                  <input type="checkbox" checked={checked} readOnly />
                  <span>{option.label}</span>
                </button>
              );
            })
          )}
        </div>
      )}
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

const scriptsBtnStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  height: 22,
  padding: "0 8px",
  background: COLORS.teal,
  color: COLORS["light green text"],
  fontFamily: FONT,
  fontSize: 12,
  lineHeight: 1,
  cursor: "pointer",
  flexShrink: 0,
};

const deleteProjectBtnStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  width: 22,
  height: 22,
  background: COLORS["device red"],
  color: "#fff",
  fontFamily: FONT,
  fontSize: 16,
  lineHeight: 1,
  cursor: "pointer",
  flexShrink: 0,
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

const deviceDeleteButtonStyle: CSSProperties = {
  border: "2px solid #1D1D1D",
  width: 28,
  height: 28,
  borderRadius: "50%",
  display: "grid",
  placeItems: "center",
  flexShrink: 0,
  marginLeft: 6,
  background: COLORS["device red"],
  color: "#fff",
  fontFamily: FONT,
  fontSize: 20,
  lineHeight: 1,
  fontWeight: 700,
  cursor: "pointer",
  boxShadow: "0 6px 12px rgba(0, 0, 0, 0.35)",
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

const modalOverlayStyle: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0, 0, 0, 0.55)",
  display: "grid",
  placeItems: "center",
  zIndex: 80,
};

const modalStyle: CSSProperties = {
  width: "min(1080px, 95vw)",
  height: "min(700px, 90vh)",
  background: COLORS["panel"],
  border: `1px solid ${COLORS["green text"]}`,
  borderRadius: 16,
  boxShadow: "0 18px 50px rgba(0, 0, 0, 0.45)",
  display: "flex",
  flexDirection: "column",
  overflow: "hidden",
};

const modalHeaderStyle: CSSProperties = {
  height: 46,
  borderBottom: `1px solid ${COLORS["green text"]}`,
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: "0 14px",
  color: COLORS["light green text"],
  fontSize: 20,
};

const modalCloseBtnStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  height: 28,
  padding: "0 10px",
  background: COLORS.teal,
  color: COLORS["light green text"],
  fontFamily: FONT,
  fontSize: 14,
  cursor: "pointer",
};

const modalContentStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "260px 1fr",
  gap: 12,
  minHeight: 0,
  flex: 1,
  padding: 12,
};

const rulesListStyle: CSSProperties = {
  border: `1px solid ${COLORS["green text"]}`,
  borderRadius: 10,
  padding: 8,
  overflow: "auto",
  display: "flex",
  flexDirection: "column",
  gap: 8,
};

const newRuleBtnStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  height: 30,
  background: COLORS.teal,
  color: COLORS["light green text"],
  fontFamily: FONT,
  fontSize: 14,
  cursor: "pointer",
};

const ruleItemStyle: CSSProperties = {
  border: "1px solid transparent",
  borderRadius: 8,
  background: "rgba(116, 143, 114, 0.18)",
  color: COLORS["light green text"],
  padding: "6px 8px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  cursor: "pointer",
  textAlign: "left",
  fontFamily: FONT,
  fontSize: 14,
};

const editorStyle: CSSProperties = {
  border: `1px solid ${COLORS["green text"]}`,
  borderRadius: 10,
  padding: 12,
  overflow: "auto",
  display: "flex",
  flexDirection: "column",
  gap: 10,
};

const editorRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
};

const textInputStyle: CSSProperties = {
  height: 30,
  borderRadius: 8,
  border: `1px solid ${COLORS["green text"]}`,
  background: COLORS["solid back"],
  color: COLORS["light green text"],
  padding: "0 8px",
  minWidth: 240,
  fontFamily: FONT,
  fontSize: 14,
};

const toggleLabelStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 6,
  color: COLORS["light green text"],
  fontSize: 14,
};

const saveBtnStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  height: 30,
  padding: "0 10px",
  background: COLORS.teal,
  color: COLORS["light green text"],
  fontFamily: FONT,
  fontSize: 14,
  cursor: "pointer",
};

const dangerBtnStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  height: 30,
  padding: "0 10px",
  background: COLORS["device red"],
  color: COLORS["light green text"],
  fontFamily: FONT,
  fontSize: 14,
  cursor: "pointer",
};

const sectionTitleStyle: CSSProperties = {
  color: COLORS["light green text"],
  fontSize: 18,
};

const conditionRowStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap",
};

const selectStyle: CSSProperties = {
  height: 30,
  borderRadius: 8,
  border: `1px solid ${COLORS["green text"]}`,
  background: COLORS["solid back"],
  color: COLORS["light green text"],
  padding: "0 8px",
  minWidth: 220,
  fontFamily: FONT,
  fontSize: 14,
};

const multiSelectWrapperStyle: CSSProperties = {
  position: "relative",
  minWidth: 220,
};

const multiSelectControlButtonStyle: CSSProperties = {
  ...selectStyle,
  width: "100%",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  cursor: "pointer",
};

const multiSelectPreviewStyle: CSSProperties = {
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  textAlign: "left",
};

const multiSelectChevronStyle: CSSProperties = {
  marginLeft: 8,
  lineHeight: 1,
  flexShrink: 0,
};

const multiSelectMenuStyle: CSSProperties = {
  position: "absolute",
  top: "calc(100% + 4px)",
  left: 0,
  right: 0,
  borderRadius: 8,
  border: `1px solid ${COLORS["green text"]}`,
  background: COLORS["solid back"],
  maxHeight: 210,
  overflowY: "auto",
  zIndex: 15,
  boxShadow: "0 12px 26px rgba(0, 0, 0, 0.35)",
};

const multiSelectOptionStyle: CSSProperties = {
  border: "none",
  width: "100%",
  minHeight: 30,
  display: "flex",
  alignItems: "center",
  gap: 8,
  color: COLORS["light green text"],
  padding: "4px 8px",
  textAlign: "left",
  fontFamily: FONT,
  fontSize: 13,
  cursor: "pointer",
};

const multiSelectEmptyStyle: CSSProperties = {
  color: COLORS["green text"],
  padding: "8px",
  fontSize: 13,
};

const smallSelectStyle: CSSProperties = {
  ...selectStyle,
  minWidth: 92,
};

const valueInputStyle: CSSProperties = {
  ...textInputStyle,
  minWidth: 120,
};

const miniBtnStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  height: 28,
  padding: "0 8px",
  background: COLORS.teal,
  color: COLORS["light green text"],
  fontFamily: FONT,
  fontSize: 14,
  cursor: "pointer",
};

const emptyModalStateStyle: CSSProperties = {
  display: "grid",
  placeItems: "center",
  flex: 1,
  color: COLORS["green text"],
  fontSize: 18,
};

const scopePanelStyle: CSSProperties = {
  border: `1px solid ${COLORS["green text"]}`,
  borderRadius: 10,
  padding: 8,
  display: "grid",
  gap: 8,
};

const scopeHeaderStyle: CSSProperties = {
  color: COLORS["light green text"],
  fontSize: 14,
};

const scopeGroupTitleStyle: CSSProperties = {
  color: COLORS["green text"],
  fontSize: 13,
};

const scopeCheckboxGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
  gap: 6,
};

const scopeCheckboxLabelStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 6,
  color: COLORS["light green text"],
  fontSize: 13,
};
