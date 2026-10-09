import { Automaton, SIZE, MAX_GENERATION, parseRule } from "./engine.js";
import { PALETTES } from "./presets.js";

export function snapshot(automaton, appearance) {
  return {
    format: "automata-studio",
    version: 2,
    size: automaton.size,
    topology: automaton.topology,
    rule: automaton.rule.text,
    seed: automaton.seed,
    key: automaton.key,
    pattern: automaton.pattern?.map((point) => [...point]) ?? null,
    generation: automaton.generation,
    cells: Array.from(automaton.cells),
    born: Array.from(automaton.born),
    appearance: { palette: appearance.palette, fit: appearance.fit },
  };
}

export function restore(data) {
  if (
    !data ||
    data.format !== "automata-studio" ||
    ![1, 2].includes(data.version) ||
    data.size !== SIZE
  ) {
    throw new Error("Choose a supported Automata Studio snapshot.");
  }
  const seeds =
    data.version === 1
      ? ["single", "ring", "disk", "scatter"]
      : ["single", "ring", "disk", "scatter", "witness"];
  if (
    !["hex", "square"].includes(data.topology) ||
    !seeds.includes(data.seed)
  ) {
    throw new Error("The snapshot has an unsupported lattice or seed.");
  }
  const pattern = data.version === 2 ? data.pattern : null;
  if (
    data.seed === "witness" &&
    (!Array.isArray(pattern) ||
      pattern.length < 1 ||
      pattern.length > 64 ||
      pattern.some(
        (point) =>
          !Array.isArray(point) ||
          point.length !== 2 ||
          point.some(
            (value) =>
              !Number.isInteger(value) ||
              Math.abs(value) >= Math.floor(SIZE / 2),
          ),
      ))
  ) {
    throw new Error("The snapshot witness coordinates are invalid.");
  }
  if (data.seed !== "witness" && pattern !== null)
    throw new Error("Only witness seeds may include coordinates.");
  if (
    typeof data.key !== "string" ||
    data.key.length > 100 ||
    typeof data.rule !== "string"
  ) {
    throw new Error("The snapshot configuration is invalid.");
  }
  parseRule(data.rule, data.topology);
  if (
    !Number.isInteger(data.generation) ||
    data.generation < 0 ||
    data.generation > MAX_GENERATION
  ) {
    throw new Error("The snapshot generation is out of range.");
  }
  const length = SIZE * SIZE;
  if (
    !Array.isArray(data.cells) ||
    data.cells.length !== length ||
    data.cells.some((cell) => cell !== 0 && cell !== 1)
  ) {
    throw new Error("The snapshot cell data is invalid.");
  }
  if (
    !Array.isArray(data.born) ||
    data.born.length !== length ||
    data.born.some(
      (value, i) =>
        !Number.isInteger(value) ||
        (data.cells[i] ? value < 0 || value > data.generation : value !== -1),
    )
  ) {
    throw new Error("The snapshot colour history is invalid.");
  }
  if (
    !data.appearance ||
    !Object.hasOwn(PALETTES, data.appearance.palette) ||
    typeof data.appearance.fit !== "number" ||
    !Number.isFinite(data.appearance.fit) ||
    data.appearance.fit < 0.45 ||
    data.appearance.fit > 0.95
  ) {
    throw new Error("The snapshot appearance is invalid.");
  }
  const automaton = new Automaton({ ...data, pattern });
  automaton.cells.set(data.cells);
  automaton.born.set(data.born);
  automaton.generation = data.generation;
  automaton.population = data.cells.reduce((sum, value) => sum + value, 0);
  return { automaton, appearance: { ...data.appearance } };
}
