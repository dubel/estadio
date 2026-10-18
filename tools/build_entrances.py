"""
Wejścia na styku łuków podkowy z trybuną główną (zdjecia/wejscia_na_trybune, trapez-murpng.png):
- czop: żelbetowa ściana w kształcie trapezu zamykająca koniec łuku (górna krawędź prosto wzdłuż spadku
  stopni, żółta barierka na szczycie);
- między czopem a końcem trybuny podest na poziomie promenady sektora dolnego i szerokie schody z placu:
  trzy biegi rozdzielone betonowymi policzkami z żółtymi poręczami, półpodest, żółte krawędzie stopni;
- na szczycie schodów żółta brama z siatką (środkowe skrzydła otwarte) i baner „ŁÓDZKI KLUB SPORTOWY WITA!”
  (ten sam na obu wejściach: czytelny jest tylko na zdjęciu bramy północnej);
- przy wejściu południowym baner „MOSiR Łódź” na końcu trybuny i tablica z planem sektorów (DSC01679.jpg).
Układ świata Blendera: X na wschód, Y na północ; trybuna główna po zachodniej stronie (X < -45).
"""

import bpy
import bmesh
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_grandstand import (  # noqa: E402
    _beam, _box, _extrude_profile, _finish, make_alpha_material, setup_pbr_nodes, TEXTURES_DIR,
    LOWER_X0, LOWER_DX, LOWER_ROWS, CONCOURSE_Z, underside,
)
from build_horseshoe_bowl import (  # noqa: E402
    _arc_point, R_TRACK_OUT, FRONT_WALK, STAND_DEPTH, ROW0_H, STAND_H, BOWL_ANGLE, STRAIGHT_L,
)

PLUG_T = 0.5                            # grubość czopu
PLUG_PARAPET = 1.0                      # górna krawędź czopu ponad linią stopni
PLUG_BACK = FRONT_WALK + STAND_DEPTH + 5.0   # stopa tylnej skarpy wału (jak w build_bowl)

STAIR_W = 8.6                           # trzy biegi z policzkami
STAIR_TREAD = 0.32
UPPER_STEPS, LOWER_STEPS = 12, 7        # bieg górny od podestu, półpodest, bieg dolny do placu
MID_LANDING = 1.6
CHEEK_W, CHEEK_H = 0.3, 0.35            # policzki biegów: szerokość, wysokość ponad linią stopni
LANDING_BACK = 13.5                     # zachodnia krawędź podestu od czoła trybuny (szczyt schodów, brama)
GATE_H, GATE_LEAVES = 2.4, 4
BANNER_W, BANNER_Z = 7.3, (2.85, 3.95)  # baner nad bramą: szerokość, dół i góra ponad podestem
MOSIR_BANNER = (8.0, 4.0, 1.2)          # szerokość, wysokość, dół banera MOSiR nad terenem
MOSIR_X = 22.0                          # środek banera MOSiR od czoła trybuny (pod sektorem górnym)
MOSIR_WALL_X = (16.0, 28.0)             # biała ściana szczytowa pod sektorem górnym, na której wisi baner


def _materials():
    def textured(name, tex):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.node_tree.nodes.get("Principled BSDF").inputs['Roughness'].default_value = 0.8
        setup_pbr_nodes(m, os.path.join(TEXTURES_DIR, tex))
        return m
    return {
        'gate_mesh': make_alpha_material("Mat_Fence_Brama_Siatka", os.path.join(TEXTURES_DIR, "brama_siatka.png"), 0.5),
        'wita': textured("Mat_Baner_LKS_Wita", "baner_lks_wita.png"),
        'mosir': textured("Mat_Baner_MOSiR", "baner_mosir.png"),
        'plan': textured("Mat_Tablica_MOSiR_Plan", "tablica_mosir_plan.png"),
    }


def _decal(bm, uv, corners):
    """Czworokąt [(x, y, z, u, v)] w kolejności przeciwnej do ruchu wskazówek patrząc na lico."""
    face = bm.faces.new([bm.verts.new(c[:3]) for c in corners])
    for loop, c in zip(face.loops, corners):
        loop[uv].uv = c[3:]


