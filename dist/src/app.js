import { Automaton, MAX_GENERATION } from "./engine.js";
import { PRESETS, PALETTES } from "./presets.js";
import { paint } from "./render.js";
import { snapshot, restore } from "./snapshot.js";

const $ = (id) => document.getElementById(id);
const canvas = $("art");
let automaton = new Automaton(PRESETS[0]).step(PRESETS[0].generation);
let appearance = { palette: "tide", fit: 0.82 };
let selectedPreset = PRESETS[0].id;
let running = false;
let previous = 0;
let accumulated = 0;
let noticeTimer;

function notify(message, error = false) {
  clearTimeout(noticeTimer);
  $("notice").textContent = message;
  $("notice").dataset.error = String(error);
  $("notice").hidden = false;
  noticeTimer = setTimeout(
    () => {
      $("notice").hidden = true;
    },
    error ? 7000 : 4000,
  );
}

function atBoundary() {
  const n = automaton.size;
  for (let i = 0; i < n; i++) {
    if (
      automaton.cells[i] ||
      automaton.cells[(n - 1) * n + i] ||
      automaton.cells[i * n] ||
      automaton.cells[i * n + n - 1]
    )
      return true;
  }
  return false;
}

function statusText() {
  if (automaton.generation >= MAX_GENERATION) return "Generation limit";
  if (atBoundary()) return "Boundary reached";
  if (!automaton.population && !automaton.rule.birth.includes(0))
    return "No living cells";
  if (automaton.generation && automaton.changed === 0) return "Stable pattern";
  return running ? "Growing" : "Paused";
}

function draw() {
  paint(canvas, automaton, appearance);
  for (const id of ["avatar-large", "avatar-medium", "avatar-small"]) {
    const preview = $(id);
    preview
      .getContext("2d")
      .drawImage(canvas, 0, 0, preview.width, preview.height);
  }
  $("generation").textContent = String(automaton.generation).padStart(4, "0");
  $("population").textContent = automaton.population.toLocaleString();
  $("stage-rule").textContent = automaton.rule.text;
  $("lattice-badge").textContent =
    automaton.topology === "hex" ? "HEXAGONAL" : "SQUARE";
  $("status").textContent = statusText();
  canvas.setAttribute(
    "aria-label",
    `${automaton.topology} cellular automaton, rule ${automaton.rule.text}, generation ${automaton.generation}, ${automaton.population} living cells.`,
  );
  document
    .querySelectorAll(".preset")
    .forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.id === selectedPreset),
      ),
    );
  document
    .querySelectorAll(".palette")
    .forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.id === appearance.palette),
      ),
    );
}

function setRunning(value) {
  running = value;
  previous = 0;
  accumulated = 0;
  $("play").textContent = running ? "Pause" : "Play";
  $("play").setAttribute("aria-pressed", String(running));
  $("step").disabled = running;
  $("status").textContent = statusText();
}

function describe() {
  const preset = PRESETS.find((item) => item.id === selectedPreset);
  $("specimen").textContent = preset
    ? `${preset.name.toUpperCase()} / 001`
    : "CUSTOM / 001";
  $("description").textContent =
    preset?.description ??
    `Rule ${automaton.rule.text} on a ${automaton.topology === "hex" ? "six-neighbour hexagonal" : "eight-neighbour square"} lattice. Birth counts create cells; survival counts keep them alive.`;
}

function updateNeighbourOptions() {
  const max = $("topology").value === "hex" ? 6 : 8;
  for (const input of document.querySelectorAll(".rule-values input")) {
    input.disabled = Number(input.value) > max;
    if (input.disabled) input.checked = false;
  }
}

function syncControls() {
  const witnessOption = $("seed").querySelector('option[value="witness"]');
  witnessOption.disabled = !automaton.pattern;
  $("seed").value = automaton.seed;
  $("seed-key").value = automaton.key;
  $("topology").value = automaton.topology;
  $("fit").value = Math.round(appearance.fit * 100);
  $("fit-value").value = `${Math.round(appearance.fit * 100)}%`;
  for (const field of ["birth", "survive"]) {
    for (const input of $(field).querySelectorAll("input"))
      input.checked = automaton.rule[field].includes(Number(input.value));
  }
  updateNeighbourOptions();
  updateSeedHint();
  describe();
}

