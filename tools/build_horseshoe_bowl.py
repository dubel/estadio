"""
Generowanie korony stadionu (wały ziemne, podkowa), murawy, bieżni żużlowej,
betonowej fosy oraz historycznej tablicy świetlnej z zegarem.
"""

import bpy
import bmesh
import mathutils
import math

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_seats import place_seats, seat_material, seats_in_row, SEAT_PITCH  # noqa: E402
from build_grandstand import _extrude_profile, _rail  # noqa: E402
import mathutils  # noqa: E402

STRAIGHT_L = 84.0  # długość prostych bieżni 400 m (środki łuków w Y = ±42 m)


def stadium_path(r, ang_start, ang_end, arc_step_deg=4.0, straight_step=3.0, close_west=False):
    """
    Punkty (x, y, nx, ny) na obrysie „stadionowym” (2 łuki + proste) w odległości r od osi bieżni,
    od kąta ang_start (0..180°, łuk północny) zgodnie z ruchem wskazówek zegara przez prostą
    wschodnią do ang_end (-180..0°, łuk południowy). Proste są dzielone co straight_step metrów —
    jeden quad na całą prostą dawał 89-metrowe trójkąty, na których kapsuła gracza się zacinała.
    close_west dokłada punkty prostej zachodniej (pełna pętla).
    """
    cy = STRAIGHT_L / 2.0
    pts = []

    def arc(a0, a1, c):
        n = max(1, math.ceil(abs(a1 - a0) / arc_step_deg))
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((r * math.cos(a), c + r * math.sin(a), math.cos(a), math.sin(a)))

    def straight(x, y0, y1, nx):
        n = max(1, math.ceil(abs(y1 - y0) / straight_step))
        for i in range(1, n):
            pts.append((x, y0 + (y1 - y0) * i / n, nx, 0.0))

    arc(ang_start, 0.0, cy)
    straight(r, cy, -cy, 1.0)
    arc(0.0, ang_end, -cy)
    if close_west:
        straight(-r, -cy, cy, -1.0)
    return pts

def build_pitch_and_track(col, mats):
    """Tworzy murawę oraz pas dawnej bieżni 400 m (w latach 2010–2012 porośnięty trawą)."""
    PITCH_L = 105.0
    PITCH_W = 68.0
    
    # 1. Płyta murawy z pasami bocznymi (112m x 74m)
    bm_pitch = bmesh.new()
    bmesh.ops.create_grid(bm_pitch, x_segments=1, y_segments=1, size=1.0)
    # create_grid(size=1) daje wierzchołki ±1, więc skala to POŁOWA wymiaru (wcześniej płyta miała 148 x 224 m
    # i przykrywała plac pod trybunami)
    bmesh.ops.scale(bm_pitch, vec=(37.0, 56.0, 1.0), verts=bm_pitch.verts)
    
    # Warstwa współrzędnych UV dla murawy
    uv_layer = bm_pitch.loops.layers.uv.verify()
    for face in bm_pitch.faces:
        for loop in face.loops:
            u = (loop.vert.co.x + 37.0) / 74.0
            v = (loop.vert.co.y + 56.0) / 112.0
            loop[uv_layer].uv = (u, v)

    mesh_pitch = bpy.data.meshes.new("Murawa_Boisko_Mesh")
    bm_pitch.normal_update()
    bm_pitch.to_mesh(mesh_pitch)
    bm_pitch.free()
    
    obj_pitch = bpy.data.objects.new("Murawa_Boisko", mesh_pitch)
    if mats and 'grass' in mats:
        obj_pitch.data.materials.append(mats['grass'])
    col.objects.link(obj_pitch)

    # Trawiaste wnętrze bieżni (łuki za bramkami), 2 cm pod płytą boiska
    bm_in = bmesh.new()
    bm_in.faces.new([bm_in.verts.new((x, y, -0.02)) for x, y, _, _ in stadium_path(37.0, 180.0, -180.0, close_west=True)])
    mesh_in = bpy.data.meshes.new("Murawa_Wnetrze_Biezni_Mesh")
    bm_in.normal_update()
    bm_in.to_mesh(mesh_in)
    bm_in.free()
    obj_in = bpy.data.objects.new("Murawa_Wnetrze_Biezni", mesh_in)
    obj_in.data.materials.append(mats['ground_grass'])
    col.objects.link(obj_in)

    # 2. Bieżnia lekkoatletyczna (czerwono-grafitowy żużel)
    # Mieści się POMIĘDZY boiskiem a trybunami (zarówno podkową, jak i Trybuną Główną)
    R_IN = 37.0
    R_OUT = 45.0  # szerokość bieżni 8.0 m
    NUM_ARC_SEGS = 32
    
    bm_track = bmesh.new()
    pts_in = []
    pts_out = []
    
    # Łuk północny (+Y)
    for i in range(NUM_ARC_SEGS + 1):
        ang = math.pi * (i / NUM_ARC_SEGS)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cy = STRAIGHT_L / 2.0
        pts_in.append((R_IN * cos_a, cy + R_IN * sin_a, 0.02))
        pts_out.append((R_OUT * cos_a, cy + R_OUT * sin_a, 0.02))
        
    # Łuk południowy (-Y)
    for i in range(NUM_ARC_SEGS + 1):
        ang = math.pi + math.pi * (i / NUM_ARC_SEGS)
        cos_a = math.cos(ang)
        sin_a = math.sin(ang)
        cy = -STRAIGHT_L / 2.0
        pts_in.append((R_IN * cos_a, cy + R_IN * sin_a, 0.02))
        pts_out.append((R_OUT * cos_a, cy + R_OUT * sin_a, 0.02))
        
    v_in = [bm_track.verts.new(p) for p in pts_in]
    v_out = [bm_track.verts.new(p) for p in pts_out]
    n_pts = len(v_in)
    for i in range(n_pts):
        next_i = (i + 1) % n_pts
        bm_track.faces.new([v_in[i], v_out[i], v_out[next_i], v_in[next_i]])
        
    mesh_track = bpy.data.meshes.new("Bieznia_Zarosnieta_Mesh")
    bm_track.normal_update()
    bm_track.to_mesh(mesh_track)
    bm_track.free()
    
    # Stan 2010–2012: bieżnia zarośnięta trawą aż do ogrodzenia (widok_z_galery.jpg, ortofotomapa 2013)
    obj_track = bpy.data.objects.new("Bieznia_Zarosnieta", mesh_track)
    obj_track.data.materials.append(mats['ground_grass'])
    col.objects.link(obj_track)

    return obj_pitch, obj_track


