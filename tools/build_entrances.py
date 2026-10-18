"""
Wejścia na styku łuków podkowy z trybuną główną (zdjecia/wejscia_na_trybune, trapez-murpng.png,
brama_od_luku_na_polnocy.jpg, sektor_gosci_od_bramy.jpg, il20250305_898037691/963/021).
Od końca trybuny w stronę łuku:
- schody z placu: biegi rozdzielone betonowymi policzkami z żółtymi poręczami, 4 stopnie, półpodest,
  10 stopni, żółte krawędzie stopni; na szczycie (2.4 m) żółta brama z siatką i baner „… WITA!”;
  za bramą podest i krótki bieg w górę na promenadę sektora dolnego (3.2 m);
- przejazd na poziomie placu wzdłuż czopu ku boisku: żółta brama wjazdowa, przy czopie furtka;
- czop: trójkątna żelbetowa ściana zamykająca koniec łuku (od gruntu przy boisku wzdłuż stopni do korony,
  dalej w dół skarpy), szara barierka na szczycie, turkusowy cokół od strony przejazdu;
- na placu: na północy dwie otwarte bramy wjazdowe (898037691), na południu ogrodzenie z siatki
  z żółtymi bramami i przerwą na kołowrotki (kołowrotków w modelu brak).
Szczyty trybuny (przeszklenia, budynki, banery na ścianach): build_grandstand.build_gables.
Układ świata Blendera: X na wschód, Y na północ; trybuna główna po zachodniej stronie (X < -45).
"""

import bpy
import bmesh
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_grandstand import (  # noqa: E402
    _beam, _box, _extrude_profile, _finish, _rail, make_alpha_material, setup_pbr_nodes, TEXTURES_DIR,
    LOWER_X0, LOWER_DX, LOWER_ROWS, CONCOURSE_Z, CONCOURSE_X1,
)
from build_horseshoe_bowl import (  # noqa: E402
    _arc_point, _finish_mesh, R_TRACK_OUT, FRONT_WALK, STAND_DEPTH, STAND_H, BOWL_ANGLE_N, BOWL_ANGLE_S, STRAIGHT_L,
)

PLUG_T = 0.5                            # grubość czopu
PLUG_TOP = (0.0, STAND_H + 0.4)         # wysokość górnej krawędzi czopu: przy ogrodzeniu boiska, nad koroną
PLUG_CROWN = FRONT_WALK + STAND_DEPTH   # odległość korony od ogrodzenia boiska
PLUG_BACK = PLUG_CROWN + 5.0            # stopa tylnej skarpy wału (jak w build_bowl)
PLUG_BAND = 1.5                         # turkusowy cokół od strony przejazdu

GATE_X = -57.0                          # szczyt schodów i brama (X świata)
GATE_Z = 2.4
STEPS_LOW, STEPS_UP = 4, 10
STAIR_TREAD, MID_LANDING = 0.32, 1.5
SHORT_STEPS = 5                         # krótki bieg z podestu bramy na promenadę
CHEEK_W, CHEEK_H = 0.3, 0.35            # policzki biegów: szerokość, wysokość ponad linią stopni
GATE_H, BANNER_W, BANNER_Z = 2.4, 7.0, (2.85, 3.95)
FENCE_H = 2.2                           # ogrodzenie z siatki na placu
# Odcinki w poprzek luki, w metrach od końca trybuny w stronę łuku
SIDES = {
    'N': dict(s=1, flights=3, gate_leaves=4, stairs=(0.3, 7.5), passage_gate=(7.7, 11.5), door=(11.6, 12.4),
              banner="baner_lks_wita.png", plaza_gates=[(-66.0, (0.8, 3.8)), (-66.0, (10.0, 14.0))]),
    'S': dict(s=-1, flights=2, gate_leaves=2, stairs=(0.3, 6.3), passage_gate=(6.5, 10.5), door=None,
              banner="baner_lks_wita_poludnie.png", plaza_fence=(-65.5, 18.0),
              fence_gates=[((0.5, 2.9), 2), ((11.6, 12.8), 1)], fence_gaps=[(3.0, 4.3)]),
}


