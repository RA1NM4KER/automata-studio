"""Search bounded hexagonal B/S rules for nontrivial tiny-seed witnesses."""

import argparse
import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


SEEDS = {
    "hook-5": ((0, -1), (0, 0), (0, 1), (1, 1), (2, 1)),
    "kite-6": ((0, -2), (-1, -1), (0, -1), (1, -1), (0, 0), (0, 1)),
    "crooked-7": ((-1, -2), (0, -2), (0, -1), (0, 0), (1, 0), (1, 1), (2, 2)),
    "cup-8": ((-2, -1), (-2, 0), (-1, 1), (0, 1), (1, 1), (2, 0), (2, -1), (0, 0)),
    "spark-9": ((0, -2), (-1, -1), (0, -1), (2, -1), (-2, 0), (0, 0), (1, 0), (-1, 1), (1, 2)),
}


def add_walk_seeds(count=18, cells=9):
    generator = random.Random(20261008)
    for index in range(1, count + 1):
        pattern = {(0, 0)}
        while len(pattern) < cells:
            x, y = generator.choice(tuple(pattern))
            side = 1 if (75 + y) % 2 else -1
            dx, dy = generator.choice(((-1, 0), (1, 0), (0, -1), (side, -1), (0, 1), (side, 1)))
            pattern.add((x + dx, y + dy))
        SEEDS[f"walk-{index:02}"] = tuple(sorted(pattern, key=lambda point: (point[1], point[0])))


add_walk_seeds()


def neighbour_counts(cells):
    padded = np.pad(cells, ((0, 0), (1, 1), (1, 1)))
    total = padded[:, 1:-1, :-2] + padded[:, 1:-1, 2:] + padded[:, :-2, 1:-1] + padded[:, 2:, 1:-1]
    left = padded[:, :-2, :-2] + padded[:, 2:, :-2]
    right = padded[:, :-2, 2:] + padded[:, 2:, 2:]
    total[:, ::2] += left[:, ::2]
    total[:, 1::2] += right[:, 1::2]
    return total


def plant(pattern, size, copies=1):
    cells = np.zeros((copies, size, size), dtype=np.uint8)
    center = size // 2
    for x, y in pattern:
        cells[:, center + y, center + x] = 1
    return cells


def masks_to_rule(birth, survive):
    values = lambda mask: "".join(str(value) for value in range(7) if mask & (1 << value))
    return f"B{values(birth)}/S{values(survive)}"


def scout(pattern, size=43, steps=64, keep=180):
    birth = np.repeat(np.arange(1, 64, dtype=np.uint8) << 1, 128)
    survive = np.tile(np.arange(128, dtype=np.uint8), 63)
    cells = plant(pattern, size, len(birth))
    peak = np.full(len(birth), len(pattern), dtype=np.int32)
    late_change = np.zeros(len(birth), dtype=np.float32)

    for generation in range(1, steps + 1):
        total = neighbour_counts(cells)
        born = ((birth[:, None, None] >> total) & 1).astype(np.uint8)
        kept = ((survive[:, None, None] >> total) & 1).astype(np.uint8)
        next_cells = np.where(cells, kept, born).astype(np.uint8)
        changed = np.count_nonzero(next_cells != cells, axis=(1, 2))
        population = np.count_nonzero(next_cells, axis=(1, 2))
        peak = np.maximum(peak, population)
        if generation > steps - 12:
            late_change += changed
        cells = next_cells

    population = np.count_nonzero(cells, axis=(1, 2))
    boundary = np.any(cells[:, 0] | cells[:, -1] | cells[:, :, 0] | cells[:, :, -1], axis=1)
    density = population / (size * size)
    viable = (
        (population >= 18) & (population <= 620) & (peak >= len(pattern) * 3) &
        (late_change >= 12) & (density < 0.34) & ~boundary & (survive != 127)
    )
    score = np.log1p(population) * np.log1p(late_change) * (1 - density)
    indices = np.flatnonzero(viable)
    indices = indices[np.argsort(score[indices])[::-1][:keep]]
    return [(int(birth[index]), int(survive[index]), float(score[index])) for index in indices]


def single_counts(cells):
    return neighbour_counts(cells[None])[0]


