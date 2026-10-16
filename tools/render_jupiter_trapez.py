import bpy
import mathutils
import math

bpy.ops.wm.open_mainfile(filepath="/home/mike/Projects/estadiodagruz/jupiter_trapez_test.blend")

cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Maszt jest w (-65, -80, 0), szczyt w (-65, -80, 48)
cam_pos = mathutils.Vector((-48.0, -62.0, 48.0))
target = mathutils.Vector((-65.0, -80.0, 47.0))
cam_obj.location = cam_pos
cam_obj.rotation_euler = (target - cam_pos).to_track_quat('-Z', 'Y').to_euler()

sun_data = bpy.data.lights.new(name="Sun", type='SUN')
sun_data.energy = 4.0
sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(-30))

world = bpy.context.scene.world
if not world:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (0.25, 0.35, 0.45, 1.0)
    bg.inputs['Strength'].default_value = 1.0

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 960
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = "/home/mike/Projects/estadiodagruz/tools/preview_jupiter_trapez.png"

bpy.ops.render.render(write_still=True)
print("Saved preview_jupiter_trapez.png")
