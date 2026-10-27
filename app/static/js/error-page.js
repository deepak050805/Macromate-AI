import { captureFocus, status } from "./common.js";

const reference = document.querySelector("#error-reference");
const copy = document.querySelector("#copy-reference");
if (reference && copy && navigator.clipboard?.writeText) {
  copy.hidden = false;
  copy.addEventListener("click", async () => {
    if (copy.disabled) return;
    const restoreFocus = captureFocus(copy);
    copy.disabled = true;
    const feedback = document.querySelector("#reference-status");
    try {
      await navigator.clipboard.writeText(reference.textContent.trim());
      status(feedback, "Reference copied.");
    } catch {
      status(feedback, "Select and copy the reference above.", true);
    } finally {
      copy.disabled = false;
      restoreFocus();
    }
  });
}
