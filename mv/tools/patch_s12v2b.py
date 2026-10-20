"""s12: tint the whale to warm paper, fade shards as the whale surfaces."""
import io
import py_compile

P = r'D:\Code\Code MV\new-word.search(you)\mv\build\shot_s12.py'
s = io.open(P, encoding='utf-8').read()

old = "    # cold backlight behind the whale"
new = '''    # tint the white whale texture to warm paper so it reads as cut paper, not a lightbox
    try:
        nt = mat.node_tree
        img_n = None
        for n in nt.nodes:
            if n.type == 'TEX_IMAGE':
                img_n = n
                break
        bsdf_in = None
        for l in nt.links:
            if l.from_node.type == 'TEX_IMAGE' and l.to_node.type in ('BSDF_PRINCIPLED', 'EMISSION'):
                bsdf_in = l.to_socket
        if img_n is not None and bsdf_in is not None:
            mixn = nt.nodes.new('ShaderNodeMixRGB')
            mixn.blend_type = 'MULTIPLY'
            mixn.inputs['Fac'].default_value = 1.0
            mixn.inputs['Color2'].default_value = (0.66, 0.575, 0.46, 1.0)
            nt.links.new(img_n.outputs['Color'], mixn.inputs['Color1'])
            nt.links.new(mixn.outputs['Color'], bsdf_in)
    except Exception as _e:
        print('whale tint failed: %r' % (_e,), flush=True)

    # cold backlight behind the whale'''
if 'whale tint failed' not in s:
    assert old in s
    s = s.replace(old, new, 1)
    print('[ok] whale tint')

old2 = "    ob.scale = (0.55, 0.55, 0.55)\n    ob.keyframe_insert('scale', frame=1400)\n    K.ease(ob)\n    return ob"
new2 = ("    ob.scale = (0.55, 0.55, 0.55)\n    ob.keyframe_insert('scale', frame=1400)\n"
        "    ob.scale = (0.28, 0.28, 0.28)\n    ob.keyframe_insert('scale', frame=1520)\n"
        "    ob.scale = (0.001, 0.001, 0.001)\n    ob.keyframe_insert('scale', frame=1592)\n"
        "    K.ease(ob)\n    return ob")
if 'frame=1592' not in s:
    assert old2 in s
    s = s.replace(old2, new2, 1)
    print('[ok] shards fade')

io.open(P, 'w', encoding='utf-8').write(s)
py_compile.compile(P, doraise=True)
print('compiled OK')