def _plug(bm_c, bm_y, s):
    """Czop łuku: s = +1 północny (kąt BOWL_ANGLE), -1 południowy. Trapez w płaszczyźnie końca łuku."""
    ang = s * BOWL_ANGLE
    cy = s * STRAIGHT_L / 2
    (ux, uy), a = _arc_point(1.0, ang, 0.0)
    tx, ty = -math.sin(a) * s, math.cos(a) * s           # styczna ku trybunie głównej
    top0, top1 = ROW0_H + PLUG_PARAPET, STAND_H + PLUG_PARAPET
    prof = [(FRONT_WALK, 0.0), (FRONT_WALK, top0), (FRONT_WALK + STAND_DEPTH, top1), (PLUG_BACK, 0.4), (PLUG_BACK, 0.0)]
    pts = lambda off: [(ux * (R_TRACK_OUT + d) + tx * off, cy + uy * (R_TRACK_OUT + d) + ty * off, z) for d, z in prof]
    inner, outer = pts(-0.05), pts(PLUG_T)
    vi = [bm_c.verts.new(p) for p in inner]
    vo = [bm_c.verts.new(p) for p in outer]
    n = len(prof)
    for i in range(n):
        bm_c.faces.new([vi[i], vi[(i + 1) % n], vo[(i + 1) % n], vo[i]])
    bm_c.faces.new(vi[::-1])
    bm_c.faces.new(vo)

    # Barierka na szczycie: poręcz 1 m nad górną krawędzią, słupki co ~2 m
    mid = PLUG_T / 2
    p0 = (ux * (R_TRACK_OUT + FRONT_WALK) + tx * mid, cy + uy * (R_TRACK_OUT + FRONT_WALK) + ty * mid, top0)
    p1 = (ux * (R_TRACK_OUT + FRONT_WALK + STAND_DEPTH) + tx * mid, cy + uy * (R_TRACK_OUT + FRONT_WALK + STAND_DEPTH) + ty * mid, top1)
    _beam(bm_y, (p0[0], p0[1], p0[2] + 1.0), (p1[0], p1[1], p1[2] + 1.0))
    k = round(STAND_DEPTH / 2.0)
    for j in range(k + 1):
        t = j / k
        x, y, z = (p0[i] + t * (p1[i] - p0[i]) for i in range(3))
        _beam(bm_y, (x, y, z), (x, y, z + 1.0))


def _stairs(bm_s, bm_c, bm_y, s, front_x, end_y):
    """
    Podest i schody między czopem a końcem trybuny. Biegi schodzą na zachód od szczytu (brama) na plac;
    s = +1 północ (szerokość schodów ku +Y od końca trybuny), -1 południe.
    """
    rise = CONCOURSE_Z / (UPPER_STEPS + LOWER_STEPS)
    x_land0 = front_x - (LOWER_X0 + (LOWER_ROWS - 1) * LOWER_DX)
    x_top = front_x - LANDING_BACK
    y0, y1 = end_y + s * 0.3, end_y + s * (0.3 + STAIR_W)
    ya, yb = min(y0, y1), max(y0, y1)

    # Podest: od ostatniego rzędu sektora dolnego do bramy; przy czole zwężony do linii czopu
    cy = s * STRAIGHT_L / 2
    slope = math.tan(math.radians(180.0 - BOWL_ANGLE))   # |dY/dX| linii czopu
    plug_y = lambda x: cy + s * (-x) * slope            # Y czopu dla danego X (X < 0)
    w_front = min(STAIR_W, abs(plug_y(x_land0) - y0) - 0.4)
    corners = [(x_land0, y0), (x_top, y0), (x_top, y1), (x_land0, y0 + s * w_front)]
    if s < 0:
        corners = corners[::-1]
    top = [bm_s.verts.new((x, y, CONCOURSE_Z)) for x, y in corners]
    bot = [bm_s.verts.new((x, y, 0.0)) for x, y in corners]
    bm_s.faces.new(top)
    bm_s.faces.new(bot[::-1])
    for i in range(4):
        bm_s.faces.new([bot[i], bot[(i + 1) % 4], top[(i + 1) % 4], top[i]])

    # Biegi: profil zębaty w płaszczyźnie XZ wyciągnięty na szerokość schodów
    x_mid1 = x_top - UPPER_STEPS * STAIR_TREAD
    x_mid0 = x_mid1 - MID_LANDING
    x_foot = x_mid0 - LOWER_STEPS * STAIR_TREAD
    z_mid = LOWER_STEPS * rise
    prof = [(x_top, 0.0)]
    for k in range(UPPER_STEPS):
        z = CONCOURSE_Z - k * rise
        prof += [(x_top - k * STAIR_TREAD, z), (x_top - (k + 1) * STAIR_TREAD, z)]
    prof += [(x_mid1, z_mid)]
    for k in range(LOWER_STEPS):
        z = z_mid - k * rise
        prof += [(x_mid0 - k * STAIR_TREAD, z), (x_mid0 - (k + 1) * STAIR_TREAD, z)]
    prof += [(x_foot, 0.0)]
    _extrude_profile(bm_s, prof, ya, yb)

    # Żółte krawędzie stopni: na każdym uskoku profilu
    for (xa, za), (xb, zb) in zip(prof[1:], prof[2:]):
        if abs(xa - xb) < 1e-6 and zb < za - 1e-6:
            _box(bm_y, xa, xa + 0.06, ya, yb, za, za + 0.008)

    # Policzki (boczne i dwa między biegami) z poręczami 0.9 m nad linią stopni
    line = [(x_foot, 0.0), (x_mid0, z_mid), (x_mid1, z_mid), (x_top, CONCOURSE_Z)]
    cheek = [(x_foot, 0.0)] + [(x, z + CHEEK_H) for x, z in line] + [(x_top, 0.0)]
    for k in range(4):
        yc = ya + CHEEK_W / 2 + k * (STAIR_W - CHEEK_W) / 3
        _extrude_profile(bm_c, cheek, yc - CHEEK_W / 2, yc + CHEEK_W / 2)
        rail = [(x, z + CHEEK_H + 0.9) for x, z in line]
        for (xa, za), (xb, zb) in zip(rail, rail[1:]):
            _beam(bm_y, (xa, yc, za), (xb, yc, zb), 0.05, 0.05)
        for x, z in line:
            _beam(bm_y, (x, yc, z + CHEEK_H), (x, yc, z + CHEEK_H + 0.9), 0.05, 0.05)
    return x_top, ya, yb, x_foot


