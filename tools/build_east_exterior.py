"""
Wschodnia strona stadionu od al. Unii Lubelskiej (zdjecia/alejaunii: Street View 2011, DSC01675, DSC01677):
- skarpa wału porośnięta suchą trawą od korony do muru (nad wejściami do tuneli Galery gołe betonowe skrzydła),
- niski szary mur z filarami wzdłuż chodnika, brama z herbem nad każdym tunelem, żółte barierki na chodniku,
- betonowy parapet na koronie z żółtą poręczą i wysokim ogrodzeniem z siatki (wysięgniki z drutem), maszty antenowe,
- płot betonowy ze sztachet, schody na koronę łuku północnego, żółta brama wjazdowa i kasy przy wejściu gości,
- trawnik za murem tam, gdzie łuki odchodzą od linii muru; rdzawe bandy i szafy przy masztach wschodnich.
Układ: X — wschód, Y — północ, metry, początek w środku boiska.
"""
import math
import os
import sys

import bmesh
import bpy
import mathutils

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_grandstand import setup_pbr_nodes, make_alpha_material, TEXTURES_DIR, _beam  # noqa: E402
from build_seats import seat_material  # noqa: E402
from build_horseshoe_bowl import (  # noqa: E402
    stadium_path, _obox, _finish_mesh, _row, _arc_point, STRAIGHT_L, R_TRACK_OUT, FRONT_WALK, STAND_DEPTH,
    STAND_BACK, STAND_H, STEP_D, NUM_STEPS, BOWL_ANGLE_N, BOWL_ANGLE_S, GALERA_TUNNELS, ABUT_SPAN_DEG,
    EAST_MAST_ANG, EAST_PAD_HALF_DEG,
)

CROWN_D = FRONT_WALK + STAND_DEPTH          # korona od ogrodzenia boiska
# Profil trawiastej skarpy: korona -> górna krawędź muru -> grunt (na prostej niżej zasłania go mur)
WALL_X, WALL_T, WALL_H = 75.4, 0.4, 2.5
SLOPE_PROFILE = [(CROWN_D, STAND_H), (WALL_X - R_TRACK_OUT, WALL_H + 0.2), (CROWN_D + 9.9, 0.0)]
SLOPE_TEX_M = 6.0                           # okres trawa_wal.png
WALL_END_Y = 56.0                           # mur kończy się przy kopcach masztów; dalej płot betonowy / siatka
FENCE_END_Y = 125.0
SIDEWALK_X = (WALL_X + WALL_T, 78.0)
SIDEWALK_TEX_M = 1.2
PICKET_FENCE_Y = (WALL_END_Y, 91.0)
NORTH_GATE_Y = (92.5, 98.5)
STAIRS_ANGLE, STAIRS_W = 38.0, 3.4          # schody na koronę łuku północnego (kąt od środka łuku)
STAIRS_RUN = 0.32
GATE_W, GATE_SIDE = 3.3, 1.4                # brama z herbem i boczne przejścia (żółte furtki)
PILLAR = 0.5
PARAPET_H, PARAPET_T = 0.9, 0.25
CROWN_FENCE_H = 2.2
POLE_EVERY, POLE_H = 12.0, 5.0              # cienkie maszty (anteny/flagi) wzdłuż korony Galery


def _materials(mats):
    def textured(name, tex, rough=0.9):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.node_tree.nodes.get("Principled BSDF").inputs['Roughness'].default_value = rough
        setup_pbr_nodes(m, os.path.join(TEXTURES_DIR, tex))
        return m
    grass = textured("Mat_Trawa_Wal", "trawa_wal.png", 0.97)
    return {
        'grass': grass,
        'wall': textured("Mat_Mur_Zewnetrzny", "mur_zewnetrzny.png"),
        'gate': textured("Mat_Brama_Al_Unii", "brama_al_unii.png", 0.7),
        'picket': textured("Mat_Plot_Betonowy", "plot_betonowy.png"),
        'paving': textured("Mat_Chodnik_Klinkier", "chodnik_klinkier.png"),
        'chain': make_alpha_material("Mat_Siatka_Korony", os.path.join(TEXTURES_DIR, "siatka_ogrodzeniowa.png"), 0.6),
        'rust': seat_material("Mat_Banda_Rdza", (0.40, 0.25, 0.09)),
        'white': seat_material("Mat_Szafa_Biala", (0.80, 0.80, 0.77)),
        'kiosk': seat_material("Mat_Kasa_Szara", (0.45, 0.50, 0.55)),
        'pavement_edge': mats['concrete_dark'],
    }


