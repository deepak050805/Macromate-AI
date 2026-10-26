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
      method,
      headers,
      credentials: "same-origin",
      signal: controller.signal,
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    let data;
    try {
      data = await response.json();
    } catch (error) {
      if (error instanceof SyntaxError)
        throw new Error("The server returned an unreadable response. Try again.", { cause: error });
      throw error;
    }
    if (data === null || typeof data !== "object" || Array.isArray(data))
      throw new Error("The server returned an unreadable response. Try again.");
    if (!response.ok)
      throw new Error(
        typeof data.message === "string" && data.message
          ? data.message
          : "The request could not be completed.",
      );
    return data;
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error("The request timed out. Try again.", { cause: error });
    if (error instanceof TypeError)
      throw new Error("Connection failed. Check your connection and try again.", { cause: error });
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function status(element, message, isError = false) {
  element.textContent = message;
  element.className = `status ${isError ? "error" : "success"}`;
}

export function captureFocus(control) {
  const wasFocused = document.activeElement === control;
  return (target = control) => {
    if (
      wasFocused &&
      target?.isConnected &&
      !target.disabled &&
      document.activeElement === document.body
    )
      target.focus();
  };
}

const pendingForms = new WeakMap();
export function busy(form, active) {
  form.setAttribute("aria-busy", String(active));
  if (active) {
    if (pendingForms.has(form)) return;
    const controls = [...form.querySelectorAll('button[type="submit"]')].map((button) => ({
      button,
      disabled: button.disabled,
      restoreFocus: captureFocus(button),
    }));
    pendingForms.set(form, controls);
    for (const { button } of controls) button.disabled = true;
  } else {
    const controls = pendingForms.get(form) || [];
    pendingForms.delete(form);
    for (const { button, disabled, restoreFocus } of controls) {
      button.disabled = disabled;
      restoreFocus();
    }
  }
}

const logout = document.querySelector("#logout");
if (logout)
  logout.addEventListener("click", async () => {
    const restoreFocus = captureFocus(logout);
    logout.disabled = true;
    try {
      await api("/api/auth/logout", { method: "POST", body: {} });
      try {
        sessionStorage.removeItem("pending-email");
      } catch {
        /* Storage restrictions must not prevent server-side logout. */
      }
      window.location.assign("/login");
    } catch (error) {
      status(document.querySelector("#global-status"), error.message, true);
      logout.disabled = false;
      restoreFocus();
    }
  });
