"""Grow a Pickle Rick rat-suit avatar as a multi-state hexagonal automaton."""

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from pickle_ca import BACKGROUND, SIZE, blend, evolve


COLORS = {
    1: (111, 193, 61),
    2: (229, 244, 207),
    3: (22, 47, 34),
    4: (239, 230, 178),
    5: (105, 83, 67),
    6: (207, 188, 145),
    7: (167, 62, 61),
    8: (76, 121, 112),
}


def limb(draw, points, outer=11, inner=7):
    draw.line(points, fill=3, width=outer, joint="curve")
    draw.line(points, fill=5, width=inner, joint="curve")


def seed_image():
    image = Image.new("L", (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(image)

    draw.arc((16, 73, 137, 145), 350, 190, fill=7, width=3)

    limb(draw, ((61, 72), (42, 68), (27, 54), (18, 38)))
    limb(draw, ((89, 72), (109, 66), (124, 51), (135, 34)))
    limb(draw, ((65, 107), (52, 123), (43, 143)))
    limb(draw, ((85, 107), (99, 123), (111, 143)))

    for x, y in ((42, 68), (27, 54), (109, 66), (124, 51), (52, 123), (99, 123)):
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=7)
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=6)

    for points in (
        ((18, 38), (10, 30)), ((19, 39), (9, 38)), ((20, 40), (13, 47)),
        ((135, 34), (142, 25)), ((134, 35), (145, 34)), ((133, 36), (140, 45)),
        ((43, 143), (35, 149)), ((43, 143), (45, 150)),
        ((111, 143), (108, 150)), ((111, 143), (120, 149)),
    ):
        draw.line(points, fill=6, width=3)

    draw.rounded_rectangle((56, 16, 95, 116), radius=20, fill=3)
    draw.rounded_rectangle((59, 18, 92, 113), radius=17, fill=1)

    draw.ellipse((62, 39, 75, 54), fill=2)
    draw.ellipse((77, 39, 90, 54), fill=2)
    draw.ellipse((67, 44, 71, 50), fill=3)
    draw.ellipse((81, 44, 85, 50), fill=3)
    draw.line((61, 36, 74, 39), fill=3, width=3)
    draw.line((76, 39, 91, 35), fill=3, width=3)

    draw.ellipse((63, 62, 89, 84), fill=3)
    draw.rectangle((66, 66, 86, 71), fill=4)
    draw.rectangle((69, 78, 84, 81), fill=4)
    draw.arc((62, 57, 90, 74), 195, 345, fill=8, width=2)

    for y in (82, 91, 100):
        draw.arc((49, y - 8, 75, y + 9), 275, 80, fill=6, width=3)
        draw.arc((76, y - 8, 102, y + 9), 100, 265, fill=6, width=3)
    draw.line((53, 77, 53, 105), fill=8, width=3)
    draw.line((98, 77, 98, 105), fill=8, width=3)
    draw.rectangle((52, 103, 99, 109), fill=5)
    draw.line((58, 106, 93, 106), fill=6, width=2)

    for x, y, r in ((63, 25, 2), (85, 28, 2), (62, 91, 2), (88, 98, 2)):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=8)
    return np.asarray(image, dtype=np.uint8).copy()


def render(states, born, output, pixels=1024):
    image = Image.new("RGB", (pixels, pixels), BACKGROUND)
    draw = ImageDraw.Draw(image)
    margin = pixels * 0.04
    scale = (pixels - margin * 2) / (SIZE * 1.75)
    center = (SIZE - 1) / 2
    for row, col in zip(*np.nonzero(states)):
        state = int(states[row, col])
        generation = int(born[row, col])
        color = COLORS[state]
        if generation:
            accent = (91, 220, 187) if generation % 2 else (235, 155, 61)
            color = blend(color, accent, 0.34)
        x = pixels / 2 + (col - center + 0.5 * (row & 1)) * math.sqrt(3) * scale
        y = pixels / 2 + (row - center) * 1.5 * scale
        points = []
        for vertex in range(6):
            angle = math.pi / 3 * vertex + math.pi / 6
            points.append((x + math.cos(angle) * scale * 0.94, y + math.sin(angle) * scale * 0.94))
        draw.polygon(points, fill=color)
    image.save(output)


def sheet(paths, output):
    tile = 384
    image = Image.new("RGB", (tile * len(paths), tile), BACKGROUND)
    for index, path in enumerate(paths):
        frame = Image.open(path).resize((tile, tile), Image.Resampling.LANCZOS)
        image.paste(frame, (tile * index, 0))
    image.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="nca-runs/pickle-rat-ca")
    parser.add_argument("--generation", type=int, default=0)
    args = parser.parse_args()
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)

    frames = evolve(seed_image(), max(args.generation, 6))
    paths = []
    for generation in range(7):
        path = destination / f"growth-g{generation:02}.png"
        render(*frames[generation], path)
        if generation in (0, 2, 4, 6):
            paths.append(path)
    render(*frames[args.generation], destination / "avatar.png")
    sheet(paths, destination / "growth.png")
    print(destination / "avatar.png")
    print(destination / "growth.png")


if __name__ == "__main__":
    main()
