"""
Renderuje dwa ujęcia Trybuny Głównej: od strony murawy oraz od al. Unii.
"""
import bpy
import mathutils
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

blend_path = os.path.join(ROOT, "trybuna_glowna_pelna.blend")
bpy.ops.wm.open_mainfile(filepath=blend_path)

# Kamera
cam_data = bpy.data.cameras.new("PreviewCam")
cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Słońce
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), math.radians(25), math.radians(-40))

# Światło wypełniające (Sky light)
fill_data = bpy.data.lights.new(name="Fill", type='SUN')
fill_data.energy = 1.5
fill_obj = bpy.data.objects.new(name="Fill", object_data=fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.rotation_euler = (math.radians(-40), math.radians(-30), math.radians(120))

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

# 1. UJĘCIE OD STRONY MURAWSKIEJ (FRONT)
cam_pos = mathutils.Vector((-40.0, -15.0, 30.0))
target = mathutils.Vector((20.0, 54.0, 14.0))
direction = target - cam_pos
cam_obj.location = cam_pos
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.render.filepath = os.path.join(ROOT, "tools/preview_grandstand_front.png")
bpy.ops.render.render(write_still=True)
print("Wyrenderowano: preview_grandstand_front.png")

# 2. UJĘCIE OD STRONY AL. UNII (REAR / BRUTALIST STRUTS)
cam_pos_rear = mathutils.Vector((75.0, -15.0, 25.0))
target_rear = mathutils.Vector((35.0, 54.0, 12.0))
direction_rear = target_rear - cam_pos_rear
cam_obj.location = cam_pos_rear
cam_obj.rotation_euler = direction_rear.to_track_quat('-Z', 'Y').to_euler()

bpy.context.scene.render.filepath = os.path.join(ROOT, "tools/preview_grandstand_rear.png")
bpy.ops.render.render(write_still=True)
print("Wyrenderowano: preview_grandstand_rear.png")
