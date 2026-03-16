"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "../../components/dashboard/Sidebar";
import Canvas from "../../components/dashboard/Canvas";
import { COLORS, FONT } from "../../types/theme";
import { Greenhouse, Device } from "../../types/dashboard";

let nextGhId = 3;
let nextDevId = 5;

const INITIAL: Greenhouse[] = [
  {
    id: 1,
    name: "pervaya teplitsa",
    expanded: true,
    devices: [
      { id: 1, name: "termometr 1", colorIndex: 0, x: 28, y: 30 },
      { id: 2, name: "termometr 2", colorIndex: 1, x: 58, y: 62 },
    ],
  },
  {
    id: 2,
    name: "vtoraya teplitsa",
    expanded: false,
    devices: [],
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const [greenhouses, setGreenhouses] = useState<Greenhouse[]>(INITIAL);
  const [selectedId, setSelectedId] = useState<number | null>(1);

  const selected = greenhouses.find((g) => g.id === selectedId) ?? null;

  /* ── sidebar actions ── */
  const handleSelect = (id: number) => setSelectedId(id);

  const handleToggleExpand = (id: number) =>
    setGreenhouses((prev) =>
      prev.map((g) => (g.id === id ? { ...g, expanded: !g.expanded } : g))
    );

  const handleAddGreenhouse = () => {
    const name = `teplitsa ${nextGhId}`;
    const newGh: Greenhouse = {
      id: nextGhId++,
      name,
      expanded: true,
      devices: [],
    };
    setGreenhouses((prev) => [...prev, newGh]);
    setSelectedId(newGh.id);
  };

  const handleAddDevice = (greenhouseId: number) => {
    setGreenhouses((prev) =>
      prev.map((g) => {
        if (g.id !== greenhouseId) return g;
        const idx = g.devices.length;
        const newDevice: Device = {
          id: nextDevId++,
          name: `sensor ${nextDevId - 1}`,
          colorIndex: idx % 4,
          x: 20 + idx * 15,
          y: 35 + (idx % 3) * 18,
        };
        return { ...g, devices: [...g.devices, newDevice] };
      })
    );
  };

  /* ── canvas actions ── */
  const handleMoveDevice = useCallback(
    (id: number, x: number, y: number) => {
      if (selectedId === null) return;
      setGreenhouses((prev) =>
        prev.map((g) =>
          g.id === selectedId
            ? {
                ...g,
                devices: g.devices.map((d) =>
                  d.id === id ? { ...d, x, y } : d
                ),
              }
            : g
        )
      );
    },
    [selectedId]
  );

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: COLORS["solid back"],
        fontFamily: FONT,
      }}
    >
      {/* ── top bar ── */}
      <header
        style={{
          height: 44,
          background: COLORS["little dark green"],
          borderBottom: `1px solid #1E261E`,
          display: "flex",
          alignItems: "center",
          padding: "0 20px",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            color: COLORS["light green text"],
            fontSize: 20,
            letterSpacing: 2,
            flex: 1,
          }}
        >
          megalaba
        </span>
        <button
          onClick={() => router.push("/auth")}
          style={{
            background: COLORS["teal"],
            border: "none",
            borderRadius: 6,
            padding: "4px 16px",
            color: "#fff",
            fontFamily: FONT,
            fontSize: 14,
            cursor: "pointer",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = ".8")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          exit
        </button>
      </header>

      {/* ── body: sidebar + canvas ── */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        <Sidebar
          greenhouses={greenhouses}
          selectedId={selectedId}
          onSelect={handleSelect}
          onToggleExpand={handleToggleExpand}
          onAddGreenhouse={handleAddGreenhouse}
          onAddDevice={handleAddDevice}
        />

        <Canvas
          devices={selected?.devices ?? []}
          hasGreenhouse={selected !== null}
          selectedName={selected?.name ?? ""}
          onMoveDevice={handleMoveDevice}
          onCreateGreenhouse={handleAddGreenhouse}
        />
      </div>
    </div>
  );
}
