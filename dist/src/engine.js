export const SIZE = 151;
export const MAX_GENERATION = 4096;

export function randomFromSeed(key) {
  let state = 2166136261;
  for (const character of String(key)) {
    state = Math.imul(state ^ character.codePointAt(0), 16777619) >>> 0;
  }
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

export function parseRule(text, topology) {
  const match = /^B([0-8]*)\/S([0-8]*)$/i.exec(text.trim());
  if (!match) throw new Error("Use a rule such as B1/S0123456.");
  const max = topology === "hex" ? 6 : 8;
  const birth = [...new Set([...match[1]].map(Number))].sort();
  const survive = [...new Set([...match[2]].map(Number))].sort();
  if ([...birth, ...survive].some((value) => value > max)) {
    throw new Error(`This lattice has ${max} neighbours per cell.`);
  }
  return { birth, survive, text: `B${birth.join("")}/S${survive.join("")}` };
}

export class Automaton {
  constructor({
    size = SIZE,
    topology = "hex",
    rule = "B1/S0123456",
    seed = "single",
    key = "kefas-001",
    pattern = null,
  } = {}) {
    this.size = size;
    this.topology = topology;
    this.rule = parseRule(rule, topology);
    this.seed = seed;
    this.key = key;
    this.pattern = pattern ? pattern.map((point) => [...point]) : null;
    this.generation = 0;
    this.cells = new Uint8Array(size * size);
    this.next = new Uint8Array(size * size);
    this.born = new Int32Array(size * size).fill(-1);
    this.neighbours = this.makeNeighbours();
    this.plant();
    this.population = this.cells.reduce((sum, cell) => sum + cell, 0);
    this.changed = this.population;
  }

  makeNeighbours() {
    const neighbours = [];
    for (let row = 0; row < this.size; row++) {
      for (let col = 0; col < this.size; col++) {
        const side = row % 2 ? 1 : -1;
        const offsets =
          this.topology === "hex"
            ? [
                [-1, 0],
                [1, 0],
                [0, -1],
                [side, -1],
                [0, 1],
                [side, 1],
              ]
            : [
                [-1, -1],
                [0, -1],
                [1, -1],
                [-1, 0],
                [1, 0],
                [-1, 1],
                [0, 1],
                [1, 1],
              ];
        neighbours.push(
          offsets.flatMap(([dx, dy]) => {
            const x = col + dx;
            const y = row + dy;
            return x >= 0 && y >= 0 && x < this.size && y < this.size
              ? [y * this.size + x]
              : [];
          }),
        );
      }
    }
    return neighbours;
  }

  plant() {
    const random = randomFromSeed(this.key);
    const center = Math.floor(this.size / 2);
    if (this.seed === "witness") {
      if (!this.pattern?.length)
        throw new Error("A discovered witness needs seed coordinates.");
      for (const [dx, dy] of this.pattern) {
        const col = center + dx;
        const row = center + dy;
        if (row < 0 || col < 0 || row >= this.size || col >= this.size)
          throw new Error("A witness cell falls outside the lattice.");
        this.cells[row * this.size + col] = 1;
        this.born[row * this.size + col] = 0;
      }
      return;
    }
    for (let row = 0; row < this.size; row++) {
      for (let col = 0; col < this.size; col++) {
        const dx = col - center;
        const dy = row - center;
        const radius = Math.hypot(dx, dy);
        let alive = false;
        if (this.seed === "single") alive = dx === 0 && dy === 0;
        if (this.seed === "ring") alive = radius >= 8 && radius <= 10;
        if (this.seed === "disk") alive = radius < 15 && random() < 0.48;
        if (this.seed === "scatter") alive = radius < 40 && random() < 0.12;
        if (alive) {
          this.cells[row * this.size + col] = 1;
          this.born[row * this.size + col] = 0;
        }
      }
    }
  }

  step(count = 1) {
    const birth = this.rule.birth;
    const survive = this.rule.survive;
    for (
      let tick = 0;
      tick < count && this.generation < MAX_GENERATION;
      tick++
    ) {
      let population = 0;
      let changed = 0;
      for (let i = 0; i < this.cells.length; i++) {
        let total = 0;
        for (const neighbour of this.neighbours[i])
          total += this.cells[neighbour];
        const alive = (this.cells[i] ? survive : birth).includes(total) ? 1 : 0;
        this.next[i] = alive;
        population += alive;
        if (alive !== this.cells[i]) changed++;
        if (alive && !this.cells[i]) this.born[i] = this.generation + 1;
        if (!alive) this.born[i] = -1;
      }
      [this.cells, this.next] = [this.next, this.cells];
      this.generation++;
      this.population = population;
      this.changed = changed;
    }
    return this;
  }
}
