import { api, busy, status } from "./common.js";
const form = document.querySelector("#calculator-form");
const feedback = document.querySelector("#calculator-status");
const format = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });
const goals = {
  maintain: "Maintenance estimate",
  fat_loss: "10% below estimated maintenance",
  gain: "10% above estimated maintenance",
};
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  busy(form, true);
  status(feedback, "Calculating…");
  const values = Object.fromEntries(new FormData(form));
  try {
    const result = await api("/api/macros/calculate", { method: "POST", body: values });
    for (const key of ["calories", "protein", "carbs", "fats"])
      document.querySelector(`#result-${key}`).textContent = format.format(result[key]);
    document.querySelector("#result-goal").textContent = goals[values.goal];
    document.querySelector("#result-placeholder").hidden = true;
    document.querySelector("#calculator-results").hidden = false;
    status(feedback, `Targets updated: ${format.format(result.calories)} kcal per day.`);
  } catch (error) {
    document.querySelector("#calculator-results").hidden = true;
    document.querySelector("#result-placeholder").hidden = false;
    status(feedback, error.message, true);
  } finally {
    busy(form, false);
  }
});
