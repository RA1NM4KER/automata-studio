export const PRESETS = [
  {
    id: "breather",
    name: "Cellular Lace",
    subtitle: "Eight cells become a persistent oscillator.",
    featured: true,
    topology: "hex",
    rule: "B2345/S0345",
    seed: "witness",
    key: "hex-search-004-cup-8",
    generation: 15,
    pattern: [
      [-2, -1],
      [-2, 0],
      [-1, 1],
      [0, 1],
      [1, 1],
      [2, 0],
      [2, -1],
      [0, 0],
    ],
    description:
      "Eight seed cells form a 55–57-cell oscillator. From generation 13, two configurations repeat with 34 cells changing per step. Checked through generation 1024 without boundary contact. A sustained small oscillator, with no claim of novelty.",
    metrics: [
      "8-cell seed",
      "55–57 sustained",
      "34 changes / step",
      "verified to G1024",
    ],
  },
  {
    id: "crystal",
    name: "Crystal",
    subtitle: "Six neighbours. One seed.",
    topology: "hex",
    rule: "B1/S0123456",
    seed: "single",
    key: "kefas-001",
    generation: 58,
    description:
      "An empty cell grows when exactly one neighbour is alive. Living cells remain alive. Branches emerge from the rule.",
  },
  {
    id: "coral",
    name: "Coral",
    subtitle: "A branching colony.",
    topology: "square",
    rule: "B3/S45678",
    seed: "disk",
    key: "coral-17",
    generation: 96,
    description:
      "An empty cell grows with three neighbours. A living cell survives with four to eight. The seeded disk develops into a colony.",
  },
  {
    id: "maze",
    name: "Maze",
    subtitle: "Order from scattered cells.",
    topology: "square",
    rule: "B3/S12345",
    seed: "scatter",
    key: "maze-23",
    generation: 60,
    description:
      "An empty cell grows with three neighbours. A living cell survives with one to five. Corridors form from the scattered seed.",
  },
];

export const PALETTES = {
  tide: {
    name: "Tide",
    background: "#07191e",
    colors: ["#e8fff5", "#72e0ca", "#239b9e", "#a9a4ff"],
  },
  ember: {
    name: "Ember",
    background: "#1b1110",
    colors: ["#fff0d1", "#ffbf75", "#e86d49", "#95334c"],
  },
  volt: {
    name: "Volt",
    background: "#11170e",
    colors: ["#f3ffd6", "#d9fa76", "#84c04a", "#4d7855"],
  },
  mono: {
    name: "Monochrome",
    background: "#101113",
    colors: ["#ffffff", "#d9dce0", "#aeb5bc", "#828d97"],
  },
};