def _materials():
    def textured(name, tex):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.node_tree.nodes.get("Principled BSDF").inputs['Roughness'].default_value = 0.8
        setup_pbr_nodes(m, os.path.join(TEXTURES_DIR, tex))
        return m
    out = {'gate_mesh': make_alpha_material("Mat_Fence_Brama_Siatka", os.path.join(TEXTURES_DIR, "brama_siatka.png"), 0.5)}
    for side in SIDES.values():
        out[side['banner']] = textured("Mat_Baner_" + side['banner'][:-4], side['banner'])
    return out


def _quad(bm, uv, corners):
    """Czworokąt [(x, y, z, u, v)]; lico po stronie, z której obieg jest przeciwny do ruchu wskazówek."""
    face = bm.faces.new([bm.verts.new(c[:3]) for c in corners])
    for loop, c in zip(face.loops, corners):
        loop[uv].uv = c[3:]


def _plug_frame(s):
    """Czop łuku s: punkt w odległości d od ogrodzenia boiska, przesunięty o off ku trybunie głównej."""
    ang = BOWL_ANGLE_N if s > 0 else -BOWL_ANGLE_S
    (ux, uy), a = _arc_point(1.0, ang, 0.0)
    cy = s * STRAIGHT_L / 2
    t = (-math.sin(a) * s, math.cos(a) * s)
    return lambda d, off=0.0: (ux * (R_TRACK_OUT + d) + t[0] * off, cy + uy * (R_TRACK_OUT + d) + t[1] * off)


def _plug_top(d):
    """Górna krawędź czopu: od gruntu przy ogrodzeniu boiska do korony, dalej w dół skarpy."""
    if d <= PLUG_CROWN:
        return PLUG_TOP[0] + (PLUG_TOP[1] - PLUG_TOP[0]) * d / PLUG_CROWN
    return PLUG_TOP[1] * (PLUG_BACK - d) / (PLUG_BACK - PLUG_CROWN)


def _plug(bm_c, bm_m, bm_t, s):
    p = _plug_frame(s)
    prof = [(0.0, 0.0), (PLUG_CROWN, _plug_top(PLUG_CROWN)), (PLUG_BACK, 0.0)]
    vi = [bm_c.verts.new((*p(d, -0.05), z)) for d, z in prof]
    vo = [bm_c.verts.new((*p(d, PLUG_T), z)) for d, z in prof]
    for i in range(3):
        bm_c.faces.new([vi[i], vi[(i + 1) % 3], vo[(i + 1) % 3], vo[i]])
    bm_c.faces.new(vi[::-1])
    bm_c.faces.new(vo)

    # Szara barierka na szczycie (poręcz 1 m nad krawędzią, słupki co ~2 m)
    k = round(PLUG_CROWN / 2.0)
    top = [(*p(PLUG_CROWN * j / k, PLUG_T / 2), _plug_top(PLUG_CROWN * j / k)) for j in range(k + 1)]
    for (xa, ya, za), (xb, yb, zb) in zip(top, top[1:]):
        _beam(bm_m, (xa, ya, za + 1.0), (xb, yb, zb + 1.0), 0.05, 0.05)
    for x, y, z in top:
        _beam(bm_m, (x, y, z), (x, y, z + 1.0), 0.05, 0.05)

    # Turkusowy cokół na licu od strony przejazdu: do PLUG_BAND, przy boisku i na skarpie niżej (pod krawędzią)
    d_front = PLUG_BAND * PLUG_CROWN / (PLUG_TOP[1] - PLUG_TOP[0])
    d_back = PLUG_BACK - PLUG_BAND * (PLUG_BACK - PLUG_CROWN) / PLUG_TOP[1]
    band = [(0.0, 0.0), (PLUG_BACK, 0.0), (d_back, PLUG_BAND), (d_front, PLUG_BAND)]
    if s > 0:
        band = band[::-1]                                  # lico ku trybunie (bez przeliczania normalnych)
    bm_t.faces.new([bm_t.verts.new((*p(d, PLUG_T + 0.01), z)) for d, z in band])


