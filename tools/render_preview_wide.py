"""
Renderuje widok perspektywiczny z ukosa pokazujący cały przekrój i 108 m trybuny.
"""
import bpy
import mathutils
import math

blend_path = "/home/mike/Projects/estadiodagruz/trybuna_glowna_baza.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

# Dodaj kamerę
cam_data = bpy.data.cameras.new("PreviewCam")
cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_pos = mathutils.Vector((-45.0, -25.0, 32.0))
target = mathutils.Vector((10.0, 45.0, 6.0))
direction = target - cam_pos
rot_quat = direction.to_track_quat('-Z', 'Y')

cam_obj.location = cam_pos
cam_obj.rotation_euler = rot_quat.to_euler()

# Dodaj słońce
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(50), math.radians(20), math.radians(-35))

# Renderer
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = "/home/mike/Projects/estadiodagruz/tools/preview_wide.png"

bpy.ops.render.render(write_still=True)
print("Zapisano szeroki render podglądu do tools/preview_wide.png")
