"""
Nakłada ortofotomapę 2013 jako podkład (płaszczyzna z teksturą, 5 cm pod terenem) w otwartej scenie,
w skali 1:1 i w układzie stadionu — do modelowania „po śladzie”. Niczego nie zapisuje.

Użycie: blender stadion_lks_pelny.blend --python tools/add_ortho_reference.py
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortho_calibration import ORTHO_PATH, ORTHO_SIZE_PX, M_PER_PX, px_to_stadium  # noqa: E402

w_px, h_px = ORTHO_SIZE_PX
cx, cy = px_to_stadium(w_px / 2.0, h_px / 2.0)
ex = px_to_stadium(w_px / 2.0 + 1.0, h_px / 2.0)
angle = math.atan2(ex[1] - cy, ex[0] - cx)  # kierunek osi x obrazu w układzie stadionu

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(cx, cy, -0.05), rotation=(0.0, 0.0, angle))
plane = bpy.context.active_object
plane.name = "Podklad_Ortofotomapa_2013"
plane.scale = (w_px * M_PER_PX, h_px * M_PER_PX, 1.0)

mat = bpy.data.materials.new("Mat_Podklad_Ortofotomapa")
mat.use_nodes = True
nodes, links = mat.node_tree.nodes, mat.node_tree.links
tex = nodes.new('ShaderNodeTexImage')
tex.image = bpy.data.images.load(ORTHO_PATH)
emit = nodes.new('ShaderNodeEmission')
links.new(tex.outputs['Color'], emit.inputs['Color'])
links.new(emit.outputs['Emission'], nodes['Material Output'].inputs['Surface'])
plane.data.materials.append(mat)

print(f"Podkład: środek ({cx:.1f}, {cy:.1f}) m, obrót {math.degrees(angle):.2f}°, "
      f"{w_px * M_PER_PX:.1f} x {h_px * M_PER_PX:.1f} m")
