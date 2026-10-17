"""
Kalibracja ortofotomapy 2013 (zdjecia/ortofotomapa2013.png) do układu stadionu.
Układ stadionu: X — wschód (oś poprzeczna boiska), Y — północ (oś długa), metry, początek w środku boiska.
Wyprowadzenie wartości: docs/zrodla.md, sekcja „Kalibracja ortofotomapy”. Bez zależności (działa też w Blenderze).
"""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORTHO_PATH = os.path.join(ROOT, "zdjecia", "ortofotomapa2013.png")
ORTHO_SIZE_PX = (1432, 1226)

M_PER_PX = 0.2675                 # linie bramkowe (105 m) i szerokość pola karnego (40.32 m)
AXIS_DEG = 24.92                  # oś długa stadionu odchylona od północy na zachód (PCA płyty boiska)
PIVOT_PX = (605.3, 597.0)         # środek obrotu (centroid płyty) w pikselach oryginału
CENTER_ROT_PX = (604.5, 575.8 + 2.4 / M_PER_PX)  # środek boiska w obrazie obróconym o AXIS_DEG


def stadium_to_px(X, Y):
    """Punkt w układzie stadionu -> piksel oryginalnej ortofotomapy (x w prawo, y w dół)."""
    xr = CENTER_ROT_PX[0] + X / M_PER_PX
    yr = CENTER_ROT_PX[1] - Y / M_PER_PX
    a = math.radians(AXIS_DEG)
    dx, dy = xr - PIVOT_PX[0], yr - PIVOT_PX[1]
    return (PIVOT_PX[0] + dx * math.cos(a) + dy * math.sin(a),
            PIVOT_PX[1] - dx * math.sin(a) + dy * math.cos(a))


def px_to_stadium(px, py):
    """Odwrotność stadium_to_px."""
    a = math.radians(AXIS_DEG)
    dx, dy = px - PIVOT_PX[0], py - PIVOT_PX[1]
    xr = PIVOT_PX[0] + dx * math.cos(a) - dy * math.sin(a)
    yr = PIVOT_PX[1] + dx * math.sin(a) + dy * math.cos(a)
    return ((xr - CENTER_ROT_PX[0]) * M_PER_PX, (CENTER_ROT_PX[1] - yr) * M_PER_PX)
