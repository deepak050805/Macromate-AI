import { api, busy, captureFocus, status } from "./common.js";

function rememberEmail(email) {
  try {
    sessionStorage.setItem("pending-email", email);
  } catch {
    /* Email can be entered manually. */
  }
}

try {
  const pending = sessionStorage.getItem("pending-email");
  if (pending)
    for (const input of document.querySelectorAll('input[name="email"]')) input.value = pending;
} catch {
  /* Storage is optional. */
}

for (const form of document.querySelectorAll("form[data-auth]")) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const feedback = form.querySelector(".status");
    busy(form, true);
    status(feedback, "Working…");
    const values = Object.fromEntries(new FormData(form));
    try {
      const data = await api(form.dataset.auth, { method: "POST", body: values });
      rememberEmail(values.email);
      for (const input of document.querySelectorAll('input[name="email"]'))
        input.value = values.email;
      status(feedback, data.message);
      if (form.dataset.redirect) window.location.assign(form.dataset.redirect);
    } catch (error) {
      status(feedback, error.message, true);
    } finally {
      busy(form, false);
    }
  });
}

const notices = {
  verified: "Email verified. You can now log in.",
  reset: "Password updated. Log in with your new password.",
};
const notice = new URLSearchParams(window.location.search).get("notice");
if (notices[notice]) status(document.querySelector("form .status"), notices[notice]);

const resend = document.querySelector("#resend");
if (resend)
  resend.addEventListener("click", async () => {
    const form = document.querySelector("#verification-form");
    const email = form.querySelector('[name="email"]');
    if (!email.reportValidity()) return;
    const feedback = form.querySelector(".status");
    const restoreFocus = captureFocus(resend);
    resend.disabled = true;
    try {
      const data = await api("/api/auth/send-otp", {
        method: "POST",
        body: { email: email.value },
      });
      status(feedback, data.message);
      const seconds = Number(resend.dataset.cooldown);
      resend.textContent = `Wait ${seconds} seconds before requesting another code`;
      restoreFocus(form.elements.otp);
      setTimeout(() => {
        resend.disabled = false;
        resend.textContent = "Send a new code";
      }, seconds * 1000);
    } catch (error) {
      status(feedback, error.message, true);
      resend.disabled = false;
      restoreFocus();
    }
  });
