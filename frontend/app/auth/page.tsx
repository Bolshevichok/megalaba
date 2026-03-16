"use client";

import { useState } from "react";
import { COLORS, FONT } from "../../types/theme";

type Mode = "login" | "register";

export default function AuthPage() {
  const [mode, setMode] = useState<Mode>("login");
  const isLogin = mode === "login";

  return (
    <div
      style={{
        minHeight: "100vh",
        background: COLORS["solid back"],
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: FONT,
        position: "relative",
        padding: "24px 12px",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 14,
          left: 16,
          color: COLORS["green text"],
          fontSize: 24,
          opacity: 0.8,
        }}
      >
        {mode}
      </div>

      <div
        style={{
          background: COLORS["panel"],
          borderRadius: 15,
          boxShadow: "13px 13px 4px rgba(0, 0, 0, 0.25)",
          padding: "52px 30px 58px",
          width: "min(453px, calc(100vw - 24px))",
          display: "flex",
          flexDirection: "column",
          gap: 26,
        }}
      >
        <div style={{ display: "flex", gap: 8, alignItems: "baseline", justifyContent: "center" }}>
          <TabButton label="Login" active={isLogin} onClick={() => setMode("login")} />
          <span style={{ color: COLORS["green text"], fontSize: 48, lineHeight: 1 }}>/</span>
          <TabButton label="Registration" active={!isLogin} onClick={() => setMode("register")} />
        </div>

        <form
          style={{ display: "flex", flexDirection: "column", gap: 12 }}
          onSubmit={(e) => e.preventDefault()}
        >
          <AuthInput placeholder="username" type="text" />
          <AuthInput placeholder="password" type="password" />
          {!isLogin && (
            <AuthInput placeholder="repeat password" type="password" />
          )}

          <div style={{ height: 22 }} />

          <button
            type="submit"
            style={{
              background: COLORS["teal"],
              border: "none",
              borderRadius: 15,
              padding: "5px 0",
              color: COLORS["light green text"],
              fontFamily: FONT,
              fontSize: 24,
              cursor: "pointer",
              lineHeight: 1.2,
              transition: "filter 0.2s ease",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.filter = "brightness(1.15)")}
            onMouseLeave={(e) => (e.currentTarget.style.filter = "none")}
          >
            {isLogin ? "login" : "create user"}
          </button>
        </form>
      </div>
    </div>
  );
}

function TabButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        background: "none",
        border: "none",
        cursor: "pointer",
        fontFamily: FONT,
        fontSize: 48,
        lineHeight: 1,
        color: active ? COLORS["light green text"] : COLORS["green text"],
        padding: 0,
      }}
    >
      {label}
    </button>
  );
}

function AuthInput({ placeholder, type }: { placeholder: string; type: string }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span
        style={{
          color: COLORS["light green text"],
          textAlign: "center",
          fontSize: 24,
          lineHeight: 1,
        }}
      >
        {placeholder}
      </span>
      <input
        type={type}
        style={{
          background: COLORS["solid back"],
          border: "none",
          borderRadius: 15,
          padding: "7px 12px",
          color: COLORS["light green text"],
          fontFamily: FONT,
          fontSize: 20,
          lineHeight: 1,
          outline: "none",
          width: "100%",
        }}
      />
    </label>
  );
}
