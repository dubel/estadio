"""
Renderuje szybki rzut izometryczny / perspektywiczny wygenerowanej bazy trybuny.
"""
import bpy
import math

blend_path = "/home/mike/Projects/estadiodagruz/trybuna_glowna_baza.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

# Dodaj kamerę
cam_data = bpy.data.cameras.new("PreviewCam")
cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Ustaw pozycję kamery z widokiem na trybunę od strony boiska
cam_obj.location = (-35.0, 54.0, 25.0)
cam_obj.rotation_euler = (math.radians(65), 0, math.radians(-70))

# Dodaj światło słońca (Sun)
sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 3.5
sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(45), math.radians(30), math.radians(-45))

# Konfiguracja renderera
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 960
bpy.context.scene.render.resolution_y = 540
bpy.context.scene.render.filepath = "/home/mike/Projects/estadiodagruz/tools/preview.png"

bpy.ops.render.render(write_still=True)
print("Zapisano render podglądu do tools/preview.png")