def _quad(bm, uv, corners, out):
    """Czworokąt [(x, y, z, u, v)] zwrócony licem w stronę out (wektor)."""
    face = bm.faces.new([bm.verts.new(c[:3]) for c in corners])
    for loop, c in zip(face.loops, corners):
        loop[uv].uv = c[3:]
    face.normal_update()
    if face.normal.dot(mathutils.Vector(out)) < 0:
        face.normal_flip()
    return face


def _in_gaps(y, gaps):
    return any(a <= y <= b for a, b in gaps)


def _east_pad_angle(ang):
    return abs(abs(ang) - EAST_MAST_ANG) < EAST_PAD_HALF_DEG


def _slope(col, m):
    """Skarpa z trawą: pas nad tylnym zboczem wału od korony do muru, przez Galerę i łuki (poza cokołami masztów)."""
    a_north, a_south = BOWL_ANGLE_N - ABUT_SPAN_DEG, -(BOWL_ANGLE_S - ABUT_SPAN_DEG)
    path = stadium_path(R_TRACK_OUT, a_north, a_south)
    gaps = [(a - 0.5, b + 0.5) for a, b in GALERA_TUNNELS]
    base_profile = SLOPE_PROFILE + [(CROWN_D + 5.0, 0.0)]       # zamknięcie od strony betonowego zbocza
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    rings, dist = [], 0.0
    for k, (px, py, nx, ny) in enumerate(path):
        if k:
            dist += math.hypot(px - path[k - 1][0], py - path[k - 1][1])
        # skarpa kończy się na linii muru i ogrodzenia (zbocze łuku nie wychodzi na chodnik)
        rings.append(([bm.verts.new((min(px + nx * d, WALL_X - 0.1), py + ny * d, z)) for d, z in base_profile], dist))

    def skipped(pa, pb):
        ang = math.degrees(math.atan2(pa[1] - (STRAIGHT_L / 2 if pa[1] > 0 else -STRAIGHT_L / 2), pa[0]))
        if abs(pa[3]) > 1e-6:
            return _east_pad_angle(ang)
        return _in_gaps(pa[1], gaps) or _in_gaps(pb[1], gaps)

    emit = [not skipped(pa, pb) for pa, pb in zip(path, path[1:])]
    caps = []
    for i, on in enumerate(emit):
        (ra, da), (rb, db) = rings[i], rings[i + 1]
        if on:
            t0 = 0.0
            for j in range(2):                                  # korona -> mur, mur -> grunt
                seg = math.hypot(SLOPE_PROFILE[j + 1][0] - SLOPE_PROFILE[j][0], SLOPE_PROFILE[j + 1][1] - SLOPE_PROFILE[j][1])
                f = bm.faces.new([ra[j], rb[j], rb[j + 1], ra[j + 1]])
                for loop, (u, v) in zip(f.loops, ((da, t0), (db, t0), (db, t0 + seg), (da, t0 + seg))):
                    loop[uv].uv = (u / SLOPE_TEX_M, v / SLOPE_TEX_M)
                t0 += seg
            if i == 0 or not emit[i - 1]:
                caps.append(rings[i])
            if i == len(emit) - 1 or not emit[i + 1]:
                caps.append(rings[i + 1])
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    for ring, dist_c in caps:                                   # ściany końcowe pasa: skarpa nie wisi nad betonem
        f = bm.faces.new(ring)
        for loop in f.loops:
            loop[uv].uv = (loop.vert.co.x / SLOPE_TEX_M, loop.vert.co.z / SLOPE_TEX_M)
    return _finish_mesh(col, bm, "Skarpa_Trawiasta", [m['grass']])


