import bpy
import mathutils
import math

bpy.ops.wm.open_mainfile(filepath="/home/mike/Projects/estadiodagruz/jupiter_test.blend")

cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_pos = mathutils.Vector((-12.0, -12.0, 50.0))
target = mathutils.Vector((0.0, 0.0, 50.0))
cam_obj.location = cam_pos
cam_obj.rotation_euler = (target - cam_pos).to_track_quat('-Z', 'Y').to_euler()

sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(35), math.radians(20), math.radians(-30))

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 960
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = "/home/mike/Projects/estadiodagruz/tools/preview_jupiter_head.png"

bpy.ops.render.render(write_still=True)
print("Saved preview_jupiter_head.png")