def evaluate(pattern, birth, survive, size=151, steps=320):
    cells = plant(pattern, size)[0]
    born_at = np.full(cells.shape, -1, dtype=np.int16)
    born_at[cells == 1] = 0
    populations = [int(cells.sum())]
    changes = []
    seen = {cells.tobytes(): 0}
    period = None
    boundary_generation = None
    peak = populations[0]
    max_extent = 1
    centroids = []
    showcase = (0, cells.copy(), born_at.copy(), 0.0)

    for generation in range(1, steps + 1):
        total = single_counts(cells)
        next_cells = np.where(cells, (survive >> total) & 1, (birth >> total) & 1).astype(np.uint8)
        changed = int(np.count_nonzero(next_cells != cells))
        born_at[(next_cells == 1) & (cells == 0)] = generation
        born_at[next_cells == 0] = -1
        cells = next_cells
        population = int(cells.sum())
        populations.append(population)
        changes.append(changed)
        peak = max(peak, population)

        if population:
            rows, cols = np.nonzero(cells)
            width = int(cols.max() - cols.min() + 1)
            height = int(rows.max() - rows.min() + 1)
            max_extent = max(max_extent, width, height)
            centroids.append((float(cols.mean()), float(rows.mean())))
            density = population / (width * height)
            compact_penalty = 1 / (1 + max(0, population - 1400) / 300)
            visual = math.log1p(population) * math.log1p(changed) * (1 - abs(density - 0.32)) * compact_penalty
            if generation >= 12 and visual > showcase[3]:
                showcase = (generation, cells.copy(), born_at.copy(), visual)

        if cells[0].any() or cells[-1].any() or cells[:, 0].any() or cells[:, -1].any():
            boundary_generation = generation
            break
        state = cells.tobytes()
        if state in seen:
            period = generation - seen[state]
            break
        else:
            seen[state] = generation
        if population == 0:
            break

    lifetime = len(populations) - 1
    window = period if period else min(128, len(changes))
    late = changes[-window:] or [0]
    final_populations = populations[-window:] if window else populations[-1:]
    sustained = min(final_populations)
    late_activity = float(np.mean(late))
    distinct_populations = len(set(populations[-min(96, len(populations)) :]))
    displacement = 0.0
    if len(centroids) > 1:
        displacement = math.dist(centroids[0], centroids[-1])
    generation, frame, frame_born, visual = showcase
    effective_lifetime = steps if period and period > 1 else lifetime
    population_penalty = max(0, peak - 1600) * 0.12
    score = (
        min(effective_lifetime, steps) * 0.75 + math.log1p(min(peak, 1600)) * 20 +
        math.log1p(late_activity) * 9 + distinct_populations * 0.45 +
        math.log1p(visual) * 24 + min(displacement, 30) * 3 - population_penalty
    )
    if boundary_generation is not None:
        score -= 240
    if period == 1 or late_activity == 0:
        score -= 180
    if period and 1 < period <= 64:
        score += 180 + period * 2
    qualifies = boundary_generation is None and sustained >= 40 and late_activity >= 8 and peak <= 1800 and period != 1
    score = math.log1p(sustained) * 100 + math.log1p(late_activity) * 20 + min(period or 0, 64) if qualifies else -1
    generation, frame, frame_born = lifetime, cells.copy(), born_at.copy()
    return {
        "rule": masks_to_rule(birth, survive),
        "birthMask": birth,
        "surviveMask": survive,
        "lifetime": lifetime,
        "period": period,
        "cycleStart": lifetime - period if period else None,
        "sustainedPopulation": sustained,
        "finalPopulation": populations[-1],
        "qualifies": qualifies,
        "boundaryGeneration": boundary_generation,
        "peakPopulation": peak,
        "lateActivity": round(late_activity, 3),
        "distinctLatePopulations": distinct_populations,
        "maxExtent": max_extent,
        "centroidDisplacement": round(displacement, 3),
        "showcaseGeneration": generation,
        "showcasePopulation": int(frame.sum()),
        "score": round(score, 3),
        "cells": frame,
        "born": frame_born,
    }


def render(record, output, pixels=512):
    cells = record["cells"]
    born = record["born"]
    image = Image.new("RGB", (pixels, pixels), (5, 17, 22))
    draw = ImageDraw.Draw(image)
    rows, cols = np.nonzero(cells)
    extent = max(18, (abs(cols - 75) * math.sqrt(3)).max(initial=1), (abs(rows - 75) * 1.5).max(initial=1)) + 2
    scale = pixels * 0.43 / extent
    colors = ((232, 255, 245), (91, 226, 201), (43, 154, 174), (244, 163, 73))
    for row, col in zip(rows, cols):
        x = pixels / 2 + (col - 75 + 0.5 * (row & 1)) * math.sqrt(3) * scale
        y = pixels / 2 + (row - 75) * 1.5 * scale
        color = colors[(int(born[row, col]) // 8) % len(colors)]
        radius = max(1, scale * 0.88)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    image.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="search-runs/hex-001")
    parser.add_argument("--scout-steps", type=int, default=64)
    parser.add_argument("--full-steps", type=int, default=1024)
    parser.add_argument("--promote", type=int, default=180)
    parser.add_argument("--keep", type=int, default=16)
    args = parser.parse_args()
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)

    records = []
    for seed_name, pattern in SEEDS.items():
        candidates = scout(pattern, steps=args.scout_steps, keep=args.promote)
        print(f"{seed_name}: promoted {len(candidates)}", flush=True)
        for birth, survive, _ in candidates:
            record = evaluate(pattern, birth, survive, steps=args.full_steps)
            record["seed"] = seed_name
            record["pattern"] = [list(point) for point in pattern]
            records.append(record)

    records.sort(key=lambda record: record["score"], reverse=True)
    viable = [record for record in records if record["qualifies"]]
    selected = viable[: args.keep]
    all_portable = [{key: value for key, value in record.items() if key not in {"cells", "born", "birthMask", "surviveMask"}} for record in records]
    (destination / "all-discoveries.json").write_text(json.dumps(all_portable, indent=2) + "\n")
    portable = []
    for index, record in enumerate(selected, 1):
        identifier = f"hex-{index:02}"
        record["id"] = identifier
        render(record, destination / f"{identifier}.png")
        portable.append({key: value for key, value in record.items() if key not in {"cells", "born", "birthMask", "surviveMask"}})
    (destination / "discoveries.json").write_text(json.dumps(portable, indent=2) + "\n")
    print(destination / "discoveries.json")


if __name__ == "__main__":
    main()