def _crown_fence(col, mats, m):
    """Parapet z żółtą poręczą, wysokie ogrodzenie z siatki z wysięgnikami i cienkie maszty na koronie."""
    a_north, a_south = BOWL_ANGLE_N - ABUT_SPAN_DEG - 0.5, -(BOWL_ANGLE_S - ABUT_SPAN_DEG - 0.5)
    path = stadium_path(STAND_BACK - 0.12, a_north, a_south, arc_step_deg=3.0)
    bm_c, bm_y, bm_post, bm_net = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    uv = bm_net.loops.layers.uv.verify()
    z0 = STAND_H
    pole_acc, post_acc = 0.0, 0.0
    for (x0, y0, nx0, ny0), (x1, y1, nx1, ny1) in zip(path, path[1:]):
        cy = STRAIGHT_L / 2 if y0 > 0 else -STRAIGHT_L / 2
        ang = math.degrees(math.atan2(y0 - cy, x0))
        if abs(ny0) > 1e-6 and _east_pad_angle(ang):
            continue
        seg = math.hypot(x1 - x0, y1 - y0)
        yaw = math.atan2(y1 - y0, x1 - x0)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        _obox(bm_c, (mx, my, z0 + PARAPET_H / 2), (PARAPET_T, seg + 0.02, PARAPET_H), yaw=yaw + math.pi / 2)
        # żółta poręcz nad parapetem, od strony zewnętrznej
        ox, oy = nx0 * 0.1, ny0 * 0.1
        _beam(bm_y, (x0 + ox, y0 + oy, z0 + PARAPET_H + 0.9), (x1 + ox, y1 + oy, z0 + PARAPET_H + 0.9), 0.04, 0.04)
        _beam(bm_y, (x0 + ox, y0 + oy, z0 + PARAPET_H + 0.45), (x1 + ox, y1 + oy, z0 + PARAPET_H + 0.45), 0.03, 0.03)
        # ogrodzenie z siatki 0.45 m za parapetem (od strony widowni); słupki co ~2.5 m, wysięgniki na zewnątrz
        ix, iy = -nx0 * 0.45, -ny0 * 0.45
        a, b = (x0 + ix, y0 + iy), (x1 + ix, y1 + iy)
        zb, zt = z0 + PARAPET_H, z0 + PARAPET_H + CROWN_FENCE_H
        for off in (0.0, 0.04):
            oa, ob = (a[0] - nx0 * off, a[1] - ny0 * off), (b[0] - nx1 * off, b[1] - ny1 * off)
            _quad(bm_net, uv, [(*oa, zb, 0, 0), (*ob, zb, seg / 0.5, 0), (*ob, zt, seg / 0.5, CROWN_FENCE_H / 0.5),
                               (*oa, zt, 0, CROWN_FENCE_H / 0.5)], (nx0 * (1 if off else -1), ny0 * (1 if off else -1), 0))
        post_acc += seg
        if post_acc >= 2.5 or not bm_post.verts:
            post_acc = 0.0
            _obox(bm_post, (*a, (zb + zt) / 2), (0.07, 0.07, CROWN_FENCE_H), yaw=yaw)
            _beam(bm_post, (a[0], a[1], zt), (a[0] + nx0 * 0.5, a[1] + ny0 * 0.5, zt + 0.35), 0.05, 0.05)
        pole_acc += seg
        if abs(ny0) < 1e-6 and pole_acc >= POLE_EVERY:
            pole_acc = 0.0
            _obox(bm_post, (x0 + 0.45, y0, z0 + POLE_H / 2), (0.05, 0.05, POLE_H))
    for bm in (bm_c, bm_y, bm_post):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _finish_mesh(col, bm_c, "Parapet_Korony", [mats['concrete']])
    _finish_mesh(col, bm_y, "Porecz_Korony", [mats['yellow']])
    _finish_mesh(col, bm_post, "Slupki_Korony", [mats['metal']])
    _finish_mesh(col, bm_net, "Siatka_Korony", [m['chain']])


