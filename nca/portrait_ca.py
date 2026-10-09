"""Grow a deterministic cellular portrait from a local image-derived seed."""

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


SIZE = 151


def parse_rule(text):
    birth_text, survive_text = text.upper().split("/")
    if not birth_text.startswith("B") or not survive_text.startswith("S"):
        raise ValueError("rule must look like B2/S2345")
    birth = {int(value) for value in birth_text[1:]}
    survive = {int(value) for value in survive_text[1:]}
    if any(value < 0 or value > 6 for value in birth | survive):
        raise ValueError("hexagonal rules use neighbour counts from 0 to 6")
    return birth, survive


def image_seed(path):
    source = Image.open(path).convert("RGBA")
    alpha = source.getchannel("A").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    gray = ImageOps.grayscale(source).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    gray = ImageEnhance.Contrast(gray).enhance(1.22)
    values = np.asarray(gray, dtype=np.float32) / 255
    mask = np.asarray(alpha, dtype=np.float32) / 255

    edges = np.asarray(gray.filter(ImageFilter.FIND_EDGES), dtype=np.float32) / 255
    darkness = 1 - values
    density = np.clip(darkness * 0.92 + edges * 0.18 - 0.04, 0, 0.96) * mask

    y, x = np.indices((SIZE, SIZE))
    bayer = np.array([
        [0, 32, 8, 40, 2, 34, 10, 42],
        [48, 16, 56, 24, 50, 18, 58, 26],
        [12, 44, 4, 36, 14, 46, 6, 38],
        [60, 28, 52, 20, 62, 30, 54, 22],
        [3, 35, 11, 43, 1, 33, 9, 41],
        [51, 19, 59, 27, 49, 17, 57, 25],
        [15, 47, 7, 39, 13, 45, 5, 37],
        [63, 31, 55, 23, 61, 29, 53, 21],
    ], dtype=np.float32)
    threshold = (bayer[y % 8, x % 8] + 0.5) / 64
    cells = density > threshold

    center = (SIZE - 1) / 2
    radius = np.hypot(x - center, y - center)
    cells |= (radius > SIZE * 0.465) & (radius < SIZE * 0.475)
    return cells.astype(np.uint8), darkness


def step(cells, rule):
    birth, survive = parse_rule(rule)
    padded = np.pad(cells, 1)
    total = np.zeros_like(cells, dtype=np.uint8)
    for row in range(SIZE):
        side = 1 if row % 2 else -1
        offsets = ((-1, 0), (1, 0), (0, -1), (side, -1), (0, 1), (side, 1))
        for dx, dy in offsets:
            y0 = row + dy + 1
            x0 = 1 + dx
            total[row] += padded[y0, x0:x0 + SIZE]
    return np.where(cells, np.isin(total, tuple(survive)), np.isin(total, tuple(birth))).astype(np.uint8)


def evolve(seed, rule, generations):
    cells = seed.copy()
    born = np.full(cells.shape, -1, dtype=np.int16)
    born[cells == 1] = 0
    for generation in range(1, generations + 1):
        next_cells = step(cells, rule)
        born[(next_cells == 1) & (cells == 0)] = generation
        born[next_cells == 0] = -1
        cells = next_cells
    return cells, born


def render(cells, born, output, pixels=1024):
    background = (5, 17, 22)
    palette = ((94, 221, 201), (239, 255, 247), (45, 151, 173), (244, 163, 73))
    image = Image.new("RGB", (pixels, pixels), background)
    draw = ImageDraw.Draw(image)
    margin = pixels * 0.055
    cell = (pixels - margin * 2) / SIZE
    radius = max(1.2, cell * 0.43)
    for row, col in zip(*np.nonzero(cells)):
        generation = int(born[row, col])
        color = palette[generation % len(palette)]
        x = margin + (col + 0.5 + 0.5 * (row & 1)) * cell
        y = margin + (row + 0.5) * cell
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    image.save(output)


def similarity(cells, target):
    sample = Image.fromarray((cells * 255).astype(np.uint8)).resize((32, 32), Image.Resampling.BOX)
    candidate = np.asarray(sample, dtype=np.float32) / 255
    reference = np.asarray(Image.fromarray((target * 255).astype(np.uint8)).resize((32, 32), Image.Resampling.BOX), dtype=np.float32) / 255
    candidate = (candidate - candidate.mean()) / max(candidate.std(), 1e-6)
    reference = (reference - reference.mean()) / max(reference.std(), 1e-6)
    return float(np.mean(candidate * reference))


def contact_sheet(records, output):
    thumb = 320
    sheet = Image.new("RGB", (thumb * 4, thumb * math.ceil(len(records) / 4)), (8, 14, 18))
    draw = ImageDraw.Draw(sheet)
    for index, record in enumerate(records):
        image = Image.open(record[3]).resize((thumb, thumb), Image.Resampling.LANCZOS)
        x = index % 4 * thumb
        y = index // 4 * thumb
        sheet.paste(image, (x, y))
        draw.rectangle((x, y, x + thumb, y + 28), fill=(8, 14, 18))
        draw.text((x + 8, y + 7), f"{record[0]} g{record[1]}  score {record[2]:.3f}", fill=(235, 244, 240))
    sheet.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="nca-runs/portrait-ca")
    parser.add_argument("--rule", default="B1/S0123456")
    parser.add_argument("--generations", type=int, default=4)
    args = parser.parse_args()
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)

    seed, target = image_seed(args.input)
    rules = ("B1/S0123456", "B2/S0123456", "B12/S0123456", "B1/S123456", "B2/S123456", "B12/S123456")
    records = []
    for rule in rules:
        for generations in (1, 2, 3, 4):
            cells, born = evolve(seed, rule, generations)
            name = f"{rule.replace('/', '-')}-g{generations}.png"
            path = destination / name
            render(cells, born, path)
            records.append((rule, generations, similarity(cells, target), path))
    records.sort(key=lambda item: item[2], reverse=True)
    contact_sheet(records, destination / "candidates.png")
    selected = next((record for record in records if record[0] == args.rule and record[1] == args.generations), None)
    if selected is None:
        cells, born = evolve(seed, args.rule, args.generations)
        selected = (args.rule, args.generations, similarity(cells, target), destination / "selected.png")
        render(cells, born, selected[3])
    Image.open(selected[3]).save(destination / "avatar.png")
    print(f"selected {selected[0]} generation {selected[1]} score {selected[2]:.4f}")
    print(destination / "avatar.png")
    print(destination / "candidates.png")


if __name__ == "__main__":
    main()