function updateSeedHint() {
  const seeded = ["disk", "scatter"].includes($("seed").value);
  $("seed-key").disabled = !seeded;
  $("randomize").disabled = !seeded;
  $("seed-hint").textContent =
    $("seed").value === "witness"
      ? `${automaton.pattern?.length ?? 0} exact cells from a replayable search witness.`
      : seeded
        ? "Same key + same rule = the same growth."
        : "This pattern is fixed. The key is used by disk and scatter seeds.";
}

function usePreset(id) {
  const preset = PRESETS.find((item) => item.id === id);
  if (!preset) throw new Error("Unknown preset.");
  setRunning(false);
  selectedPreset = id;
  automaton = new Automaton(preset).step(preset.generation);
  syncControls();
  draw();
}

function fresh() {
  return new Automaton({
    topology: automaton.topology,
    rule: automaton.rule.text,
    seed: automaton.seed,
    key: automaton.key,
    pattern: automaton.pattern,
  });
}

function reset(play = false) {
  setRunning(false);
  automaton = fresh();
  draw();
  setRunning(play);
}

function applySeed() {
  setRunning(false);
  selectedPreset = null;
  automaton = new Automaton({
    topology: automaton.topology,
    rule: automaton.rule.text,
    seed: $("seed").value,
    key: $("seed-key").value,
    pattern: $("seed").value === "witness" ? automaton.pattern : null,
  });
  syncControls();
  draw();
  notify("Seed applied. Play or step to grow it.");
}

function advance(count = 1) {
  if (automaton.generation >= MAX_GENERATION) {
    setRunning(false);
    notify("Generation limit reached. Export this frame or reset.");
    return;
  }
  automaton.step(count);
  if (
    running &&
    (automaton.changed === 0 ||
      atBoundary() ||
      automaton.generation >= MAX_GENERATION)
  )
    setRunning(false);
  draw();
}

function filename(extension) {
  const key =
    automaton.key.replace(/[^a-z0-9_-]/gi, "-").slice(0, 40) || "seed";
  return `automata-${automaton.topology}-${key}-g${automaton.generation}.${extension}`;
}

function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

async function exportPNG() {
  setRunning(false);
  const size = Number($("resolution").value);
  const image = document.createElement("canvas");
  image.width = image.height = size;
  paint(image, automaton, appearance);
  const name = filename("png");
  const blob = await new Promise((resolve) =>
    image.toBlob(resolve, "image/png"),
  );
  if (!blob) throw new Error("PNG export failed. Try a smaller image size.");
  download(blob, name);
  notify(`${size} × ${size} PNG exported.`);
}

for (const preset of PRESETS) {
  const button = document.createElement("button");
  button.className = "preset";
  if (preset.featured) button.classList.add("featured");
  button.dataset.id = preset.id;
  button.setAttribute("aria-pressed", String(preset.id === selectedPreset));
  const metrics = preset.metrics
    ? `<em>${preset.metrics.map((metric) => `<span>${metric}</span>`).join("")}</em>`
    : "";
  button.innerHTML = `<canvas width="128" height="128" aria-hidden="true"></canvas><span><b>${preset.name}</b><small>${preset.subtitle}</small>${metrics}</span>`;
  paint(
    button.querySelector("canvas"),
    new Automaton(preset).step(preset.generation),
    { palette: "tide", fit: 0.92 },
  );
  button.addEventListener("click", () => usePreset(preset.id));
  $("presets").append(button);
}

for (const [id, palette] of Object.entries(PALETTES)) {
  const button = document.createElement("button");
  button.className = "palette";
  button.dataset.id = id;
  button.title = palette.name;
  button.setAttribute("aria-label", palette.name);
  button.setAttribute("aria-pressed", String(id === appearance.palette));
  const swatch = document.createElement("span");
  for (const color of palette.colors) {
    const chip = document.createElement("i");
    chip.style.backgroundColor = color;
    swatch.append(chip);
  }
  button.append(swatch);
  button.addEventListener("click", () => {
    appearance.palette = id;
    draw();
  });
  $("palettes").append(button);
}

for (const field of ["birth", "survive"]) {
  for (let count = 0; count <= 8; count++) {
    const label = document.createElement("label");
    label.className = "rule-cell";
    label.innerHTML = `<input type="checkbox" value="${count}" aria-label="${field === "birth" ? "Birth" : "Survival"} with ${count} neighbours"><span>${count}</span>`;
    $(field).append(label);
  }
}

