(() => {
  const key = "macromate-theme";
  let choice = "system";
  let select;
  function apply(value) {
    choice = value === "light" || value === "dark" ? value : "system";
    if (choice === "system") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = choice;
    if (select) select.value = choice;
  }
  try { apply(localStorage.getItem(key)); } catch { apply("system"); }
  function initialize() {
    select = document.querySelector("#appearance");
    if (!select) return;
    select.value = choice;
    document.querySelector("#appearance-control").hidden = false;
    select.addEventListener("change", () => {
      apply(select.value);
      try {
        if (choice === "system") localStorage.removeItem(key);
        else localStorage.setItem(key, choice);
      } catch { /* Appearance still works for this document when storage is unavailable. */ }
    });
  }
  window.addEventListener("storage", (event) => {
    if (event.key === key || event.key === null) apply(event.newValue);
  });
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
