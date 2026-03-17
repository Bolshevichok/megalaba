content = '''// Base URL for the API
export const API_URL = "http://localhost:8000/api/v1";

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: Bearer \ } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(\\, { ...options, headers });

  if (!response.ok) {
    let errText = response.statusText;
    try {
        const errorData = await response.json();
        if (errorData && errorData.detail) errText = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
    } catch (e) {}
    throw new Error(API error: \ \);
  }

  return response.json();
}

// =======================
// Greenhouses
// =======================
export async function getGreenhouses() {
  return fetchWithAuth("/greenhouses");
}

export async function createGreenhouse(data: { name: string; canvas_state?: string }) {
  return fetchWithAuth("/greenhouses", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateGreenhouseCanvas(id: number, canvasState: string) {
  return fetchWithAuth(/greenhouses/\, {
    method: "PUT",
    body: JSON.stringify({ canvas_state: canvasState }),
  });
}

// =======================
// Devices
// =======================
export async function getGreenhouseDevices(greenhouseId: number) {
  return fetchWithAuth(/greenhouses/\/devices);
}

export async function getUnassignedDevices() {
  return fetchWithAuth("/devices/unassigned");
}

export async function assignDevice(deviceId: number, greenhouseId: number | null) {
  return fetchWithAuth(/devices/\/assign?greenhouse_id=\, {
    method: "PATCH",
  });
}

// =======================
// Scripts
// =======================
export async function getScripts(greenhouseId: number) {
  return fetchWithAuth(/greenhouses/\/scripts);
}

export async function saveScript(greenhouseId: number, data: { name: string; script_code: string; enabled: boolean }) {
  return fetchWithAuth(/greenhouses/\/scripts, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// =======================
// Auth
// =======================
export async function login(data: { email: string; password: string }) {
  const response = await fetch(\/auth/login, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    let errText = response.statusText;
    try {
        const errorData = await response.json();
        if (errorData && errorData.detail) errText = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
    } catch (e) {}
    throw new Error(API error: \ \);
  }
  return response.json();
}

export async function registerUser(data: { name: string; email: string; password: string }) {
  const response = await fetch(\/auth/register, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    let errText = response.statusText;
    try {
        const errorData = await response.json();
        if (errorData && errorData.detail) errText = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
    } catch (e) {}
    throw new Error(API error: \ \);
  }
  return response.json();
}
'''
with open('frontend/lib/api.ts', 'w', encoding='utf-8') as f:
    f.write(content)