def _leaf(bm_y, bm_mesh, uv, hinge, direction, length, z0, height):
    """Skrzydło bramy: żółta rama i siatka (dwie ściany: kolizje są jednostronne). direction: wektor (dx, dy)."""
    hx, hy = hinge
    ex, ey = hx + direction[0] * length, hy + direction[1] * length
    nx, ny = -direction[1] * 0.02, direction[0] * 0.02
    for sgn in (-1, 1):
        c = [(hx + sgn * nx, hy + sgn * ny, z0 + 0.1, 0.0, 0.1), (ex + sgn * nx, ey + sgn * ny, z0 + 0.1, length, 0.1),
             (ex + sgn * nx, ey + sgn * ny, z0 + height, length, height), (hx + sgn * nx, hy + sgn * ny, z0 + height, 0.0, height)]
        _quad(bm_mesh, uv, c if sgn < 0 else c[::-1])
    for z in (z0 + 0.1, z0 + height):
        _beam(bm_y, (hx, hy, z), (ex, ey, z), 0.05, 0.05)
    for x, y in ((hx, hy), (ex, ey)):
        _beam(bm_y, (x, y, z0 + 0.1), (x, y, z0 + height), 0.05, 0.05)


def _gate(bm_y, bm_mesh, uv, x, ya, yb, z0, height, leaves, open_dir=None):
    """Brama w poprzek osi Y na X = x: słupy i skrzydła; open_dir = ±1 obraca skrzydła o 90° ku ±X."""
    w = (yb - ya) / leaves
    for k in range(leaves + 1):
        y = ya + k * w
        _box(bm_y, x - 0.06, x + 0.06, y - 0.06, y + 0.06, z0, z0 + height + 0.1)
    for k in range(leaves):
        y0, y1 = ya + k * w + 0.08, ya + (k + 1) * w - 0.08
        if open_dir is None:
            _leaf(bm_y, bm_mesh, uv, (x, y0), (0.0, 1.0), y1 - y0, z0, height)
        else:
            hinge = y0 if k < leaves / 2 else y1          # skrzydła na zewnątrz: zawiasy przy skrajnych słupach
            _leaf(bm_y, bm_mesh, uv, (x, hinge), (open_dir, 0.0), y1 - y0, z0, height)


