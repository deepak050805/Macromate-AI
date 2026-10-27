import { api, captureFocus, status } from "./common.js";
import { utcDateRange } from "./date-ranges.js";
import { validateProgressSummary } from "./responses.js";

const feedback = document.querySelector("#summary-status");
const refresh = document.querySelector("#refresh-summary");
const format = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });
const changeFormat = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 2, signDisplay: "exceptZero",
});

async function loadSummary() {
  if (refresh.disabled) return;
  const restoreFocus = captureFocus(refresh);
  refresh.disabled = true;
  status(feedback, "Loading your recent record summary…");
  try {
    const { date_from: start, date_to: end } = utcDateRange(30);
    const query = new URLSearchParams({ date_from: start, date_to: end });
    const data = await api(`/api/tracker/summary?${query}`);
    validateProgressSummary(data, { date_from: start, date_to: end });
    document.querySelector("#summary-range").textContent = `${start} through ${end} (UTC)`;
    document.querySelector("#summary-total").textContent = format.format(data.total);
    document.querySelector("#summary-weight").textContent = data.average_weight === null
      ? "No data" : `${format.format(data.average_weight)} kg`;
    document.querySelector("#summary-calories").textContent = data.average_calories === null
      ? "No data" : `${format.format(data.average_calories)} kcal`;
    document.querySelector("#summary-change").textContent = data.weight_change === null
      ? "Not enough data" : `${changeFormat.format(data.weight_change)} kg`;
    document.querySelector("#summary-values").hidden = false;
    status(feedback, data.total ? "Recent record summary updated."
      : "No dated entries in this period. Your older history remains available.");
  } catch (error) {
    status(feedback, error.message, true);
  } finally {
    refresh.disabled = false;
    restoreFocus();
  }
}
refresh.addEventListener("click", loadSummary);
loadSummary();
