const feedback = document.querySelector("#connection-status");
function offline() {
  feedback.hidden = false;
  feedback.textContent = "Your browser is offline. Keep this page open to retain unsaved work, then retry when you reconnect.";
}
function online() {
  feedback.hidden = false;
  feedback.textContent = "Your browser is online again. You can retry your last action.";
}
window.addEventListener("offline", offline);
window.addEventListener("online", online);
if (!navigator.onLine) offline();
