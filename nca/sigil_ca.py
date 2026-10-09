"""Grow a deterministic personal sigil with the studio's hexagonal CA geometry."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from portrait_ca import SIZE, evolve


def line(seed, start, end, spacing=3):
    x0, y0 = start
    x1, y1 = end
    distance = max(abs(x1 - x0), abs(y1 - y0))
    for step in range(0, distance + 1, spacing):
        amount = step / max(distance, 1)
        x = round(x0 + (x1 - x0) * amount)
        y = round(y0 + (y1 - y0) * amount)
        seed[y, x] = 1


def make_seed():
    seed = np.zeros((SIZE, SIZE), dtype=np.uint8)
    line(seed, (53, 35), (53, 115), 3)
    line(seed, (53, 75), (101, 34), 3)
    line(seed, (53, 75), (105, 117), 3)

    center = (SIZE - 1) / 2
    y, x = np.indices((SIZE, SIZE))
    radius = np.hypot(x - center, y - center)
    spokes = ((radius > 58) & (radius < 59.4) & (((x + 2 * y) % 11) == 0))
    seed[spokes] = 1
    return seed


def render(cells, born, output, pixels=1024):
    image = Image.new("RGB", (pixels, pixels), (4, 13, 18))
    draw = ImageDraw.Draw(image)
    colors = ((237, 255, 246), (78, 230, 200), (25, 154, 180), (247, 170, 68), (132, 107, 246))
    margin = pixels * 0.055
    unit = (pixels - margin * 2) / SIZE
    radius = unit * 0.45
    for row, col in zip(*np.nonzero(cells)):
        generation = int(born[row, col])
        color = colors[generation % len(colors)]
        x = margin + (col + 0.5 + 0.5 * (row & 1)) * unit
        y = margin + (row + 0.5) * unit
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    image.save(output)


def sheet(paths, output):
    tile = 512
    image = Image.new("RGB", (tile * 2, tile * 2), (4, 13, 18))
    for index, path in enumerate(paths):
        specimen = Image.open(path).resize((tile, tile), Image.Resampling.LANCZOS)
        image.paste(specimen, ((index % 2) * tile, (index // 2) * tile))
    image.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="nca-runs/kefas-sigil")
    parser.add_argument("--rule", default="B1/S0123456")
    parser.add_argument("--generation", type=int, default=14)
    args = parser.parse_args()
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)

    seed = make_seed()
    paths = []
    for generation in range(18):
        cells, born = evolve(seed, args.rule, generation)
        path = destination / f"sigil-g{generation:02}.png"
        render(cells, born, path)
        if generation in (8, 11, 14, 17):
            paths.append(path)
        if generation == args.generation:
            Image.open(path).save(destination / "avatar.png")
    sheet(paths, destination / "generations.png")
    print(destination / "avatar.png")
    print(destination / "generations.png")


if __name__ == "__main__":
    main()
