import bpy, math, time, json, sys, os, random
from mathutils import Vector

OUT = r"D:\Code\Code MV\new-word.search(you)\mv\out\bench"
os.makedirs(OUT, exist_ok=True)

# clean
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.resolution_x = 2560
scene.render.resolution_y = 1440
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = os.path.join(OUT, 'bench_')

# world
w = bpy.data.worlds.new("W"); scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.004, 0.008, 0.02, 1)
bg.inputs[1].default_value = 1.0
# volume
vol = w.node_tree.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.012
vol.inputs["Color"].default_value = (0.35, 0.55, 0.9, 1)
w.node_tree.links.new(vol.outputs[0], w.node_tree.nodes["World Output"].inputs["Volume"])

# fish-ish mesh
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1)
fish = bpy.context.object
fish.scale = (1.6, 1.0, 0.85)
for p in fish.data.vertices:
    x, y, z = p.co
    # taper tail
    t = max(0.0, -x)
    p.co.z *= (1.0 - 0.55 * t)
    p.co.y *= (1.0 - 0.35 * t)
fish.data.update()
mod = fish.modifiers.new("sub", 'SUBSURF'); mod.levels = 1; mod.render_levels = 1
mat = bpy.data.materials.new("fishmat"); mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.15, 0.45, 0.9, 1)
bsdf.inputs["Roughness"].default_value = 0.35
bsdf.inputs["Metallic"].default_value = 0.1
try:
    bsdf.inputs["Coat Weight"].default_value = 0.6
except Exception: pass
fish.data.materials.append(mat)
fish.rotation_euler = (0, 0, 0)

# glyph instances: use simple icospheres as proxy for text meshes
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.03)
proto = bpy.context.object
gmat = bpy.data.materials.new("glow"); gmat.use_nodes = True
gb = gmat.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (0.2, 0.7, 1.0, 1)
gb.inputs["Emission Color"].default_value = (0.25, 0.75, 1.0, 1)
gb.inputs["Emission Strength"].default_value = 6.0
proto.data.materials.append(gmat)
random.seed(1)
inst = proto.modifiers.new("arr", 'ARRAY'); inst.count = 600
inst.use_relative_offset = True
inst.relative_offset_displace = (0.13, 0.05, 0.02)
proto.location = (0, 0, -2)

# lights
def light(name, ltype, energy, loc, size=5, color=(1,1,1)):
    d = bpy.data.lights.new(name, ltype); d.energy = energy; d.color = color
    if ltype == 'AREA': d.size = size
    o = bpy.data.objects.new(name, d); o.location = loc
    bpy.context.collection.objects.link(o); return o
light("key", 'AREA', 2500, (5, -4, 6), 6, (1.0, 0.85, 0.65))
light("rim", 'AREA', 4000, (-5, 4, 3), 4, (0.35, 0.7, 1.0))
light("fill", 'POINT', 800, (0, -3, 2), 2, (0.4, 0.7, 1.0))
# warm point to simulate her
bpy.ops.object.light_add(type='POINT', location=(-1.2, 2.0, 0.2))
her = bpy.context.object; her.data.energy = 250; her.data.color = (1.0, 0.45, 0.2); her.data.shadow_soft_size = 0.3

# camera
bpy.ops.object.camera_add(location=(4.5, -6.5, 2.2))
cam = bpy.context.object; cam.data.lens = 50
cam.rotation_euler = (math.radians(78), 0, math.radians(35))
scene.camera = cam
focus = bpy.data.objects.new("focus", None); bpy.context.collection.objects.link(focus); focus.location = (0,0,0)
cam.data.dof.use_dof = True; cam.data.dof.focus_object = focus; cam.data.dof.aperture_fstop = 2.8

# eevee settings
ee = scene.eevee
for attr, val in [('taa_render_samples', 24), ('use_raytracing', True), ('use_shadows', True),
                  ('shadow_ray_count', 1), ('shadow_step_count', 6), ('volumetric_samples', 32),
                  ('volumetric_tile_size', '8'), ('use_volumetric_shadows', False)]:
    if hasattr(ee, attr):
        try: setattr(ee, attr, val)
        except Exception as e: print("attr fail", attr, e)
print("eevee attrs:", [a for a in dir(ee) if 'ray' in a or 'volum' in a or 'sample' in a][:40])
print("engine:", scene.render.engine)
try:
    import gpu
    print("GPU:", gpu.platform.renderer_get(), gpu.platform.backend_type_get())
except Exception as e:
    print("gpu info fail", e)

scene.frame_start = 1; scene.frame_end = 6
scene.render.use_file_extension = True
times = []
for f in range(1, 7):
    scene.frame_set(f)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    times.append(dt)
    print("FRAME", f, round(dt, 3))
print("HEADLESS " + json.dumps({"times": times, "avg": sum(times)/len(times), "res": [2560,1440]}))
