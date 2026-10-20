"""dbg_s02_c.py - render combined frame 250, print camera + object transforms."""
import bpy, sys
sys.path.insert(0, r'D:\Code\Code MV\new-word.search(you)\mv\build')
for _m in ('core', 'world', 'geo', 'world_theater', 'shotkit', 'stage', 'specimens', 'char_paper', 'shot_s02'):
    sys.modules.pop(_m, None)
import shot_s02

shot_s02.build()
sc = bpy.context.scene
sc.frame_set(250)
cam = sc.camera
print('CAMERA', cam.name, 'loc', tuple(round(v, 3) for v in cam.location),
      'rotmode', cam.rotation_mode, 'dof', cam.data.dof.use_dof, 'fstop', cam.data.dof.aperture_fstop)
print('CAM matrix translation', tuple(round(v, 3) for v in cam.matrix_world.translation))
print('CAM -Z dir', tuple(round(v, 3) for v in (cam.matrix_world.to_quaternion() @ __import__('mathutils').Vector((0, 0, -1)))))
for ob in bpy.data.objects:
    if ob.name == 'index_page' or ob.name.startswith('idx_'):
        print('OBJ', ob.name, 'hide_render', ob.hide_render, 'visible_camera', ob.visible_camera,
              'mwY', round(ob.matrix_world.translation.y, 3),
              'scale', tuple(round(v, 3) for v in ob.scale),
              'rot', tuple(round(v, 3) for v in ob.rotation_euler),
              'dims', tuple(round(v, 3) for v in ob.dimensions))
sc.render.resolution_x = 960
sc.render.resolution_y = 540
sc.render.filepath = r'D:\Code\Code MV\new-word.search(you)\mv\out\lookdev\dbg_s02_combined.png'
bpy.ops.render.render(write_still=True)
print('DBG_C_DONE')
