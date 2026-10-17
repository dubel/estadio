"""
Otoczenie stadionu (stan z ortofotomapy 2013, docs/zrodla.md):
- teren (trawa) i utwardzony plac wokół stadionu — bez nich spacer kończył się spadkiem w próżnię,
- al. Unii Lubelskiej (wschód) i pas torów przy stacji Łódź Kaliska,
- uproszczona bryła Atlas Areny (zachód),
- pnie drzew (kolizje) w pozycjach z ortofotomapy (tools/data/drzewa_ortofoto.json); drzewa: tools/generate_trees.mjs,
- panorama bloków za torami (widoczna z trybuny głównej nad Galerą, zdjęcia lks07, lks08).
Układ stadionu: X — wschód, Y — północ, metry, początek w środku boiska.
"""
import json
import math
import os

import bmesh
import bpy
import mathutils

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREES_JSON = os.path.join(ROOT, "tools", "data", "drzewa_ortofoto.json")
FACADE_TEX = os.path.join(ROOT, "assets", "textures", "facade_blok.png")

# Bloki za torami, kompozycja wg zdjęć lks07/lks08 (z trybuny głównej: nad Galerą i łukiem południowym).
# Pozycje orientacyjne (brak pomiaru): środek X, Y, długość, głębokość, wysokość [m], obrót [°], kolor elewacji.
SKYLINE = [
    (480,   40, 60, 13, 36,  10, (0.30, 0.58, 0.70)),   # niebiesko-turkusowy blok (lks07/lks08, lewa strona)
    (520,  -30, 45, 13, 31,  -5, (0.93, 0.68, 0.36)),   # żółto-pomarańczowy
    (470,  115, 55, 12, 30,  15, (0.72, 0.72, 0.74)),
    (560, -110, 60, 13, 33,   0, (0.80, 0.76, 0.68)),
    (600, -190, 16, 16, 48,  20, (0.92, 0.92, 0.92)),   # białe punktowce
    (640, -235, 16, 16, 45,  35, (0.92, 0.92, 0.92)),
    (700,  -60, 70, 13, 30, -10, (0.86, 0.81, 0.70)),
    (760, -150, 50, 12, 36,   5, (0.72, 0.72, 0.74)),
    (650,   95, 40, 12, 27,   0, (0.90, 0.58, 0.34)),
    (560,  185, 50, 12, 24,  20, (0.74, 0.74, 0.76)),
    (900, -235, 20, 20, 60,   0, (0.48, 0.62, 0.78)),
    (820, -335, 18, 18, 72,  15, (0.38, 0.56, 0.76)),   # wysoki niebieski (lks07, prawa strona)
]
FACADE_TILE_M = 6.0

TERRAIN_HALF = 1200.0   # teren sięga za panoramę bloków (do ~900 m)
ATLAS_CENTER = (-174.0, 10.0)   # ortofotomapa 2013, dokładność ±5 m
ATLAS_RADIUS = 68.0
ATLAS_WALL_H = 12.0
ATLAS_DOME_H = 12.0


def _flat_material(name, color, roughness, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return mat


def _quad(col, name, x0, x1, y0, y1, z, mat):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]]
    bm.faces.new(vs)
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    col.objects.link(obj)
    return obj


def build_ground(col, mats):
    """Teren pod całym stadionem i utwardzony plac wokół niego (ortofotomapa: jasna kostka/beton)."""
    # Poziomy rozsunięte o centymetry migotały (z-fighting przy zasięgu kamery 2 km): plac 5 cm pod murawą,
    # teren 25 cm pod placem — krawędź placu to niski, przechodni stopień.
    _quad(col, "Teren_Trawa", -TERRAIN_HALF, TERRAIN_HALF, -TERRAIN_HALF, TERRAIN_HALF, -0.25, mats['ground_grass'])
    _quad(col, "Plac_Wokol_Stadionu", -110.0, 76.0, -125.0, 125.0, -0.05, mats['concrete_dark'])


def build_streets(col, mats):
    asphalt = _flat_material("Mat_Asfalt", (0.09, 0.09, 0.10), 0.92)
    ballast = _flat_material("Mat_Tluczen_Torowy", (0.24, 0.21, 0.18), 0.95)
    _quad(col, "Al_Unii_Lubelskiej", 78.0, 94.0, -TERRAIN_HALF, TERRAIN_HALF, -0.20, asphalt)
    _quad(col, "Tory_Lodz_Kaliska", 115.0, 200.0, -TERRAIN_HALF, TERRAIN_HALF, -0.20, ballast)