def _wall_and_gates(col, mats, m):
    """Mur wzdłuż chodnika, bramy z herbem nad tunelami, chodnik z kostki i żółte barierki."""
    gate_centers = [(a + b) / 2 for a, b in GALERA_TUNNELS]
    half = GATE_W / 2 + PILLAR + GATE_SIDE + PILLAR
    gaps = [(c - half, c + half) for c in gate_centers]
    bm_w, bm_p, bm_g, bm_y, bm_cap = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    uv_w, uv_g = bm_w.loops.layers.uv.verify(), bm_g.loops.layers.uv.verify()
    x0, x1 = WALL_X, WALL_X + WALL_T
    # mur: odcinki między przerwami na bramy; szary, z filarami co ~6 m
    ys = sorted({-WALL_END_Y, WALL_END_Y, *(v for g in gaps for v in g)})
    for ya, yb in zip(ys, ys[1:]):
        if any(g[0] - 1e-6 <= ya and yb <= g[1] + 1e-6 for g in gaps):
            continue
        for xx, out in ((x1, (1, 0, 0)), (x0, (-1, 0, 0))):
            _quad(bm_w, uv_w, [(xx, ya, 0, ya / 4.0, 0), (xx, yb, 0, yb / 4.0, 0), (xx, yb, WALL_H, yb / 4.0, 1.0),
                               (xx, ya, WALL_H, ya / 4.0, 1.0)], out)
        _quad(bm_w, uv_w, [(x0, ya, WALL_H, ya / 4.0, 0), (x1, ya, WALL_H, ya / 4.0, 0.1), (x1, yb, WALL_H, yb / 4.0, 0.1),
                           (x0, yb, WALL_H, yb / 4.0, 0)], (0, 0, 1))
        for yy in (ya, yb):
            _quad(bm_w, uv_w, [(x0, yy, 0, 0, 0), (x1, yy, 0, 0.1, 0), (x1, yy, WALL_H, 0.1, 1), (x0, yy, WALL_H, 0, 1)],
                  (0, -1 if yy == ya else 1, 0))
        n = max(1, round((yb - ya) / 6.0))
        for k in range(1, n):
            _obox(bm_p, (x1 + 0.05, ya + (yb - ya) * k / n, WALL_H / 2), (0.1, 0.5, WALL_H))
    for c in gate_centers:
        # filary po obu stronach bramy (białe, z płytą), boczne przejścia z otwartą żółtą furtką
        for sgn in (-1, 1):
            for yy in (c + sgn * (GATE_W / 2 + PILLAR / 2), c + sgn * (GATE_W / 2 + PILLAR * 1.5 + GATE_SIDE)):
                _obox(bm_cap, ((x0 + x1) / 2, yy, WALL_H / 2 + 0.15), (0.7, PILLAR, WALL_H + 0.3))
                _obox(bm_cap, ((x0 + x1) / 2, yy, WALL_H + 0.35), (0.95, PILLAR + 0.25, 0.1))
            hinge = c + sgn * (GATE_W / 2 + PILLAR + 0.05)
            for i in range(8):                                       # otwarta furtka: skrzydło prostopadłe do muru
                _beam(bm_y, (x1 + 0.1 + i * 0.16, hinge, 0.1), (x1 + 0.1 + i * 0.16, hinge, 2.3), 0.035, 0.035)
            for zz in (0.15, 1.2, 2.3):
                _beam(bm_y, (x1 + 0.1, hinge, zz), (x1 + 0.1 + 1.28, hinge, zz), 0.04, 0.04)
        # brama z herbem: dwa skrzydła ze zdjęcia na jednej płaszczyźnie w osi muru; nadproże z wąskiego pasa muru
        for xx, out in ((x1 - 0.1, (1, 0, 0)), (x0 + 0.1, (-1, 0, 0))):
            ya, yb = c - GATE_W / 2, c + GATE_W / 2
            flip = out[0] < 0
            u0, u1 = (1.0, 0.0) if flip else (0.0, 1.0)
            _quad(bm_g, uv_g, [(xx, ya, 0.05, u0, 0), (xx, yb, 0.05, u1, 0), (xx, yb, WALL_H, u1, 1), (xx, ya, WALL_H, u0, 1)], out)
        _obox(bm_cap, ((x0 + x1) / 2, c, WALL_H + 0.05), (WALL_T, GATE_W, 0.1))
    # chodnik z kostki wzdłuż muru; barierki z rur przed bramami (słupki co 2 m, dwie poręcze)
    bm_s = bmesh.new()
    uv_s = bm_s.loops.layers.uv.verify()
    sx0, sx1 = SIDEWALK_X
    _quad(bm_s, uv_s, [(sx0, -FENCE_END_Y, 0.0, sx0 / SIDEWALK_TEX_M, -FENCE_END_Y / SIDEWALK_TEX_M),
                       (sx1, -FENCE_END_Y, 0.0, sx1 / SIDEWALK_TEX_M, -FENCE_END_Y / SIDEWALK_TEX_M),
                       (sx1, FENCE_END_Y, 0.0, sx1 / SIDEWALK_TEX_M, FENCE_END_Y / SIDEWALK_TEX_M),
                       (sx0, FENCE_END_Y, 0.0, sx0 / SIDEWALK_TEX_M, FENCE_END_Y / SIDEWALK_TEX_M)], (0, 0, 1))
    for c in gate_centers:
        rx = sx0 + 0.9
        for dy0, dy1 in ((-half - 1.0, half + 1.0),):
            n = round((dy1 - dy0) / 2.0)
            for zz in (0.45, 0.95):
                _beam(bm_y, (rx, c + dy0, zz), (rx, c + dy1, zz), 0.035, 0.035)
            for k in range(n + 1):
                yy = c + dy0 + (dy1 - dy0) * k / n
                _beam(bm_y, (rx, yy, 0.0), (rx, yy, 1.0), 0.04, 0.04)
    for bm in (bm_p, bm_y, bm_cap):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _finish_mesh(col, bm_w, "Mur_Zewnetrzny", [m['wall']])
    _finish_mesh(col, bm_p, "Mur_Filary", [m['wall']])
    _finish_mesh(col, bm_cap, "Bramy_Filary", [m['white']])
    _finish_mesh(col, bm_g, "Bramy_Skrzydla", [m['gate']])
    _finish_mesh(col, bm_y, "Bramy_Furtki_Barierki", [mats['yellow']])
    _finish_mesh(col, bm_s, "Chodnik_Al_Unii", [m['paving']])


