"""
Generowanie Trybuny Głównej (Zachodniej) Stadionu ŁKS Łódź, stan ok. 2010–2012.
Przekrój wg rysunku J. Wyżnikiewicza (1969), długość i rozstaw przęseł wg ortofotomapy 2013 (docs/zrodla.md):
- 14 przęseł × ~9.3 m (130 m), 15 dźwigarów z ukośnymi odciągami od strony zachodniej
- Sektor dolny: 10 rzędów pod daszkiem (biały–czerwony–biały), promenada na 3.2 m
- Sektor górny: 33 rzędy ławek, korona ok. 18.4 m nad terenem, bez dachu
- 4 tunele ze schodami z hali pod trybuną do połowy sektora górnego
- Podwieszony budynek z tyłu (wstęga okien od zachodu, strona Atlas Areny)
"""

import bpy
import bmesh
import mathutils
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "textures")

def setup_pbr_nodes(mat, color_path=None, normal_path=None, roughness_path=None, scale=(1.0, 1.0)):
    """Dołącza tekstury PBR do materiału w Blenderze."""
    if not mat.use_nodes:
        mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        return
        
    tex_coord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (scale[0], scale[1], 1.0)
    links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    
    if color_path and os.path.exists(color_path):
        img_color = bpy.data.images.load(color_path)
        node_color = nodes.new('ShaderNodeTexImage')
        node_color.image = img_color
        links.new(mapping.outputs['Vector'], node_color.inputs['Vector'])
        links.new(node_color.outputs['Color'], bsdf.inputs['Base Color'])
        
    if roughness_path and os.path.exists(roughness_path):
        img_rough = bpy.data.images.load(roughness_path)
        img_rough.colorspace_settings.name = 'Non-Color'
        node_rough = nodes.new('ShaderNodeTexImage')
        node_rough.image = img_rough
        links.new(mapping.outputs['Vector'], node_rough.inputs['Vector'])
        links.new(node_rough.outputs['Color'], bsdf.inputs['Roughness'])
        
    if normal_path and os.path.exists(normal_path):
        img_norm = bpy.data.images.load(normal_path)
        img_norm.colorspace_settings.name = 'Non-Color'
        node_norm = nodes.new('ShaderNodeTexImage')
        node_norm.image = img_norm
        node_norm_map = nodes.new('ShaderNodeNormalMap')
        links.new(mapping.outputs['Vector'], node_norm.inputs['Vector'])
        links.new(node_norm.outputs['Color'], node_norm_map.inputs['Color'])
        links.new(node_norm_map.outputs['Normal'], bsdf.inputs['Normal'])

