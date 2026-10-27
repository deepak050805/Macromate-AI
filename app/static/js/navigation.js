const toggle = document.querySelector("#navigation-toggle");
const navigation = document.querySelector("#main-navigation");
const mobile = window.matchMedia("(max-width: 760px)");
let expanded = false;

function render() {
  const hidingNavigation = mobile.matches && !expanded;
  const active = document.activeElement;
  navigation.hidden = hidingNavigation;
  toggle.hidden = !mobile.matches;
  toggle.setAttribute("aria-expanded", String(mobile.matches && expanded));
  toggle.textContent = expanded ? "Close menu" : "Menu";
  if (hidingNavigation && navigation.contains(active)) toggle.focus();
  else if (!mobile.matches && active === toggle)
    (navigation.querySelector('[aria-current="page"]') || navigation.querySelector("a"))?.focus();
}

toggle.addEventListener("click", () => {
  expanded = !expanded;
  render();
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !mobile.matches || !expanded) return;
  if (navigation.contains(event.target) || event.target === toggle) {
    event.preventDefault();
    expanded = false;
    render();
    toggle.focus();
  }
});
document.addEventListener("click", (event) => {
  if (mobile.matches && expanded && !navigation.contains(event.target) && !toggle.contains(event.target)) {
    expanded = false;
    render();
  }
});
mobile.addEventListener("change", () => {
  expanded = false;
  render();
});
render();