def _north_entrance(col, mats, m):
    """Płot betonowy, kasy, żółta brama wjazdowa i siatka za nią (drzewa_schody_wejscie_trybuna_gosci_polnoc.png)."""
    bm_f, bm_post, bm_y, bm_k = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    uv = bm_f.loops.layers.uv.verify()
    x = WALL_X + 0.2
    ya, yb = PICKET_FENCE_Y
    h = 2.2
    n = round((yb - ya) / 2.5)
    for k in range(n):
        y0, y1 = ya + (yb - ya) * k / n, ya + (yb - ya) * (k + 1) / n
        for off, out in ((0.1, (1, 0, 0)), (-0.1, (-1, 0, 0))):
            _quad(bm_f, uv, [(x + off, y0, 0, 0, 0), (x + off, y1, 0, 1, 0), (x + off, y1, h, 1, 1), (x + off, y0, h, 0, 1)], out)
        _quad(bm_f, uv, [(x - 0.1, y0, h, 0, 1), (x + 0.1, y0, h, 0, 1), (x + 0.1, y1, h, 1, 1), (x - 0.1, y1, h, 1, 1)], (0, 0, 1))
    # kasy: dwie szare budki przy płocie przed schodami
    for yy in (ya + 8.0, ya + 10.0):
        _obox(bm_k, (x + 1.1, yy, 1.35), (1.2, 1.4, 2.7))
        _obox(bm_k, (x + 1.1, yy, 2.78), (1.5, 1.7, 0.12))
    # brama wjazdowa (żółte kraty, skrzydła otwarte do środka) i betonowe słupy; za nią siatka do końca placu
    g0, g1 = NORTH_GATE_Y
    for yy in (g0 - 0.3, (g0 + g1) / 2, g1 + 0.3):
        _obox(bm_post, (x, yy, 1.5), (0.5, 0.5, 3.0), yaw=0.0)
    for hinge, sgn in ((g0, 1), (g1, -1)):
        for i in range(10):
            xx = x - 0.4 - i * 0.28
            _beam(bm_y, (xx, hinge, 0.1), (xx, hinge, 2.1), 0.03, 0.03)
        for zz in (0.15, 1.1, 2.1):
            _beam(bm_y, (x - 0.4, hinge, zz), (x - 0.4 - 2.8, hinge, zz), 0.04, 0.04)
    ya2 = NORTH_GATE_Y[1] + 0.3
    for yy in [ya2 + 2.5 * k for k in range(int((FENCE_END_Y - ya2) / 2.5) + 1)]:
        _beam(bm_post, (x, yy, 0.0), (x, yy, 2.0), 0.06, 0.06)
    for zz in (0.3, 1.0, 2.0):
        _beam(bm_post, (x, ya2, zz), (x, FENCE_END_Y, zz), 0.03, 0.03)
    for bm in (bm_post, bm_y, bm_k):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _finish_mesh(col, bm_f, "Plot_Betonowy", [m['picket']])
    _finish_mesh(col, bm_k, "Kasy_Biletowe", [m['kiosk']])
    _finish_mesh(col, bm_post, "Brama_Wjazdowa_Slupy_Siatka", [mats['concrete']])
    _finish_mesh(col, bm_y, "Brama_Wjazdowa_Kraty", [mats['yellow']])
    # południe: za murem tylko siatka do końca placu
    bm_s = bmesh.new()
    for yy in [-WALL_END_Y - 2.5 * k for k in range(int((FENCE_END_Y - WALL_END_Y) / 2.5) + 1)]:
        _beam(bm_s, (x, yy, 0.0), (x, yy, 2.0), 0.06, 0.06)
    for zz in (0.3, 1.0, 2.0):
        _beam(bm_s, (x, -WALL_END_Y, zz), (x, -FENCE_END_Y, zz), 0.03, 0.03)
    bmesh.ops.recalc_face_normals(bm_s, faces=bm_s.faces)
    _finish_mesh(col, bm_s, "Siatka_Poludnie", [mats['concrete']])


