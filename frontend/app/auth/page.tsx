"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { COLORS, FONT } from "../../types/theme";
import { login, registerUser } from "../../lib/api";

type Mode = "login" | "register";

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [repeatPassword, setRepeatPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isLogin = mode === "login";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!isLogin && password !== repeatPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      if (isLogin) {
        const response = await login({ email, password });
        if (response.access_token) {
          localStorage.setItem("token", response.access_token);
          router.push("/");
        }
      } else {
        const response = await registerUser({ name, email, password });
        if (response.id) {
          // Immediately login after register
          const loginResponse = await login({ email, password });
          if (loginResponse.access_token) {
            localStorage.setItem("token", loginResponse.access_token);
            router.push("/");
          }
        }
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

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
          <TabButton label="Login" active={isLogin} onClick={() => { setMode("login"); setError(""); }} />
          <span style={{ color: COLORS["green text"], fontSize: 48, lineHeight: 1 }}>/</span>
          <TabButton label="Registration" active={!isLogin} onClick={() => { setMode("register"); setError(""); }} />
        </div>

        {error && (
            <div style={{ color: "red", textAlign: "center", fontSize: 16 }}>{error}</div>
        )}

        <form
          style={{ display: "flex", flexDirection: "column", gap: 12 }}
          onSubmit={handleSubmit}
        >
          {!isLogin && (
            <AuthInput placeholder="name" type="text" value={name} onChange={setName} />
          )}
          <AuthInput placeholder="email" type="email" value={email} onChange={setEmail} />
          <AuthInput placeholder="password" type="password" value={password} onChange={setPassword} />
          {!isLogin && (
            <AuthInput placeholder="repeat password" type="password" value={repeatPassword} onChange={setRepeatPassword} />
          )}

          <div style={{ height: 22 }} />

          <button
            type="submit"
            disabled={loading}
            style={{
              background: COLORS["teal"],
              border: "none",
              borderRadius: 15,
              padding: "5px 0",
              color: COLORS["light green text"],
              fontFamily: FONT,
              fontSize: 24,
              cursor: loading ? "not-allowed" : "pointer",
              lineHeight: 1.2,
              transition: "filter 0.2s ease",
              opacity: loading ? 0.7 : 1,
            }}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.filter = "brightness(1.15)"; }}
            onMouseLeave={(e) => { if (!loading) e.currentTarget.style.filter = "none"; }}
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
      type="button"
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

function AuthInput({ placeholder, type, value, onChange }: { placeholder: string; type: string; value: string; onChange: (v: string) => void }) {
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
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
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