def _stairs(bm_s, bm_c, bm_y, s, side, end_y, front_x):
    """Schody z placu do bramy, podest bramy, krótki bieg na promenadę. Zwraca (y_a, y_b) schodów."""
    y0, y1 = (end_y + s * d for d in side['stairs'])
    ya, yb = min(y0, y1), max(y0, y1)
    rise = GATE_Z / (STEPS_LOW + STEPS_UP)
    x_mid1 = GATE_X - STEPS_UP * STAIR_TREAD
    x_mid0 = x_mid1 - MID_LANDING
    x_foot = x_mid0 - STEPS_LOW * STAIR_TREAD
    z_mid = STEPS_LOW * rise

    prof = [(GATE_X, 0.0)]
    for k in range(STEPS_UP):
        z = GATE_Z - k * rise
        prof += [(GATE_X - k * STAIR_TREAD, z), (GATE_X - (k + 1) * STAIR_TREAD, z)]
    prof += [(x_mid1, z_mid)]
    for k in range(STEPS_LOW):
        z = z_mid - k * rise
        prof += [(x_mid0 - k * STAIR_TREAD, z), (x_mid0 - (k + 1) * STAIR_TREAD, z)]
    prof += [(x_foot, 0.0)]
    _extrude_profile(bm_s, prof, ya, yb)
    for (xa, za), (xb, zb) in zip(prof[1:], prof[2:]):     # żółte krawędzie stopni na uskokach
        if abs(xa - xb) < 1e-6 and zb < za - 1e-6:
            _box(bm_y, xa, xa + 0.06, ya, yb, za, za + 0.008)

    line = [(x_foot, 0.0), (x_mid0, z_mid), (x_mid1, z_mid), (GATE_X, GATE_Z)]
    cheek = [(x_foot, 0.0)] + [(x, z + CHEEK_H) for x, z in line] + [(GATE_X, 0.0)]
    n = side['flights']
    for k in range(n + 1):
        yc = ya + CHEEK_W / 2 + k * (yb - ya - CHEEK_W) / n
        _extrude_profile(bm_c, cheek, yc - CHEEK_W / 2, yc + CHEEK_W / 2)
        rail = [(x, z + CHEEK_H + 0.9) for x, z in line]
        for (xa, za), (xb, zb) in zip(rail, rail[1:]):
            _beam(bm_y, (xa, yc, za), (xb, yc, zb), 0.05, 0.05)
        for x, z in line:
            _beam(bm_y, (x, yc, z + CHEEK_H), (x, yc, z + CHEEK_H + 0.9), 0.05, 0.05)

    # Podest bramy (GATE_Z) aż pod tylną krawędź promenady; przy końcu trybuny krótki bieg na wąski
    # podest promenady (CONCOURSE_Z), który przylega do jej końca
    x_prom_back = front_x - CONCOURSE_X1
    x_prom_front = front_x - (LOWER_X0 + (LOWER_ROWS - 1) * LOWER_DX)
    x_land = x_prom_back + 2.6
    _box(bm_s, GATE_X, x_land, ya, yb, 0.0, GATE_Z)
    sa, sb = sorted((end_y + s * 0.3, end_y + s * 3.3))
    x_short = x_land - SHORT_STEPS * STAIR_TREAD
    srise = (CONCOURSE_Z - GATE_Z) / SHORT_STEPS
    short = [(x_short, GATE_Z - 0.01)]
    for k in range(SHORT_STEPS):
        short += [(x_short + k * STAIR_TREAD, GATE_Z + (k + 1) * srise), (x_short + (k + 1) * STAIR_TREAD, GATE_Z + (k + 1) * srise)]
    short += [(x_prom_front, CONCOURSE_Z), (x_prom_front, 0.0), (x_land, 0.0), (x_land, GATE_Z - 0.01)]
    _extrude_profile(bm_s, short, sa, sb)
    # Poręcze podestu: od strony przejazdu i na krawędzi nad placem przy krótkim biegu
    y_edge = yb - 0.05 if s > 0 else ya + 0.05
    _rail(bm_y, (GATE_X + 0.1, y_edge, GATE_Z), (x_land - 0.05, y_edge, GATE_Z), 1.8)
    y_short = sb + 0.05 if s > 0 else sa - 0.05
    _rail(bm_y, (x_land - 0.05, y_short, GATE_Z), (x_land - 0.05, y_edge, GATE_Z), 1.8)
    return ya, yb


def _banner(bm_y, bm_b, uv, x, ya, yb):
    """Baner na ramie nad bramą: lico na zachód (ku wchodzącym), tył bez nadruku."""
    z0 = GATE_Z
    yc = (ya + yb) / 2
    b0, b1 = yc - BANNER_W / 2, yc + BANNER_W / 2
    for y in (b0 - 0.1, b1 + 0.1):
        _box(bm_y, x - 0.05, x + 0.05, y - 0.05, y + 0.05, z0 + GATE_H, z0 + BANNER_Z[1] + 0.1)
    _box(bm_y, x - 0.03, x + 0.03, b0 - 0.1, b1 + 0.1, z0 + BANNER_Z[1] + 0.05, z0 + BANNER_Z[1] + 0.1)
    za, zb = z0 + BANNER_Z[0], z0 + BANNER_Z[1]
    _quad(bm_b, uv, [(x - 0.03, b1, za, 0.0, 0.0), (x - 0.03, b0, za, 1.0, 0.0),
                     (x - 0.03, b0, zb, 1.0, 1.0), (x - 0.03, b1, zb, 0.0, 1.0)])
    _quad(bm_b, uv, [(x + 0.03, b0, za, 0.002, 0.5), (x + 0.03, b1, za, 0.002, 0.5),
                     (x + 0.03, b1, zb, 0.002, 0.5), (x + 0.03, b0, zb, 0.002, 0.5)])


