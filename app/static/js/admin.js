import { api, captureFocus, status } from "./common.js";
const feedback = document.querySelector("#admin-status");
const previous = document.querySelector("#admin-previous");
const next = document.querySelector("#admin-next");
let page = 1;
let pages = 0;
async function load(requestedPage = page) {
  const restorePrevious = captureFocus(previous);
  const restoreNext = captureFocus(next);
  previous.disabled = true;
  next.disabled = true;
  status(feedback, "Loading accounts…");
  try {
    const data = await api(`/api/auth/all-users?page=${requestedPage}`);
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
        : "No accounts registered yet.",
    );
  } catch (error) {
    status(feedback, error.message, true);
  } finally {
    previous.disabled = page <= 1;
    next.disabled = page >= pages;
    const fallback = [previous, next, document.querySelector("#users-title")].find(
      (control) => control && !control.disabled,
    );
    restorePrevious(previous.disabled ? fallback : previous);
    restoreNext(next.disabled ? fallback : next);
  }
}
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
