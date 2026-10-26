import { api, busy, captureFocus, status } from "./common.js";
const feedback = document.querySelector("#admin-status");
const retryDirectory = document.querySelector("#retry-users");
const previous = document.querySelector("#admin-previous");
const next = document.querySelector("#admin-next");
const filters = document.querySelector("#account-filters");
const emailSearch = document.querySelector("#account-search");
const verification = document.querySelector("#account-verification");
let activeFilters = { q: "", verification: "all" };
let page = 1;
let pages = 0;
let directoryRevision = 0;
async function load(requestedPage = page, requestRevision = ++directoryRevision) {
  const restoreRetry = captureFocus(retryDirectory);
  retryDirectory.hidden = true;
  retryDirectory.disabled = true;
  const restorePrevious = captureFocus(previous);
  const restoreNext = captureFocus(next);
  previous.disabled = true;
  next.disabled = true;
  status(feedback, "Loading accounts…");
  try {
    const query = new URLSearchParams({ page: requestedPage });
    if (activeFilters.q) query.set("q", activeFilters.q);
    if (activeFilters.verification !== "all") query.set("verification", activeFilters.verification);
    const data = await api(`/api/auth/all-users?${query}`);
    if (requestRevision !== directoryRevision) return;
    if (!data.users.length && requestedPage > 1) {
      const fallbackPage = Math.min(requestedPage - 1, Math.max(1, data.pages));
      return await load(fallbackPage, requestRevision);
    }
    page = data.page;
    pages = data.pages;
    const rows = data.users.map((user) => {
      const row = document.createElement("tr");
      for (const value of [
        user.id,
        user.email,
        user.verified ? "Verified" : "Pending verification",
      ]) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      }
      return row;
    });
    document.querySelector("#users-rows").replaceChildren(...rows);
    document.querySelector("#admin-pagination").hidden = pages <= 1;
    document.querySelector("#admin-page").textContent = `Page ${data.page} of ${data.pages}`;
    status(
      feedback,
      data.total
        ? `${data.total} registered accounts. Showing ${data.users.length} on this page.`
        : activeFilters.q || activeFilters.verification !== "all"
          ? "No accounts match these filters." : "No accounts registered yet.",
    );
  } catch (error) {
    if (requestRevision === directoryRevision) {
      status(feedback, error.message, true);
      retryDirectory.hidden = false;
    }
  } finally {
    if (requestRevision === directoryRevision) {
    retryDirectory.disabled = false;
    previous.disabled = page <= 1;
    next.disabled = page >= pages;
    const fallback = [previous, next, document.querySelector("#users-title")].find(
      (control) => control && !control.disabled,
    );
    restorePrevious(previous.disabled ? fallback : previous);
    restoreNext(next.disabled ? fallback : next);
    restoreRetry(retryDirectory.hidden ? document.querySelector("#users-title") : retryDirectory);
    }
  }
}
retryDirectory.addEventListener("click", () => load());
filters.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!busy(filters, true)) return;
  activeFilters = { q: emailSearch.value.trim(), verification: verification.value };
  try {
    await load(1);
  } finally {
    busy(filters, false);
  }
});
document.querySelector("#clear-account-filters").addEventListener("click", () => {
  filters.reset();
  activeFilters = { q: "", verification: "all" };
  load(1);
});
previous.addEventListener("click", () => {
  if (page > 1) {
    load(page - 1);
  }
});
next.addEventListener("click", () => {
  if (page < pages) {
    load(page + 1);
  }
});
load();
