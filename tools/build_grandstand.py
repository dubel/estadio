"""
Generowanie Trybuny Głównej (Zachodniej) Stadionu ŁKS Łódź, stan ok. 2010–2012.
Przekrój wg rysunku J. Wyżnikiewicza (1969), długość i rozstaw przęseł wg ortofotomapy 2013 (docs/zrodla.md):
- 14 przęseł × ~9.3 m (130 m), 15 dźwigarów z ukośnymi odciągami od strony zachodniej
- Sektor dolny: 10 rzędów pod daszkiem (biały–czerwony–biały), promenada na 3.2 m
- Sektor górny: 33 rzędy ławek, korona ok. 18.4 m nad terenem, bez dachu
- tunel w każdym przęśle: schody z hali pod trybuną na 7. rząd sektora górnego, żółte barierki
- bloczki z Przeplatanką 4–5 rzędów nad daszkiem sektora dolnego, poniżej wyjść z tuneli
- ławki rezerwowych z pleksi wpuszczone w sektor dolny
- Podwieszony budynek z tyłu (wstęga okien od zachodu, strona Atlas Areny)
"""

import bpy
import bmesh
import mathutils
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_seats import place_seats, seat_material, SEAT_BACK_GAP  # noqa: E402

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

    # Blacha trapezowa ocynkowana ogrodzenia północnego (ambientCG CorrugatedSteel005, CC0)
    mat_sheet = bpy.data.materials.new("Mat_Blacha_Falista")
    mat_sheet.use_nodes = True
    bsdf = mat_sheet.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Metallic'].default_value = 0.6
    steel = os.path.join(TEXTURES_DIR, "corrugated_steel", "CorrugatedSteel005_1K-JPG_")
    setup_pbr_nodes(mat_sheet, steel + "Color.jpg", steel + "NormalGL.jpg", steel + "Roughness.jpg")
    mat_sheet.use_backface_culling = False
    mats['sheet_steel'] = mat_sheet

    # Mural „Tutaj wychowani … wierni i oddani” (grafy_na_trybunie.png,
    # tools/generate_stadium_textures.py: generate_mural_texture)
    m = bpy.data.materials.new("Mat_Mural_Tutaj_Wychowani")
    m.use_nodes = True
    m.node_tree.nodes.get("Principled BSDF").inputs['Roughness'].default_value = 0.85
    setup_pbr_nodes(m, os.path.join(TEXTURES_DIR, "mural_tutaj_wychowani.png"))
    mats['mural'] = m

    # Żółta farba: barierki i obrzeża tuneli (detale_trybuny_zachodniej.png, widok_z_galery.jpg)
    mats['yellow'] = seat_material("Mat_Barierki_Zolte", (0.85, 0.66, 0.08))

    # Mleczna pleksi ławek rezerwowych (lawka_rezerwowych.png): półprzezroczysta, dwustronna
    mat_plexi = bpy.data.materials.new("Mat_Pleksi_Mleczna")
    mat_plexi.use_nodes = True
    bsdf = mat_plexi.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = (0.90, 0.91, 0.92, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.35
    bsdf.inputs['Alpha'].default_value = 0.6
    if hasattr(mat_plexi, 'surface_render_method'):
        mat_plexi.surface_render_method = 'BLENDED'
    mat_plexi.use_backface_culling = False
    mats['plexi'] = mat_plexi

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


# Tunele (vomitoria) w każdym przęśle (widok_na_trybune_z_sektora_gosci.png): schody z hali pod trybuną,
# wyjście na stopień VOM_EXIT_ROW w osi przęsła. Ściany tunelu mają żółto malowane obrzeża
# (detale_trybuny_zachodniej.png).
VOM_EXIT_ROW = 6
VOM_SLOT_ROWS = 4                       # usunięte stopnie nad biegiem schodów (prześwit > 2.1 m)
VOM_WIDTH = 2.4
VOM_WALL = 0.25
VOM_RISE, VOM_TREAD = 0.2933, 0.42
AISLE_W = 1.4                           # przejście w osi przęsła: od korony do tunelu i od tunelu w dół

# Bloczki z Przeplatanką (bloczki_na_trybunie.png): rząd betonowych bloków na stopniu BLOCK_ROW, 4–5 rzędów
# nad daszkiem sektora dolnego i poniżej wyjść z tuneli. Stoją w osiach dźwigarów, więc przerwy między
# nimi wypadają pod tunelami — schodzący z tunelu nie trafia na bloczek.
BLOCK_ROW, BLOCK_W, BLOCK_H, BLOCK_D = 4, 3.6, 1.5, 0.4
# Mural na licu balustrady czołowej nad północną częścią sektora dolnego (grafy_na_trybunie.png):
# od MURAL_Y[0] (lewy koniec patrząc z boiska, południe) do MURAL_Y[1]; ok. 35 m według podziału na przęsła
MURAL_Y = (4.3 * TOTAL_LENGTH_Y / NUM_BAYS, 0.5 * TOTAL_LENGTH_Y / NUM_BAYS)
# Platforma kamery telewizyjnej na koronie na wysokości linii środkowej (grafy_na_trybunie.png,
# detale_trybuny_zachodniej.png): kabina na słupkach, otwarta ku boisku
CAMERA_Y = 68.0

# Ławki rezerwowych wpuszczone w sektor VIP (lawka_rezerwowych.png): ćwiartki walca z mlecznej pleksi
# na stelażu z białych i czerwonych profili. Linia środkowa boiska leży na Y lokalnym 68 (środek trybuny
# 3 m na północ od niej, build_full_stadium.py), ławki po ±12 m od niej. Zakresy Y w układzie lokalnym.
DUGOUTS = ((52.5, 59.5), (76.5, 83.5))
DUG_ROWS = 3                            # usunięte rzędy sektora dolnego nad wnęką ławki
DUG_X0 = 0.35                           # pionowe lico (oś walca) od czoła trybuny
DUG_R = 2.3                             # promień ćwiartki walca: dach 2.3 m nad posadzką przy licu

# Tunel harmonijkowy wyjścia piłkarzy (tunel_harmonijkowy.png) na linii środkowej, między ławkami rezerwowych:
# kanał wycięty w sektorze dolnym aż do rzędu, którego stopień jest wyższy niż tunel, w kanale drzwi do hali
# pod trybuną. Tunel złożony (wyciągany tylko na wyjście drużyn) jak harmonijka: stały przekrój, łuki stelaża
# ściśnięte co TUNNEL_FOLD, między nimi fałdy obicia wypchnięte na zewnątrz. Złożony wypełnia kanał od drzwi
# do wylotu, w środku da się przejść. Obicie w poprzeczne pasy biało-czerwone (fałda po fałdzie),
# w ścianach bocznych stelaż nożycowy.
TUNNEL_Y = (66.6, 69.4)
TUNNEL_ROWS = 7                         # usunięte rzędy: stopień 7. rzędu na 2.6 m, tunel ma 2.4 m
TUNNEL_HALF_W, TUNNEL_WALL_H = 1.1, 1.3 # połowa szerokości, ściana boczna pod półkolistym dachem
TUNNEL_FOLD, TUNNEL_PLEAT = 0.4, 0.12   # rozstaw łuków złożonego tunelu, wypchnięcie fałdy obicia
TUNNEL_FRONT_X = -0.3                   # wylot tunelu przed czołem trybuny

# Pawilon (loże/VIP) na tylnych rzędach sektora dolnego pod muralem (grafy_na_trybunie.png,
# widok_na_trybune_z_sektora_gosci.png): przed nim 3 rzędy krzesełek, ściany z blachy ocynkowanej, wstęga okien
# na całej długości. Od schodów na promenadę przy północnym krańcu do białego daszku (przęsło 4); z tyłu kończy
# się na ostatnim rzędzie, promenada za nim zostaje przejściem. Biały daszek nad pawilonem — jeszcze nie.
PAVILION_Y = (5.0, 4.0 * BAY_WIDTH_Y)
PAVILION_ROW = 3                        # pierwszy rząd pod pawilonem
PAVILION_TOP = 4.4
PAVILION_WIN = (2.4, 3.6)               # dół i góra wstęgi okien
PAVILION_MULLION = 1.6                  # rozstaw słupków okiennych
SHEET_TILE = 1.4                        # kafel tekstury blachy jak w ogrodzeniu (SHEET_TILE_M, build_horseshoe_bowl.py)

# Wycięcia w sektorze dolnym: (y0, y1, liczba usuniętych pierwszych rzędów)
LOWER_CUTS = sorted([(a, b, DUG_ROWS) for a, b in DUGOUTS] + [(*TUNNEL_Y, TUNNEL_ROWS)])


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


def _beam(bm, p0, p1, w=0.05, h=0.05):
    """Prostopadłościan od p0 do p1 o przekroju w × h (poręcze, profile stelaży)."""
    p0, p1 = mathutils.Vector(p0), mathutils.Vector(p1)
    d = p1 - p0
    ax = d.normalized()
    side = mathutils.Vector((0.0, 0.0, 1.0)).cross(ax)
    if side.length < 1e-6:                                  # odcinek pionowy
        side = mathutils.Vector((0.0, 1.0, 0.0))
    side.normalize()
    m = mathutils.Matrix((ax, side, ax.cross(side))).transposed().to_4x4()
    m.translation = (p0 + p1) / 2
    bmesh.ops.create_cube(bm, size=1.0, matrix=m @ mathutils.Matrix.Diagonal((d.length, w, h, 1.0)))


def _rail(bm, p0, p1, post_every):
    """Poręcz 0.9 m nad linią p0–p1 i słupki co post_every metrów (bryły — kolizje są jednostronne)."""
    p0, p1 = mathutils.Vector(p0), mathutils.Vector(p1)
    up = mathutils.Vector((0.0, 0.0, 0.9))
    _beam(bm, p0 + up, p1 + up)
    n = max(1, round((p1 - p0).length / post_every))
    for k in range(n + 1):
        p = p0.lerp(p1, k / n)
        _beam(bm, p, p + up, 0.05, 0.05)


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


def _lower_profile(first_row=0):
    """Przekrój sektora dolnego z promenadą; first_row > 0 — bez pierwszych rzędów (wnęka ławki rezerwowych)."""
    if first_row == 0:
        pts = [(0.0, 0.0), (0.0, FRONT_PARAPET_H), (LOWER_X0, FRONT_PARAPET_H)]
    else:
        pts = [(LOWER_X0 + first_row * LOWER_DX, 0.0)]
    for i in range(first_row, LOWER_ROWS):
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
    Trybuna główna w lokalnym układzie (patrz stałe przekroju). 14 przęseł budowanych jawnie, bo każde
    ma tunel z wycięciem w widowni. Każdy element to zamknięta bryła: kolizje Octree w Three.js są jednostronne.
    """
    bm_lower, bm_upper, bm_girder, bm_vom, bm_stairs = (bmesh.new() for _ in range(5))
    bm_benches, bm_lights, bm_yellow = bmesh.new(), bmesh.new(), bmesh.new()

    # Sektor dolny + promenada; we wnękach ławek rezerwowych i w kanale tunelu bez pierwszych rzędów
    y = 0.0
    for ya, yb, rows in LOWER_CUTS:
        _extrude_profile(bm_lower, _lower_profile(), y, ya)
        _extrude_profile(bm_lower, _lower_profile(rows), ya, yb)
        y = yb
    _extrude_profile(bm_lower, _lower_profile(), y, TOTAL_LENGTH_Y)

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
    xb, _, z_back = upper_row(slot[1])
    wall = [(exit_x0, 0.0), (exit_x0, exit_z + 1.0), (xb, z_back + 1.0),
            (xb, underside(xb)), (vom_x_start, underside(vom_x_start)), (vom_x_start, 0.0)]
    paint = [(exit_x0 - 0.01, exit_z + 0.8), (exit_x0 - 0.01, exit_z + 1.02), (xb, z_back + 1.02), (xb, z_back + 0.8)]
    in_slot = lambda i: slot[0] <= i < slot[1]
    # Bieg schodów tunelu jako jedna bryła z profilu zębatego: osobne stopnie-prostopadłościany miały
    # zdublowane ściany na podstopniach, a kontroler kapsuły zacinał się na nich zależnie od kolejności
    # trójkątów w Octree
    stair_profile = [(vom_x_start, 0.0)]
    for k in range(n_steps):
        xs1 = vom_x_start - k * VOM_TREAD
        stair_profile += [(xs1, (k + 1) * VOM_RISE), (xs1 - VOM_TREAD, (k + 1) * VOM_RISE)]
    stair_profile.append((exit_x0, 0.0))

    for b in range(NUM_BAYS):
        y0, y1 = b * BAY_WIDTH_Y, (b + 1) * BAY_WIDTH_Y
        yc = (y0 + y1) / 2
        sa, sb = yc - VOM_WIDTH / 2, yc + VOM_WIDTH / 2

        # Widownia sektora górnego z wycięciem nad tunelem
        for prof in _upper_profiles():
            _extrude_profile(bm_upper, prof, y0, sa)
            _extrude_profile(bm_upper, prof, sb, y1)
        for prof in _upper_profiles(slot):
            _extrude_profile(bm_upper, prof, sa, sb)

        # Schody tunelu (bryła od terenu), ściany boczne z żółtym obrzeżem i balustrada nad wylotem schodów
        _extrude_profile(bm_stairs, stair_profile, sa + VOM_WALL, sb - VOM_WALL)
        for wa in (sa, sb - VOM_WALL):
            _extrude_profile(bm_vom, wall, wa, wa + VOM_WALL)
            _extrude_profile(bm_yellow, paint, wa - 0.01, wa + VOM_WALL + 0.01)
        _box(bm_vom, xb, xb + 0.25, sa + VOM_WALL, sb - VOM_WALL, z_back, z_back + 1.0)
        _box(bm_yellow, xb - 0.01, xb + 0.26, sa + VOM_WALL, sb - VOM_WALL, z_back + 0.8, z_back + 1.02)

        # Przejście w osi przęsła (poza wycięciem): stopnie pośrednie i żółte poręcze po obu stronach
        for i in range(UPPER_ROWS - 1):
            if not in_slot(i) and not in_slot(i + 1):
                _, x1, z = upper_row(i)
                _box(bm_stairs, x1 - UPPER_DX / 2, x1, yc - AISLE_W / 2, yc + AISLE_W / 2, z, z + UPPER_DZ / 2)
        for yr in (yc - AISLE_W / 2 - 0.03, yc + AISLE_W / 2 + 0.03):
            for i0, i1 in ((0, slot[0] - 1), (slot[1], UPPER_ROWS - 1)):
                (xa, _, za), (xe, _, ze) = upper_row(i0), upper_row(i1)
                _rail(bm_yellow, (xa + UPPER_DX / 2, yr, za), (xe + UPPER_DX / 2, yr, ze), 2.5)

        # Ławki sektora górnego (malowane drewno, kość słoniowa): siedzisko 0.40 m nad stopniem, wsporniki co ~1.5 m.
        # Przerwa w osi przęsła (przejście albo wycięcie tunelu); w rzędzie bloczków ławki tylko między nimi.
        for i in range(UPPER_ROWS):
            xa, _, z = upper_row(i)
            half = VOM_WIDTH / 2 + 0.1 if in_slot(i) else AISLE_W / 2 + 0.05
            edge = BLOCK_W / 2 + 0.1 if i == BLOCK_ROW else 0.1
            spans = [(y0 + (edge if b > 0 else 0.1), yc - half), (yc + half, y1 - (edge if b < NUM_BAYS - 1 else 0.1))]
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

    # Żółte barierki wzdłuż trybuny: na balustradzie czołowej sektora górnego i na koronie
    _rail(bm_yellow, (LIP_X + 0.05, 0.3, LIP_TOP - 0.45), (LIP_X + 0.05, TOTAL_LENGTH_Y - 0.3, LIP_TOP - 0.45), 1.55)
    _rail(bm_yellow, (REAR_X - 0.08, 0.3, UPPER_Z1 + 0.6), (REAR_X - 0.08, TOTAL_LENGTH_Y - 0.3, UPPER_Z1 + 0.6), 1.55)

    # Bloczki z Przeplatanką w osiach wewnętrznych dźwigarów (lica malowideł buduje build_tribune_paintings)
    bx0, _, bz = upper_row(BLOCK_ROW)
    for k in range(1, NUM_BAYS):
        yk = k * BAY_WIDTH_Y
        _box(bm_upper, bx0, bx0 + BLOCK_D, yk - BLOCK_W / 2, yk + BLOCK_W / 2, bz - 0.05, bz + BLOCK_H)

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
    _finish(col, bm_yellow, "Barierki_Zolte_Trybuna", mats['yellow'])

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

    build_tribune_paintings(col, mats)
    build_camera_platform(col, mats)
    build_dugouts(col, mats)
    build_players_tunnel(col, mats)
    build_vip_pavilion(col, mats)

    print(f"Zbudowano Trybune Glowna wg przekroju Wyznikiewicza (33 + 10 rzedow, {NUM_BAYS} tuneli).")
    return obj_lower, obj_upper


def _wall_decal(col, name, mat, quads):
    """Płaskie lica malowideł skierowane ku boisku (-X): quads = [(x, y_lewy, y_prawy, z0, z1, (u0, u1), (v0, v1))].
    „Lewy” patrząc z boiska to większe Y (południe)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    for x, y_left, y_right, z0, z1, (u0, u1), (v0, v1) in quads:
        face = bm.faces.new([bm.verts.new(p) for p in [(x, y_right, z0), (x, y_right, z1), (x, y_left, z1), (x, y_left, z0)]])
        for loop in face.loops:
            t = (y_left - loop.vert.co.y) / (y_left - y_right)
            loop[uv].uv = (u0 + t * (u1 - u0), v0 + (loop.vert.co.z - z0) / (z1 - z0) * (v1 - v0))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    col.objects.link(obj)


def build_tribune_paintings(col, mats):
    """
    Malowidła na sektorze górnym:
    - Przeplatanka ŁKS na licach wszystkich bloczków; tekstura 4:1 z trybem EXTEND: u poza [0, 1] przedłuża
      białe tło, więc herb zachowuje proporcje na bloczku o innych proporcjach;
    - mural „Tutaj wychowani … wierni i oddani” na licu balustrady czołowej (MURAL_Y).
    """
    bx0, _, bz = upper_row(BLOCK_ROW)
    x, z_bot, z_top = bx0 - 0.02, bz, bz + BLOCK_H
    half_u = BLOCK_W / BLOCK_H / PRZEPLATANKA_ASPECT / 2
    przp = [(x, k * BAY_WIDTH_Y + BLOCK_W / 2, k * BAY_WIDTH_Y - BLOCK_W / 2, z_bot, z_top, (0.5 - half_u, 0.5 + half_u), (0.0, 1.0))
            for k in range(1, NUM_BAYS)]
    _wall_decal(col, "Murki_Przeplatanka", mats['przeplatanka'], przp)
    _wall_decal(col, "Mural_Tutaj_Wychowani", mats['mural'],
                [(LIP_X - 0.02, MURAL_Y[0], MURAL_Y[1], CANOPY_BACK_Z + 0.06, LIP_TOP, (0.0, 1.0), (0.0, 1.0))])


def build_camera_platform(col, mats):
    """
    Platforma kamery telewizyjnej na koronie (grafy_na_trybunie.png): kabina 2.2 × 2.2 m na czterech
    słupkach, podłoga 0.5 m nad koroną, ściany z tyłu i z boków, od boiska niski parapet, daszek z okapem.
    """
    bm = bmesh.new()
    y0, y1 = CAMERA_Y - 1.1, CAMERA_Y + 1.1
    xf, xb = UPPER_X1 - 1.8, REAR_X                     # przód kabiny nad 31. rzędem, tył na koronie
    floor_z, roof_z = UPPER_Z1 + 1.5, UPPER_Z1 + 3.7
    row_front = upper_row(int((xf - UPPER_X0) / UPPER_DX))
    for px, base in ((xf + 0.05, row_front[2]), (xb - 0.05, UPPER_Z1 + 1.0)):
        for py in (y0 + 0.05, y1 - 0.05):
            _box(bm, px - 0.05, px + 0.05, py - 0.05, py + 0.05, base, floor_z)
    _box(bm, xf, xb, y0, y1, floor_z, floor_z + 0.1)                   # podłoga
    _box(bm, xb - 0.06, xb, y0, y1, floor_z + 0.1, roof_z)             # ściana tylna
    for ya in (y0, y1 - 0.05):
        _box(bm, xf, xb, ya, ya + 0.05, floor_z + 0.1, roof_z)         # ściany boczne
    _box(bm, xf, xf + 0.05, y0, y1, floor_z + 0.1, floor_z + 1.0)      # parapet od boiska
    _box(bm, xf - 0.35, xb + 0.1, y0 - 0.1, y1 + 0.1, roof_z, roof_z + 0.08)   # daszek z okapem
    _finish(col, bm, "Platforma_Kamery", mats['metal'])


def build_dugouts(col, mats):
    """
    Ławki rezerwowych we wnękach sektora dolnego: powłoka z mlecznej pleksi (ćwiartka walca od dachu przy
    pionowym licu do posadzki z tyłu), boczne ścianki z pleksi, białe żebra i słupki, czerwona belka czołowa,
    czerwone krzesełka. Lokalnie -X to kierunek boiska.
    """
    bm_shell, bm_white, bm_red, bm_floor = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    arc = lambda r: [(DUG_X0 + r * math.sin(math.radians(t)), r * math.cos(math.radians(t))) for t in range(0, 91, 10)]
    seats = []
    for ya, yb in DUGOUTS:
        _extrude_profile(bm_shell, arc(DUG_R + 0.02) + arc(DUG_R)[::-1], ya, yb)
        for y in (ya, yb - 0.02):
            _extrude_profile(bm_shell, [(DUG_X0, 0.0)] + arc(DUG_R), y, y + 0.02)
        n = round((yb - ya) / 1.75)
        for k in range(n + 1):
            y = ya + 0.04 + k * (yb - ya - 0.08) / n
            ribs = arc(DUG_R + 0.06)
            for (xa, za), (xe, ze) in zip(ribs, ribs[1:]):
                _beam(bm_white, (xa, y, za), (xe, y, ze), 0.06, 0.06)
            _beam(bm_white, (DUG_X0 - 0.03, y, 0.0), (DUG_X0 - 0.03, y, DUG_R), 0.07, 0.07)
        _beam(bm_red, (DUG_X0 - 0.03, ya, DUG_R + 0.08), (DUG_X0 - 0.03, yb, DUG_R + 0.08), 0.12, 0.16)
        _beam(bm_red, (DUG_X0 + DUG_R, ya, 0.06), (DUG_X0 + DUG_R, yb, 0.06), 0.1, 0.12)
        _box(bm_floor, 0.0, LOWER_X0 + DUG_ROWS * LOWER_DX, ya, yb, -0.05, 0.02)
        n_seat = int((yb - ya - 0.8) / 0.55)
        seats += [(1.55, ya + 0.4 + (k + 0.5) * (yb - ya - 0.8) / n_seat, 0.02) for k in range(n_seat)]
    _finish(col, bm_shell, "Lawki_Rezerwowych_Pleksi", mats['plexi'])
    _finish(col, bm_white, "Lawki_Rezerwowych_Stelaz_Bialy", mats['goal_white'])
    _finish(col, bm_red, "Lawki_Rezerwowych_Stelaz_Czerwony", mats['lks_red'])
    _finish(col, bm_floor, "Lawki_Rezerwowych_Posadzka", mats['concrete_dark'])
    place_seats(col, "Krzeselka_Lawki_Rezerwowych", seat_material("Mat_Krzeselka_Rezerwowych", (0.62, 0.07, 0.09)), seats)


def build_players_tunnel(col, mats):
    """
    Złożony tunel harmonijkowy w kanale TUNNEL_Y, od drzwi w tylnej ścianie kanału do TUNNEL_FRONT_X.
    Łuki stelaża (ściana boczna + półkolisty dach) co TUNNEL_FOLD; fałda obicia między łukami to dwie
    zamknięte powłoki: od łuku do szczytu fałdy wypchniętego o TUNNEL_PLEAT i z powrotem. Fałdy na przemian
    białe i czerwone, nożyce stelaża w ścianach bocznych między sąsiednimi łukami. Lokalnie -X to kierunek boiska.
    """
    bm_white, bm_red, bm_frame, bm_floor = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    yc = sum(TUNNEL_Y) / 2
    w, h = TUNNEL_HALF_W, TUNNEL_WALL_H

    def outline(r):
        """Obrys przekroju (y, z) o połowie szerokości r: ściana, półkolisty dach, druga ściana."""
        arc = [(yc - r * math.cos(math.radians(t)), h + r * math.sin(math.radians(t))) for t in range(0, 181, 15)]
        return [(yc - r, 0.0)] + arc + [(yc + r, 0.0)]

    def shell(r):
        return outline(r) + outline(r - 0.03)[::-1]

    def loft(bm, xa, ra, xb, rb):
        """Zamknięta powłoka między przekrojem shell(ra) na xa i shell(rb) na xb."""
        va = [bm.verts.new((xa, y, z)) for y, z in shell(ra)]
        vb = [bm.verts.new((xb, y, z)) for y, z in shell(rb)]
        n = len(va)
        for i in range(n):
            bm.faces.new([va[i], va[(i + 1) % n], vb[(i + 1) % n], vb[i]])
        bm.faces.new(va[::-1])
        bm.faces.new(vb)

    x_wall = LOWER_X0 + TUNNEL_ROWS * LOWER_DX
    n = round((x_wall - TUNNEL_FRONT_X) / TUNNEL_FOLD)
    hoops = [TUNNEL_FRONT_X + k * (x_wall - TUNNEL_FRONT_X) / n for k in range(n + 1)]
    ring = outline(w - 0.06)
    for k, x in enumerate(hoops):
        for a, b in zip(ring, ring[1:]):
            _beam(bm_frame, (x, a[0], a[1]), (x, b[0], b[1]), 0.05, 0.05)
        if k == n:
            break
        xn = hoops[k + 1]
        xm = (x + xn) / 2
        bm = bm_white if k % 2 else bm_red
        loft(bm, x, w, xm, w + TUNNEL_PLEAT)
        loft(bm, xm, w + TUNNEL_PLEAT, xn, w)
        for ys in (yc - w + 0.06, yc + w - 0.06):
            _beam(bm_frame, (x, ys, 0.1), (xn, ys, h), 0.03, 0.03)
            _beam(bm_frame, (x, ys, h), (xn, ys, 0.1), 0.03, 0.03)

    _box(bm_floor, 0.0, x_wall, TUNNEL_Y[0], TUNNEL_Y[1], -0.05, 0.02)
    _finish(col, bm_white, "Tunel_Harmonijkowy_Bialy", mats['goal_white'])
    _finish(col, bm_red, "Tunel_Harmonijkowy_Czerwony", mats['lks_red'])
    _finish(col, bm_frame, "Tunel_Harmonijkowy_Stelaz", mats['metal'])
    _finish(col, bm_floor, "Tunel_Harmonijkowy_Posadzka", mats['concrete_dark'])
    bm_door = bmesh.new()
    _box(bm_door, x_wall - 0.03, x_wall, yc - 0.8, yc + 0.8, 0.02, 2.2)
    _finish(col, bm_door, "Tunel_Harmonijkowy_Drzwi", mats['board_dark'])


def build_vip_pavilion(col, mats):
    """Pawilon VIP: bryła z blachy (UV wg kierunku ściany, przetłoczenia pionowe), wstęga okien od boiska ze słupkami."""
    ya, yb = PAVILION_Y
    x_f, x_b = LOWER_X0 + PAVILION_ROW * LOWER_DX, LOWER_X0 + LOWER_ROWS * LOWER_DX
    bm = bmesh.new()
    _box(bm, x_f, x_b, ya, yb, 0.0, PAVILION_TOP)
    uv = bm.loops.layers.uv.verify()
    for face in bm.faces:
        n = face.normal
        for loop in face.loops:
            co = loop.vert.co
            if abs(n.z) > 0.5:
                loop[uv].uv = (co.y / SHEET_TILE, co.x / SHEET_TILE)
            else:
                loop[uv].uv = ((co.y if abs(n.x) > 0.5 else co.x) / SHEET_TILE, co.z / SHEET_TILE)
    _finish(col, bm, "Pawilon_VIP", mats['sheet_steel'])

    z0, z1 = PAVILION_WIN
    bm_glass, bm_frame = bmesh.new(), bmesh.new()
    _box(bm_glass, x_f - 0.03, x_f, ya + 0.3, yb - 0.3, z0, z1)
    _box(bm_frame, x_f - 0.08, x_f, ya + 0.25, yb - 0.25, z0 - 0.08, z0)        # parapet
    _box(bm_frame, x_f - 0.06, x_f, ya + 0.25, yb - 0.25, z1, z1 + 0.06)         # nadproże
    n = round((yb - ya - 0.6) / PAVILION_MULLION)
    for k in range(n + 1):
        y = ya + 0.3 + k * (yb - ya - 0.6) / n
        _box(bm_frame, x_f - 0.06, x_f, y - 0.04, y + 0.04, z0, z1)
    _finish(col, bm_glass, "Pawilon_VIP_Okna", mats['glass'])
    _finish(col, bm_frame, "Pawilon_VIP_Ramy", mats['metal'])


def lower_seat_rows():
    """Rzędy krzesełek sektora dolnego: (x, z) siedziska w układzie lokalnym trybuny."""
    return [(LOWER_X0 + (i + 1) * LOWER_DX - SEAT_BACK_GAP, LOWER_Z0 + i * LOWER_DZ) for i in range(LOWER_ROWS)]


def lower_seat_removed(y, row):
    """Czy krzesełka rzędu row na pozycji y nie ma: wycięcie sektora dolnego (ławka rezerwowych, tunel) albo pawilon VIP."""
    if row >= PAVILION_ROW and PAVILION_Y[0] - 0.3 < y < PAVILION_Y[1] + 0.3:
        return True
    return any(row < rows and a - 0.3 < y < b + 0.3 for a, b, rows in LOWER_CUTS)


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = create_materials()
    col = bpy.data.collections.new("LKS_Trybuna_Glowna")
    bpy.context.scene.collection.children.link(col)
    build_grandstand(col, mats)
    
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "trybuna_glowna_v2.blend"))
    print("Zapisano v2 trybuny glownej.")