def _stairs(col, mats, m):
    """Betonowe schody od trawnika na koronę łuku północnego, na skarpie, z żółtymi poręczami."""
    cy = STRAIGHT_L / 2
    yaw = math.radians(STAIRS_ANGLE)
    bm_s, bm_y = bmesh.new(), bmesh.new()

    def surface(d):
        for (d0, z0), (d1, z1) in zip(SLOPE_PROFILE, SLOPE_PROFILE[1:]):
            if d <= d1:
                return z0 + (z1 - z0) * (d - d0) / (d1 - d0)
        return 0.0

    d, i = CROWN_D, 0
    while surface(d) > 0.05:
        z = surface(d + STAIRS_RUN) + 0.04
        r = R_TRACK_OUT + d + STAIRS_RUN / 2
        (x, y), _ = _arc_point(r, STAIRS_ANGLE, cy)
        _obox(bm_s, (x, y, z / 2 - 0.1), (STAIRS_RUN + 0.02, STAIRS_W, z + 0.2), yaw=yaw)
        d += STAIRS_RUN
        i += 1
    d_end = d
    for side in (-1, 1):
        t = side * (STAIRS_W / 2 + 0.05)
        p0 = _arc_point(R_TRACK_OUT + CROWN_D - 0.5, STAIRS_ANGLE, cy)[0]
        p1 = _arc_point(R_TRACK_OUT + d_end, STAIRS_ANGLE, cy)[0]
        off = (-math.sin(yaw) * t, math.cos(yaw) * t)
        a = (p0[0] + off[0], p0[1] + off[1], surface(CROWN_D - 0.5) + 1.0)
        b = (p1[0] + off[0], p1[1] + off[1], 1.0)
        _beam(bm_y, a, b, 0.04, 0.04)
        _beam(bm_y, (a[0], a[1], a[2] - 0.45), (b[0], b[1], b[2] - 0.45), 0.03, 0.03)
        for k in range(0, 9):
            f = k / 8
            px, py = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            pz = a[2] + (b[2] - a[2]) * f
            _beam(bm_y, (px, py, pz - 1.0), (px, py, pz), 0.04, 0.04)
    for bm in (bm_s, bm_y):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _finish_mesh(col, bm_s, "Schody_Luk_Polnocny", [mats['concrete']])
    _finish_mesh(col, bm_y, "Schody_Luk_Polnocny_Poreczy", [mats['yellow']])


