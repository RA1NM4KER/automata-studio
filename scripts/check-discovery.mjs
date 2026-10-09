import assert from "node:assert/strict";
import { Automaton } from "../dist/src/engine.js";
import { PRESETS } from "../dist/src/presets.js";
import { snapshot, restore } from "../dist/src/snapshot.js";

const preset = PRESETS[0];
const model = new Automaton(preset);
assert.ok(model.population <= 12);
let minimum = Infinity;
let activity = Infinity;
for (let generation = 1; generation <= 1024; generation++) {
  model.step();
  if (generation > 896) {
    minimum = Math.min(minimum, model.population);
    activity = Math.min(activity, model.changed);
  }
  const n = model.size;
  for (let i = 0; i < n; i++) {
    assert.equal(
      model.cells[i] |
        model.cells[(n - 1) * n + i] |
        model.cells[i * n] |
        model.cells[i * n + n - 1],
      0,
    );
  }
}
assert.ok(minimum >= 40, `Surviving body fell to ${minimum} cells`);
assert.ok(activity >= 8, `Activity fell to ${activity} changes`);
const recovered = restore(
  snapshot(model, { palette: "tide", fit: 0.82 }),
).automaton;
model.step(16);
recovered.step(16);
assert.deepEqual(model.cells, recovered.cells);
assert.deepEqual(model.born, recovered.born);
console.log(
  `${preset.name}: minimum ${minimum} cells, minimum ${activity} changes in G897–1024; no boundary contact; exact snapshot continuation.`,
);
