import { api, captureFocus, status } from "./common.js";
import { validateProgressPage } from "./responses.js";
const feedback = document.querySelector("#dashboard-status");
const retry = document.querySelector("#retry-dashboard");
async function loadDashboard() {
  const restoreFocus = captureFocus(retry);
  retry.hidden = true;
  retry.disabled = true;
  status(feedback, "Loading your history…");
try {
  const data = await api("/api/tracker/history");
  validateProgressPage(data, 1);
  if (!data.records.length) {
    status(feedback, "No entries yet. Your first record will appear here.");
  } else {
    const latest = data.records[0];
    document.querySelector("#latest-date").textContent = latest.date || "Date unavailable";
    document.querySelector("#latest-weight").textContent = `${latest.weight} kg`;
    document.querySelector("#latest-calories").textContent = `${latest.calories} kcal`;
    document.querySelector("#latest-entry").hidden = false;
    status(feedback, `${data.total} ${data.total === 1 ? "entry" : "entries"} recorded.`);
  }
} catch (error) {
  status(feedback, error.message, true);
  retry.hidden = false;
} finally {
  retry.disabled = false;
  restoreFocus(retry.hidden ? document.querySelector("#latest-title") : retry);
}
}
retry.addEventListener("click", loadDashboard);
loadDashboard();
