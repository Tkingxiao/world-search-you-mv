"""core.py - shared render/scene helpers for the MV (lead's pipeline).
Blender 4.5.3 / EEVEE-Next. Import inside headless scripts.
"""
import bpy, math, os, json, random
from mathutils import Vector, Euler

ROOT = r'D:\Code\Code MV\new-word.search(you)'
MV = os.path.join(ROOT, 'mv')
TEX = os.path.join(MV, 'ref', 'art')

W, H, FPS = 1920, 1080, 60
SAMPLES = 10

# ----------------------------------------------------------------------------- palette
INK      = (0.043, 0.055, 0.075)      # #1d2029
PAPER    = (0.775, 0.745, 0.680)      # #ece8de-ish after AgX
PAPER_HI = (0.88, 0.855, 0.79)
HER      = (0.075, 0.16, 1.0)         # #4d6bfe blue
WARM     = (1.0, 0.19, 0.10)          # #ff6b4a coral
GOLD     = (1.0, 0.62, 0.20)          # #ffd28a
CYAN     = (0.03, 0.46, 1.0)          # #38c9ff
ABYSS    = (0.006, 0.022, 0.035)      # #0a2230

# ----------------------------------------------------------------------------- scene reset
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start = 1
    sc.frame_end = 100
    return sc


def reset_soft():
    """Clear the current scene without touching preferences/addons (GUI-safe)."""
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                 bpy.data.cameras, bpy.data.curves, bpy.data.images):
        for b in list(coll):
            if b.users == 0:
                try:
                    coll.remove(b)
                except Exception:
                    pass
    sc.render.fps = FPS
    sc.frame_start = 1
    sc.frame_end = 100
    return sc

def setup_render(frames=None, samples=SAMPLES, w=W, h=H, glare=True):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.film_transparent = False
    sc.eevee.taa_render_samples = samples
    # camera-move polish: motion blur on (cheap in EEVEE-Next for camera-only moves)
    try:
        import os as _os
        # NOTE: EEVEE-Next motion blur is 8-10x per frame on this scene mix (BLENDED paper
        # cards + world volume), measured 24s vs 2.5s per frame -> OFF unless explicitly asked.
        sc.render.use_motion_blur = _os.environ.get('MV_MOTION_BLUR', '0') == '1'
        sc.render.motion_blur_shutter = 0.45
    except Exception:
        pass
    # EEVEE-Next quality knobs
    # NOTE: raytraced reflections are OFF on purpose: the look is matte paper, RT added
    # almost nothing visually yet dominated per-frame cost / VRAM with several renders
    # sharing the 8 GB card.
    for attr, val in (('use_raytracing', False), ('use_shadows', True),
                      ('volumetric_tile_size', '8'), ('volumetric_samples', 32),
                      ('volumetric_sample_distribution', 0.9),
                      ('use_volumetric_shadows', False)):
        if hasattr(sc.eevee, attr):
            try:
                setattr(sc.eevee, attr, val)
            except Exception:
                pass
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        try:
            sc.view_settings.look = 'AgX - Punchy'
        except Exception:
            pass
    sc.view_settings.exposure = 0.0
    if frames:
        sc.frame_start, sc.frame_end = frames
    if glare:
        add_glare(sc)
    return sc

def add_glare(sc, threshold=1.0, size=8, mix=-0.55, quality='MEDIUM'):
    sc.use_nodes = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new('CompositorNodeRLayers')
    gl = nt.nodes.new('CompositorNodeGlare')
    comp = nt.nodes.new('CompositorNodeComposite')
    try:
        gl.glare_type = 'BLOOM'
    except Exception:
        gl.glare_type = 'FOG_GLOW'
    gl.quality = quality
    gl.threshold = threshold
    gl.size = size
    if hasattr(gl, 'mix'):
        gl.mix = mix if gl.glare_type != 'BLOOM' else 0.0
    nt.links.new(rl.outputs['Image'], gl.inputs['Image'])
    nt.links.new(gl.outputs['Image'], comp.inputs['Image'])
    return gl

# ----------------------------------------------------------------------------- materials
def _bsdf(nt):
    """Find the Principled BSDF node by type (node *names* are localized in the GUI)."""
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    n = nt.nodes.new('ShaderNodeBsdfPrincipled')
    out = next((x for x in nt.nodes if x.type == 'OUTPUT_MATERIAL'), None)
    if out:
        nt.links.new(n.outputs['BSDF'], out.inputs['Surface'])
    return n