def _fence(bm_m, bm_mesh, uv, x, ya, yb):
    """Ogrodzenie z siatki na placu: panele między słupkami co ~2.5 m (dwie ściany)."""
    n = max(1, round((yb - ya) / 2.5))
    for k in range(n):
        y0, y1 = ya + k * (yb - ya) / n, ya + (k + 1) * (yb - ya) / n
        for sgn in (-1, 1):
            c = [(x + sgn * 0.02, y0, 0.05, y0, 0.05), (x + sgn * 0.02, y1, 0.05, y1, 0.05),
                 (x + sgn * 0.02, y1, FENCE_H, y1, FENCE_H), (x + sgn * 0.02, y0, FENCE_H, y0, FENCE_H)]
            _quad(bm_mesh, uv, c if sgn > 0 else c[::-1])
    for k in range(n + 1):
        y = ya + k * (yb - ya) / n
        _box(bm_m, x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, FENCE_H + 0.05)
    _beam(bm_m, (x, ya, FENCE_H), (x, yb, FENCE_H), 0.04, 0.04)


def build_entrances(col, mats, front_x, north_y, south_y):
    """front_x: X czoła trybuny głównej; north_y, south_y: Y jej końców."""
    m = _materials()
    bm_c, bm_s, bm_y, bm_m, bm_t = (bmesh.new() for _ in range(5))
    bm_mesh = bmesh.new()
    uv = bm_mesh.loops.layers.uv.verify()
    banners = {}
    for key, end_y in (('N', north_y), ('S', south_y)):
        side = SIDES[key]
        s = side['s']
        span = lambda d0, d1: sorted((end_y + s * d0, end_y + s * d1))
        _plug(bm_c, bm_m, bm_t, s)
        ya, yb = _stairs(bm_s, bm_c, bm_y, s, side, end_y, front_x)
        _gate(bm_y, bm_mesh, uv, GATE_X, ya, yb, GATE_Z, GATE_H, side['gate_leaves'], open_dir=1)
        bm_b = banners.setdefault(side['banner'], bmesh.new())
        _banner(bm_y, bm_b, bm_b.loops.layers.uv.verify(), GATE_X, ya, yb)

        # Przejazd wzdłuż czopu: brama wjazdowa (skrzydła otwarte ku boisku) i furtka przy czopie
        _gate(bm_y, bm_mesh, uv, GATE_X, *span(*side['passage_gate']), 0.0, 2.6, 2, open_dir=1)
        if side['door']:
            _gate(bm_y, bm_mesh, uv, GATE_X, *span(*side['door']), 0.0, 2.6, 1)

        for x, (d0, d1) in side.get('plaza_gates', []):       # otwarte bramy wjazdowe na placu (północ)
            _gate(bm_y, bm_mesh, uv, x, *span(d0, d1), 0.0, 2.4, 2, open_dir=-1)
        if 'plaza_fence' in side:                             # ogrodzenie placu z bramami (południe)
            x, reach = side['plaza_fence']
            cuts = sorted([g for g, _ in side['fence_gates']] + side['fence_gaps'])
            d = 0.3
            for a, b in cuts + [(reach, reach)]:
                if a > d:
                    _fence(bm_m, bm_mesh, uv, x, *span(d, a))
                d = b
            for g, leaves in side['fence_gates']:
                _gate(bm_y, bm_mesh, uv, x, *span(*g), 0.0, FENCE_H, leaves)

    _finish(col, bm_c, "Wejscia_Czopy_i_Policzki", mats['concrete'])
    _finish(col, bm_s, "Wejscia_Schody_i_Podesty", mats['concrete_dark'])
    _finish(col, bm_y, "Wejscia_Barierki_i_Bramy", mats['yellow'])
    _finish(col, bm_m, "Wejscia_Barierki_Szare", mats['metal'])
    bm_t.normal_update()
    _finish_mesh(col, bm_t, "Wejscia_Czopy_Cokol", [mats['turquoise']])
    _finish(col, bm_mesh, "Wejscia_Bramy_Siatka", m['gate_mesh'])
    for tex, bm_b in banners.items():
        _finish(col, bm_b, "Wejscia_" + tex[:-4], m[tex])
