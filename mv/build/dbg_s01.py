"""debug s01 layout: build the scene in GUI, print object bounds, show solid view."""
import bpy, sys, os
MV = r'D:\Code\Code MV\new-word.search(you)'
sys.path.insert(0, os.path.join(MV, 'mv', 'build'))
for _m in list(sys.modules):
    if _m in ('shotkit', 'shot_s01') or _m.startswith('core') or _m.startswith('world') or _m.startswith('geo') or _m.startswith('stage') or _m.startswith('char_paper'):
        sys.modules.pop(_m, None)
import shotkit as K
import shot_s01
shot_s01.build()
sc = bpy.context.scene
print('=== OBJECTS ===')
for ob in bpy.data.objects:
    d = tuple(round(v, 3) for v in ob.dimensions)
    l = tuple(round(v, 3) for v in ob.location)
    print('%-16s %-10s dim=%s loc=%s hide_render=%s' % (ob.name, ob.type, d, l, ob.hide_render))
print('camera', sc.camera.name if sc.camera else None)
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.overlay.show_overlays = True
                space.region_3d.view_perspective = 'CAMERA'
sc.frame_set(1)
