"""Grow a Millennium Falcon fan-art study as a multi-state hex automaton."""

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from pickle_ca import BACKGROUND, SIZE, blend, evolve


COLORS = {
    1: (177, 181, 169),
    2: (102, 110, 105),
    3: (36, 48, 49),
    4: (214, 202, 163),
    5: (138, 60, 49),
    6: (93, 224, 225),
    7: (42, 117, 132),
}


def seed_image():
    image = Image.new("L", (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(image)

    draw.ellipse((21, 35, 121, 137), fill=3)
    draw.ellipse((25, 39, 117, 133), fill=1)

    draw.polygon(((36, 62), (43, 8), (67, 8), (71, 67)), fill=3)
    draw.polygon(((40, 60), (47, 12), (63, 12), (67, 66)), fill=1)
    draw.polygon(((78, 67), (84, 8), (108, 8), (116, 61)), fill=3)
    draw.polygon(((82, 66), (88, 12), (104, 12), (112, 60)), fill=1)
    draw.polygon(((66, 4), (85, 4), (82, 48), (75, 63), (68, 48)), fill=0)

    draw.polygon(((108, 59), (132, 67), (139, 76), (132, 89), (108, 93)), fill=3)
    draw.polygon(((109, 64), (129, 70), (134, 76), (129, 85), (109, 89)), fill=1)
    draw.ellipse((127, 68, 142, 85), fill=2)
    draw.line((132, 72, 139, 76, 132, 82), fill=7, width=2)

    draw.arc((27, 42, 115, 132), 8, 172, fill=2, width=3)
    draw.arc((31, 47, 111, 128), 190, 350, fill=2, width=2)
    draw.ellipse((61, 67, 91, 97), outline=2, width=3)
    draw.ellipse((68, 74, 84, 90), fill=3)
    draw.ellipse((72, 78, 80, 86), fill=4)

    for x, y in ((48, 72), (57, 57), (93, 57), (104, 74), (50, 99), (99, 101)):
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=3)
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=2)

    draw.ellipse((42, 49, 62, 66), fill=3)
    draw.ellipse((45, 51, 59, 63), fill=4)
    draw.line((52, 57, 63, 73), fill=3, width=2)

    for points in (
        ((31, 81), (57, 82)), ((95, 82), (117, 79)), ((39, 109), (63, 96)),
        ((88, 96), (108, 113)), ((54, 44), (68, 59)), ((96, 43), (83, 61)),
        ((47, 16), (62, 16)), ((89, 17), (103, 17)), ((45, 30), (64, 30)),
        ((88, 31), (107, 31)),
    ):
        draw.line(points, fill=2, width=2)

    for box in ((31, 89, 39, 95), (111, 87, 117, 94), (69, 112, 78, 119), (86, 119, 94, 125)):
        draw.rectangle(box, fill=5)

    draw.arc((27, 39, 116, 134), 36, 144, fill=6, width=4)
    draw.arc((30, 43, 113, 130), 40, 140, fill=7, width=2)
    return np.asarray(image, dtype=np.uint8).copy()


def render(states, born, output, pixels=1024):
    image = Image.new("RGB", (pixels, pixels), BACKGROUND)
    draw = ImageDraw.Draw(image)
    margin = pixels * 0.045
    scale = (pixels - margin * 2) / (SIZE * 1.72)
    center = (SIZE - 1) / 2
    for row, col in zip(*np.nonzero(states)):
        state = int(states[row, col])
        generation = int(born[row, col])
        color = COLORS[state]
        if generation:
            accent = (77, 210, 200) if generation % 2 else (211, 133, 58)
            color = blend(color, accent, 0.32)
        x = pixels / 2 + (col - center + 0.5 * (row & 1)) * math.sqrt(3) * scale
        y = pixels / 2 + (row - center) * 1.5 * scale
        points = []
        for vertex in range(6):
            angle = math.pi / 3 * vertex + math.pi / 6
            points.append((x + math.cos(angle) * scale * 0.94, y + math.sin(angle) * scale * 0.94))
        draw.polygon(points, fill=color)
    image.save(output)


def make_sheet(paths, output):
    tile = 384
    sheet = Image.new("RGB", (tile * len(paths), tile), BACKGROUND)
    for index, path in enumerate(paths):
        frame = Image.open(path).resize((tile, tile), Image.Resampling.LANCZOS)
        sheet.paste(frame, (index * tile, 0))
    sheet.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="nca-runs/falcon-ca")
    parser.add_argument("--generation", type=int, default=2)
    args = parser.parse_args()
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)

    frames = evolve(seed_image(), max(args.generation, 8))
    paths = []
    for generation in range(9):
        path = destination / f"growth-g{generation:02}.png"
        render(*frames[generation], path)
        if generation in (0, 2, 4, 6):
            paths.append(path)
    render(*frames[args.generation], destination / "avatar.png")
    make_sheet(paths, destination / "growth.png")
    print(destination / "avatar.png")
    print(destination / "growth.png")


if __name__ == "__main__":
    main()
