"""Generate a Pickle Rick cellular-automata avatar from a procedural seed."""

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


SIZE = 151
BACKGROUND = (4, 16, 18)
COLORS = {
    1: (115, 196, 66),
    2: (225, 244, 205),
    3: (24, 57, 38),
    4: (244, 237, 188),
    5: (173, 220, 77),
    6: (45, 108, 48),
}


def draw_seed():
    image = Image.new("L", (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((47, 9, 104, 141), radius=27, fill=6)
    draw.rounded_rectangle((50, 12, 101, 138), radius=24, fill=1)

    for box in ((57, 42, 75, 61), (78, 41, 97, 61)):
        draw.ellipse(box, fill=2)
    draw.ellipse((64, 49, 70, 57), fill=3)
    draw.ellipse((84, 48, 90, 56), fill=3)

    draw.line((56, 38, 73, 42), fill=3, width=4)
    draw.line((77, 42, 98, 37), fill=3, width=4)
    draw.line((73, 41, 78, 41), fill=3, width=3)

    draw.ellipse((57, 72, 95, 104), fill=3)
    draw.rectangle((61, 77, 91, 83), fill=4)
    draw.rectangle((64, 94, 89, 99), fill=4)
    for x in (68, 77, 86):
        draw.line((x, 77, x - 1, 83), fill=3, width=1)
    draw.arc((60, 68, 93, 91), 190, 345, fill=5, width=2)

    draw.arc((52, 55, 65, 72), 80, 240, fill=3, width=2)
    draw.arc((91, 54, 101, 73), 285, 100, fill=3, width=2)
    draw.arc((61, 103, 91, 121), 8, 170, fill=6, width=2)

    for x, y, r in ((57, 24, 3), (91, 27, 2), (55, 113, 3), (94, 122, 3), (77, 18, 2), (52, 88, 2), (99, 69, 2)):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=5)

    states = np.asarray(image, dtype=np.uint8).copy()
    for angle in range(0, 360, 30):
        radius = 63 + (angle // 30 % 3) * 3
        x = round(75 + math.cos(math.radians(angle)) * radius)
        y = round(75 + math.sin(math.radians(angle)) * radius)
        if 1 <= x < SIZE - 1 and 1 <= y < SIZE - 1:
            states[y, x] = 5 if angle % 60 else 1
    return states


def step(states):
    padded = np.pad(states, 1)
    next_states = states.copy()
    for row in range(SIZE):
        side = 1 if row % 2 else -1
        offsets = ((-1, 0), (1, 0), (0, -1), (side, -1), (0, 1), (side, 1))
        empty_columns = np.flatnonzero(states[row] == 0)
        for col in empty_columns:
            neighbours = []
            for dx, dy in offsets:
                value = padded[row + dy + 1, col + dx + 1]
                if value:
                    neighbours.append(int(value))
            if len(neighbours) == 1:
                next_states[row, col] = neighbours[0]
            elif len(neighbours) == 2 and neighbours[0] == neighbours[1]:
                next_states[row, col] = neighbours[0]
    return next_states


def evolve(seed, generations):
    states = seed.copy()
    born = np.full(states.shape, -1, dtype=np.int16)
    born[states != 0] = 0
    frames = [(states.copy(), born.copy())]
    for generation in range(1, generations + 1):
        next_states = step(states)
        born[(states == 0) & (next_states != 0)] = generation
        states = next_states
        frames.append((states.copy(), born.copy()))
    return frames


def blend(color, accent, amount):
    return tuple(round(channel * (1 - amount) + other * amount) for channel, other in zip(color, accent))


def render(states, born, output, pixels=1024):
    image = Image.new("RGB", (pixels, pixels), BACKGROUND)
    draw = ImageDraw.Draw(image)
    margin = pixels * 0.045
    scale = (pixels - margin * 2) / (SIZE * 1.55)
    center = (SIZE - 1) / 2
    for row, col in zip(*np.nonzero(states)):
        state = int(states[row, col])
        generation = int(born[row, col])
        color = COLORS[state]
        if generation:
            color = blend(color, (99, 234, 196) if generation % 2 else (250, 179, 65), 0.42)
        x = pixels / 2 + (col - center + 0.5 * (row & 1)) * math.sqrt(3) * scale
        y = pixels / 2 + (row - center) * 1.5 * scale
        points = []
        for vertex in range(6):
            angle = math.pi / 3 * vertex + math.pi / 6
            points.append((x + math.cos(angle) * scale * 0.95, y + math.sin(angle) * scale * 0.95))
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
    parser.add_argument("--output", default="nca-runs/pickle-rick-ca")
    parser.add_argument("--generation", type=int, default=4)
    args = parser.parse_args()
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)

    frames = evolve(draw_seed(), max(args.generation, 6))
    paths = []
    for generation in range(7):
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
