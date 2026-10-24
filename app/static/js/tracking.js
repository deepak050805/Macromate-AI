import { api, busy, status } from "./common.js";
const form = document.querySelector("#tracking-form");
const feedback = document.querySelector("#entry-status");
const historyStatus = document.querySelector("#history-status");
const dateInput = document.querySelector("#record-date");
const recordId = document.querySelector("#record-id");
const cancel = document.querySelector("#cancel-edit");
const previous = document.querySelector("#previous-page");
const next = document.querySelector("#next-page");
const today = new Date().toISOString().slice(0, 10);
let page = 1;
let lastPage = 0;
dateInput.value = today;
dateInput.max = today;

function resetForm() {
  form.reset();
  recordId.value = "";
  dateInput.value = today;
  document.querySelector("#entry-title").textContent = "Add a progress entry";
  document.querySelector("#save-entry").textContent = "Save entry";
  cancel.hidden = true;
}
cancel.addEventListener("click", resetForm);

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
    dateInput.value = record.date || today;
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
    remove.disabled = true;
    try {
      await api(`/api/tracker/${record.id}`, { method: "DELETE" });
      if (Number(recordId.value) === record.id) resetForm();
      status(feedback, "Entry deleted.");
      await loadHistory();
    } catch (error) {
      status(feedback, error.message, true);
      remove.disabled = false;
    }
  });
  actions.append(edit, document.createTextNode(" "), remove);
  return row;
}

async function loadHistory() {
  previous.disabled = true;
  next.disabled = true;
  status(historyStatus, "Loading your history…");
  try {
    const data = await api(`/api/tracker/history?page=${page}`);
    if (!data.records.length && page > 1) {
      page -= 1;
      return await loadHistory();
    }
    lastPage = data.pages;
    document.querySelector("#history-rows").replaceChildren(...data.records.map(rowFor));
    document.querySelector("#history-table").hidden = data.records.length === 0;
    document.querySelector("#history-empty").hidden = data.records.length !== 0;
    document.querySelector("#history-pagination").hidden = data.pages <= 1;
    document.querySelector("#page-label").textContent = `Page ${data.page} of ${data.pages}`;
    status(historyStatus, `${data.total} ${data.total === 1 ? "entry" : "entries"} recorded.`);
  } catch (error) {
    status(historyStatus, error.message, true);
  } finally {
    previous.disabled = page <= 1;
    next.disabled = page >= lastPage;
  }
}
previous.addEventListener("click", () => {
  if (page > 1) {
    page -= 1;
    loadHistory();
  }
});
next.addEventListener("click", () => {
  if (page < lastPage) {
    page += 1;
    loadHistory();
  }
});
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  busy(form, true);
  status(feedback, "Saving…");
  const editing = recordId.value;
  try {
    await api(editing ? `/api/tracker/${editing}` : "/api/tracker/add", {
      method: editing ? "PUT" : "POST",
      body: Object.fromEntries(new FormData(form)),
    });
    resetForm();
    page = 1;
    status(feedback, editing ? "Entry updated." : "Entry saved.");
    await loadHistory();
  } catch (error) {
    status(feedback, error.message, true);
  } finally {
    busy(form, false);
  }
});
loadHistory();
