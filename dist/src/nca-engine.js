export class NeuralCA {
  constructor(model) {
    this.model = model;
    this.size = model.size;
    this.channels = model.channels;
    this.reset();
  }
  reset() {
    this.state = new Float32Array(this.size * this.size * this.channels);
    const p = ((this.size >> 1) * this.size + (this.size >> 1)) * this.channels;
    for (let c = 3; c < this.channels; c++) this.state[p + c] = 1;
    this.generation = 0;
  }
  living(state, y, x) {
    const { size: s, channels: c } = this;
    for (let yy = y - 1; yy <= y + 1; yy++)
      for (let xx = x - 1; xx <= x + 1; xx++)
        if (
          yy >= 0 &&
          xx >= 0 &&
          yy < s &&
          xx < s &&
          state[(yy * s + xx) * c + 3] > 0.1
        )
          return true;
    return false;
  }
  step(random = Math.random) {
    const { size: s, channels: c } = this,
      { hidden: h, weights: w, fireRate } = this.model,
      prev = this.state,
      candidate = new Float32Array(prev),
      next = new Float32Array(prev.length);
    const at = (y, x, k) =>
      y >= 0 && x >= 0 && y < s && x < s ? prev[(y * s + x) * c + k] : 0;
    for (let y = 0; y < s; y++)
      for (let x = 0; x < s; x++) {
        const input = new Float32Array(c * 3);
        for (let k = 0; k < c; k++) {
          input[k] = at(y, x, k);
          input[c + k] =
            (-at(y - 1, x - 1, k) -
              2 * at(y, x - 1, k) -
              at(y + 1, x - 1, k) +
              at(y - 1, x + 1, k) +
              2 * at(y, x + 1, k) +
              at(y + 1, x + 1, k)) /
            8;
          input[2 * c + k] =
            (-at(y - 1, x - 1, k) -
              2 * at(y - 1, x, k) -
              at(y - 1, x + 1, k) +
              at(y + 1, x - 1, k) +
              2 * at(y + 1, x, k) +
              at(y + 1, x + 1, k)) /
            8;
        }
        const mid = new Float32Array(h);
        for (let j = 0; j < h; j++) {
          let v = w.b1[j];
          for (let q = 0; q < input.length; q++)
            v += input[q] * w.w1[j * input.length + q];
          mid[j] = Math.max(0, v);
        }
        if (random() <= fireRate)
          for (let k = 0; k < c; k++) {
            let delta = w.b2[k];
            for (let j = 0; j < h; j++) delta += mid[j] * w.w2[k * h + j];
            candidate[(y * s + x) * c + k] += delta;
          }
      }
    for (let y = 0; y < s; y++)
      for (let x = 0; x < s; x++) {
        const keep = this.living(prev, y, x) && this.living(candidate, y, x);
        for (let k = 0; k < c; k++)
          next[(y * s + x) * c + k] = keep ? candidate[(y * s + x) * c + k] : 0;
      }
    this.state = next;
    this.generation++;
  }
  rgba() {
    const out = new Uint8ClampedArray(this.size * this.size * 4);
    for (let p = 0; p < this.size * this.size; p++) {
      const a = Math.max(0, Math.min(1, this.state[p * this.channels + 3]));
      for (let k = 0; k < 3; k++)
        out[p * 4 + k] = Math.round(
          Math.max(
            0,
            Math.min(1, a > 0.001 ? this.state[p * this.channels + k] / a : 0),
          ) * 255,
        );
      out[p * 4 + 3] = Math.round(a * 255);
    }
    return out;
  }
}
