import re

def update_page_tsx():
    with open("app/page.tsx", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Imports
    content = content.replace(
        'import { useEffect, useMemo, useRef, useState } from "react";\nimport { COLORS, FONT } from "../types/theme";',
        'import { useEffect, useMemo, useRef, useState, useCallback } from "react";\nimport { COLORS, FONT } from "../types/theme";\nimport { \n  getGreenhouses, \n  createGreenhouse as apiCreateGreenhouse,\n  updateGreenhouseCanvas,\n  getUnassignedDevices,\n  assignDevice,\n  saveScript\n} from "../lib/api";'
    )

    # 2. DeviceTemplate Add sourceId
    content = content.replace(
        'type DeviceTemplate = {\n  key: string;\n  label: string;\n  color: string;\n  type: DeviceType;\n};',
        'type DeviceTemplate = {\n  key: string;\n  label: string;\n  color: string;\n  type: DeviceType;\n  sourceId?: number;\n};'
    )
    
    # 3. PlacedDevice Add sourceId
    content = content.replace(
        'type PlacedDevice = {\n  id: string;\n  label: string;\n  color: string;\n  type: DeviceType;\n  order: number;\n  x: number;\n  y: number;\n  currentReading?: string | number;\n};',
        'type PlacedDevice = {\n  id: string;\n  label: string;\n  color: string;\n  type: DeviceType;\n  order: number;\n  x: number;\n  y: number;\n  currentReading?: string | number;\n  sourceId?: number;\n};'
    )

    # 4. Remove KNOWN_DEVICES completely
    known_devices_regex = r'const KNOWN_DEVICES:.*?\];'
    content = re.sub(known_devices_regex, '', content, flags=re.DOTALL)

    # 5. Add availableDevices and replace initialization
    content = content.replace(
        'const [projects, setProjects] = useState<Project[]>([]);\n  const [selectedId, setSelectedId] = useState<string | null>(null);',
        'const [projects, setProjects] = useState<Project[]>([]);\n  const [availableDevices, setAvailableDevices] = useState<DeviceTemplate[]>([]);\n  const [selectedId, setSelectedId] = useState<string | null>(null);'
    )

    # 6. Add loadData and useEffect
    load_data_code = """
  const loadData = useCallback(async () => {
    try {
      const [fetchedGreenhouses, unassigned] = await Promise.all([
        getGreenhouses(),
        getUnassignedDevices(),
      ]);

      setProjects(
        fetchedGreenhouses.map((gh: any) => {
          let placed: PlacedDevice[] = [];
          if (gh.canvas_state) {
            try {
              placed = JSON.parse(gh.canvas_state);
            } catch (e) {
              console.error("Failed to parse canvas_state", e);
            }
          }
          return {
            id: String(gh.id),
            name: gh.name,
            expanded: true,
            devices: [],
            placed,
          };
        }),
      );

      setAvailableDevices(
        unassigned.map((d: any) => {
          let type: DeviceType = "sensors";
          let color: string = COLORS["device teal"];
          if (d.device_type?.includes("actuator")) {
             type = "actuators"; color = COLORS["device orange"];
          } else if (d.device_type?.includes("light")) {
             type = "actuators"; color = COLORS["device red"];
          }
          else if (d.device_type?.includes("automation")) {
             type = "automation"; color = COLORS["device olive"];
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
    } catch (e) {
      console.error("Failed to load data", e);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);
"""
    content = content.replace(
        'const [draggingDeviceId, setDraggingDeviceId] = useState<string | null>(null);\n\n  const selected = useMemo(',
        'const [draggingDeviceId, setDraggingDeviceId] = useState<string | null>(null);\n' + load_data_code + '\n  const selected = useMemo('
    )

    # 7. update save rule
    save_rule_func = """
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
"""
    content = content.replace(
        '  const createProject = () => {',
        save_rule_func + '\n  const createProject = async () => {\n'
    )
    
    # modify createProject logic
    old_cp = """const typedName = window.prompt("project name", `teplitsa ${projects.length + 1}`);
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
  };"""
    new_cp = """const typedName = window.prompt("project name", `teplitsa ${projects.length + 1}`);
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
  };"""
    content = content.replace(old_cp, new_cp)

    # Place Device
    old_pd = """  const placeDevice = (x: number, y: number) => {
    if (!selected || !pending) {
      return;
    }

    const placed: PlacedDevice = {
      id: `placed-${Date.now()}`,
      label: pending.label,
      color: pending.color,
      type: pending.type,
      order: selected.placed.length + 1,
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
  };"""
    new_pd = """  const persistCanvasState = async (projectId: string, newPlaced: PlacedDevice[]) => {
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
      
      setProjects((prev) =>
        prev.map((project) =>
          project.id === selected.id ? { ...project, placed: newPlaced } : project,
        ),
      );
      
      setAvailableDevices((prev) => prev.filter((d) => d.sourceId !== pending.sourceId));
      
      setActivePlacedId(placed.id);
      setPending(null);

      await persistCanvasState(selected.id, newPlaced);
    } catch (e) {
      console.error("Failed to assign and place device", e);
      alert("Failed to place device on server");
    }
  };"""
  
    content = content.replace(old_pd, new_pd)
    
    # Remove placed device
    old_rpd = """  const removePlacedDevice = (projectId: string, placedId: string) => {
    setProjects((prev) =>
      prev.map((project) =>
        project.id === projectId
          ? { ...project, placed: project.placed.filter((device) => device.id !== placedId) }
          : project,
      ),
    );
    setActivePlacedId(null);
  };"""
    new_rpd = """  const removePlacedDevice = async (projectId: string, placedId: string) => {
    const project = projects.find((p) => p.id === projectId);
    if (!project) return;
    const deviceToRemove = project.placed.find((d) => d.id === placedId);
    if (!deviceToRemove || !deviceToRemove.sourceId) return;

    const newPlaced = project.placed.filter((device) => device.id !== placedId);

    try {
      await assignDevice(deviceToRemove.sourceId, null);

      setProjects((prev) =>
        prev.map((p) =>
          p.id === projectId ? { ...p, placed: newPlaced } : p,
        ),
      );
      setActivePlacedId(null);
      
      loadData();
      await persistCanvasState(projectId, newPlaced);
    } catch (e) {
      console.error("Failed to remove placed device", e);
      alert("Failed to remove placed device");
    }
  };"""
    content = content.replace(old_rpd, new_rpd)

    old_pu = """  const handleCanvasPointerUp = () => {
    if (!draggingRef.current) {
      return;
    }

    draggingRef.current = null;
    dragMovedRef.current = false;
    setDraggingDeviceId(null);

    window.setTimeout(() => {
      skipPlacementClickRef.current = false;
    }, 0);
  };"""

    new_pu = """  const handleCanvasPointerUp = () => {
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
  };"""
    content = content.replace(old_pu, new_pu)

    # UI updates: 
    # Use availableDevices in the sidebar
    old_sidebar_map = "const typedDevices = project.devices.filter((device) => device.type === type);"
    new_sidebar_map = "const typedDevices = availableDevices.filter((device) => device.type === type);"
    content = content.replace(old_sidebar_map, new_sidebar_map)

    # Sidebar unassigned string
    old_title = "{DEVICE_TYPE_TITLES[type]} ({typedDevices.length})"
    new_title = "unassigned {DEVICE_TYPE_TITLES[type]} ({typedDevices.length})"
    # Actually just replace the first exact match inside the mapped block
    content = re.sub(
        r'\{DEVICE_TYPE_TITLES\[type\]\} \(\{typedDevices\.length\}\)',
        r'unassigned {DEVICE_TYPE_TITLES[type]} ({typedDevices.length})', 
        content, 
        count=1
    )

    # Add save button UI and it's style
    old_editor_row = """                          <label style={toggleLabelStyle}>
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
                        </div>"""
    new_editor_row = """                          <label style={toggleLabelStyle}>
                            <input
                              type="checkbox"
                              checked={activeRule.enabled}
                              onChange={(event) =>
                                updateRule(activeRule.id, (rule) => ({ ...rule, enabled: event.target.checked }))
                              }
                            />
                            enabled
                          </label>
                          <button type="button" style={saveBtnStyle} onClick={() => saveRuleToServer(activeRule)}>
                            сохранить
                          </button>
                          <button type="button" style={dangerBtnStyle} onClick={() => deleteRule(activeRule.id)}>
                            удалить
                          </button>
                        </div>"""
    content = content.replace(old_editor_row, new_editor_row)

    # Add saveBtnStyle
    old_styles = """const dangerBtnStyle: CSSProperties = {
  border: "none",
  borderRadius: 8,
  height: 30,
  padding: "0 10px","""
    new_styles = """const saveBtnStyle: CSSProperties = {
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
  padding: "0 10px","""
    content = content.replace(old_styles, new_styles)

    with open("app/page.tsx", "w", encoding="utf-8") as f:
        f.write(content)

update_page_tsx()
