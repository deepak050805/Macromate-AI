import { api, busy, captureFocus, status } from "./common.js";
const form = document.querySelector("#tracking-form");
const feedback = document.querySelector("#entry-status");
const historyStatus = document.querySelector("#history-status");
const retryHistory = document.querySelector("#retry-history");
const dateInput = document.querySelector("#record-date");
const recordId = document.querySelector("#record-id");
const cancel = document.querySelector("#cancel-edit");
const previous = document.querySelector("#previous-page");
const next = document.querySelector("#next-page");
const todayUtc = () => new Date().toISOString().slice(0, 10);
let page = 1;
let lastPage = 0;
let historyRevision = 0;
dateInput.value = todayUtc();
function refreshDateLimit() {
  dateInput.max = todayUtc();
}
refreshDateLimit();
dateInput.addEventListener("focus", refreshDateLimit);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") refreshDateLimit();
});

function resetForm() {
  form.reset();
  recordId.value = "";
  dateInput.value = todayUtc();
  refreshDateLimit();
  document.querySelector("#entry-title").textContent = "Add a progress entry";
  document.querySelector("#save-entry").textContent = "Save entry";
  cancel.hidden = true;
}
cancel.addEventListener("click", () => {
  resetForm();
  form.elements.weight.focus();
});

function cell(row, value) {
  const td = document.createElement("td");
  td.textContent = value;
  row.append(td);
  return td;
}

function rowFor(record) {
  const row = document.createElement("tr");
  cell(row, record.date || "Date unavailable");
  cell(row, record.weight);
  cell(row, record.calories);
  const actions = cell(row, "");
  const edit = document.createElement("button");
  edit.type = "button";
  edit.className = "secondary";
  edit.textContent = "Edit";
  edit.setAttribute("aria-label", `Edit entry for ${record.date || "unknown date"}`);
  edit.addEventListener("click", () => {
    recordId.value = record.id;
    dateInput.value = record.date || todayUtc();
    form.elements.weight.value = record.weight;
    form.elements.calories.value = record.calories;
    document.querySelector("#entry-title").textContent = "Edit progress entry";
    document.querySelector("#save-entry").textContent = "Update entry";
    cancel.hidden = false;
    form.elements.weight.focus();
  });
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "danger";
  remove.textContent = "Delete";
  remove.setAttribute("aria-label", `Delete entry for ${record.date || "unknown date"}`);
  remove.addEventListener("click", async () => {
    if (!window.confirm("Delete this progress entry? This cannot be undone.")) return;
    const restoreFocus = captureFocus(remove);
    remove.disabled = true;
    try {
      await api(`/api/tracker/${record.id}`, { method: "DELETE" });
      if (Number(recordId.value) === record.id) resetForm();
      status(feedback, "Entry deleted.");
      await loadHistory();
      restoreFocus(document.querySelector("#history-title"));
    } catch (error) {
      status(feedback, error.message, true);
      remove.disabled = false;
      restoreFocus();
    }
  });
  actions.append(edit, document.createTextNode(" "), remove);
  return row;
}

async function loadHistory(requestedPage = page, requestRevision = ++historyRevision) {
  const restoreRetry = captureFocus(retryHistory);
  retryHistory.hidden = true;
  retryHistory.disabled = true;
  const restorePrevious = captureFocus(previous);
  const restoreNext = captureFocus(next);
  previous.disabled = true;
  next.disabled = true;
  status(historyStatus, "Loading your history…");
  try {
    const data = await api(`/api/tracker/history?page=${requestedPage}`);
    if (requestRevision !== historyRevision) return;
    if (!data.records.length && requestedPage > 1) {
      const fallbackPage = Math.min(requestedPage - 1, Math.max(1, data.pages));
      return await loadHistory(fallbackPage, requestRevision);
    }
    page = data.page;
    lastPage = data.pages;
    document.querySelector("#history-rows").replaceChildren(...data.records.map(rowFor));
    document.querySelector("#history-table").hidden = data.records.length === 0;
    document.querySelector("#history-empty").hidden = data.records.length !== 0;
    document.querySelector("#history-pagination").hidden = data.pages <= 1;
    document.querySelector("#page-label").textContent = `Page ${data.page} of ${data.pages}`;
    status(historyStatus, `${data.total} ${data.total === 1 ? "entry" : "entries"} recorded.`);
  } catch (error) {
    if (requestRevision === historyRevision) {
      status(historyStatus, error.message, true);
      retryHistory.hidden = false;
    }
  } finally {
    if (requestRevision === historyRevision) {
    retryHistory.disabled = false;
    previous.disabled = page <= 1;
    next.disabled = page >= lastPage;
    const fallback = [previous, next, document.querySelector("#history-title")].find(
      (control) => control && !control.disabled,
    );
    restorePrevious(previous.disabled ? fallback : previous);
    restoreNext(next.disabled ? fallback : next);
    restoreRetry(retryHistory.hidden ? document.querySelector("#history-title") : retryHistory);
    }
  }
}
retryHistory.addEventListener("click", () => loadHistory());
previous.addEventListener("click", () => {
  if (page > 1) {
    loadHistory(page - 1);
  }
});
next.addEventListener("click", () => {
  if (page < lastPage) {
    loadHistory(page + 1);
  }
});
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!busy(form, true)) return;
  status(feedback, "Saving…");
  const editing = recordId.value;
  const submitted = Object.fromEntries(new FormData(form));
  try {
    await api(editing ? `/api/tracker/${editing}` : "/api/tracker/add", {
      method: editing ? "PUT" : "POST",
      body: submitted,
    });
    const current = Object.fromEntries(new FormData(form));
    const newerDraft =
      recordId.value !== editing ||
      Object.entries(submitted).some(([key, value]) => current[key] !== value);
    if (!newerDraft) resetForm();
    const message = editing ? "Entry updated." : "Entry saved.";
    status(feedback, message + (newerDraft ? " Your newer draft was kept." : ""));
    await loadHistory(1);
  } catch (error) {
    status(feedback, error.message, true);
  } finally {
    busy(form, false);
  }
});
loadHistory();
