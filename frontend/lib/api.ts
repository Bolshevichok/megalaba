// Base URL for the API
export const API_URL = "http://localhost:8000/api/v1";

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_URL}${url}`, { ...options, headers });

  if (!response.ok) {
    let errText = response.statusText;
    try {
        const errorData = await response.json();
        if (errorData && errorData.detail) errText = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
    } catch (e) {}
    throw new Error(`API error ${response.status}: ${errText}`);
  }

  if (response.status === 204) {
    return null;
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
  return fetchWithAuth(`/greenhouses/${id}`, {
    method: "PUT",
    body: JSON.stringify({ canvas_state: canvasState }),
  });
}

export async function deleteGreenhouse(id: number) {
  return fetchWithAuth(`/greenhouses/${id}`, {
    method: "DELETE",
  });
}

// =======================
// Devices
// =======================
export async function getGreenhouseDevices(greenhouseId: number) {
  return fetchWithAuth(`/greenhouses/${greenhouseId}/devices`);
}

export async function getUnassignedDevices() {
  return fetchWithAuth("/devices/unassigned");
}

export async function assignDevice(deviceId: number, greenhouseId: number | null) {
  const qs = greenhouseId !== null ? `?greenhouse_id=${greenhouseId}` : "";
  return fetchWithAuth(`/devices/${deviceId}/assign${qs}`, {
    method: "PATCH",
  });
}

// =======================
// Scripts
// =======================
export async function getScripts(greenhouseId: number) {
  return fetchWithAuth(`/greenhouses/${greenhouseId}/scripts`);
}

export async function saveScript(greenhouseId: number, data: { name: string; script_code: string; enabled: boolean }) {
  return fetchWithAuth(`/greenhouses/${greenhouseId}/scripts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// =======================
// Sensor Readings
// =======================
export async function getSensorReadings(sensorId: number, limit = 1) {
  return fetchWithAuth(`/sensors/${sensorId}/readings?limit=${limit}`);
}

// =======================
// Dashboard
// =======================
export async function getDashboardOverview() {
  return fetchWithAuth("/dashboard/overview");
}

// =======================
// Auth
// =======================
export async function login(data: { email: string; password: string }) {
  const response = await fetch(`${API_URL}/auth/login`, {
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
    throw new Error(`API error ${response.status}: ${errText}`);
  }
  return response.json();
}

export async function registerUser(data: { name: string; email: string; password: string }) {
  const response = await fetch(`${API_URL}/auth/register`, {
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
    throw new Error(`API error ${response.status}: ${errText}`);
  }
  return response.json();
}