def _principled(name, base, rough=0.7, metal=0.0, emission=None, strength=1.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = _bsdf(nt)
    bsdf.inputs['Base Color'].default_value = (*base, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1)
        bsdf.inputs['Emission Strength'].default_value = strength
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'DITHERED'
    return m

def paper(name='paper', base=PAPER, rough=0.82, fiber=1.0):
    """Paper: warm off-white with fibrous bump + faint mottling."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = _bsdf(nt)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Base Color'].default_value = (*base, 1)
    bsdf.inputs['Specular IOR Level'].default_value = 0.25
    tex = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 260; noise.inputs['Detail'].default_value = 6; noise.inputs['Roughness'].default_value = 0.65
    links.new(tex.outputs['Object'], noise.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.25 * fiber; bump.inputs['Distance'].default_value = 0.0006
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    # subtle color variation
    n2 = nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 12; n2.inputs['Detail'].default_value = 3
    links.new(tex.outputs['Object'], n2.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*[c * 0.86 for c in base], 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (*[min(1, c * 1.06) for c in base], 1)
    links.new(n2.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    return m

def emissive(name, color, strength=4.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*color, 1)
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m

def glass(name='glass', base=(0.72, 0.82, 0.92), rough=0.06):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = _bsdf(nt)
    bsdf.inputs['Base Color'].default_value = (*base, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Transmission Weight'].default_value = 1.0
    bsdf.inputs['IOR'].default_value = 1.45
    m.use_raytrace_refraction = True
    return m

def text_mat(name='label_text', color=(0.03, 0.035, 0.045), strength=0.0):
    """Very dark ink for engraved label text; slight emission for legibility in fog."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = _bsdf(nt)
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = 0.9
    if strength:
        bsdf.inputs['Emission Color'].default_value = (*color, 1)
        bsdf.inputs['Emission Strength'].default_value = strength
    return m

def copy_mat_emission_alpha(name, color, strength, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*color, 1); em.inputs['Strength'].default_value = strength
    if alpha < 1:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = 1.0 - alpha
        nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
        nt.links.new(em.outputs['Emission'], mix.inputs[2])
        m.surface_render_method = 'DITHERED'
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    else:
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m

# ----------------------------------------------------------------------------- fog / world
def fog_world(density=0.012, color=(0.02, 0.09, 0.13), ambient=(0.008, 0.03, 0.05),
              anisotropy=0.35):
    sc = bpy.context.scene
    w = bpy.data.worlds.get('mv_world') or bpy.data.worlds.new('mv_world')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (*ambient, 1)
    bg.inputs['Strength'].default_value = 1.0
    vol = nt.nodes.new('ShaderNodeVolumeScatter')
    vol.inputs['Color'].default_value = (*color, 1)
    vol.inputs['Density'].default_value = density
    vol.inputs['Anisotropy'].default_value = anisotropy
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    nt.links.new(vol.outputs['Volume'], out.inputs['Volume'])
    return w

# ----------------------------------------------------------------------------- objects
def plane(name, size=1.0, loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    if mat:
        ob.data.materials.append(mat)
    return ob

def box(name, dims=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (dims[0], dims[1], dims[2])  # size=1 cube -> scale == edge length
    ob.rotation_euler = rot
    if mat:
        ob.data.materials.append(mat)
    return ob

def text_obj(name, body, size=0.1, loc=(0, 0, 0), rot=(0, 0, 0), font='C:/Windows/Fonts/georgia.ttf',
             mat=None, align='LEFT', extrude=0.0, spacing=1.0):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.space_character = spacing
    cu.extrude = extrude
    if font and os.path.exists(font):
        cu.font = bpy.data.fonts.load(font)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    if mat:
        ob.data.materials.append(mat)
    return ob

# ----------------------------------------------------------------------------- lights
def light(name, kind='AREA', loc=(0, 0, 0), energy=100.0, color=(1, 1, 1), size=1.0, target=None, angle=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == 'AREA':
        ld.size = size
    elif kind == 'SPOT':
        ld.spot_size = angle if angle is not None else math.radians(45)
        ld.spot_blend = 0.35
        ld.shadow_soft_size = size
    elif kind == 'POINT':
        ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    if target:
        c = ob.constraints.new('TRACK_TO')
        c.target = target
        c.track_axis = 'TRACK_NEGATIVE_Z'
        c.up_axis = 'UP_Y'
    return ob

def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

# ----------------------------------------------------------------------------- camera
def camera(name='cam', lens=35.0, loc=(0, -6, 1.5), target=(0, 0, 1.2), dof=False, fstop=2.8, focus=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    ob = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    if dof:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        if focus is not None:
            cd.dof.focus_object = focus
        else:
            cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
    bpy.context.scene.camera = ob
    return ob

def keyframe(ob, frame, loc=None, rot=None, scale=None):
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert('location', frame=frame)
    if rot is not None:
        ob.rotation_euler = rot
        ob.keyframe_insert('rotation_euler', frame=frame)
    if scale is not None:
        ob.scale = scale
        ob.keyframe_insert('scale', frame=frame)

# ----------------------------------------------------------------------------- particles / dust
def dust(name='dust', count=1200, extent=(12, 12, 10), center=(0, 0, 4), size=0.012,
         color=(0.5, 0.85, 1.0), strength=2.0):
    """Glowing plankton/dust via instanced icospheres on a point cloud."""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    random.seed(7)
    for _ in range(count):
        x = random.uniform(-extent[0] / 2, extent[0] / 2) + center[0]
        y = random.uniform(-extent[1] / 2, extent[1] / 2) + center[1]
        z = random.uniform(-extent[2] / 2, extent[2] / 2) + center[2]
        bm.verts.new((x, y, z))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    # instance small icosphere on points
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=size, location=(0, 0, 0))
    ico = bpy.context.object
    ico.name = name + '_proto'
    ico.data.materials.append(emissive(name + '_mat', color, strength))
    ico.hide_render = False
    bpy.context.view_layer.objects.active = ob
    mod = ob.modifiers.new('pts', 'NODES') if False else None
    # simplest robust: use dupli on verts
    ico.parent = ob
    ico.location = (0, 0, 0)
    ob.instance_type = 'VERTS'
    ob.show_instancer_for_render = False
    ico.hide_viewport = True
    ico.hide_render = True
    return ob

def simple_world(bg_color=(0.01, 0.03, 0.05), strength=1.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.get('simple_world') or bpy.data.worlds.new('simple_world')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (*bg_color, 1)
    bg.inputs['Strength'].default_value = strength
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return w

# ----------------------------------------------------------------------------- character (fallback, replaced by char_paper when available)
def illustration_card(path, height=1.72, loc=(0, 0, 0), face_neg_y=True, alpha_clip=False, name='fish_card',
                      emission_strength=0.0, bend=0.0):
    img = bpy.data.images.load(path)
    iw, ih = img.size
    aspect = iw / ih
    h = height
    wdt = h * aspect
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (wdt, h, 1)
    # stand up facing +Y (camera sits at larger Y); texture reads left-to-right
    ob.rotation_euler = (math.radians(90), 0, math.pi)
    m = bpy.data.materials.new(name + '_mat')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = _bsdf(nt)
    bsdf.inputs['Roughness'].default_value = 0.78
    bsdf.inputs['Specular IOR Level'].default_value = 0.2
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Linear'
    tex.extension = 'CLIP'
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    if emission_strength > 0:
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    m.surface_render_method = 'DITHERED'
    m.use_backface_culling = False
    if alpha_clip:
        m.use_transparent_shadow = True
    ob.data.materials.append(m)
    # lift so feet sit at z = loc.z
    ob.location = (loc[0], loc[1], loc[2] + h / 2)
    return ob, m


def paper_cutout(path, height=1.72, loc=(0, 0, 0), name='cutout', emission_strength=0.10,
                 rim=0.010, tint=None):
    """Official art as a paper cut-out: textured front card + dark backing card offset a
    hair behind it, which reads as the thickness/shadow edge of cut paper.
    Returns (front_ob, front_mat, back_ob)."""
    front, mat = illustration_card(path, height=height, loc=loc, name=name,
                                   emission_strength=emission_strength)
    if tint is not None:
        bsdf = _bsdf(mat.node_tree)
        bsdf.inputs['Base Color'].default_value = (*tint, 1)
    img = bpy.data.images.load(path)
    iw, ih = img.size
    aspect = iw / ih
    h = height
    wdt = h * aspect
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0))
    back = bpy.context.object
    back.name = name + '_back'
    back.scale = (wdt + rim * 2, h + rim * 2, 1)
    back.rotation_euler = (math.radians(90), 0, math.pi)
    mb = bpy.data.materials.new(name + '_back_mat')
    mb.use_nodes = True
    nt = mb.node_tree
    bsdf = _bsdf(nt)
    bsdf.inputs['Base Color'].default_value = (0.012, 0.014, 0.018, 1)
    bsdf.inputs['Roughness'].default_value = 0.9
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.extension = 'CLIP'
    nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    mb.surface_render_method = 'DITHERED'
    mb.use_backface_culling = False
    back.data.materials.append(mb)
    back.location = (loc[0], loc[1] - 0.008, loc[2] + h / 2)
    return front, mat, back