def make_alpha_material(name, tex_path, roughness):
    """Materiał z teksturą RGBA (siatki, ogrodzenia): kolor i alfa z obrazu, alpha clip, dwustronny."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Roughness'].default_value = roughness
        if os.path.exists(tex_path):
            node_tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
            node_tex.image = bpy.data.images.load(tex_path)
            tc = mat.node_tree.nodes.new('ShaderNodeTexCoord')
            mat.node_tree.links.new(tc.outputs['UV'], node_tex.inputs['Vector'])
            mat.node_tree.links.new(node_tex.outputs['Color'], bsdf.inputs['Base Color'])
            mat.node_tree.links.new(node_tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    if hasattr(mat, 'blend_method'):
        mat.blend_method = 'CLIP'
        mat.alpha_threshold = 0.20
    if hasattr(mat, 'use_backface_culling'):
        mat.use_backface_culling = False
    return mat


def create_materials():
    """Tworzy zoptymalizowane materiały PBR dla stadionu z autentycznymi teksturami CC0 i grafikami ŁKS."""
    mats = {}
    
    # 1. Surowy beton brutalistyczny (PBR CC0)
    mat_concrete = bpy.data.materials.new("Mat_Concrete_Brutalist")
    mat_concrete.use_nodes = True
    bsdf = mat_concrete.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.55, 0.53, 0.50, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.85
    c_col = os.path.join(TEXTURES_DIR, "concrete", "Concrete019_1K-JPG_Color.jpg")
    c_norm = os.path.join(TEXTURES_DIR, "concrete", "Concrete019_1K-JPG_NormalGL.jpg")
    c_rough = os.path.join(TEXTURES_DIR, "concrete", "Concrete019_1K-JPG_Roughness.jpg")
    setup_pbr_nodes(mat_concrete, c_col, c_norm, c_rough, scale=(1.33, 1.33))
    mats['concrete'] = mat_concrete

    # 2. Ciemny beton (fosa, fundamenty)
    mat_concrete_dark = bpy.data.materials.new("Mat_Concrete_Dark")
    mat_concrete_dark.use_nodes = True
    bsdf = mat_concrete_dark.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.32, 0.31, 0.30, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.92
    setup_pbr_nodes(mat_concrete_dark, c_col, c_norm, c_rough, scale=(1.33, 1.33))
    mats['concrete_dark'] = mat_concrete_dark

    # 3. Fotorealistyczna murawa z pasami koszenia (PBR CC0)
    mat_grass = bpy.data.materials.new("Mat_Grass_Pitch")
    mat_grass.use_nodes = True
    bsdf = mat_grass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.22, 0.48, 0.18, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.90
    g_col = os.path.join(TEXTURES_DIR, "pitch_grass_mowed.jpg")
    g_norm = os.path.join(TEXTURES_DIR, "grass", "Grass001_1K-JPG_NormalGL.jpg")
    # Bez mapy chropowatości Grass001: jej wartości (~0.5) dawały połysk mokrej murawy pod jasnym niebem
    setup_pbr_nodes(mat_grass, g_col, g_norm, None, scale=(1.0, 1.0))
    bsdf.inputs['Roughness'].default_value = 0.95
    mats['grass'] = mat_grass

    # 4. Kredowe linie piłkarskie
    mat_lines = bpy.data.materials.new("Mat_Pitch_Lines")
    mat_lines.use_nodes = True
    bsdf = mat_lines.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.96, 0.96, 0.95, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.90
    mats['pitch_lines'] = mat_lines

    # 5. Szkło okien hali
    mat_glass = bpy.data.materials.new("Mat_Glass_Ribbon")
    mat_glass.use_nodes = True
    bsdf = mat_glass.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.18, 0.24, 0.28, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.15
    mats['glass'] = mat_glass

    # 6. Drewno / ławki
    mat_wood = bpy.data.materials.new("Mat_Wood_Benches")
    mat_wood.use_nodes = True
    bsdf = mat_wood.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.80, 0.76, 0.64, 1.0)  # malowane drewno, kość słoniowa (zdjęcia 2010–2012)
        bsdf.inputs['Roughness'].default_value = 0.70
    mats['wood'] = mat_wood

    # 7. Metal / stal ocynkowana (jupitery, barierki)
    mat_metal = bpy.data.materials.new("Mat_Galvanized_Steel")
    mat_metal.use_nodes = True
    bsdf = mat_metal.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.65, 0.67, 0.70, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.75
        bsdf.inputs['Roughness'].default_value = 0.35
    mats['metal'] = mat_metal

    # 8. Biała blacha trapezowa daszku dolnego sektora
    mat_rw = bpy.data.materials.new("Mat_Roof_Corrugated_White")
    mat_rw.use_nodes = True
    bsdf = mat_rw.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.92, 0.92, 0.92, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.20
        bsdf.inputs['Roughness'].default_value = 0.45
    rw_col = os.path.join(TEXTURES_DIR, "roof_corrugated_white.jpg")
    setup_pbr_nodes(mat_rw, rw_col, scale=(4.0, 4.0))
    mats['roof_white'] = mat_rw

    # 9. Czerwona blacha trapezowa daszku dolnego sektora (ŁKS Red)
    mat_rr = bpy.data.materials.new("Mat_Roof_Corrugated_Red")
    mat_rr.use_nodes = True
    bsdf = mat_rr.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.76, 0.10, 0.12, 1.0)
        bsdf.inputs['Metallic'].default_value = 0.20
        bsdf.inputs['Roughness'].default_value = 0.45
    rr_col = os.path.join(TEXTURES_DIR, "roof_corrugated_red.jpg")
    setup_pbr_nodes(mat_rr, rr_col, scale=(4.0, 4.0))
    mats['roof_red'] = mat_rr

    # Czerwień klubowa ŁKS (ogólna)
    mat_red = bpy.data.materials.new("Mat_LKS_Red")
    mat_red.use_nodes = True
    bsdf = mat_red.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.76, 0.10, 0.12, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.60
    mats['lks_red'] = mat_red

    # 10. Biała fasada obróbki blacharskiej daszku
    mat_fascia = bpy.data.materials.new("Mat_Fascia_White")
    mat_fascia.use_nodes = True
    bsdf = mat_fascia.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.94, 0.94, 0.92, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.40
        bsdf.inputs['Metallic'].default_value = 0.15
    mats['fascia'] = mat_fascia

    # 11. Biały murek z czerwoną Przeplatanką ŁKS na wyższej trybunie (z oficjalnej grafiki)
    mat_przp = bpy.data.materials.new("Mat_Przeplatanka_Wall")
    mat_przp.use_nodes = True
    bsdf = mat_przp.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.96, 0.96, 0.94, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.70
    przp_col = os.path.join(TEXTURES_DIR, "przeplatanka_wall.png")
    setup_pbr_nodes(mat_przp, przp_col, scale=(1.0, 1.0))
    for node in mat_przp.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            node.extension = 'EXTEND'      # glTF: CLAMP_TO_EDGE — białe tło poza herbem
    mats['przeplatanka'] = mat_przp

    # 14. Świecące reflektory jupiterów (oślepiający biały blask w nocy)
    mat_lamp = bpy.data.materials.new("Mat_Lamp_Glow")
    mat_lamp.use_nodes = True
    bsdf = mat_lamp.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = (1.0, 1.0, 1.0, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 50.0
    mats['lamp_glow'] = mat_lamp

    # 15. Czerwone światło ostrzegawcze na szczycie jupitera
    mat_beacon = bpy.data.materials.new("Mat_Beacon_Red")
    mat_beacon.use_nodes = True
    bsdf = mat_beacon.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (1.0, 0.05, 0.05, 1.0)
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = (1.0, 0.05, 0.05, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 10.0
    mats['lamp_beacon'] = mat_beacon

    # 16. Ciemna tablica wyników i konstrukcja
    mat_board = bpy.data.materials.new("Mat_Board_Dark")
    mat_board.use_nodes = True
    bsdf = mat_board.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.12, 0.13, 0.14, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.7
    mats['board_dark'] = mat_board

    # 17. Autentyczna historyczna tablica wyników z zegarem (z archiwalnego zdjęcia)
    mat_bh = bpy.data.materials.new("Mat_Board_Historic")
    mat_bh.use_nodes = True
    bsdf = mat_bh.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.65
    bh_col = os.path.join(TEXTURES_DIR, "scoreboard_historic.png")
    bh_em = os.path.join(TEXTURES_DIR, "scoreboard_emission.png")
    setup_pbr_nodes(mat_bh, bh_col, scale=(1.0, 1.0))
    if os.path.exists(bh_em):
        img_em = bpy.data.images.load(bh_em)
        node_em = mat_bh.node_tree.nodes.new('ShaderNodeTexImage')
        node_em.image = img_em
        tc = mat_bh.node_tree.nodes.get('ShaderNodeTexCoord')
        if tc:
            mat_bh.node_tree.links.new(tc.outputs['UV'], node_em.inputs['Vector'])
        if 'Emission Color' in bsdf.inputs:
            mat_bh.node_tree.links.new(node_em.outputs['Color'], bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = 1.8
    mats['board_historic'] = mat_bh

    # 18. Kibicowskie banery wzdłuż boiska
    mat_fan = bpy.data.materials.new("Mat_Fan_Banners")
    mat_fan.use_nodes = True
    bsdf = mat_fan.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.90, 0.90, 0.90, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.65
    fan_col = os.path.join(TEXTURES_DIR, "fan_graffiti_banners.png")
    setup_pbr_nodes(mat_fan, fan_col, scale=(1.0, 1.0))
    mats['fan_banners'] = mat_fan

    # 19. Lakierowane na biało bramki piłkarskie
    mat_gw = bpy.data.materials.new("Mat_Goal_White")
    mat_gw.use_nodes = True
    bsdf = mat_gw.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.96, 0.96, 0.96, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.20
        bsdf.inputs['Metallic'].default_value = 0.15
    mats['goal_white'] = mat_gw

    # 20. Siatka bramki w biało-czerwono-białe pasy (Ajax / ŁKS) z przezroczystością
    mats['goal_net'] = make_alpha_material("Mat_Goal_Net", os.path.join(TEXTURES_DIR, "goal_net_striped.png"), 0.85)

    # 21. Stalowe ogrodzenie trybun (czerwone przęsła z prętami, zdjęcia 516e09e41f411 / 516e09e800a6f)
    # 22. Trawa terenu wokół stadionu (Grass001, kafel ~2 m przy UV = 4 m / jednostkę)
    mat_ground = bpy.data.materials.new("Mat_Ground_Grass")
    mat_ground.use_nodes = True
    bsdf = mat_ground.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Roughness'].default_value = 0.95
    setup_pbr_nodes(mat_ground, os.path.join(TEXTURES_DIR, "grass", "Grass001_1K-JPG_Color.jpg"), scale=(2.0, 2.0))
    mats['ground_grass'] = mat_ground

    # 23. Bandy reklamowe na koronie łuku południowego (atlas 4 reklam, widok_na_zegar_u2.png)
    mat_ads = bpy.data.materials.new("Mat_Bandy_Reklamowe")
    mat_ads.use_nodes = True
    bsdf = mat_ads.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Roughness'].default_value = 0.6
    setup_pbr_nodes(mat_ads, os.path.join(TEXTURES_DIR, "ads_crown.png"), scale=(1.0, 1.0))
    mats['ads_crown'] = mat_ads

    mats['fence'] = make_alpha_material("Mat_Fence_Red", os.path.join(TEXTURES_DIR, "fence_steel_red.png"), 0.55)

    return mats


# 14 przęseł × ~9.3 m: rozstaw dźwigarów i długość zmierzone na ortofotomapie 2013 (docs/zrodla.md)
TOTAL_LENGTH_Y = 130.0
NUM_BAYS = 14
BAY_WIDTH_Y = TOTAL_LENGTH_Y / NUM_BAYS  # ~9.29 m

# Przekrój wg rysunku J. Wyżnikiewicza (1969), docs/zrodla.md. Układ lokalny: X — od czoła (bieżni)
# w głąb trybuny, Y — wzdłuż trybuny (0..TOTAL_LENGTH_Y), Z — w górę. Wartości lekko uproszczone,
# żeby każdy stopień dał się przejść (podstopień < 0.48 m, prześwit > 2 m).
LOWER_X0, LOWER_ROWS, LOWER_DX, LOWER_Z0, LOWER_DZ = 0.25, 10, 0.835, 0.5, 0.30   # sektor dolny: do X 8.6, Z 3.2
FRONT_PARAPET_H = 1.1
CONCOURSE_X1 = 11.2                     # promenada między sektorami na Z 3.2
CONCOURSE_Z = LOWER_Z0 + (LOWER_ROWS - 1) * LOWER_DZ
UPPER_X0, UPPER_ROWS, UPPER_Z0 = 11.5, 33, 5.5
UPPER_X1, UPPER_Z1 = 37.2, 18.4         # korona: ~18.4 m nad terenem
UPPER_DX = (UPPER_X1 - UPPER_X0) / UPPER_ROWS
UPPER_DZ = (UPPER_Z1 - UPPER_Z0) / (UPPER_ROWS - 1)
LIP_X = 11.4                            # balustrada czołowa sektora górnego (biały murek z Przeplatanką)
LIP_TOP = UPPER_Z0 + 1.0
REAR_X = 37.6
CANOPY_BACK_Z = 5.4                     # tylna krawędź daszku sektora dolnego (przy balustradzie sektora górnego)
PRZEPLATANKA_ASPECT = 4.0               # przeplatanka_wall.png: 2048 x 512
SLAB = 0.9                              # grubość płyty widowni pod nosami stopni


def underside(x):
    """Spód płyty sektora górnego (rośnie równolegle do widowni)."""
    return UPPER_Z0 - SLAB + (x - LIP_X) * (UPPER_Z1 - UPPER_Z0) / (UPPER_X1 - UPPER_X0)


def upper_row(i):
    """(x_początku, x_końca, z) stopnia i sektora górnego."""
    x = UPPER_X0 + i * UPPER_DX
    return x, x + UPPER_DX, UPPER_Z0 + i * UPPER_DZ


# Tunele (vomitoria): schody z hali pod trybuną, wyjście na stopień VOM_EXIT_ROW w połowie przęsła
VOM_BAYS = (2, 5, 8, 11)
VOM_EXIT_ROW = 6
VOM_SLOT_ROWS = 4                       # usunięte stopnie nad biegiem schodów (prześwit > 2.1 m)
VOM_WIDTH = 2.4
VOM_WALL = 0.25
VOM_RISE, VOM_TREAD = 0.2933, 0.42


def _extrude_profile(bm, pts_xz, y0, y1):
    """Bryła z wielokąta w płaszczyźnie XZ wyciągniętego od y0 do y1 (zamknięta — kolizje z obu stron)."""
    face = bm.faces.new([bm.verts.new((x, y0, z)) for x, z in pts_xz])
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    ev = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0.0, y1 - y0, 0.0), verts=ev)


def _box(bm, x0, x1, y0, y1, z0, z1):
    c = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=c['verts'])
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=c['verts'])


def _finish(col, bm, name, mat):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj


def _lower_profile():
    pts = [(0.0, 0.0), (0.0, FRONT_PARAPET_H), (LOWER_X0, FRONT_PARAPET_H)]
    for i in range(LOWER_ROWS):
        z = LOWER_Z0 + i * LOWER_DZ
        pts += [(LOWER_X0 + i * LOWER_DX, z), (LOWER_X0 + (i + 1) * LOWER_DX, z)]
    pts += [(CONCOURSE_X1, CONCOURSE_Z), (CONCOURSE_X1, 0.0)]
    return pts


def _upper_profiles(slot=None):
    """Wielokąty XZ sektora górnego; slot=(i0, i1) wycina stopnie i0..i1-1 nad biegiem schodów tunelu."""
    def treads(i0, i1):
        out = []
        for i in range(i0, i1):
            x0, x1, z = upper_row(i)
            out += [(x0, z), (x1, z)]
        return out

    if slot is None:
        front = [(LIP_X, underside(LIP_X)), (LIP_X, LIP_TOP), (UPPER_X0, LIP_TOP)] + treads(0, UPPER_ROWS)
        return [front + [(UPPER_X1, UPPER_Z1 + 1.0), (REAR_X, UPPER_Z1 + 1.0), (REAR_X, underside(REAR_X))]]
    i0, i1 = slot
    xa, xb = upper_row(i0)[0], upper_row(i1)[0]
    front = [(LIP_X, underside(LIP_X)), (LIP_X, LIP_TOP), (UPPER_X0, LIP_TOP)] + treads(0, i0) + [(xa, underside(xa))]
    back = [(xb, underside(xb))] + treads(i1, UPPER_ROWS) + [(UPPER_X1, UPPER_Z1 + 1.0), (REAR_X, UPPER_Z1 + 1.0), (REAR_X, underside(REAR_X))]
    return [front, back]


def build_grandstand(col, mats):
    """
    Trybuna główna w lokalnym układzie (patrz stałe przekroju). 14 przęseł budowanych jawnie,
    bo przęsła z tunelami (VOM_BAYS) mają wycięcie w widowni. Każdy element to zamknięta bryła:
    kolizje Octree w Three.js są jednostronne.
    """
    bm_lower, bm_upper, bm_girder, bm_vom, bm_stairs = (bmesh.new() for _ in range(5))
    bm_benches, bm_lights = bmesh.new(), bmesh.new()

    # Sektor dolny + promenada (jedna bryła na całą długość)
    _extrude_profile(bm_lower, _lower_profile(), 0.0, TOTAL_LENGTH_Y)

    # Schody z terenu na promenadę na obu krańcach trybuny
    n_end = math.ceil(CONCOURSE_Z / 0.3)
    for sign, y_edge in ((-1, 0.0), (1, TOTAL_LENGTH_Y)):
        for k in range(n_end):
            ya = y_edge + sign * (n_end - k - 1) * 0.42
            yb = ya + sign * 0.42
            _box(bm_stairs, LOWER_X0 + (LOWER_ROWS - 1) * LOWER_DX, CONCOURSE_X1, min(ya, yb), max(ya, yb), 0.0, (k + 1) * CONCOURSE_Z / n_end)

    exit_x0, _, exit_z = upper_row(VOM_EXIT_ROW)
    n_steps = math.ceil(exit_z / VOM_RISE)
    vom_x_start = exit_x0 + n_steps * VOM_TREAD
    slot = (VOM_EXIT_ROW, VOM_EXIT_ROW + VOM_SLOT_ROWS)

    for b in range(NUM_BAYS):
        y0, y1 = b * BAY_WIDTH_Y, (b + 1) * BAY_WIDTH_Y
        yc = (y0 + y1) / 2

        # Widownia sektora górnego (z wycięciem nad tunelem)
        if b in VOM_BAYS:
            sa, sb = yc - VOM_WIDTH / 2, yc + VOM_WIDTH / 2
            for prof in _upper_profiles():
                _extrude_profile(bm_upper, prof, y0, sa)
                _extrude_profile(bm_upper, prof, sb, y1)
            for prof in _upper_profiles(slot):
                _extrude_profile(bm_upper, prof, sa, sb)

            # Schody tunelu (bryły od terenu) i ściany boczne: tunel pod płytą, balustrada w wycięciu
            for k in range(n_steps):
                xs1 = vom_x_start - k * VOM_TREAD
                _box(bm_stairs, xs1 - VOM_TREAD, xs1, sa + VOM_WALL, sb - VOM_WALL, 0.0, (k + 1) * VOM_RISE)
            xb = upper_row(slot[1])[0]
            wall = [(exit_x0, 0.0), (exit_x0, exit_z + 1.0), (xb, upper_row(slot[1])[2] + 1.0),
                    (xb, underside(xb)), (vom_x_start, underside(vom_x_start)), (vom_x_start, 0.0)]
            _extrude_profile(bm_vom, wall, sa, sa + VOM_WALL)
            _extrude_profile(bm_vom, wall, sb - VOM_WALL, sb)
        else:
            for prof in _upper_profiles():
                _extrude_profile(bm_upper, prof, y0, y1)

        # Ławki sektora górnego (malowane drewno, kość słoniowa): siedzisko 0.40 m nad stopniem, wsporniki co ~1.5 m
        for i in range(UPPER_ROWS):
            xa, xbb, z = upper_row(i)
            spans = [(y0 + 0.9, y1 - 0.1)]
            if b in VOM_BAYS and slot[0] <= i < slot[1]:
                spans = [(y0 + 0.9, yc - VOM_WIDTH / 2 - 0.1), (yc + VOM_WIDTH / 2 + 0.1, y1 - 0.1)]
            for ya, yb in spans:
                bx = xa + UPPER_DX * 0.35
                _box(bm_benches, bx - 0.16, bx + 0.16, ya, yb, z + 0.37, z + 0.42)
                n_leg = max(2, int((yb - ya) / 1.5) + 1)
                for k in range(n_leg):
                    ly = ya + 0.1 + k * (yb - ya - 0.2) / (n_leg - 1)
                    _box(bm_benches, bx - 0.12, bx + 0.12, ly - 0.03, ly + 0.03, z, z + 0.37)

        # Słupki oświetleniowe na koronie
        POLE_H = 3.2
        _box(bm_lights, UPPER_X1 + 0.12, UPPER_X1 + 0.24, yc - 0.06, yc + 0.06, UPPER_Z1 + 1.0, UPPER_Z1 + 1.0 + POLE_H)
        _box(bm_lights, UPPER_X1 + 0.05, UPPER_X1 + 0.35, yc - 0.65, yc + 0.65, UPPER_Z1 + 1.0 + POLE_H - 0.1, UPPER_Z1 + 1.0 + POLE_H)

    # Dźwigary (15 osi): belka pod płytą, słup czołowy, ukośny odciąg do terenu za trybuną
    for b in range(NUM_BAYS + 1):
        y = b * BAY_WIDTH_Y
        ya, yb = y - 0.25, y + 0.25
        beam = [(LIP_X, underside(LIP_X)), (REAR_X, underside(REAR_X)), (REAR_X, underside(REAR_X) - 1.6), (LIP_X + 0.6, underside(LIP_X + 0.6) - 1.0)]
        _extrude_profile(bm_girder, beam, ya, yb)
        _box(bm_girder, LIP_X, LIP_X + 0.6, ya, yb, 0.0, underside(LIP_X))
        sx = 30.0
        strut = [(sx, underside(sx) - 1.0), (sx + 0.8, underside(sx + 0.8) - 1.0), (39.4, 0.0), (38.6, 0.0)]
        _extrude_profile(bm_girder, strut, y - 0.22, y + 0.22)

    obj_lower = _finish(col, bm_lower, "Widownia_Dolna", mats['concrete'])
    obj_upper = _finish(col, bm_upper, "Widownia_Gorna", mats['concrete'])
    _finish(col, bm_girder, "Dzwigary_i_Odciagi", mats['concrete'])
    _finish(col, bm_vom, "Tunele_Sciany", mats['concrete'])
    _finish(col, bm_stairs, "Schody_Tunele_i_Promenada", mats['concrete_dark'])
    _finish(col, bm_benches, "Lawki_Sektor_Gorny", mats['wood'])
    _finish(col, bm_lights, "Latarnie_Korona", mats['metal'])

    # Podwieszony budynek z tyłu (biura/loże wg przekroju): X 32.5–41.5, Z 3.5–7.1, wstęga okien od zachodu
    bm_rear = bmesh.new()
    _box(bm_rear, 32.5, 41.5, 0.0, TOTAL_LENGTH_Y, 3.5, 7.1)
    _finish(col, bm_rear, "Pawilon_Zachodni", mats['concrete'])
    bm_w = bmesh.new()
    _box(bm_w, 41.5, 41.55, 0.4, TOTAL_LENGTH_Y - 0.4, 4.3, 6.4)
    _finish(col, bm_w, "Okna_Hala_Zachod", mats['glass'])

    # Daszek sektora dolnego: z czoła (X 0.6, Z 4.6) do balustrady sektora górnego (X 11.3, Z 5.4).
    # Podział kolorów jak na zdjęciach (widok_z_galery.jpg): od południowego krańca biały, czerwony, biały.
    def make_canopy_section(name, ya, yb, mat):
        bm = bmesh.new()
        prof = [(0.6, 4.6), (LIP_X - 0.1, CANOPY_BACK_Z), (LIP_X - 0.1, CANOPY_BACK_Z - 0.12), (0.6, 4.48)]
        _extrude_profile(bm, prof, ya, yb)
        uv_l = bm.loops.layers.uv.verify()
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_l].uv = (loop.vert.co.y / 4.0, loop.vert.co.x / 4.0)
        return _finish(col, bm, name, mat)

    make_canopy_section("Daszek_Bialy_Poludnie", 11.0 * BAY_WIDTH_Y, 14.0 * BAY_WIDTH_Y, mats['roof_white'])
    make_canopy_section("Daszek_Czerwony_Srodek", 6.0 * BAY_WIDTH_Y, 11.0 * BAY_WIDTH_Y, mats['roof_red'])
    make_canopy_section("Daszek_Bialy_Polnoc", 4.0 * BAY_WIDTH_Y, 6.0 * BAY_WIDTH_Y, mats['roof_white'])
    bm_f = bmesh.new()
    _box(bm_f, 0.5, 0.6, 4.0 * BAY_WIDTH_Y, 14.0 * BAY_WIDTH_Y, 4.3, 4.65)
    _finish(col, bm_f, "Blenda_Fasada_Biala", mats['roof_white'])

    # Biały murek z Przeplatanką ŁKS: lico balustrady czołowej sektora górnego, NAD daszkiem sektora dolnego
    # (tylna krawędź daszku na Z 5.4; widok_z_galery.jpg). Tekstura 4:1 z trybem EXTEND: u poza [0, 1]
    # przedłuża białe tło, więc herb zachowuje proporcje na szerokim, niskim panelu.
    bm_przp = bmesh.new()
    uv_przp = bm_przp.loops.layers.uv.verify()
    z_bot, z_top = CANOPY_BACK_Z + 0.06, LIP_TOP
    for k in range(NUM_BAYS):
        ya, yb = k * BAY_WIDTH_Y + 0.4, (k + 1) * BAY_WIDTH_Y - 0.4
        half_u = (yb - ya) / (z_top - z_bot) / PRZEPLATANKA_ASPECT / 2
        face = bm_przp.faces.new([bm_przp.verts.new(p) for p in [(LIP_X - 0.02, ya, z_bot), (LIP_X - 0.02, ya, z_top),
                                                               (LIP_X - 0.02, yb, z_top), (LIP_X - 0.02, yb, z_bot)]])
        for loop in face.loops:
            t = (yb - loop.vert.co.y) / (yb - ya)
            loop[uv_przp].uv = (0.5 + (t - 0.5) * 2 * half_u, (loop.vert.co.z - z_bot) / (z_top - z_bot))
    mesh_przp = bpy.data.meshes.new("Murki_Przeplatanka_Mesh")
    bm_przp.normal_update()
    bm_przp.to_mesh(mesh_przp)
    bm_przp.free()
    obj_przp = bpy.data.objects.new("Murki_Przeplatanka", mesh_przp)
    obj_przp.data.materials.append(mats['przeplatanka'])
    col.objects.link(obj_przp)

    print("Zbudowano Trybune Glowna wg przekroju Wyznikiewicza (33 + 10 rzedow, 4 tunele).")
    return obj_lower, obj_upper


def lower_seat_rows():
    """Rzędy krzesełek sektora dolnego: (x, z) siedziska w układzie lokalnym trybuny."""
    return [(LOWER_X0 + (i + 0.55) * LOWER_DX, LOWER_Z0 + i * LOWER_DZ) for i in range(LOWER_ROWS)]


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = create_materials()
    col = bpy.data.collections.new("LKS_Trybuna_Glowna")
    bpy.context.scene.collection.children.link(col)
    build_grandstand(col, mats)
    
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "trybuna_glowna_v2.blend"))
    print("Zapisano v2 trybuny glownej.")
