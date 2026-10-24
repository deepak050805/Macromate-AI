export async function api(path, { method = "GET", body } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const headers = { Accept: "application/json" };
    if (method !== "GET") {
      headers["Content-Type"] = "application/json";
      headers["X-CSRFToken"] = document.querySelector('meta[name="csrf-token"]').content;
    }
    const response = await fetch(path, {
      method, headers, credentials: "same-origin", signal: controller.signal,
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "The request could not be completed.");
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("The request timed out. Try again.");
    if (error instanceof TypeError) throw new Error("Connection failed. Check your connection and try again.");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function status(element, message, isError = false) {
  element.textContent = message;
  element.className = `status ${isError ? "error" : "success"}`;
}

export function busy(form, active) {
  form.setAttribute("aria-busy", String(active));
  for (const button of form.querySelectorAll('button[type="submit"]')) button.disabled = active;
}

const logout = document.querySelector("#logout");
if (logout) logout.addEventListener("click", async () => {
  logout.disabled = true;
  try {
    await api("/api/auth/logout", { method: "POST", body: {} });
    window.location.assign("/login");
  } catch (error) {
    status(document.querySelector("#global-status"), error.message, true);
    logout.disabled = false;
  }
});