def _lawn(col, m):
    """Trawnik za murem tam, gdzie łuki odchodzą od linii muru: od okręgu u stopy skarpy do ogrodzenia."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    r = R_TRACK_OUT + CROWN_D + 9.9 - 0.2
    for sign in (1, -1):
        cy = sign * STRAIGHT_L / 2
        y0, y1 = WALL_END_Y - 6.0, FENCE_END_Y
        pts = []
        steps = 12
        for k in range(steps + 1):
            dy = (y0 - STRAIGHT_L / 2) + (y1 - y0) * k / steps
            pts.append((min(math.sqrt(max(r * r - dy * dy, 0.0)), WALL_X + 0.2), sign * (STRAIGHT_L / 2 + dy)))
        pts += [(WALL_X + 0.2, sign * y1), (WALL_X + 0.2, sign * y0)]
        c = mathutils.Vector((sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts), 0.0))
        vc = bm.verts.new((c.x, c.y, 0.0))
        vs = [bm.verts.new((px, py, 0.0)) for px, py in pts]
        for a, b in zip(vs, vs[1:] + vs[:1]):
            f = bm.faces.new([vc, a, b])
            for loop in f.loops:
                loop[uv].uv = (loop.vert.co.x / SLOPE_TEX_M, loop.vert.co.y / SLOPE_TEX_M)
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    _finish_mesh(col, bm, "Trawnik_Za_Murem", [m['grass']])


def _mast_fittings(col, mats, m):
    """Przy masztach wschodnich: rdzawe bandy na koronie Galery od strony muru i białe szafy przy podstawie."""
    bm_b, bm_p, bm_w = bmesh.new(), bmesh.new(), bmesh.new()
    for sign in (1, -1):
        for y0 in (26.0, 33.5):
            yc = sign * (y0 + 3.5)
            _obox(bm_b, (STAND_BACK - 0.5, yc, STAND_H + 2.4 + 0.9), (0.08, 7.0, 1.8))
            for dy in (-3.0, 3.0):
                _obox(bm_p, (STAND_BACK - 0.5, yc + dy, STAND_H + 1.5), (0.1, 0.1, 3.0))
        a = math.radians(sign * EAST_MAST_ANG)
        r = STAND_BACK + 3.6
        px, py = r * math.cos(a), sign * STRAIGHT_L / 2 + r * math.sin(a)
        for k, (dx, dy) in enumerate(((0.0, -1.3), (0.0, 0.2), (0.9, 1.5))):
            _obox(bm_w, (px + dx, py + dy, STAND_H + 0.95), (0.9, 1.0, 1.9 + 0.2 * (k % 2)))
    for bm in (bm_b, bm_p, bm_w):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _finish_mesh(col, bm_b, "Bandy_Rdzawe_Korona", [m['rust']])
    _finish_mesh(col, bm_p, "Bandy_Slupki_Korona", [mats['metal']])
    _finish_mesh(col, bm_w, "Szafy_Masztow", [m['white']])


def build_east_exterior(col, mats):
    m = _materials(mats)
    for obj in bpy.data.objects:                        # kopce pod masztami wschodnimi: ta sama sucha trawa co skarpa
        if obj.name.endswith("_Kopce"):
            obj.data.materials[0] = m['grass']
    _slope(col, m)
    _crown_fence(col, mats, m)
    _wall_and_gates(col, mats, m)
    _north_entrance(col, mats, m)
    _stairs(col, mats, m)
    _lawn(col, m)
    _mast_fittings(col, mats, m)