def _gate(bm_y, bm_mesh, uv, bm_banner, uv_b, x, ya, yb):
    """Brama na szczycie schodów: żółte słupy i ramy skrzydeł, siatka; dwa środkowe skrzydła otwarte ku boisku."""
    z0 = CONCOURSE_Z
    leaf = (yb - ya) / GATE_LEAVES
    for k in range(GATE_LEAVES + 1):
        y = ya + k * leaf
        _box(bm_y, x - 0.06, x + 0.06, y - 0.06, y + 0.06, z0, z0 + GATE_H + 0.1)
    for k in range(GATE_LEAVES):
        ys = ya + k * leaf
        is_open = k in (1, 2)
        hinge = ys if k == 1 else ys + leaf
        for off in (-0.02, 0.02):
            if is_open:                                     # skrzydło obrócone o 90° wokół słupa
                c = [(x, hinge + off, z0 + 0.1, 0.0, 0.1), (x + leaf - 0.1, hinge + off, z0 + 0.1, leaf, 0.1),
                     (x + leaf - 0.1, hinge + off, z0 + GATE_H, leaf, GATE_H), (x, hinge + off, z0 + GATE_H, 0.0, GATE_H)]
            else:
                c = [(x + off, ys + 0.08, z0 + 0.1, 0.0, 0.1), (x + off, ys + leaf - 0.08, z0 + 0.1, leaf, 0.1),
                     (x + off, ys + leaf - 0.08, z0 + GATE_H, leaf, GATE_H), (x + off, ys + 0.08, z0 + GATE_H, 0.0, GATE_H)]
            _decal(bm_mesh, uv, c if off < 0 else c[::-1])
        frame = ([(x, hinge, 0), (x + leaf - 0.1, hinge, 0)] if is_open else [(x, ys + 0.08, 0), (x, ys + leaf - 0.08, 0)])
        (fx0, fy0, _), (fx1, fy1, _) = frame
        for z in (z0 + 0.1, z0 + GATE_H):
            _beam(bm_y, (fx0, fy0, z), (fx1, fy1, z), 0.05, 0.05)
        _beam(bm_y, (fx1, fy1, z0 + 0.1), (fx1, fy1, z0 + GATE_H), 0.05, 0.05)

    # Baner na ramie nad bramą, lico na zachód (ku wchodzącym), tył bez nadruku
    yc = (ya + yb) / 2
    b0, b1 = yc - BANNER_W / 2, yc + BANNER_W / 2
    for y in (b0 - 0.1, b1 + 0.1):
        _box(bm_y, x - 0.05, x + 0.05, y - 0.05, y + 0.05, z0 + GATE_H, z0 + BANNER_Z[1] + 0.1)
    _box(bm_y, x - 0.03, x + 0.03, b0 - 0.1, b1 + 0.1, z0 + BANNER_Z[1] + 0.05, z0 + BANNER_Z[1] + 0.1)
    za, zb = z0 + BANNER_Z[0], z0 + BANNER_Z[1]
    _decal(bm_banner, uv_b, [(x - 0.03, b1, za, 0.0, 0.0), (x - 0.03, b0, za, 1.0, 0.0),
                             (x - 0.03, b0, zb, 1.0, 1.0), (x - 0.03, b1, zb, 0.0, 1.0)])
    _decal(bm_banner, uv_b, [(x + 0.03, b0, za, 0.002, 0.5), (x + 0.03, b1, za, 0.002, 0.5),
                             (x + 0.03, b1, zb, 0.002, 0.5), (x + 0.03, b0, zb, 0.002, 0.5)])


