"""
Generowanie Trybuny Głównej (Zachodniej) Stadionu ŁKS Łódź (1969-2012).
Wierne odwzorowanie proporcji z nagrań i zdjęć historycznych:
- Otwarta ku górze korona trybuny (brak wielkiego dachu na szczycie)
- 14 przęseł modułowych (108 m) z 15 prefabrykowanymi dźwigarami kablobetonowymi
- Realistyczna wysokość korony: ok. 14.0 m nad murawą (nachylenie ok. 29°)
- Sektor dolny z charakterystycznym, niskim daszkiem blaszanym (sektor VIP / trybuna kryta z białym pasem fasadowym)
- Sektor górny: 26 rzędów stopni betonowych z drewnianymi ławkami
- Brutalistyczne ukośne odciągi żelbetowe i wstęga okien hali od strony al. Unii
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
    g_rough = os.path.join(TEXTURES_DIR, "grass", "Grass001_1K-JPG_Roughness.jpg")
    setup_pbr_nodes(mat_grass, g_col, g_norm, g_rough, scale=(1.0, 1.0))
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
        bsdf.inputs['Base Color'].default_value = (0.44, 0.28, 0.16, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.75
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
    mat_net = bpy.data.materials.new("Mat_Goal_Net")
    mat_net.use_nodes = True
    bsdf = mat_net.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Roughness'].default_value = 0.85
    net_col = os.path.join(TEXTURES_DIR, "goal_net_striped.png")
    if os.path.exists(net_col):
        img_net = bpy.data.images.load(net_col)
        node_tex = mat_net.node_tree.nodes.new('ShaderNodeTexImage')
        node_tex.image = img_net
        tc = mat_net.node_tree.nodes.new('ShaderNodeTexCoord')
        mat_net.node_tree.links.new(tc.outputs['UV'], node_tex.inputs['Vector'])
        mat_net.node_tree.links.new(node_tex.outputs['Color'], bsdf.inputs['Base Color'])
        mat_net.node_tree.links.new(node_tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    
    if hasattr(mat_net, 'blend_method'):
        mat_net.blend_method = 'CLIP'
        mat_net.alpha_threshold = 0.20
    if hasattr(mat_net, 'use_backface_culling'):
        mat_net.use_backface_culling = False
    mats['goal_net'] = mat_net

    return mats


def build_grandstand(col, mats):
    TOTAL_LENGTH_Y = 108.0
    NUM_BAYS = 14
    BAY_WIDTH_Y = TOTAL_LENGTH_Y / NUM_BAYS # 7.7142857 m
    
    # -------------------------------------------------------------------------
    # 1. PROFILE DŹWIGARÓW I ODCIĄGÓW (SKALA I PROPORCJE 1:1)
    # -------------------------------------------------------------------------
    # Rzut w osi X:
    # X=0: krawędź dolnego sektora (przy fosie i bieżni)
    # X=7.0: pionowa ściana pawilonu pod trybuną (wys. 3.2 m)
    # X=7.0 do X=25.0: rzut górnej trybuny opartej na dźwigarze (szer. 18 m)
    # X=25.0: korona górnej trybuny na wysokości Z = 14.0 m
    # X=27.0: tylna ściana pawilonu hali od al. Unii
    # Odciąg ukośny: od węzła korony (X=24.0, Z=13.0) do fundamentu (X=29.5, Z=0.0)
    
    GIRDER_THICK = 0.50
    girder_mesh = bpy.data.meshes.new("Dzwigar_Nosny_Mesh")
    bm_g = bmesh.new()
    
    # Punkty profilu 2D dźwigara (XZ):
    pts_girder = [
        (6.8,  0.0, 0.0),   # stopa przednia na gruncie
        (6.8,  0.0, 3.2),   # wierzchołek ściany przedniej
        (25.0, 0.0, 14.0),  # korona trybuny szczyt
        (25.8, 0.0, 13.6),  # głowica tylna
        (24.5, 0.0, 11.5),  # węzeł odciągu
        (7.8,  0.0, 2.5),   # spód dźwigara nad halą
        (7.8,  0.0, 0.0)    # stopa przednia tył
    ]
    bm_v = [bm_g.verts.new(p) for p in pts_girder]
    bm_g.faces.new(bm_v)
    
    # Wytłoczenie profilu dźwigara w osi Y
    res_g = bmesh.ops.extrude_face_region(bm_g, geom=bm_g.faces[:])
    ev_g = [v for v in res_g['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_g, vec=(0.0, GIRDER_THICK, 0.0), verts=ev_g)
    bmesh.ops.translate(bm_g, vec=(0.0, -GIRDER_THICK / 2.0, 0.0), verts=bm_g.verts)

    # Ukośny słup / odciąg żelbetowy od strony al. Unii:
    STRUT_THICK = 0.45
    pts_strut = [
        (24.2, 0.0, 11.8),
        (25.0, 0.0, 11.4),
        (29.8, 0.0, 0.0),
        (28.8, 0.0, 0.0)
    ]
    s_verts = [bm_g.verts.new(p) for p in pts_strut]
    f_strut = bm_g.faces.new(s_verts)
    res_s = bmesh.ops.extrude_face_region(bm_g, geom=[f_strut])
    ev_s = [v for v in res_s['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_g, vec=(0.0, STRUT_THICK, 0.0), verts=ev_s)
    bmesh.ops.translate(bm_g, vec=(0.0, -STRUT_THICK / 2.0, 0.0), verts=[v for v in bm_g.verts if v in s_verts or v in ev_s])

    bm_g.normal_update()
    bm_g.to_mesh(girder_mesh)
    bm_g.free()
    
    obj_girder = bpy.data.objects.new("Dzwigar_i_Odciag_Modul", girder_mesh)
    obj_girder.data.materials.append(mats['concrete'])
    col.objects.link(obj_girder)

    # -------------------------------------------------------------------------
    # 2. SEKTOR GÓRNY STOPNI (GÓRNA WIDOWNIA - BEZ DACHU)
    # -------------------------------------------------------------------------
    # 26 rzędów stopni: X od 7.0 do 25.0 m, Z od 3.2 do 14.0 m
    NUM_UPPER = 26
    dx_up = (25.0 - 7.0) / NUM_UPPER   # ~0.692 m
    dz_up = (14.0 - 3.2) / NUM_UPPER   # ~0.415 m
    
    upper_mesh = bpy.data.meshes.new("Widownia_Gorna_Mesh")
    bm_u = bmesh.new()
    
    cur_x = 7.0
    cur_z = 3.2
    pts_u = [(cur_x, 0.0, cur_z)]
    for _ in range(NUM_UPPER):
        cur_z += dz_up
        pts_u.append((cur_x, 0.0, cur_z))
        cur_x += dx_up
        pts_u.append((cur_x, 0.0, cur_z))
    pts_u.append((cur_x, 0.0, cur_z - 0.25))
    pts_u.append((7.0, 0.0, 3.2 - 0.25))
    
    v_u = [bm_u.verts.new(p) for p in pts_u]
    bm_u.faces.new(v_u)
    res_u = bmesh.ops.extrude_face_region(bm_u, geom=bm_u.faces[:])
    ev_u = [v for v in res_u['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_u, vec=(0.0, BAY_WIDTH_Y, 0.0), verts=ev_u)
    
    bm_u.normal_update()
    bm_u.to_mesh(upper_mesh)
    bm_u.free()
    
    obj_upper = bpy.data.objects.new("Widownia_Gorna_Modul", upper_mesh)
    obj_upper.data.materials.append(mats['concrete'])
    col.objects.link(obj_upper)

    # -------------------------------------------------------------------------
    # 3. SEKTOR DOLNY STOPNI (WIDOWNIA DOLNA)
    # -------------------------------------------------------------------------
    # 10 rzędów stopni: X od 0.0 do 6.5 m, Z od 0.4 do 2.6 m
    NUM_LOWER = 10
    dx_low = 6.5 / NUM_LOWER # 0.65 m
    dz_low = (2.6 - 0.4) / NUM_LOWER # 0.22 m
    
    lower_mesh = bpy.data.meshes.new("Widownia_Dolna_Mesh")
    bm_l = bmesh.new()
    
    cur_x = 0.0
    cur_z = 0.4
    pts_l = [(cur_x, 0.0, cur_z)]
    for _ in range(NUM_LOWER):
        cur_z += dz_low
        pts_l.append((cur_x, 0.0, cur_z))
        cur_x += dx_low
        pts_l.append((cur_x, 0.0, cur_z))
    pts_l.append((6.5, 0.0, 0.0))
    pts_l.append((0.0, 0.0, 0.0))
    
    v_l = [bm_l.verts.new(p) for p in pts_l]
    bm_l.faces.new(v_l)
    res_l = bmesh.ops.extrude_face_region(bm_l, geom=bm_l.faces[:])
    ev_l = [v for v in res_l['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_l, vec=(0.0, BAY_WIDTH_Y, 0.0), verts=ev_l)
    
    bm_l.normal_update()
    bm_l.to_mesh(lower_mesh)
    bm_l.free()
    
    obj_lower = bpy.data.objects.new("Widownia_Dolna_Modul", lower_mesh)
    obj_lower.data.materials.append(mats['concrete'])
    col.objects.link(obj_lower)

    # -------------------------------------------------------------------------
    # 4. NISKIE ZADASZENIE BLASZANE (BIAŁO-CZERWONO-BIAŁE) OD POŁUDNIOWEGO KRAŃCA
    # -------------------------------------------------------------------------
    # W rzucie stadionu Trybuna Główna biegnie od Y = -54.0m (Południe) do Y = +54.0m (Północ).
    # Ze względu na obrót o 180° w build_full_stadium (Y_global = 54.0 - Y_local):
    # - Krańcowe południe to Y_local = 14.0 * BAY_WIDTH_Y (108.0m)
    # - Krańcowa północ to Y_local = 0.0m
    # Zgodnie z archiwalnym zdjęciem (media_1792191531931.png):
    # Daszek biało-czerwono-biały ZACZYNA SIĘ OD POŁUDNIOWEGO KRAŃCA (Y_local = 108.0m):
    # 1. Biały daszek południowy: przęsła 11..13 (od 11*BAY_W do 14*BAY_W, ~23.1m)
    # 2. Czerwony daszek środkowy: przęsła 6..10 (od 6*BAY_W do 11*BAY_W, ~38.6m)
    # 3. Biały daszek północny zadaszonego sektora: przęsła 4..5 (od 4*BAY_W do 6*BAY_W, ~15.4m)
    # Na północ od przęsła 4 (Y_local < 4*BAY_W, na północ od środka murawy):
    # Daszek się urywa! Mamy otwarty sektor z betonowymi stopniami oraz niski pawilon.
    # Wszelkie sztuczne tekstury graffiti pod trybuną zostały całkowicie usunięte.
    
    def make_canopy_section(name, y_start, y_end, mat):
        bm = bmesh.new()
        pts = [
            (1.0, y_start, 3.4),
            (7.0, y_start, 4.3),
            (7.0, y_start, 4.15),
            (1.0, y_start, 3.25)
        ]
        f = bm.faces.new([bm.verts.new(p) for p in pts])
        res = bmesh.ops.extrude_face_region(bm, geom=[f])
        ev = [v for v in res['geom'] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0.0, y_end - y_start, 0.0), verts=ev)
        
        uv_l = bm.loops.layers.uv.verify()
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_l].uv = (loop.vert.co.y / 4.0, loop.vert.co.x / 4.0)
                
        mesh = bpy.data.meshes.new(f"{name}_Mesh")
        bm.normal_update()
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        obj.data.materials.append(mat)
        col.objects.link(obj)
        return obj

    # 1. Biały daszek od krańca południowego (przęsła 11..13: od 11*BAY_W do 14*BAY_W)
    obj_canopy_s = make_canopy_section("Daszek_Bialy_Poludnie", 11.0 * BAY_WIDTH_Y, 14.0 * BAY_WIDTH_Y, mats['roof_white'])
    # 2. Czerwony daszek środkowy (przęsła 6..10: od 6*BAY_W do 11*BAY_W)
    obj_canopy_c = make_canopy_section("Daszek_Czerwony_Srodek", 6.0 * BAY_WIDTH_Y, 11.0 * BAY_WIDTH_Y, mats['roof_red'])
    # 3. Biały daszek północny zadaszonego sektora (przęsła 4..5: od 4*BAY_W do 6*BAY_W)
    obj_canopy_n = make_canopy_section("Daszek_Bialy_Polnoc", 4.0 * BAY_WIDTH_Y, 6.0 * BAY_WIDTH_Y, mats['roof_white'])

    # 4. Czysta, biała blenda / obróbka blacharska czoła daszku (na długości zadaszenia)
    CANOPY_FRONT_Y_START = 4.0 * BAY_WIDTH_Y
    CANOPY_FRONT_Y_END = 14.0 * BAY_WIDTH_Y
    fascia_mesh = bpy.data.meshes.new("Blenda_Fasada_Biala_Mesh")
    bm_f = bmesh.new()
    FX = 0.95
    FZ_BOT = 3.20
    FZ_TOP = 3.48
    f_pts_front = [
        (FX, CANOPY_FRONT_Y_START, FZ_BOT),
        (FX, CANOPY_FRONT_Y_START, FZ_TOP),
        (FX, CANOPY_FRONT_Y_END, FZ_TOP),
        (FX, CANOPY_FRONT_Y_END, FZ_BOT)
    ]
    bm_f.faces.new([bm_f.verts.new(p) for p in f_pts_front])
    bm_f.normal_update()
    bm_f.to_mesh(fascia_mesh)
    bm_f.free()
    obj_fascia = bpy.data.objects.new("Blenda_Fasada_Biala", fascia_mesh)
    obj_fascia.data.materials.append(mats['roof_white'])
    col.objects.link(obj_fascia)

    # -------------------------------------------------------------------------
    # 5. BIAŁE MURKI Z AUTENTYCZNĄ PRZEPLATANKĄ ŁKS NA WYŻSZEJ TRYBUNIE
    # -------------------------------------------------------------------------
    # Na wyższej trybunie, 4-5 rzędów od dołu (X = 9.85m, Z od 5.05m do 6.20m),
    # w każdym przęśle stoi przerywany biały murek z czerwoną Przeplatanką
    bm_przp = bmesh.new()
    WALL_X = 9.85
    WALL_H = 1.15
    WALL_Z_BOT = 5.05
    WALL_Z_TOP = WALL_Z_BOT + WALL_H
    uv_przp = bm_przp.loops.layers.uv.verify()
    
    for k in range(NUM_BAYS):
        y0 = k * BAY_WIDTH_Y + 1.2
        y1 = (k + 1) * BAY_WIDTH_Y - 0.2
        
        # Przednia ściana murka z Przeplatanką (skierowana ku murawie w -X)
        p_front = [
            (WALL_X, y0, WALL_Z_BOT),
            (WALL_X, y0, WALL_Z_TOP),
            (WALL_X, y1, WALL_Z_TOP),
            (WALL_X, y1, WALL_Z_BOT)
        ]
        face_f = bm_przp.faces.new([bm_przp.verts.new(p) for p in p_front])
        for loop in face_f.loops:
            u = (y1 - loop.vert.co.y) / (y1 - y0)
            v = (loop.vert.co.z - WALL_Z_BOT) / WALL_H
            loop[uv_przp].uv = (u, v)
            
        # Grubość murka (wierzch)
        p_top = [
            (WALL_X, y0, WALL_Z_TOP),
            (WALL_X + 0.18, y0, WALL_Z_TOP),
            (WALL_X + 0.18, y1, WALL_Z_TOP),
            (WALL_X, y1, WALL_Z_TOP)
        ]
        f_top = bm_przp.faces.new([bm_przp.verts.new(p) for p in p_top])
        for loop in f_top.loops:
            loop[uv_przp].uv = (0.05, 0.05)

    mesh_przp = bpy.data.meshes.new("Murki_Przeplatanka_Upper_Mesh")
    bm_przp.normal_update()
    bm_przp.to_mesh(mesh_przp)
    bm_przp.free()
    obj_przp = bpy.data.objects.new("Murki_Przeplatanka_Upper", mesh_przp)
    obj_przp.data.materials.append(mats['przeplatanka'])
    col.objects.link(obj_przp)

    # -------------------------------------------------------------------------
    # 5. PAWILON ZAPLECZA I OKNA OD STRONY AL. UNII
    # -------------------------------------------------------------------------
    # Pionowa ściana hali: X od 24.0 do 27.5 m, wysokość Z = 5.5 m
    pav_mesh = bpy.data.meshes.new("Pawilon_Al_Unii_Mesh")
    bm_p = bmesh.new()
    
    pts_p = [
        (24.5, 0.0, 0.0),
        (24.5, 0.0, 5.5),
        (27.5, 0.0, 5.5),
        (27.5, 0.0, 0.0)
    ]
    v_p = [bm_p.verts.new(p) for p in pts_p]
    bm_p.faces.new(v_p)
    res_p = bmesh.ops.extrude_face_region(bm_p, geom=bm_p.faces[:])
    ev_p = [v for v in res_p['geom'] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm_p, vec=(0.0, BAY_WIDTH_Y, 0.0), verts=ev_p)
    
    bm_p.normal_update()
    bm_p.to_mesh(pav_mesh)
    bm_p.free()
    
    obj_pav = bpy.data.objects.new("Pawilon_Al_Unii_Modul", pav_mesh)
    obj_pav.data.materials.append(mats['concrete'])
    col.objects.link(obj_pav)

    # Wstęga okien al. Unii
    win_mesh = bpy.data.meshes.new("Okna_Hala_Al_Unii_Mesh")
    bm_w = bmesh.new()
    pts_w = [
        (27.52, 0.3, 2.2),
        (27.52, BAY_WIDTH_Y - 0.3, 2.2),
        (27.52, BAY_WIDTH_Y - 0.3, 4.8),
        (27.52, 0.3, 4.8)
    ]
    bm_w.faces.new([bm_w.verts.new(p) for p in pts_w])
    bm_w.normal_update()
    bm_w.to_mesh(win_mesh)
    bm_w.free()
    
    obj_win = bpy.data.objects.new("Okna_Hala_Al_Unii_Modul", win_mesh)
    obj_win.data.materials.append(mats['glass'])
    col.objects.link(obj_win)

    # -------------------------------------------------------------------------
    # 6. SŁUPKI OŚWIETLENIOWE NA SZCZYCIE KORONY (JAK NA NAGRANIACH)
    # -------------------------------------------------------------------------
    # Na szczycie korony (X=25.0, Z=14.0) stoją charakterystyczne smukłe słupki
    # oświetleniowe z oprawami skierowanymi ku murawie
    lights_mesh = bpy.data.meshes.new("Latarnie_Korona_Mesh")
    bm_lt = bmesh.new()
    
    POLE_H = 3.2
    c_pole = bmesh.ops.create_cone(
        bm_lt,
        cap_ends=True,
        segments=8,
        radius1=0.06,
        radius2=0.05,
        depth=POLE_H
    )
    bmesh.ops.translate(bm_lt, vec=(25.0, BAY_WIDTH_Y / 2.0, 14.0 + POLE_H / 2.0), verts=c_pole['verts'])
    
    c_bar = bmesh.ops.create_cube(bm_lt, size=1.0)
    bmesh.ops.scale(bm_lt, vec=(0.08, 1.2, 0.08), verts=c_bar['verts'])
    bmesh.ops.translate(bm_lt, vec=(25.0, BAY_WIDTH_Y / 2.0, 14.0 + POLE_H), verts=c_bar['verts'])
    
    for ly in [BAY_WIDTH_Y / 2.0 - 0.45, BAY_WIDTH_Y / 2.0 + 0.45]:
        lamp = bmesh.ops.create_cube(bm_lt, size=1.0)
        bmesh.ops.scale(bm_lt, vec=(0.35, 0.22, 0.16), verts=lamp['verts'])
        bmesh.ops.rotate(bm_lt, cent=(0,0,0), matrix=mathutils.Matrix.Rotation(math.radians(-30), 3, 'Y'), verts=lamp['verts'])
        bmesh.ops.translate(bm_lt, vec=(24.85, ly, 14.0 + POLE_H + 0.05), verts=lamp['verts'])
        
    bm_lt.normal_update()
    bm_lt.to_mesh(lights_mesh)
    bm_lt.free()
    
    obj_roof_lights = bpy.data.objects.new("Latarnie_Korona_Modul", lights_mesh)
    obj_roof_lights.data.materials.append(mats['metal'])
    col.objects.link(obj_roof_lights)

    # -------------------------------------------------------------------------
    # 7. DREWNIANE ŁAWKI (26 RZĘDÓW GÓRNYCH, 10 DOLNYCH) Z PRZEJŚCIAMI
    # -------------------------------------------------------------------------
    bm_benches = bmesh.new()
    BENCH_THICK = 0.05
    BENCH_DEPTH = 0.35
    BENCH_Y_START = 0.9  # 90 cm na ciąg pieszy / schody przy dźwigarze
    BENCH_Y_END = BAY_WIDTH_Y - 0.1
    
    # Ławki sektora górnego (26 rzędów)
    for i in range(NUM_UPPER):
        bx = 7.0 + (i + 0.5) * dx_up
        bz = 3.2 + (i + 1) * dz_up + BENCH_THICK / 2.0 + 0.04
        b_box = bmesh.ops.create_cube(bm_benches, size=1.0)
        bmesh.ops.scale(bm_benches, vec=(BENCH_DEPTH, BENCH_Y_END - BENCH_Y_START, BENCH_THICK), verts=b_box['verts'])
        bmesh.ops.translate(bm_benches, vec=(bx, (BENCH_Y_START + BENCH_Y_END) / 2.0, bz), verts=b_box['verts'])

    # Ławki sektora dolnego (10 rzędów)
    for i in range(NUM_LOWER):
        bx = 0.0 + (i + 0.5) * dx_low
        bz = 0.4 + (i + 1) * dz_low + BENCH_THICK / 2.0 + 0.04
        b_box = bmesh.ops.create_cube(bm_benches, size=1.0)
        bmesh.ops.scale(bm_benches, vec=(BENCH_DEPTH, BENCH_Y_END - BENCH_Y_START, BENCH_THICK), verts=b_box['verts'])
        bmesh.ops.translate(bm_benches, vec=(bx, (BENCH_Y_START + BENCH_Y_END) / 2.0, bz), verts=b_box['verts'])

    mesh_benches = bpy.data.meshes.new("Lawki_Drewniane_Mesh")
    bm_benches.normal_update()
    bm_benches.to_mesh(mesh_benches)
    bm_benches.free()

    obj_benches = bpy.data.objects.new("Lawki_Drewniane_Modul", mesh_benches)
    if mats and 'wood' in mats:
        obj_benches.data.materials.append(mats['wood'])
    col.objects.link(obj_benches)

    # -------------------------------------------------------------------------
    # 8. MODYFIKATOR ARRAY DLA PRZĘSEŁ (14 POWTÓRZEŃ W OSI Y)
    # -------------------------------------------------------------------------
    modular_objs = [obj_girder, obj_upper, obj_lower, obj_pav, obj_win, obj_roof_lights, obj_benches]
    for o in modular_objs:
        arr = o.modifiers.new("Array_14_Przensel", 'ARRAY')
        arr.count = NUM_BAYS
        arr.use_relative_offset = False
        arr.use_constant_offset = True
        arr.constant_offset_displace = (0.0, BAY_WIDTH_Y, 0.0)

    # Dźwigar końcowy zamykający skrajnię północną (15. oś)
    end_girder = bpy.data.objects.new("Dzwigar_Zamykajacy_Os15", girder_mesh)
    end_girder.location = (0.0, TOTAL_LENGTH_Y, 0.0)
    end_girder.data.materials.append(mats['concrete'])
    col.objects.link(end_girder)

    print("Zbudowano Trybune Glowna bez dachu szczytowego (prawidlowe proporcje historyczne).")

if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = create_materials()
    col = bpy.data.collections.new("LKS_Trybuna_Glowna")
    bpy.context.scene.collection.children.link(col)
    build_grandstand(col, mats)
    
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "trybuna_glowna_v2.blend"))
    print("Zapisano v2 trybuny glownej.")
