"use client";

import { COLORS, DEVICE_COLORS, FONT } from "../../types/theme";
import { Greenhouse } from "../../types/dashboard";

type SidebarProps = {
  greenhouses: Greenhouse[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onToggleExpand: (id: number) => void;
  onAddGreenhouse: () => void;
  onAddDevice: (greenhouseId: number) => void;
};

export default function Sidebar({
  greenhouses,
  selectedId,
  onSelect,
  onToggleExpand,
  onAddGreenhouse,
  onAddDevice,
}: SidebarProps) {
  return (
    <div
      style={{
        width: 180,
        minWidth: 180,
        background: COLORS["sidebar"],
        borderRight: `1px solid #1E261E`,
        display: "flex",
        flexDirection: "column",
        fontFamily: FONT,
        overflowY: "auto",
      }}
    >
      {/* title */}
      <div
        style={{
          padding: "14px 16px 10px",
          color: COLORS["light green text"],
          fontSize: 18,
          letterSpacing: 1,
          borderBottom: `1px solid #1E261E`,
        }}
      >
        teplitsi
      </div>

      {/* greenhouse list */}
      <div style={{ flex: 1, padding: "8px 0" }}>
        {greenhouses.length === 0 ? (
          <div
            style={{
              padding: "8px 16px",
              color: COLORS["green text"],
              fontSize: 13,
            }}
          >
            no greenhouses yet
          </div>
        ) : (
          greenhouses.map((gh) => (
            <div key={gh.id}>
              {/* greenhouse row */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  padding: "6px 16px",
                  cursor: "pointer",
                  background: selectedId === gh.id ? "#243224" : "transparent",
                  gap: 6,
                }}
                onClick={() => onSelect(gh.id)}
              >
                <span
                  style={{
                    color: COLORS["green text"],
                    fontSize: 11,
                    display: "inline-block",
                    transition: "transform .15s",
                    transform: gh.expanded ? "rotate(90deg)" : "rotate(0deg)",
                    cursor: "pointer",
                    lineHeight: 1,
                    paddingRight: 2,
                  }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleExpand(gh.id);
                  }}
                >
                  ▶
                </span>
                <span
                  style={{
                    color: selectedId === gh.id ? COLORS["light green text"] : COLORS["green text"],
                    fontSize: 14,
                    flex: 1,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {gh.name}
                </span>
              </div>

              {/* devices */}
              {gh.expanded && (
                <div style={{ paddingLeft: 28, paddingBottom: 4 }}>
                  {gh.devices.map((device) => (
                    <div
                      key={device.id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        padding: "3px 8px 3px 0",
                      }}
                    >
                      <div
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: "50%",
                          background: DEVICE_COLORS[device.colorIndex % DEVICE_COLORS.length],
                          flexShrink: 0,
                        }}
                      />
                      <span
                        style={{
                          color: COLORS["green text"],
                          fontSize: 12,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {device.name}
                      </span>
                    </div>
                  ))}

                  {/* add device button */}
                  <button
                    onClick={() => onAddDevice(gh.id)}
                    style={{
                      background: COLORS["teal"],
                      border: "none",
                      borderRadius: 4,
                      padding: "3px 10px",
                      color: "#fff",
                      fontFamily: FONT,
                      fontSize: 12,
                      cursor: "pointer",
                      marginTop: 4,
                      marginBottom: 2,
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.opacity = ".8")}
                    onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
                  >
                    + add
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* add greenhouse button */}
      <div style={{ padding: "10px 16px", borderTop: `1px solid #1E261E` }}>
        <button
          onClick={onAddGreenhouse}
          style={{
            background: COLORS["teal"],
            border: "none",
            borderRadius: 6,
            padding: "7px 0",
            color: "#fff",
            fontFamily: FONT,
            fontSize: 14,
            cursor: "pointer",
            width: "100%",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.opacity = ".8")}
          onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
        >
          + create
        </button>
      </div>
    </div>
  );
}