def build_entrances(col, mats, front_x, north_y, south_y):
    """front_x: X czoła trybuny głównej; north_y, south_y: Y jej końców."""
    m = _materials()
    bm_c, bm_s, bm_y = bmesh.new(), bmesh.new(), bmesh.new()
    bm_mesh, bm_banner = bmesh.new(), bmesh.new()
    uv, uv_b = bm_mesh.loops.layers.uv.verify(), bm_banner.loops.layers.uv.verify()
    for s, end_y in ((1, north_y), (-1, south_y)):
        _plug(bm_c, bm_y, s)
        x_top, ya, yb, x_foot = _stairs(bm_s, bm_c, bm_y, s, front_x, end_y)
        _gate(bm_y, bm_mesh, uv, bm_banner, uv_b, x_top, ya, yb)
    _finish(col, bm_c, "Wejscia_Czopy_i_Policzki", mats['concrete'])
    _finish(col, bm_s, "Wejscia_Schody_i_Podesty", mats['concrete_dark'])
    _finish(col, bm_y, "Wejscia_Barierki_i_Bramy", mats['yellow'])
    _finish(col, bm_mesh, "Wejscia_Bramy_Siatka", m['gate_mesh'])
    _finish(col, bm_banner, "Wejscia_Baner_Wita", m['wita'])

    # Wejście południowe: biała ściana szczytowa pod sektorem górnym (do spodu płyty), na niej baner MOSiR
    # (lico na południe); tablica z planem sektorów przy stopie schodów (lico na zachód, ku placowi)
    bm_w = bmesh.new()
    wall = [(front_x - x, 0.0) for x in MOSIR_WALL_X[::-1]] + [(front_x - x, underside(x) - 0.05) for x in MOSIR_WALL_X]
    _extrude_profile(bm_w, wall, south_y - 0.25, south_y)
    _finish(col, bm_w, "Sciana_Szczytowa_Poludnie", mats['goal_white'])
    bm_m = bmesh.new()
    uv_m = bm_m.loops.layers.uv.verify()
    w, h, z0 = MOSIR_BANNER
    xc, y = front_x - MOSIR_X, south_y - 0.27
    _decal(bm_m, uv_m, [(xc - w / 2, y, z0, 0.0, 0.0), (xc + w / 2, y, z0, 1.0, 0.0),
                        (xc + w / 2, y, z0 + h, 1.0, 1.0), (xc - w / 2, y, z0 + h, 0.0, 1.0)])
    _finish(col, bm_m, "Baner_MOSiR", m['mosir'])
    bm_p, bm_post = bmesh.new(), bmesh.new()
    uv_p = bm_p.loops.layers.uv.verify()
    xp, yp = x_foot - 1.5, south_y - 0.3 - STAIR_W - 1.2
    _box(bm_post, xp, xp + 0.04, yp - 0.8, yp + 0.8, 0.9, 2.03)
    _decal(bm_p, uv_p, [(xp - 0.005, yp + 0.8, 0.9, 0.0, 0.0), (xp - 0.005, yp - 0.8, 0.9, 1.0, 0.0),
                        (xp - 0.005, yp - 0.8, 2.03, 1.0, 1.0), (xp - 0.005, yp + 0.8, 2.03, 0.0, 1.0)])
    for dy in (-0.7, 0.7):
        _box(bm_post, xp + 0.04, xp + 0.1, yp + dy - 0.03, yp + dy + 0.03, 0.0, 2.1)
    _finish(col, bm_p, "Tablica_MOSiR_Plan", m['plan'])
    _finish(col, bm_post, "Tablica_MOSiR_Slupki", mats['metal'])