def build_atlas_arena(col, mats):
    """Atlas Arena jako bryła tła: walcowa ściana i płaska kopuła (widok z korony trybun)."""
    roof = _flat_material("Mat_Atlas_Dach", (0.62, 0.64, 0.66), 0.45, 0.6)
    bm = bmesh.new()
    segs = 64
    cx, cy = ATLAS_CENTER
    base = [bm.verts.new((cx + ATLAS_RADIUS * math.cos(2 * math.pi * i / segs),
                          cy + ATLAS_RADIUS * math.sin(2 * math.pi * i / segs), 0.0)) for i in range(segs)]
    rings = [base]
    for k, t in enumerate([0.0, 0.45, 0.75, 0.93]):
        r = ATLAS_RADIUS * math.cos(t * math.pi / 2) if k else ATLAS_RADIUS
        z = ATLAS_WALL_H + ATLAS_DOME_H * math.sin(t * math.pi / 2)
        rings.append([bm.verts.new((cx + r * math.cos(2 * math.pi * i / segs),
                                    cy + r * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            bm.faces.new([a[i], a[(i + 1) % segs], b[(i + 1) % segs], b[i]])
    bm.faces.new(rings[-1])
    mesh = bpy.data.meshes.new("Atlas_Arena_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Atlas_Arena", mesh)
    obj.data.materials.append(roof)
    col.objects.link(obj)


def build_trees(col, mats):
    """
    Pnie drzew z ortofotomapy jako niewidoczna siatka kolizyjna (src/main.ts ukrywa Drzewa_Pnie_Kolizje).
    Same drzewa (EZ-Tree) generuje tools/generate_trees.mjs do public/assets/drzewa.glb — te same pozycje.
    """
    with open(TREES_JSON) as f:
        trees = json.load(f)["trees"]

    bm = bmesh.new()
    for t in trees:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.35 * t["scale"], radius2=0.3 * t["scale"],
                              depth=3.0, matrix=mathutils.Matrix.Translation((t["x"], t["y"], 1.5)))
    mesh = bpy.data.meshes.new("Drzewa_Pnie_Kolizje_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(_flat_material("Mat_Kolizje", (0.5, 0.5, 0.5), 1.0))
    col.objects.link(bpy.data.objects.new("Drzewa_Pnie_Kolizje", mesh))


def build_skyline(col, mats):
    """Bloki z wielkiej płyty jako proste prostopadłościany z elewacją (tekstura × kolor bloku)."""
    img = bpy.data.images.load(FACADE_TEX)
    for i, (cx, cy, length, depth, height, rot, color) in enumerate(SKYLINE):
        mat = bpy.data.materials.new(f"Mat_Blok_{i:02d}")
        mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        bsdf.inputs['Roughness'].default_value = 0.9
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = img
        mapping = nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (4.0 / FACADE_TILE_M, 4.0 / FACADE_TILE_M, 1.0)  # UV = 4 m / jednostkę
        links.new(nodes.new('ShaderNodeTexCoord').outputs['UV'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        mix.inputs[7].default_value = (*color, 1.0)       # B (kolor bloku)
        links.new(tex.outputs['Color'], mix.inputs[6])     # A (elewacja)
        links.new(mix.outputs[2], bsdf.inputs['Base Color'])

        bm = bmesh.new()
        c = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(depth, length, height), verts=c['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, height / 2), verts=c['verts'])
        mesh = bpy.data.meshes.new(f"Panorama_Blok_{i:02d}_Mesh")
        bm.normal_update()
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(f"Panorama_Blok_{i:02d}", mesh)
        obj.location = (cx, cy, 0.0)
        obj.rotation_euler = (0.0, 0.0, math.radians(rot))
        obj.data.materials.append(mat)
        col.objects.link(obj)


def build_surroundings(col, mats):
    build_ground(col, mats)
    build_streets(col, mats)
    build_atlas_arena(col, mats)
    build_trees(col, mats)
    build_skyline(col, mats)
