// ==================================================================
// THEME COLOR PICKER
// ==================================================================
// The idea: --accent is a CSS variable defined in style.css.
// Every button, link, and highlight in the CSS uses var(--accent)
// instead of a hardcoded color. That means if we change --accent
// with JavaScript, every one of those elements updates instantly —
// we never have to touch the CSS itself.

// The list of colors the user can pick from.
// Add or remove entries here to change the options everywone sees.
const THEME_COLORS = [
  { name: "Electric Blue", hex: "#3b82f6" },
  { name: "Orange", hex: "#f97316" },
  { name: "Green", hex: "#22c55e" },
  { name: "Purple", hex: "#a855f7" },
  { name: "Red", hex: "#ef4444" },
  { name: "Yellow", hex: "#eab308" },
  { name: "Pink", hex: "#ec4899" },
  { name: "Teal", hex: "#14b8a6" },
];

const DEFAULT_ACCENT = "#3b82f6"; // Electric Blue

// Changes the live theme color and remembers the choice.
function applyAccentColor(hex) {
  // document.documentElement = the <html> tag, which is where :root lives.
  // setProperty overwrites the --accent variable on the fly.
  document.documentElement.style.setProperty("--accent", hex);

  // localStorage saves a small piece of data in the browser that
  // survives page reloads and closing the tab (unlike a normal JS
  // variable, which resets every time the page loads).
  localStorage.setItem("liftlog-accent", hex);
}

// Runs on every page load, before the picker even exists, so the
// saved color shows up immediately instead of flashing blue first.
function loadSavedAccentColor() {
  const saved = localStorage.getItem("liftlog-accent");
  const colorToUse = saved || DEFAULT_ACCENT;
  document.documentElement.style.setProperty("--accent", colorToUse);
  return colorToUse;
}

// Builds the row of clickable color circles.
// Looks for a container with id="theme-picker" — if a page doesn't
// have one, this just quietly does nothing (no errors).
function renderThemePicker() {
  const container = document.getElementById("theme-picker");
  if (!container) return;

  const currentColor = loadSavedAccentColor();

  THEME_COLORS.forEach(function (color) {
    const swatch = document.createElement("div");
    swatch.className = "theme-swatch";
    swatch.style.backgroundColor = color.hex;
    swatch.title = color.name; // shows as a tooltip on hover

    if (color.hex.toLowerCase() === currentColor.toLowerCase()) {
      swatch.classList.add("selected");
    }

    swatch.onclick = function () {
      applyAccentColor(color.hex);

      // Move the "selected" ring to whichever swatch was just clicked
      document.querySelectorAll(".theme-swatch").forEach(function (s) {
        s.classList.remove("selected");
      });
      swatch.classList.add("selected");
    };

    container.appendChild(swatch);
  });
}

// Apply the saved color as early as possible (before the page fully renders)
loadSavedAccentColor();

// Build the picker once the page's HTML has loaded
document.addEventListener("DOMContentLoaded", renderThemePicker);