"use strict";

const motion = window.matchMedia("(prefers-reduced-motion: reduce)");

const calendar = document.querySelector("#calendar");
const filters = calendar.querySelector(".calendar-filters");
const days = Array.from(calendar.querySelectorAll(".day"));
const selection = { pillar: "all", format: "all" };

function filterDays() {
  let visible = 0;
  for (const day of days) {
    day.hidden = !Object.entries(selection).every(([key, value]) =>
      value === "all" || value === day.dataset[key]
    );
    if (!day.hidden) visible++;
  }
  calendar.classList.toggle("is-filtered", visible !== days.length);
  filters.querySelector(".filter-count").textContent = visible
    ? `Showing ${visible} of ${days.length} days`
    : "No days match. Try a different pillar or format.";
}
filters.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  const group = button.closest("[data-filter]");
  selection[group.dataset.filter] = button.dataset.value;
  for (const chip of group.querySelectorAll("button")) {
    chip.setAttribute("aria-pressed", String(chip === button));
  }
  filterDays();
});
filterDays();
filters.hidden = false;

function setupStoryboard(panel) {
  const range = panel.querySelector(".scrub");
  const play = panel.querySelector(".play");
  const clock = panel.querySelector(".reel-time");
  const rows = Array.from(panel.querySelectorAll("[data-start]"));
  const previews = Array.from(panel.querySelectorAll(".shot-preview"));
  const segments = Array.from(panel.querySelectorAll("[data-time]"));
  const length = Number(range.max);
  let time = 0;
  let timer = null;
  let start = 0;

  function show(seconds) {
    time = Math.min(seconds, length);
    const shot = rows.findIndex((row, i) =>
      time < Number(row.dataset.end) || i === rows.length - 1
    );
    rows.forEach((row, i) => {
      row.classList.toggle("is-current", i === shot);
      previews[i].hidden = i !== shot;
      segments[i].setAttribute("aria-current", String(i === shot));
    });
    range.value = time;
    range.setAttribute("aria-valuetext", `${time} of ${length} seconds, shot ${shot + 1}`);
    clock.textContent = `${time}s / ${length}s`;
  }

  function pause() {
    if (timer !== null) clearTimeout(timer);
    timer = null;
    play.textContent = "Play storyboard";
  }

  function tick() {
    const elapsed = performance.now() - start;
    show(Math.floor(elapsed / 1000));
    if (time === length) pause();
    else timer = setTimeout(tick, 1000 - elapsed % 1000);
  }

  play.addEventListener("click", () => {
    if (timer !== null) {
      pause();
      return;
    }
    if (time === length) show(0);
    start = performance.now() - time * 1000;
    play.textContent = "Pause storyboard";
    tick();
  });

  range.addEventListener("input", () => {
    pause();
    show(Number(range.value));
  });

  for (const button of segments) {
    button.addEventListener("click", () => {
      pause();
      show(Number(button.dataset.time));
    });
  }

  panel.querySelector(".shot-controls").hidden = false;
  show(0);
  return pause;
}

const tabs = document.querySelector(".reel-tabs");
const tabLinks = Array.from(tabs.querySelectorAll("a"));
const panels = tabLinks.map((link) => document.getElementById(link.hash.slice(1)));
const pauseStoryboard = panels.map(setupStoryboard);
let active = 0;

function selectReel(index, focus = false) {
  if (index !== active) pauseStoryboard[active]();
  active = index;
  tabLinks.forEach((link, i) => {
    const selected = i === index;
    link.setAttribute("aria-selected", String(selected));
    link.tabIndex = selected ? 0 : -1;
    panels[i].hidden = !selected;
  });
  if (focus) tabLinks[index].focus();
}

function revealLinkedReel() {
  const index = tabLinks.findIndex((link) => link.hash === location.hash);
  if (index !== -1) {
    selectReel(index);
    panels[index].scrollIntoView({ behavior: "instant" });
  }
}

tabs.setAttribute("role", "tablist");
tabLinks.forEach((link, i) => {
  link.setAttribute("role", "tab");
  link.setAttribute("aria-controls", panels[i].id);
  panels[i].setAttribute("role", "tabpanel");
  panels[i].setAttribute("aria-labelledby", link.id);
  panels[i].tabIndex = 0;
  link.addEventListener("click", (event) => {
    event.preventDefault();
    selectReel(i, true);
  });
  link.addEventListener("keydown", (event) => {
    const last = tabLinks.length - 1;
    const next = { ArrowLeft: i ? i - 1 : last, ArrowRight: i === last ? 0 : i + 1, Home: 0, End: last };
    if (!Object.hasOwn(next, event.key)) return;
    event.preventDefault();
    selectReel(next[event.key], true);
  });
});
selectReel(0);
tabs.hidden = false;
revealLinkedReel();
window.addEventListener("hashchange", revealLinkedReel);
document.querySelectorAll(".calendar-link").forEach((link) => {
  link.addEventListener("click", () => {
    const index = tabLinks.findIndex((tab) => tab.hash === link.hash);
    if (index !== -1) selectReel(index);
  });
});
document.addEventListener("visibilitychange", () => {
  if (document.hidden) pauseStoryboard[active]();
});

for (const frame of document.querySelectorAll(".deck-frame")) {
  const strip = frame.querySelector(".slides");
  const slides = Array.from(strip.children);
  const controls = frame.querySelector(".deck-controls");
  const dots = Array.from(controls.querySelectorAll(".slide-dot"));
  const previous = controls.querySelector('[data-step="-1"]');
  const next = controls.querySelector('[data-step="1"]');
  let current = 0;
  let target = 0;
  let settle;

  function update() {
    const width = strip.clientWidth;
    current = width ? Math.round(strip.scrollLeft / width) : 0;
    current = Math.max(0, Math.min(slides.length - 1, current));
    previous.disabled = current === 0;
    next.disabled = current === slides.length - 1;
    dots.forEach((dot, i) => dot.setAttribute("aria-current", String(i === current)));
  }

  function goTo(index) {
    target = Math.max(0, Math.min(slides.length - 1, index));
    strip.scrollTo({ left: target * strip.clientWidth, behavior: motion.matches ? "instant" : "smooth" });
  }

  controls.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    goTo(button.hasAttribute("data-slide") ? Number(button.dataset.slide) : target + Number(button.dataset.step));
  });
  strip.addEventListener("scroll", () => {
    update();
    clearTimeout(settle);
    settle = setTimeout(() => { target = current; }, 140);
  }, { passive: true });
  strip.addEventListener("keydown", (event) => {
    const offsets = { ArrowLeft: -1, ArrowRight: 1 };
    if (!Object.hasOwn(offsets, event.key)) return;
    event.preventDefault();
    goTo(target + offsets[event.key]);
  });
  update();
  controls.hidden = false;
}
