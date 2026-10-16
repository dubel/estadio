"""
Renderuje 3 ikoniczne ujęcia zrekonstruowanego stadionu ŁKS:
1. Panorama z łuku południowego (klasyczny widok na boisko, Trybunę Główną, zegar i 4 jupitery)
2. Widok ze środka murawy na Trybunę Główną (brutalizm, schodki, kurnik i maszty)
3. Widok z al. Unii (zewnętrzne ukośne odciągi i brutalistyczna elewacja)
"""

import bpy
import mathutils
import math

bpy.ops.wm.open_mainfile(filepath="/home/mike/Projects/estadiodagruz/stadion_lks_pelny.blend")

# Ustawienie oświetlenia
sun_data = bpy.data.lights.new(name="SunMain", type='SUN')
sun_data.energy = 4.5
sun_obj = bpy.data.objects.new(name="SunMain", object_data=sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(52), math.radians(25), math.radians(-50))

# Niebo i światło rozproszone
world = bpy.context.scene.world
if not world:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (0.35, 0.42, 0.52, 1.0)
    bg.inputs['Strength'].default_value = 0.85

# Kamera
cam_data = bpy.data.cameras.new("RenderCam")
cam_data.lens = 28 # obiektyw szerokokątny 28mm
cam_obj = bpy.data.objects.new("RenderCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

# -------------------------------------------------------------------------
# UJĘCIE 1: PANORAMA BOISKA Z PÓŁNOCY NA POŁUDNIE (LINIE, PASY, TRYBUNA, ZEGAR)
# -------------------------------------------------------------------------
pos_north = mathutils.Vector((15.0, 85.0, 14.0))
target_south = mathutils.Vector((-10.0, -40.0, 3.0))
cam_obj.location = pos_north
cam_obj.rotation_euler = (target_south - pos_north).to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.render.filepath = "/home/mike/Projects/estadiodagruz/tools/shot1_panorama_south.png"
bpy.ops.render.render(write_still=True)
print("Wyrenderowano: shot1_panorama_south.png")

# -------------------------------------------------------------------------
# UJĘCIE 2: WIDOK ZE ŚRODKA MURAWY NA TRYBUNĘ GŁÓWNĄ I BANER "TUTAJ WYCHOWANI"
# -------------------------------------------------------------------------
pos_pitch = mathutils.Vector((12.0, -8.0, 2.5))
target_pitch = mathutils.Vector((-55.0, 0.0, 7.5))
cam_obj.location = pos_pitch
cam_obj.rotation_euler = (target_pitch - pos_pitch).to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.render.filepath = "/home/mike/Projects/estadiodagruz/tools/shot2_pitch_grandstand.png"
bpy.ops.render.render(write_still=True)
print("Wyrenderowano: shot2_pitch_grandstand.png")

# -------------------------------------------------------------------------
# UJĘCIE 3: WIDOK NA GALERĘ (TRYBUNĘ WSCHODNIĄ OD STRONY AL. UNII) I BANERY
# -------------------------------------------------------------------------
pos_galera = mathutils.Vector((-20.0, -5.0, 2.5))
target_galera = mathutils.Vector((58.0, 0.0, 5.5))
cam_obj.location = pos_galera
cam_obj.rotation_euler = (target_galera - pos_galera).to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.render.filepath = "/home/mike/Projects/estadiodagruz/tools/shot3_al_unii.png"
bpy.ops.render.render(write_still=True)
print("Wyrenderowano: shot3_al_unii.png")

# -------------------------------------------------------------------------
# UJĘCIE 4: ZBLIŻENIE NA KULTOWY ZEGAR I TABLICĘ NA KORONIE ŁUKU POŁUDNIOWEGO
# -------------------------------------------------------------------------
pos_clock = mathutils.Vector((0.0, -80.0, 3.5))
target_clock = mathutils.Vector((0.0, -110.5, 9.0))
cam_obj.location = pos_clock
cam_obj.rotation_euler = (target_clock - pos_clock).to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.render.filepath = "/home/mike/Projects/estadiodagruz/tools/shot4_vis_a_vis_zegar.png"
bpy.ops.render.render(write_still=True)
print("Wyrenderowano: shot4_vis_a_vis_zegar.png")