$("play").addEventListener("click", () => setRunning(!running));
$("step").addEventListener("click", () => advance());
$("regrow").addEventListener("click", () => reset(true));
$("reset").addEventListener("click", () => reset(false));
$("seed").addEventListener("change", updateSeedHint);
$("apply-seed").addEventListener("click", applySeed);
$("randomize").addEventListener("click", () => {
  $("seed-key").value = `seed-${crypto.randomUUID().slice(0, 8)}`;
});
$("fit").addEventListener("input", () => {
  appearance.fit = Number($("fit").value) / 100;
  $("fit-value").value = `${$("fit").value}%`;
  draw();
});
$("topology").addEventListener("change", updateNeighbourOptions);
$("rule-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const counts = (field) =>
    [...$(field).querySelectorAll("input:checked:not(:disabled)")]
      .map((input) => input.value)
      .join("");
  const candidate = new Automaton({
    topology: $("topology").value,
    rule: `B${counts("birth")}/S${counts("survive")}`,
    seed: $("seed").value,
    key: $("seed-key").value,
    pattern: $("seed").value === "witness" ? automaton.pattern : null,
  });
  setRunning(false);
  selectedPreset = null;
  automaton = candidate;
  syncControls();
  draw();
  notify("Rule applied at generation 0.");
});
$("export").addEventListener("click", () =>
  exportPNG().catch((error) => notify(error.message, true)),
);
$("save").addEventListener("click", () => {
  setRunning(false);
  download(
    new Blob([JSON.stringify(snapshot(automaton, appearance))], {
      type: "application/json",
    }),
    filename("json"),
  );
  notify("Exact snapshot saved. Reopen it to continue growing.");
});
$("load").addEventListener("click", () => $("file").click());
$("file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    if (file.size > 1_000_000)
      throw new Error("Snapshot is too large. Choose a file under 1 MB.");
    const recovered = restore(JSON.parse(await file.text()));
    setRunning(false);
    automaton = recovered.automaton;
    appearance = recovered.appearance;
    selectedPreset = null;
    syncControls();
    draw();
    notify(`Snapshot restored at generation ${automaton.generation}.`);
  } catch (error) {
    notify(
      error instanceof SyntaxError
        ? "That file is not valid JSON."
        : error.message,
      true,
    );
  }
  event.target.value = "";
});
document.addEventListener("keydown", (event) => {
  if (
    event.ctrlKey ||
    event.metaKey ||
    event.altKey ||
    event.repeat ||
    event.target.closest(
      "input, select, textarea, button, summary, [contenteditable]",
    )
  )
    return;
  if (event.code === "Space") {
    event.preventDefault();
    setRunning(!running);
  }
  if (event.key.toLowerCase() === "n") {
    setRunning(false);
    advance();
  }
});
document.addEventListener("visibilitychange", () => {
  if (document.hidden) setRunning(false);
});

function animate(time) {
  if (running) {
    if (!previous) previous = time;
    accumulated += Math.min(time - previous, 150);
    previous = time;
    const interval = 1000 / Number($("speed").value);
    const steps = Math.min(4, Math.floor(accumulated / interval));
    if (steps) {
      accumulated -= steps * interval;
      for (let i = 0; i < steps && running; i++) advance();
    }
  }
  requestAnimationFrame(animate);
}

syncControls();
draw();
requestAnimationFrame(animate);

const context = document.modelContext;
if (context?.registerTool) {
  const lifecycle = new AbortController();
  const tools = [
    {
      name: "read_automata_state",
      description:
        "Read the current automaton configuration and frame statistics.",
      inputSchema: {
        type: "object",
        properties: {},
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true },
      execute: () => ({
        topology: automaton.topology,
        rule: automaton.rule.text,
        seed: automaton.seed,
        key: automaton.key,
        generation: automaton.generation,
        population: automaton.population,
        running,
        appearance: { ...appearance },
      }),
    },
    {
      name: "select_automata_preset",
      description:
        "Replace the current frame with a preset at its showcase generation. Unsaved work is replaced.",
      inputSchema: {
        type: "object",
        properties: {
          preset: { type: "string", enum: PRESETS.map((item) => item.id) },
        },
        required: ["preset"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false },
      execute: (input) => {
        if (!input || !PRESETS.some((item) => item.id === input.preset))
          throw new Error(
            `Choose ${PRESETS.map((item) => item.id).join(", ")}.`,
          );
        usePreset(input.preset);
        return {
          preset: selectedPreset,
          generation: automaton.generation,
          population: automaton.population,
        };
      },
    },
  ];
  for (const tool of tools) {
    try {
      Promise.resolve(
        context.registerTool(tool, { signal: lifecycle.signal }),
      ).catch(() => {});
    } catch {}
  }
  window.addEventListener("pagehide", () => lifecycle.abort(), { once: true });
}
