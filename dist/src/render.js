import { PALETTES } from "./presets.js";

function rgb(hex) {
  return [1, 3, 5].map((index) =>
    Number.parseInt(hex.slice(index, index + 2), 16),
  );
}

export function paint(
  canvas,
  automaton,
  { palette = "tide", fit = 0.82, transparent = false } = {},
) {
  const context = canvas.getContext("2d");
  const theme = PALETTES[palette];
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);
  if (!transparent) {
    context.fillStyle = theme.background;
    context.fillRect(0, 0, width, height);
  }
  const center = Math.floor(automaton.size / 2);
  const hex = automaton.topology === "hex";
  const positions = [];
  let extent = 1;
  for (let i = 0; i < automaton.cells.length; i++) {
    if (!automaton.cells[i]) continue;
    const row = Math.floor(i / automaton.size);
    const col = i % automaton.size;
    const x = hex
      ? (col - center + 0.5 * ((row & 1) - (center & 1))) * Math.sqrt(3)
      : col - center;
    const y = hex ? (row - center) * 1.5 : row - center;
    extent = Math.max(extent, Math.abs(x) + 1, Math.abs(y) + 1);
    positions.push([i, x, y]);
  }
  const minimumExtent = hex ? 20 : 18;
  const scale =
    (Math.min(width, height) * fit) / (2 * Math.max(extent, minimumExtent));
  const stops = theme.colors.map(rgb);
  for (const [index, x, y] of positions) {
    const value = (automaton.born[index] % 72) / 24;
    const low = Math.floor(value);
    const blend = value - low;
    const color = stops[low].map((channel, n) =>
      Math.round(channel * (1 - blend) + stops[low + 1][n] * blend),
    );
    context.fillStyle = `rgb(${color.join(",")})`;
    const px = width / 2 + x * scale;
    const py = height / 2 + y * scale;
    if (hex) {
      context.beginPath();
      for (let vertex = 0; vertex < 6; vertex++) {
        const angle = (Math.PI / 3) * vertex + Math.PI / 6;
        const vx = px + Math.cos(angle) * scale * 0.96;
        const vy = py + Math.sin(angle) * scale * 0.96;
        if (vertex === 0) context.moveTo(vx, vy);
        else context.lineTo(vx, vy);
      }
      context.closePath();
      context.fill();
    } else {
      context.fillRect(
        px - scale * 0.47,
        py - scale * 0.47,
        scale * 0.94,
        scale * 0.94,
      );
    }
  }
}
