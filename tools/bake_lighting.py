"""
Wypalanie ambient occlusion (Cycles) dla dużych betonowych brył i placu wokół stadionu.

Po co: w Three.js światło otoczenia z HDRI (IBL) nie zna zasłonięcia — hala pod trybuną, tunele
i nisze pod daszkiem świeciły jak plac na zewnątrz. Wypalone AO trafia do glTF jako occlusionTexture
(drugi kanał UV „Lightmap”), a Three.js nakłada je na światło otoczenia (aoMap).

Każda wypalana bryła dostaje własne kopie materiałów (occlusionTexture jest per materiał w glTF).
Obrazy zapisywane są do build/ao/ (artefakt builda, poza gitem). BAKE_AO=0 pomija wypalanie.
"""
import os

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "build", "ao")

# (nazwa obiektu, rozdzielczość mapy) — ok. 5–11 cm na teksel
BAKE_TARGETS = [
    ("Widownia_Gorna", 2048),
    ("Widownia_Dolna", 1024),
    ("Dzwigary_i_Odciagi", 1024),
    ("Tunele_Sciany", 1024),
    ("Schody_Tunele_i_Promenada", 1024),
    ("Pawilon_Zachodni", 1024),
    ("Trybuna_Podkowa", 2048),
    ("Galera_Tunele", 1024),
    ("Plac_Wokol_Stadionu", 2048),
]
AO_DISTANCE = 8.0      # zasięg promieni AO [m]: hala pod trybuną ma 5–12 m wysokości
SAMPLES = 64
LIGHTMAP_UV = "Lightmap"


def _gltf_output_group():
    """Grupa węzłów rozpoznawana przez eksporter glTF jako wyjście occlusion."""
    name = "glTF Material Output"
    ng = bpy.data.node_groups.get(name)
    if ng is None:
        ng = bpy.data.node_groups.new(name, 'ShaderNodeTree')
        ng.interface.new_socket("Occlusion", in_out='INPUT', socket_type='NodeSocketFloat')
    return ng


def _prepare_object(obj, size):
    """Drugi kanał UV, kopie materiałów i obraz docelowy podpięty jako aktywny węzeł bake."""
    mesh = obj.data
    render_uv = mesh.uv_layers.active_render or mesh.uv_layers[0]
    lm = mesh.uv_layers.get(LIGHTMAP_UV) or mesh.uv_layers.new(name=LIGHTMAP_UV)
    render_uv.active_render = True
    mesh.uv_layers.active = lm

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=1.0, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    # „Lightmap” zostaje aktywna (wymóg bake); tekstury czytają UVMap jako warstwę renderowaną (TEXCOORD_0)

    img = bpy.data.images.new(f"AO_{obj.name}", size, size, alpha=False)
    group = _gltf_output_group()
    for slot in obj.material_slots:
        mat = slot.material.copy()
        mat.name = f"{slot.material.name}__AO_{obj.name}"
        slot.material = mat
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        uv = nodes.new('ShaderNodeUVMap')
        uv.uv_map = LIGHTMAP_UV
        tex = nodes.new('ShaderNodeTexImage')
        tex.image = img
        tex.image.colorspace_settings.name = 'Non-Color'
        links.new(uv.outputs['UV'], tex.inputs['Vector'])
        sep = nodes.new('ShaderNodeSeparateColor')
        links.new(tex.outputs['Color'], sep.inputs['Color'])
        out = nodes.new('ShaderNodeGroup')
        out.node_tree = group
        links.new(sep.outputs['Red'], out.inputs['Occlusion'])
        nodes.active = tex                      # cel wypalania
    return img


def bake_ambient_occlusion():
    if os.environ.get("BAKE_AO", "1") == "0":
        print("BAKE_AO=0 — pomijam wypalanie AO")
        return
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = SAMPLES
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.light_settings.distance = AO_DISTANCE
    os.makedirs(OUT_DIR, exist_ok=True)

    for name, size in BAKE_TARGETS:
        obj = bpy.data.objects.get(name)
        if obj is None:
            print(f"Brak obiektu {name} — pomijam")
            continue
        img = _prepare_object(obj, size)
        print(f"Wypalanie AO: {name} ({size}px)...")
        bpy.ops.object.bake(type='AO', margin=6, use_clear=True)
        img.filepath_raw = os.path.join(OUT_DIR, f"ao_{name}.jpg")
        img.file_format = 'JPEG'
        scene.render.image_settings.quality = 88
        img.save()
    bpy.ops.object.select_all(action='DESELECT')
