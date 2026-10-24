import { api, status } from "./common.js";
const feedback = document.querySelector("#dashboard-status");
try {
  const data = await api("/api/tracker/history");
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
}
