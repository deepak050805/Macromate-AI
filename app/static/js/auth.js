import { api, busy, captureFocus, status } from "./common.js";

const maskPasswords = [];
for (const button of document.querySelectorAll("[data-password-toggle]")) {
  const input = document.getElementById(button.dataset.passwordToggle);
  if (!input) continue;
  const label = input.labels?.[0]?.textContent.trim().toLowerCase() || "password";
  button.hidden = false;
  const setRevealed = (revealed) => {
    input.type = revealed ? "text" : "password";
    button.textContent = revealed ? "Hide password" : "Show password";
    button.setAttribute("aria-pressed", String(revealed));
    button.setAttribute("aria-label", `${revealed ? "Hide" : "Show"} ${label}`);
  };
  setRevealed(false);
  maskPasswords.push(() => setRevealed(false));
  button.addEventListener("click", () => setRevealed(input.type === "password"));
}
document.addEventListener("visibilitychange", () => {
  if (document.hidden) for (const mask of maskPasswords) mask();
});
window.addEventListener("pagehide", () => {
  for (const mask of maskPasswords) mask();
});

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
    for (const input of document.querySelectorAll('input[name="email"]'))
      if (!input.value) input.value = pending;
} catch {
  /* Storage is optional. */
}

for (const form of document.querySelectorAll("form[data-auth]")) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const feedback = form.querySelector(".status");
    if (!busy(form, true)) return;
    status(feedback, "Working…");
    const values = Object.fromEntries(new FormData(form));
    const emailDrafts = [...document.querySelectorAll('input[name="email"]')].map((input) => ({
      input,
      value: input.value,
    }));
    try {
      const data = await api(form.dataset.auth, { method: "POST", body: values });
      if (typeof values.email === "string") {
        rememberEmail(values.email);
        for (const { input, value } of emailDrafts)
          if (input.value === value) input.value = values.email;
      }
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
  sessions: "All sessions signed out. Log in to continue.",
  verified: "Email verified. You can now log in.",
  reset: "Password updated. Log in with your new password.",
};
const notice = new URLSearchParams(window.location.search).get("notice");
if (notices[notice]) status(document.querySelector("form .status"), notices[notice]);

const resend = document.querySelector("#resend");
if (resend) {
  const form = document.querySelector("#verification-form");
  const email = form.querySelector('[name="email"]');
  const feedback = form.querySelector(".status");
  let pending = false;
  let cooldownEmail = null;
  let cooldownTimer = null;
  const clearCooldown = () => {
    clearTimeout(cooldownTimer);
    cooldownTimer = null;
    cooldownEmail = null;
    resend.disabled = pending;
    resend.textContent = "Send a new code";
  };
  email.addEventListener("input", () => {
    if (cooldownEmail !== null && email.value !== cooldownEmail) {
      clearCooldown();
      status(feedback, "");
    }
  });
  resend.addEventListener("click", async () => {
    if (pending || cooldownTimer !== null) return;
    if (!email.reportValidity()) return;
    const requestedEmail = email.value;
    const restoreFocus = captureFocus(resend);
    pending = true;
    resend.disabled = true;
    try {
      const data = await api("/api/auth/send-otp", {
        method: "POST",
        body: { email: requestedEmail },
      });
      if (email.value !== requestedEmail) return;
      rememberEmail(requestedEmail);
      status(feedback, data.message);
      const seconds = Number(resend.dataset.cooldown);
      cooldownEmail = requestedEmail;
      resend.textContent = `Wait ${seconds} seconds before requesting another code`;
      restoreFocus(form.elements.otp);
      cooldownTimer = setTimeout(clearCooldown, seconds * 1000);
    } catch (error) {
      if (email.value === requestedEmail) status(feedback, error.message, true);
    } finally {
      pending = false;
      if (cooldownTimer === null) {
        resend.disabled = false;
        if (email.value === requestedEmail) restoreFocus();
      }
    }
  });
}