def build_pitch_lines(col, mats):
    """Tworzy kredowe linie boiska piłkarskiego 105 x 68 m (zgodne z przepisami FIFA/PZPN)."""
    bm = bmesh.new()
    LW = 0.12 # szerokość linii 12 cm
    Z_LINE = 0.025 # 2.5 cm nad murawą
    
    def add_line_segment(p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length < 1e-4:
            return
        nx = -dy / length * (LW / 2.0)
        ny =  dx / length * (LW / 2.0)
        v0 = bm.verts.new((p1[0] - nx, p1[1] - ny, Z_LINE))
        v1 = bm.verts.new((p1[0] + nx, p1[1] + ny, Z_LINE))
        v2 = bm.verts.new((p2[0] + nx, p2[1] + ny, Z_LINE))
        v3 = bm.verts.new((p2[0] - nx, p2[1] - ny, Z_LINE))
        bm.faces.new([v0, v1, v2, v3])
        
    def add_circle_ring(cx, cy, radius, num_segs=48, start_ang=0.0, end_ang=2.0*math.pi):
        d_ang = (end_ang - start_ang) / num_segs
        pts_in = []
        pts_out = []
        for i in range(num_segs + 1):
            ang = start_ang + i * d_ang
            ca = math.cos(ang)
            sa = math.sin(ang)
            pts_in.append(bm.verts.new((cx + (radius - LW/2.0) * ca, cy + (radius - LW/2.0) * sa, Z_LINE)))
            pts_out.append(bm.verts.new((cx + (radius + LW/2.0) * ca, cy + (radius + LW/2.0) * sa, Z_LINE)))
        for i in range(num_segs):
            bm.faces.new([pts_in[i], pts_out[i], pts_out[i+1], pts_in[i+1]])

    def add_spot(cx, cy, r=0.18, num_segs=16):
        v_center = bm.verts.new((cx, cy, Z_LINE))
        rim = []
        for i in range(num_segs):
            ang = 2.0 * math.pi * (i / num_segs)
            rim.append(bm.verts.new((cx + r * math.cos(ang), cy + r * math.sin(ang), Z_LINE)))
        for i in range(num_segs):
            bm.faces.new([v_center, rim[i], rim[(i+1)%num_segs]])

    # 1. Linie obwodowe (105 x 68 m)
    add_line_segment((-34.0, -52.5), ( 34.0, -52.5)) # południowa linia bramkowa
    add_line_segment((-34.0,  52.5), ( 34.0,  52.5)) # północna linia bramkowa
    add_line_segment((-34.0, -52.5), (-34.0,  52.5)) # zachodnia linia boczna
    add_line_segment(( 34.0, -52.5), ( 34.0,  52.5)) # wschodnia linia boczna

    # 2. Linia środkowa i koło środkowe (R = 9.15 m)
    add_line_segment((-34.0, 0.0), (34.0, 0.0))
    add_circle_ring(0.0, 0.0, 9.15, num_segs=64)
    add_spot(0.0, 0.0)

    # 3. Pola karne (16.5 m od linii i 16.5 m od słupków: X od -20.16 do +20.16)
    for sign_y in [-1, 1]:
        gy = sign_y * 52.5
        fy = sign_y * 36.0 # 52.5 - 16.5 = 36.0
        add_line_segment((-20.16, gy), (-20.16, fy))
        add_line_segment(( 20.16, gy), ( 20.16, fy))
        add_line_segment((-20.16, fy), ( 20.16, fy))
        
        # Pole bramkowe (5.5 m od linii i 5.5 m od słupków: X od -9.16 do +9.16)
        by = sign_y * 47.0 # 52.5 - 5.5 = 47.0
        add_line_segment((-9.16, gy), (-9.16, by))
        add_line_segment(( 9.16, gy), ( 9.16, by))
        add_line_segment((-9.16, by), ( 9.16, by))

        # Punkt karny (11.0 m od linii bramkowej)
        py = sign_y * 41.5
        add_spot(0.0, py)

        # Łuk pola karnego (R = 9.15 m wokół punktu karnego na zewnątrz pola)
        alpha = math.acos(5.5 / 9.15)
        if sign_y < 0:
            add_circle_ring(0.0, py, 9.15, num_segs=24, start_ang=math.pi/2.0 - alpha, end_ang=math.pi/2.0 + alpha)
        else:
            add_circle_ring(0.0, py, 9.15, num_segs=24, start_ang=-math.pi/2.0 - alpha, end_ang=-math.pi/2.0 + alpha)

    # 4. Łuki narożne (R = 1.0 m w 4 narożnikach)
    add_circle_ring(-34.0, -52.5, 1.0, num_segs=12, start_ang=0.0, end_ang=math.pi/2.0)
    add_circle_ring( 34.0, -52.5, 1.0, num_segs=12, start_ang=math.pi/2.0, end_ang=math.pi)
    add_circle_ring( 34.0,  52.5, 1.0, num_segs=12, start_ang=math.pi, end_ang=1.5*math.pi)
    add_circle_ring(-34.0,  52.5, 1.0, num_segs=12, start_ang=1.5*math.pi, end_ang=2.0*math.pi)

    mesh_lines = bpy.data.meshes.new("Linie_Boiska_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh_lines)
    bm.free()

    obj_lines = bpy.data.objects.new("Linie_Boiska", mesh_lines)
    if mats and 'pitch_lines' in mats:
        obj_lines.data.materials.append(mats['pitch_lines'])
    col.objects.link(obj_lines)
    return obj_lines


R_TRACK_OUT = 45.0     # zewnętrzna krawędź bieżni = czoło trybun
FRONT_WALL_H = 1.5     # mur oporowy przed pierwszym rzędem (zdjęcia lks02, 516e09e41f411, przekrój Wyżnikiewicza — bez fosy)
FENCE_H = 2.5          # stalowe ogrodzenie na koronie muru: pełne panele u dołu, siatka wyżej (widok_z_galery.jpg)
BOWL_ANGLE = 149.0     # podkowa kończy się tam, gdzie zaczyna się trybuna główna (Y = ±65 m)
STAND_DEPTH = 22.0     # głębokość wału ziemnego
STAND_H = 6.8          # wysokość korony wału (na niej stoi tablica wyników, build_scoreboard)
NUM_STEPS = 20         # 20 betonowych stopni
STEP_D = STAND_DEPTH / NUM_STEPS
STEP_H = (STAND_H - FRONT_WALL_H) / (NUM_STEPS - 1)  # ~0.28 m
LOW_FENCE_H = 1.2      # niskie ogrodzenie łuków z biało-czerwonymi słupkami (widok_na_zegar_u2.png)

# Łuk południowy (kąty jak w stadium_path, środek łuku w Y = -42 m), widok_na_zegar_u2.png:
# od zachodniego krańca do osi stadionu czerwone krzesełka w sektorach, dalej ku Galerze ławki z żółtymi barierkami
SOUTH_SEAT_SECTORS = [(-149.0, -135.0), (-135.0, -121.0), (-121.0, -107.0), (-107.0, -93.0)]
SOUTH_BENCH_ARC = (-88.0, -3.0)
# Dwa duże tunele wejściowe Galery przy styku z łukami (tunel_galera.png — północny, południowy symetrycznie):
# przelot pod wałem od bieżni do placu, nad wylotem podest na wysokości rzędu GALERA_TUNNEL_ROW.
# Zakresy Y na wierzchołkach podziału prostej (co 3 m, stadium_path).
GALERA_TUNNELS = ((-39.0, -33.0), (33.0, 39.0))
GALERA_TUNNEL_H = 2.8
GALERA_TUNNEL_ROW = 6
GALERA_TUNNEL_WALL = 0.3
SOUTH_ADS = [(-142.0, 0), (-129.0, 1), (-116.0, 2), (-103.0, 3)]   # bandy na koronie: (kąt, wiersz atlasu)


def _obox(bm, center, size, yaw=0.0, pitch=0.0):
    """Prostopadłościan o wymiarach size=(dx, dy, dz), obrócony o yaw (wokół Z) i pitch (wokół lokalnego Y)."""
    m = (mathutils.Matrix.Translation(center) @ mathutils.Matrix.Rotation(yaw, 4, 'Z')
         @ mathutils.Matrix.Rotation(pitch, 4, 'Y') @ mathutils.Matrix.Diagonal((*size, 1.0)))
    return bmesh.ops.create_cube(bm, size=1.0, matrix=m)


def _row(i):
    """(odległość przodu stopnia od czoła, wysokość stopnia) rzędu i podkowy."""
    return i * STEP_D, FRONT_WALL_H + i * STEP_H


def _arc_point(r, ang_deg, cy=-42.0):
    a = math.radians(ang_deg)
    return (r * math.cos(a), cy + r * math.sin(a)), a


def _in_galera_tunnel(y, margin=0.0):
    return any(a - margin <= y <= b + margin for a, b in GALERA_TUNNELS)


def _finish_mesh(col, bm, name, mats_list):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    for m in mats_list:
        mesh.materials.append(m)
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def build_bowl(col, mats):
    """
    Podkowa trybun na wałach ziemnych: od łuku północnego przez prostą wschodnią (Galera) do łuku
    południowego. Czoło to mur oporowy FRONT_WALL_H przy zewnętrznej krawędzi bieżni, dalej
    20 betonowych stopni i tylna skarpa. Strona zachodnia pozostaje wolna na Trybunę Główną.
    Fosy nie było — wcześniejsza wersja modelu ją zakładała, źródła (docs/zrodla.md) tego nie potwierdzają.
    """
    bm_bowl = bmesh.new()
    bowl_rings = []
    bowl_path = stadium_path(R_TRACK_OUT, BOWL_ANGLE, -BOWL_ANGLE)
    for px, py, nx, ny in bowl_path:
        # Mur oporowy, potem stopnie na wale ziemnym
        b_pts = [(px, py, 0.0)]
        cur_d = 0.0
        cur_z = FRONT_WALL_H - STEP_H
        for s in range(NUM_STEPS):
            cur_z += STEP_H
            b_pts.append((px + nx * cur_d, py + ny * cur_d, cur_z))
            cur_d += STEP_D
            b_pts.append((px + nx * cur_d, py + ny * cur_d, cur_z))

        # Tylna skarpa wału
        cur_d += 5.0
        b_pts.append((px + nx * cur_d, py + ny * cur_d, 0.0))

        bowl_rings.append([bm_bowl.verts.new(p) for p in b_pts])

    for i in range(len(bowl_rings) - 1):
        (_, ya, nxa, _), (_, yb, nxb, _) = bowl_path[i], bowl_path[i + 1]
        if nxa == 1.0 and nxb == 1.0 and _in_galera_tunnel(ya, 1e-6) and _in_galera_tunnel(yb, 1e-6):
            continue                                   # przęsło tunelu Galery (build_galera_tunnels)
        bA = bowl_rings[i]
        bB = bowl_rings[i + 1]
        for j in range(len(bA) - 1):
            bm_bowl.faces.new([bA[j], bB[j], bB[j+1], bA[j+1]])

    mesh_bowl = bpy.data.meshes.new("Trybuna_Podkowa_Mesh")
    bm_bowl.normal_update()
    bm_bowl.to_mesh(mesh_bowl)
    bm_bowl.free()
    obj_bowl = bpy.data.objects.new("Trybuna_Podkowa", mesh_bowl)
    obj_bowl.data.materials.append(mats['concrete'])
    col.objects.link(obj_bowl)

    # Wysokie ogrodzenie tylko przed Galerą (prosta): panele z teksturą alfa (u w metrach / 2.5 m przęsła).
    # Dwie ściany 4 cm od siebie: kolizje Octree w Three.js są jednostronne, pojedyncza płaszczyzna
    # przepuszczała gracza schodzącego z trybuny. Na łukach niskie ogrodzenie (build_bowl_details).
    bm_f = bmesh.new()
    uv = bm_f.loops.layers.uv.verify()
    # Nad tunelami Galery panele stoją na podeście nad wylotem, nie na murze oporowym
    path = stadium_path(R_TRACK_OUT, BOWL_ANGLE, -BOWL_ANGLE, straight_step=3.0)
    landing_z = _row(GALERA_TUNNEL_ROW)[1]
    for off, flip in [(0.02, False), (0.06, True)]:
        dist = 0.0
        for (x0, y0, nx0, ny0), (x1, y1, nx1, ny1) in zip(path, path[1:]):
            seg = math.hypot(x1 - x0, y1 - y0)
            if abs(ny0) > 1e-6 or abs(ny1) > 1e-6:   # odcinek łuku
                continue
            a0 = (x0 + nx0 * off, y0 + ny0 * off)
            a1 = (x1 + nx1 * off, y1 + ny1 * off)
            zb = landing_z if _in_galera_tunnel((y0 + y1) / 2) else FRONT_WALL_H
            corners = [(a0, zb, dist, 0.0), (a1, zb, dist + seg, 0.0),
                       (a1, zb + FENCE_H, dist + seg, 1.0), (a0, zb + FENCE_H, dist, 1.0)]
            if flip:
                corners.reverse()
            face = bm_f.faces.new([bm_f.verts.new((p[0], p[1], z)) for p, z, _, _ in corners])
            for loop, (_, _, u, v) in zip(face.loops, corners):
                loop[uv].uv = (u / 2.5, v)
            dist += seg
    mesh_f = bpy.data.meshes.new("Ogrodzenie_Trybun_Mesh")
    bm_f.normal_update()
    bm_f.to_mesh(mesh_f)
    bm_f.free()
    obj_f = bpy.data.objects.new("Ogrodzenie_Trybun", mesh_f)
    obj_f.data.materials.append(mats['fence'])
    col.objects.link(obj_f)

    # Czerwone krzesełka na prostej Galery (widok_z_galery.jpg); przejścia co 10 m
    seats = []
    cy = STRAIGHT_L / 2.0
    aisles = [-cy + 2.0 + k * 10.0 for k in range(9)]
    for i in range(NUM_STEPS):
        d, z = _row(i)
        for a, b in zip(aisles, aisles[1:]):
            seats += [s for s in seats_in_row(R_TRACK_OUT + d + 0.7, z, a + 0.6, b - 0.6)
                      if not (i <= GALERA_TUNNEL_ROW and _in_galera_tunnel(s[1], 0.3))]
    red_seat = seat_material("Mat_Krzeselka_Czerwone_Galera", (0.62, 0.07, 0.09))
    place_seats(col, "Krzeselka_Galera", red_seat, seats)

    build_bowl_details(col, mats, red_seat, aisles)
    build_galera_tunnels(col, mats)
    return obj_bowl, obj_f


def build_galera_tunnels(col, mats):
    """
    Tunele wejściowe Galery (tunel_galera.png): przelot GALERA_TUNNEL_H pod wałem od bieżni do tylnej skarpy.
    Nad wylotem podest na wysokości rzędu GALERA_TUNNEL_ROW wysunięty do muru oporowego, ściany boczne
    sięgają podestu, po krawędziach żółte barierki. Bryły zamknięte (kolizje Octree są jednostronne).
    """
    bm = bmesh.new()
    bm_y = bmesh.new()
    d_land, z_land = _row(GALERA_TUNNEL_ROW)
    treads = []
    for i in range(GALERA_TUNNEL_ROW, NUM_STEPS):
        d, z = _row(i)
        treads += [(R_TRACK_OUT + d, z), (R_TRACK_OUT + d + STEP_D, z)]
    back = R_TRACK_OUT + STAND_DEPTH + 5.0                    # stopa tylnej skarpy (build_bowl)
    slope_x = lambda z: back - 5.0 * z / STAND_H
    side = [(R_TRACK_OUT, 0.0), (R_TRACK_OUT, z_land)] + treads + [(back, 0.0)]
    roof = ([(R_TRACK_OUT, GALERA_TUNNEL_H), (R_TRACK_OUT, z_land)] + treads
            + [(slope_x(GALERA_TUNNEL_H), GALERA_TUNNEL_H)])
    w = GALERA_TUNNEL_WALL
    for ya, yb in GALERA_TUNNELS:
        _extrude_profile(bm, side, ya, ya + w)
        _extrude_profile(bm, side, yb - w, yb)
        _extrude_profile(bm, roof, ya + w, yb - w)
        # Barierki wzdłuż obu krawędzi podestu (od strony boiska stoi ogrodzenie Galery)
        for ye in (ya + w / 2, yb - w / 2):
            _rail(bm_y, (R_TRACK_OUT + 0.15, ye, z_land), (R_TRACK_OUT + d_land, ye, z_land), 2.2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.recalc_face_normals(bm_y, faces=bm_y.faces)
    _finish_mesh(col, bm, "Galera_Tunele", [mats['concrete']])
    _finish_mesh(col, bm_y, "Galera_Tunele_Barierki", [mats['yellow']])


def build_bowl_details(col, mats, red_seat, galera_aisles):
    """
    Wyposażenie podkowy ze zdjęć 2010–2012 (widok_z_galery.jpg, widok_na_zegar_u2.png): krzesełka i ławki
    łuku południowego, żółte barierki, niskie ogrodzenie łuków, ślad dawnej bieżni, bandy na koronie.
    Barierki i ogrodzenie to bryły (kolizje Octree są jednostronne).
    """
    yellow = mats['yellow']
    bench_grey = seat_material("Mat_Lawki_Luk", (0.62, 0.62, 0.60))

    # Krzesełka łuku południowego: sektory rozdzielone przejściami 1.2 m, skierowane do środka łuku
    seats = []
    for i in range(NUM_STEPS):
        d, z = _row(i)
        r = R_TRACK_OUT + d + 0.7
        for a0, a1 in SOUTH_SEAT_SECTORS:
            gap = math.degrees(0.6 / r)
            n = int(math.radians(a1 - a0 - 2 * gap) * r / SEAT_PITCH)
            for k in range(n):
                (x, y), a = _arc_point(r, a0 + gap + (k + 0.5) * (a1 - a0 - 2 * gap) / n)
                seats.append((x, y, z, a))
    place_seats(col, "Krzeselka_Luk_Poludniowy", red_seat, seats)

    # Ławki we wschodniej części łuku (deska 0.32 m na wsporniku, 0.40 m nad stopniem), przejścia co 15°
    bm_b = bmesh.new()
    seg_deg = 3.0
    for i in range(NUM_STEPS):
        d, z = _row(i)
        r = R_TRACK_OUT + d + 0.6
        ang = SOUTH_BENCH_ARC[0]
        while ang + seg_deg <= SOUTH_BENCH_ARC[1]:
            if int((ang - SOUTH_BENCH_ARC[0]) / seg_deg) % 5 != 4:          # co piąty odcinek to przejście
                (x, y), a = _arc_point(r, ang + seg_deg / 2)
                chord = 2 * r * math.sin(math.radians(seg_deg / 2))
                _obox(bm_b, (x, y, z + 0.395), (0.32, chord, 0.05), yaw=a)
                _obox(bm_b, (x, y, z + 0.185), (0.22, 0.08, 0.37), yaw=a)
            ang += seg_deg
    _finish_mesh(col, bm_b, "Lawki_Luk_Poludniowy", [bench_grey])

    # Żółte barierki: poręcze przy przejściach Galery (wzdłuż spadku, przy krawędzi sektora)
    # i poprzeczna barierka w połowie wysokości sekcji ławek łuku
    bm_y = bmesh.new()
    run = math.hypot(STEP_D, STEP_H)
    pitch = -math.atan2(STEP_H, STEP_D)
    for a in galera_aisles[1:-1]:
        y = a + 0.52
        for i in range(NUM_STEPS - 1):
            d, z = _row(i)
            _obox(bm_y, (R_TRACK_OUT + d + STEP_D, y, z + STEP_H / 2 + 1.0), (run, 0.05, 0.05), pitch=pitch)
            if i % 2 == 0:
                _obox(bm_y, (R_TRACK_OUT + d + 0.55, y, z + 0.5), (0.05, 0.05, 1.0))
    i_rail = 10
    d, z = _row(i_rail)
    r = R_TRACK_OUT + d + 0.15
    ang = SOUTH_BENCH_ARC[0]
    while ang + seg_deg <= SOUTH_BENCH_ARC[1]:
        if int((ang - SOUTH_BENCH_ARC[0]) / seg_deg) % 5 != 4:
            (x, y), a = _arc_point(r, ang + seg_deg / 2)
            _obox(bm_y, (x, y, z + 1.0), (0.05, 2 * r * math.sin(math.radians(seg_deg / 2)), 0.05), yaw=a)
            (px, py), _ = _arc_point(r, ang + 0.2)
            _obox(bm_y, (px, py, z + 0.5), (0.05, 0.05, 1.0))
        ang += seg_deg
    _finish_mesh(col, bm_y, "Barierki_Zolte", [yellow])

    # Niskie ogrodzenie łuków: słupki co ~2.5 m na przemian czerwone i białe, dwie poręcze
    bm_lf = bmesh.new()
    path = stadium_path(R_TRACK_OUT + 0.15, BOWL_ANGLE, -BOWL_ANGLE, arc_step_deg=3.0)
    k = 0
    for (x0, y0, nx0, ny0), (x1, y1, nx1, ny1) in zip(path, path[1:]):
        if abs(ny0) < 1e-6 and abs(ny1) < 1e-6:     # prosta Galery ma wysokie ogrodzenie
            continue
        yaw = math.atan2(y1 - y0, x1 - x0) - math.pi / 2
        seg = math.hypot(x1 - x0, y1 - y0)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        for h in (0.6, LOW_FENCE_H - 0.03):
            _obox(bm_lf, (mx, my, FRONT_WALL_H + h), (0.05, seg, 0.05), yaw=yaw)
        post = _obox(bm_lf, (x0, y0, FRONT_WALL_H + LOW_FENCE_H / 2), (0.09, 0.09, LOW_FENCE_H), yaw=yaw)
        for f in {f for v in post['verts'] for f in v.link_faces}:
            f.material_index = k % 2
        k += 1
    _finish_mesh(col, bm_lf, "Ogrodzenie_Niskie_Luki", [mats['lks_red'], mats['goal_white']])

    # Ślad dawnej bieżni: wydeptany, ciemny pas żużlu w trawie (pełna pętla)
    trace = _flat("Mat_Slad_Biezni", (0.075, 0.065, 0.055), 0.95)
    bm_t = bmesh.new()
    inner = stadium_path(42.7, 180.0, -180.0, close_west=True)
    outer = stadium_path(43.8, 180.0, -180.0, close_west=True)
    vi = [bm_t.verts.new((x, y, 0.035)) for x, y, _, _ in inner]
    vo = [bm_t.verts.new((x, y, 0.035)) for x, y, _, _ in outer]
    for j in range(len(vi)):
        bm_t.faces.new([vi[j], vo[j], vo[(j + 1) % len(vo)], vi[(j + 1) % len(vi)]])
    _finish_mesh(col, bm_t, "Slad_Biezni", [trace])

    # Bandy reklamowe na słupach na koronie łuku południowego (atlas ads_crown.png: 4 wiersze 4:1)
    bm_ad = bmesh.new()
    uv = bm_ad.loops.layers.uv.verify()
    r = R_TRACK_OUT + STAND_DEPTH - 0.4
    for ang, row in SOUTH_ADS:
        (x, y), a = _arc_point(r, ang)
        board = _obox(bm_ad, (x, y, STAND_H + 3.05), (0.08, 3.6, 0.9), yaw=a)
        v0, v1 = 1.0 - (row + 1) / 4.0, 1.0 - row / 4.0
        tangent = mathutils.Vector((-math.sin(a), math.cos(a), 0.0))
        radial = mathutils.Vector((math.cos(a), math.sin(a), 0.0))
        for f in {f for v in board['verts'] for f in v.link_faces}:
            front = f.normal.dot(radial) < -0.9                     # lico skierowane do boiska
            for loop in f.loops:
                p = loop.vert.co - mathutils.Vector((x, y, STAND_H + 3.05))
                if front:
                    u = 0.5 - p.dot(tangent) / 3.6                  # od lewej patrząc z boiska
                    v = v0 + (p.z / 0.9 + 0.5) * (v1 - v0)
                    loop[uv].uv = (u, v)
                else:
                    loop[uv].uv = (0.004, v0 + 0.004)               # biały margines atlasu
        for side in (-1.3, 1.3):
            sx, sy = x + side * tangent.x, y + side * tangent.y
            _obox(bm_ad, (sx, sy, STAND_H + 1.3), (0.1, 0.1, 2.6), yaw=a)
    _finish_mesh(col, bm_ad, "Bandy_Korona_Luk", [mats['ads_crown']])


def _flat(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


def build_fan_banners(col, mats):
    """
    Tworzy kibicowskie banery i historyczne graffiti wzdłuż prostej wschodniej ("Galera").
    """
    bm = bmesh.new()
    BX = R_TRACK_OUT - 0.03  # lico muru oporowego Galery
    BY_START = -32.5   # między tunelami Galery (GALERA_TUNNELS)
    BY_END = 32.5
    BZ_BOT = 0.2
    BZ_TOP = 1.3
    
    # Czoło od strony boiska (widok z murawy i Trybuny Głównej ku Galerze)
    pts_front = [
        (BX - 0.02, BY_END,   BZ_BOT),
        (BX - 0.02, BY_START, BZ_BOT),
        (BX - 0.02, BY_START, BZ_TOP),
        (BX - 0.02, BY_END,   BZ_TOP)
    ]
    f_front = bm.faces.new([bm.verts.new(p) for p in pts_front])
    uv_layer = bm.loops.layers.uv.verify()
    for loop in f_front.loops:
        u = (BY_END - loop.vert.co.y) / (BY_END - BY_START)
        v = (loop.vert.co.z - BZ_BOT) / (BZ_TOP - BZ_BOT)
        loop[uv_layer].uv = (u, v)

    # Tył od strony korony trybuny Galera
    pts_back = [
        (BX + 0.02, BY_START, BZ_BOT),
        (BX + 0.02, BY_END,   BZ_BOT),
        (BX + 0.02, BY_END,   BZ_TOP),
        (BX + 0.02, BY_START, BZ_TOP)
    ]
    f_back = bm.faces.new([bm.verts.new(p) for p in pts_back])
    for loop in f_back.loops:
        u = (loop.vert.co.y - BY_START) / (BY_END - BY_START)
        v = (loop.vert.co.z - BZ_BOT) / (BZ_TOP - BZ_BOT)
        loop[uv_layer].uv = (u, v)
        
    mesh_b = bpy.data.meshes.new("Banery_Kibicowskie_Galera_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh_b)
    bm.free()
    
    obj_b = bpy.data.objects.new("Banery_Kibicowskie_Galera", mesh_b)
    if mats and 'fan_banners' in mats:
        obj_b.data.materials.append(mats['fan_banners'])
    col.objects.link(obj_b)
    return obj_b


def build_scoreboard(col, mats):
    """
    Historyczna tablica wyników z zegarem stojąca na KORONIE KRÓTKIEJ TRYBUNY OD POŁUDNIA.
    Skierowana na północ (+Y), twarzą do murawy i Trybuny Głównej.
    Czoło tablicy posiada autentyczną teksturę ze zdjęcia archiwalnego (z zegarem, matrycą i napisem).
    """
    BOARD_W = 20.0
    BOARD_H = 7.5
    BOARD_D = 1.2
    CLEARANCE = 4.2 # słupy nośne nad wałem
    
    # 1. Konstrukcja i skrzynia tablicy
    bm_board = bmesh.new()
    uv_layer = bm_board.loops.layers.uv.verify()
    
    # 2 słupy nośne
    COL_R = 0.50
    for sy in [-BOARD_W/3.5, BOARD_W/3.5]:
        c = bmesh.ops.create_cone(
            bm_board,
            cap_ends=True,
            segments=12,
            radius1=COL_R,
            radius2=COL_R,
            depth=CLEARANCE + 1.0
        )
        bmesh.ops.translate(bm_board, vec=(0.0, sy, (CLEARANCE + 1.0)/2.0), verts=c['verts'])

    # Skrzynia tablicy (czoło w -X w lokalnym układzie)
    box = bmesh.ops.create_cube(bm_board, size=1.0)
    bmesh.ops.scale(bm_board, vec=(BOARD_D, BOARD_W, BOARD_H), verts=box['verts'])
    bmesh.ops.translate(bm_board, vec=(0.0, 0.0, CLEARANCE + BOARD_H/2.0), verts=box['verts'])

    # Mapowanie UV i indeksy materiałów dla skrzyni tablicy i słupów
    for f in bm_board.faces:
        # Płyta czołowa skrzyni skierowana w stronę murawy (-X)
        if f.normal.x < -0.8 and f.calc_center_median().z > CLEARANCE:
            f.material_index = 1 # Mat_Board_Historic
            for loop in f.loops:
                u = (BOARD_W / 2.0 - loop.vert.co.y) / BOARD_W
                v = (loop.vert.co.z - CLEARANCE) / BOARD_H
                loop[uv_layer].uv = (u, v)
        else:
            f.material_index = 0 # Mat_Board_Dark (stalowa obudowa i słupy)
            for loop in f.loops:
                loop[uv_layer].uv = (0.1, 0.1)

    mesh_board = bpy.data.meshes.new("Tablica_Wynikow_Mesh")
    bm_board.normal_update()
    bm_board.to_mesh(mesh_board)
    bm_board.free()

    obj_board = bpy.data.objects.new("Tablica_Wynikow_Zegar", mesh_board)
    # Pozycja: na koronie krótkiej trybuny od południa (X = 0.0m, Y = -110.5m, Z = 6.8m)
    obj_board.location = (0.0, -110.5, 6.8)
    # Obrót o -90° wokół Z (normalna czoła z -X obraca się w stronę +Y ku murawie)
    obj_board.rotation_euler = (0.0, 0.0, math.radians(-90))
    
    if mats and 'board_dark' in mats:
        obj_board.data.materials.append(mats['board_dark'])       # Index 0
    if mats and 'board_historic' in mats:
        obj_board.data.materials.append(mats['board_historic'])   # Index 1
        
    col.objects.link(obj_board)
    return obj_board

if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import sys, os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from build_grandstand import create_materials
    
    mats = create_materials()
    col = bpy.data.collections.new("Test_Bowl")
    bpy.context.scene.collection.children.link(col)
    
    build_pitch_and_track(col, mats)
    build_bowl(col, mats)
    build_scoreboard(col, mats)
    
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bowl_v2_test.blend"))
    print("Zapisano test korony z bieznią i zegarem vis a vis.")
