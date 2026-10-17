"""
Wyznacza pozycje drzew z ortofotomapy 2013 (zdjecia/ortofotomapa2013.png) w układzie stadionu
i zapisuje je do tools/data/drzewa_ortofoto.json (wejście dla build_surroundings.py).

Układ stadionu: X — wschód (w osi poprzecznej boiska), Y — północ (w osi długiej), metry,
początek w środku boiska. Kalibracja: tools/ortho_calibration.py.

Uruchomienie: python3 tools/extract_trees_from_ortho.py  (wymaga Pillow i numpy)
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from PIL import Image

from ortho_calibration import ORTHO_PATH, ROOT, M_PER_PX, stadium_to_px

PX_PER_M = 1.0 / M_PER_PX
GRID_M = 8.0                     # rozstaw próbkowania (≈ średnica korony)
EXTENT_M = 260.0


def inside_stadium(X, Y):
    """Obrys stadionu (podkowa + trybuna główna) z marginesem — tam nie sadzimy drzew."""
    if -95.0 < X < 78.0 and abs(Y) < 75.0:
        return True
    cy = 42.0 if Y > 0 else -42.0
    return math.hypot(X, Y - cy) < 80.0 and X > -95.0


def main():
    img = np.asarray(Image.open(ORTHO_PATH).convert("RGB")).astype(float)
    h, w, _ = img.shape
    trees = []
    rng = np.random.default_rng(1969)
    steps = np.arange(-EXTENT_M, EXTENT_M + 0.1, GRID_M)
    for X in steps:
        for Y in steps:
            if inside_stadium(X, Y) or 76.0 < X < 205.0:  # aleja i tory bez drzew
                continue
            px, py = stadium_to_px(X, Y)
            r = int(round(GRID_M * PX_PER_M / 3))
            x0, y0 = int(px) - r, int(py) - r
            if x0 < 0 or y0 < 0 or x0 + 2 * r >= w or y0 + 2 * r >= h:
                continue
            patch = img[y0:y0 + 2 * r, x0:x0 + 2 * r].reshape(-1, 3)
            R, G, B = patch[:, 0], patch[:, 1], patch[:, 2]
            lum = patch.mean(1)
            # korona drzewa: ciemna zieleń lub głęboki cień zieleni (trawa jest jaśniejsza)
            canopy = ((G > R + 2) & (lum < 120)) | ((lum < 70) & (G >= R))
            if canopy.mean() > 0.45:
                jx, jy = rng.uniform(-GRID_M / 3, GRID_M / 3, 2)
                trees.append({
                    "x": round(float(X + jx), 2),
                    "y": round(float(Y + jy), 2),
                    "scale": round(float(rng.uniform(0.8, 1.25)), 2),
                })
    out = os.path.join(ROOT, "tools", "data", "drzewa_ortofoto.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({"source": "zdjecia/ortofotomapa2013.png", "trees": trees}, f, indent=1)
    print(f"Zapisano {len(trees)} drzew: {out}")


if __name__ == "__main__":
    main()
