"""specimens.py -- "Museum of Approximations" specimen / koinobori / prop API.

Blender 4.5.3 LTS + EEVEE-Next.  Pure procedural geometry: no external assets
except Windows system fonts (Georgia / Consolas).  Every build_* function is
deterministic (fixed local RNG, no scene-random) and returns a *Collection*
whose objects are parented to one root Empty.

Look:  museum hologram scan =
        thin emissive wireframe  (Wireframe modifier, cyan-ish line)
      + sparse point cloud       (tiny emissive triangles sampled on the surface)
      + very faint transluc shell (blended fresnel, ~4% alpha)
      + paper plinth with a soft radial "projector" halo
      + hanging paper label plate, engraved name (Georgia) + data (Consolas).

Conventions
-----------
* Specimens: scan volume normalised to `style["height"]` (default 1.0) tall,
  footprint centred on x=y=0, plinth base at z=0.  With the default plinth the
  assembly stands on the floor (z=0) and the scan floats above the plinth.
  style={"plinth": False} gives the bare scan: base exactly z=0, height 1.0.
* Props (bucket / tomato / index sheet): paper objects, base z=0, height 1.0.
* Koinobori: paper carp kite, total nose-to-tail length = `length` (default
  1.4); lowest point of the kite at z=0, body axis centred above it.

Public API
----------
builders
    build_table, build_eggplant, build_cat, build_steak, build_flower,
    build_human, build_koinobori, build_bucket, build_tomato_paper,
    build_index_sheet
helpers
    animate_flutter(obj, ...)   -- float + tail wave (shape keys + root keys)
    animate_scan(coll, ...)     -- travelling emissive scan ring on a specimen
    set_scan_params(coll, ...)  -- retune wire thickness / strength / points
    measure(coll) -> dict       -- evaluated triangle counts
    root_of(coll) -> Empty
    PEER_COLORS, PALETTE, SPECIMEN_STYLES, DEFAULT_STYLE
"""

from __future__ import annotations

import bisect
import json
import math
import random
import zlib

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

__all__ = [
    "build_table", "build_eggplant", "build_cat", "build_steak",
    "build_flower", "build_human", "build_koinobori", "build_bucket",
    "build_tomato_paper", "build_index_sheet",
    "animate_flutter", "animate_scan", "set_scan_params",
    "measure", "root_of", "PEER_COLORS", "PALETTE", "SPECIMEN_STYLES",
    "DEFAULT_STYLE", "FONT_GEORGIA", "FONT_CONSOLAS",
]

# ---------------------------------------------------------------------------
# palette / fonts / constants
# ---------------------------------------------------------------------------

PALETTE = {
    "water": "#0a2230",     # sunken archive water
    "scan": "#38c9ff",      # world / retrieval cyan
    "spot": "#ffd28a",      # museum spot gold
    "paper": "#ece8de",     # warm white paper
    "coral": "#ff6b4a",     # her / you warm coral
    "ink": "#1d2029",       # label ink / deep charcoal
}

# One paper colour per peer model (paper-kite koinobori).  `merged` is the
# evolved self: warm unbleached paper.  Muted print-ink tones, never neon.
PEER_COLORS = {
    "kimi":    "#ffcf7a",
    "qwen":    "#6fa8ff",
    "mimo":    "#ff9a6a",
    "glm":     "#7fd8b0",
    "minimax": "#b08cff",
    "hy4":     "#ff7f9e",
    "ernie":   "#5aa0e8",
    "step":    "#bfe07a",
    "longcat": "#ffbe6e",
    "doubao":  "#8fc8ff",
    "merged":  "#efe6d6",
}

FONT_GEORGIA = r"C:\Windows\Fonts\georgia.ttf"
FONT_CONSOLAS = r"C:\Windows\Fonts\consola.ttf"

WIRE_MOD = "SCAN_WIRE"

DEFAULT_STYLE = {
    "height": 1.0,
    "fit": "height",          # height | max | width
    "plinth": True,
    "plinth_h": 0.40,
    "plinth_gap": 0.10,
    "label": True,
    "label_side": "right",
    "label_lines": None,      # [NAME, data1, data2, ...]
    "points": True,
    "point_count": 380,
    "point_size": 0.0032,
    "shell": True,
    "shell_alpha": 0.05,
    "wire": True,
    "wire_ratio": 0.40,
    "wire_thickness": 0.0032,
    "wire_strength": 1.7,
    "point_strength": 2.8,
    "scan_color": PALETTE["scan"],
    "paper_color": PALETTE["paper"],
    "halo": True,
    "seed": 0,
    "mount": None,            # None | "wedge" (leaning slab support)
    "triangulate": True,
}

# Per-specimen art direction (shots s06-s12 of TREATMENT.md).
SPECIMEN_STYLES = {
    "table": dict(scan_color="#aee4ff", point_count=380, wire_thickness=0.0030,
                  plinth_h=0.38, label_lines=[
                      "TABLE", "sim 0.31   mass 0.00 kg", "function: surface"]),
    "eggplant": dict(scan_color="#b98cff", point_count=380, wire_thickness=0.0030,
                     wire_strength=1.9, plinth_h=0.40, label_lines=[
                         "EGGPLANT", "sim 0.28   mass 0.00 kg", "function: food"]),
    "cat": dict(scan_color="#8fe0ff", point_count=380, wire_thickness=0.0030,
                plinth_h=0.42, label_lines=[
                    "CAT", "sim 0.22   mass 0.00 kg", "function: pet"]),
    "steak": dict(scan_color="#ffb066", point_count=300, wire_thickness=0.0028,
                  plinth_h=0.36, label_lines=[
                      "STEAK", "sim 0.19   mass 0.00 kg", "function: food"]),
    "flower": dict(scan_color="#ff9a7a", point_count=380, wire_thickness=0.0026,
                   wire_strength=1.9, plinth_h=0.40, label_lines=[
                       "FLOWER", "sim 0.26   mass 0.00 kg", "function: ornament"]),
    "human": dict(scan_color="#ffd28a", point_count=380, wire_thickness=0.0036,
                  wire_strength=1.9, wire_ratio=0.40, plinth_h=0.44,
                  label_lines=[
                      "HUMAN", "sim 0.13   mass 0.00 kg", "function: you"]),
}

_GEOMETRY_MATERIALS: dict[str, bpy.types.Material] = {}
_FONTS: dict[str, bpy.types.VectorFont] = {}


# ---------------------------------------------------------------------------
# colour / material helpers
# ---------------------------------------------------------------------------

def _srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h: str, a: float = 1.0):
    """sRGB hex string -> linear RGBA tuple (Blender node colours are linear)."""
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), a)


def hex_luma(h: str) -> float:
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _rgba_scaled(color, k: float):
    return (color[0] * k, color[1] * k, color[2] * k, color[3])


def _material(name: str):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    return mat, nt, out


def _principled(nt):
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (280, 0)
    return bsdf


def _link(nt, a, b):
    nt.links.new(a, b)


def mat_paper(name, color=None, roughness=0.86, edge_glow=0.55,
              edge_color=None, emission=0.0, alpha=1.0, noise_scale=55.0,
              bump=0.28):
    key = (f"MAT_paper_{name}_{color}_{roughness:.2f}_{edge_glow:.2f}_"
           f"{emission:.3f}_{alpha:.2f}_{noise_scale:.0f}")
    if key in _GEOMETRY_MATERIALS:
        return _GEOMETRY_MATERIALS[key]
    color = color or PALETTE["paper"]
    mat, nt, out = _material(key)
    bsdf = _principled(nt)
    base = hex_rgba(color)
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    # fibre noise: slight tonal variation + micro bump
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = noise_scale
    tex.inputs["Detail"].default_value = 3.0
    tex.inputs["Roughness"].default_value = 0.55
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.32
    ramp.color_ramp.elements[0].color = (0.88, 0.88, 0.88, 1.0)
    ramp.color_ramp.elements[1].position = 0.68
    ramp.color_ramp.elements[1].color = (1.05, 1.05, 1.05, 1.0)
    _link(nt, tex.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.55
    mix.inputs["Color1"].default_value = base
    _link(nt, ramp.outputs["Color"], mix.inputs["Color2"])
    _link(nt, mix.outputs["Color"], bsdf.inputs["Base Color"])
    if bump > 0.0:
        bmp = nt.nodes.new("ShaderNodeBump")
        bmp.inputs["Strength"].default_value = bump
        bmp.inputs["Distance"].default_value = 0.004
        _link(nt, tex.outputs["Fac"], bmp.inputs["Height"])
        _link(nt, bmp.outputs["Normal"], bsdf.inputs["Normal"])
    # paper edge glow (thin paper edges catching the water light) + base emission
    ec = hex_rgba(edge_color or PALETTE["scan"])
    if edge_glow > 0.0 or emission > 0.0:
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.30
        p = nt.nodes.new("ShaderNodeMath")
        p.operation = "POWER"
        p.inputs[1].default_value = 2.2
        _link(nt, lw.outputs["Facing"], p.inputs[0])
        m = nt.nodes.new("ShaderNodeMath")
        m.operation = "MULTIPLY"
        m.inputs[1].default_value = edge_glow
        _link(nt, p.outputs[0], m.inputs[0])
        edge = nt.nodes.new("ShaderNodeMixRGB")
        edge.blend_type = "MULTIPLY"
        edge.inputs["Fac"].default_value = 1.0
        edge.inputs["Color1"].default_value = ec
        _link(nt, m.outputs[0], edge.inputs["Color2"])
        emit = edge.outputs["Color"]
        if emission > 0.0:
            base_emit = nt.nodes.new("ShaderNodeMixRGB")
            base_emit.blend_type = "MULTIPLY"
            base_emit.inputs["Fac"].default_value = 1.0
            base_emit.inputs["Color1"].default_value = base
            base_emit.inputs["Color2"].default_value = (emission, emission,
                                                         emission, 1.0)
            add = nt.nodes.new("ShaderNodeMixRGB")
            add.blend_type = "ADD"
            add.inputs["Fac"].default_value = 1.0
            _link(nt, emit, add.inputs["Color1"])
            _link(nt, base_emit.outputs["Color"], add.inputs["Color2"])
            emit = add.outputs["Color"]
        _link(nt, emit, bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.0
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.surface_render_method = "BLENDED"
        mat.use_transparent_shadow = True
    _link(nt, bsdf.outputs["BSDF"], out.inputs["Surface"])
    _GEOMETRY_MATERIALS[key] = mat
    return mat


def mat_ink(name, color=None):
    key = f"MAT_ink_{name}_{color}"
    if key in _GEOMETRY_MATERIALS:
        return _GEOMETRY_MATERIALS[key]
    mat, nt, out = _material(key)
    bsdf = _principled(nt)
    c = hex_rgba(color or PALETTE["ink"])
    bsdf.inputs["Base Color"].default_value = c
    bsdf.inputs["Roughness"].default_value = 0.62
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Emission Color"].default_value = c
    bsdf.inputs["Emission Strength"].default_value = 0.05
    _link(nt, bsdf.outputs["BSDF"], out.inputs["Surface"])
    _GEOMETRY_MATERIALS[key] = mat
    return mat


def mat_metal(name, color="#3a444d"):
    key = f"MAT_metal_{name}_{color}"
    if key in _GEOMETRY_MATERIALS:
        return _GEOMETRY_MATERIALS[key]
    mat, nt, out = _material(key)
    bsdf = _principled(nt)
    bsdf.inputs["Base Color"].default_value = hex_rgba(color)
    bsdf.inputs["Metallic"].default_value = 0.75
    bsdf.inputs["Roughness"].default_value = 0.34
    bsdf.inputs["Emission Color"].default_value = hex_rgba("#9fc6d8")
    bsdf.inputs["Emission Strength"].default_value = 0.35
    _link(nt, bsdf.outputs["BSDF"], out.inputs["Surface"])
    _GEOMETRY_MATERIALS[key] = mat
    return mat


def mat_emission(color, strength, tag=""):
    key = f"MAT_emit_{color}_{strength:.2f}_{tag}"
    if key in _GEOMETRY_MATERIALS:
        return _GEOMETRY_MATERIALS[key]
    mat, nt, out = _material(key)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex_rgba(color)
    em.inputs["Strength"].default_value = strength
    _link(nt, em.outputs[0], out.inputs["Surface"])
    _GEOMETRY_MATERIALS[key] = mat
    return mat


def mat_shell(color, alpha=0.05, tag=""):
    key = f"MAT_shell_{color}_{alpha:.3f}_{tag}"
    if key in _GEOMETRY_MATERIALS:
        return _GEOMETRY_MATERIALS[key]
    mat, nt, out = _material(key)
    bsdf = _principled(nt)
    c = hex_rgba(color)
    bsdf.inputs["Base Color"].default_value = _rgba_scaled(c, 0.85)
    bsdf.inputs["Roughness"].default_value = 0.28
    bsdf.inputs["IOR"].default_value = 1.42
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.22
    p = nt.nodes.new("ShaderNodeMath")
    p.operation = "POWER"
    p.inputs[1].default_value = 1.8
    _link(nt, lw.outputs["Facing"], p.inputs[0])
    a = nt.nodes.new("ShaderNodeMath")
    a.operation = "MULTIPLY_ADD"
    a.inputs[1].default_value = alpha * 2.4
    a.inputs[2].default_value = alpha * 0.45
    _link(nt, p.outputs[0], a.inputs[0])
    _link(nt, a.outputs[0], bsdf.inputs["Alpha"])
    e = nt.nodes.new("ShaderNodeMath")
    e.operation = "MULTIPLY"
    e.inputs[1].default_value = 0.22
    _link(nt, p.outputs[0], e.inputs[0])
    ec = nt.nodes.new("ShaderNodeMixRGB")
    ec.blend_type = "MULTIPLY"
    ec.inputs["Fac"].default_value = 1.0
    ec.inputs["Color1"].default_value = c
    _link(nt, e.outputs[0], ec.inputs["Color2"])
    _link(nt, ec.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    mat.surface_render_method = "BLENDED"
    mat.use_transparent_shadow = True
    mat.show_transparent_back = True
    _link(nt, bsdf.outputs["BSDF"], out.inputs["Surface"])
    _GEOMETRY_MATERIALS[key] = mat
    return mat


def mat_halo(color, radius):
    key = f"MAT_halo_{color}_{radius:.3f}"
    if key in _GEOMETRY_MATERIALS:
        return _GEOMETRY_MATERIALS[key]
    mat, nt, out = _material(key)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = "LENGTH"
    _link(nt, tc.outputs["Object"], vm.inputs[0])
    dv = nt.nodes.new("ShaderNodeMath")
    dv.operation = "DIVIDE"
    dv.inputs[1].default_value = max(radius, 1e-4)
    _link(nt, vm.outputs["Value"], dv.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
    _link(nt, dv.outputs[0], ramp.inputs["Fac"])
    # Soft transparent glow pad: alpha falls off with radius, no hard disc edge.
    fall = nt.nodes.new("ShaderNodeMath")
    fall.operation = "POWER"
    fall.inputs[1].default_value = 1.35
    _link(nt, ramp.outputs["Color"], fall.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex_rgba(color)
    em.inputs["Strength"].default_value = 2.4
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixs = nt.nodes.new("ShaderNodeMixShader")
    _link(nt, fall.outputs[0], mixs.inputs["Fac"])
    _link(nt, tr.outputs[0], mixs.inputs[1])
    _link(nt, em.outputs[0], mixs.inputs[2])
    _link(nt, mixs.outputs[0], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparent_shadow = True
    mat.show_transparent_back = True
    _GEOMETRY_MATERIALS[key] = mat
    return mat


def _font(path):
    if path in _FONTS:
        return _FONTS[path]
    font = None
    try:
        font = bpy.data.fonts.load(path, check_existing=True)
    except Exception as exc:  # pragma: no cover - font missing on other OS
        print(f"[specimens] font not found {path}: {exc}")
    _FONTS[path] = font
    return font


# ---------------------------------------------------------------------------
# low level geometry helpers
# ---------------------------------------------------------------------------

def _scene_coll():
    return bpy.context.scene.collection


def _new_collection(name, parent=None):
    """Create a collection and link it into the scene immediately, so every
    object created inside it is in the view layer (modifier_apply needs that).
    The final target collection is applied later by _finish_collection()."""
    coll = bpy.data.collections.new(name)
    (parent or _scene_coll()).children.link(coll)
    return coll


def _finish_collection(coll, target=None, link=True):
    if link:
        if target is not None and target != coll.users_scene and target != _scene_coll():
            for c in list(coll.users_scene):
                c.collection.children.unlink(coll)
            if coll.name not in target.children:
                target.children.link(coll)
    else:
        for sc in list(coll.users_scene):
            sc.collection.children.unlink(coll)


def _collect(obj, coll=None):
    coll = coll or _scene_coll()
    if obj.name not in coll.objects:
        coll.objects.link(obj)
    return obj


def _mesh_obj(name, verts, faces, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    obj = bpy.data.objects.new(name, me)
    _collect(obj, coll)
    return obj


def _apply_mod(obj, mod_name):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod_name)


def _remove_obj(obj):
    me = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    if me is not None and me.users == 0:
        try:
            bpy.data.meshes.remove(me)
        except Exception:
            pass


def _move_to(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def _convert_to_mesh(objs):
    """Curves / text objects -> mesh so they can be normalised with the rest."""
    out = []
    for o in objs:
        if o.type == "MESH":
            out.append(o)
            continue
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.convert(target="MESH")
        out.append(bpy.context.object)
    return out


def _triangulate(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def _smooth(obj, smooth=True):
    vals = [smooth] * len(obj.data.polygons)
    obj.data.polygons.foreach_set("use_smooth", vals)
    obj.data.update()


def _set_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def _obj_tris(obj):
    me = obj.data
    return sum(max(0, len(p.vertices) - 2) for p in me.polygons)


# --- bpy.ops primitives with baked transforms ------------------------------

def _bake_matrix(obj, matrix):
    obj.data.transform(matrix)
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    return obj


def _prim_sphere(loc, radius, segments=20, rings=12, scale=(1, 1, 1), rot=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                         radius=1.0, location=(0, 0, 0))
    obj = bpy.context.object
    mat = Matrix.LocRotScale(Vector(loc), rot or Euler((0, 0, 0)),
                             Vector((radius * scale[0], radius * scale[1],
                                     radius * scale[2])))
    return _bake_matrix(obj, mat)


def _prim_cone(loc, r1, r2, depth, rot=None, vertices=12):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2,
                                    depth=1.0, location=(0, 0, 0))
    obj = bpy.context.object
    mat = Matrix.LocRotScale(Vector(loc), rot or Euler((0, 0, 0)),
                             Vector((1.0, 1.0, depth)))
    return _bake_matrix(obj, mat)


def _prim_cube(loc, size, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.object
    mat = Matrix.LocRotScale(Vector(loc), rot or Euler((0, 0, 0)),
                             Vector(size))
    return _bake_matrix(obj, mat)


def _capsule(p1, p2, r1, r2, verts=10):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    length = max(d.length, 1e-5)
    quat = d.to_track_quat("Z", "Y")
    out = [_prim_cone((p1 + p2) * 0.5, r1, r2, length,
                      rot=quat.to_euler(), vertices=verts)]
    out.append(_prim_sphere(p1, r1, segments=verts, rings=max(6, verts // 2)))
    out.append(_prim_sphere(p2, r2, segments=verts, rings=max(6, verts // 2)))
    return out


def _join_meshes(name, objs, coll=None):
    """Merge objects (transforms must already be baked) into one new object."""
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    _collect(obj, coll)
    for o in objs:
        _remove_obj(o)
    return obj


def _lathe(name, profile, segments=20, cap_bottom=False, cap_top=False,
           axis="z"):
    """Revolve a 2D profile [(radius, along)] around an axis ('z' or 'x')."""
    verts = []
    rings = []
    for r, t in profile:
        if r < 1e-6:
            rings.append([len(verts)])
            if axis == "z":
                verts.append((0.0, 0.0, t))
            else:
                verts.append((t, 0.0, 0.0))
            continue
        ring = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ring.append(len(verts))
            cr, sr = r * math.cos(a), r * math.sin(a)
            if axis == "z":
                verts.append((cr, sr, t))
            else:
                verts.append((t, cr, sr))
        rings.append(ring)
    faces = []
    for ra, rb in zip(rings, rings[1:]):
        if len(ra) == 1 and len(rb) == 1:
            continue
        if len(ra) == 1:
            for i in range(segments):
                faces.append((ra[0], rb[i], rb[(i + 1) % segments]))
        elif len(rb) == 1:
            for i in range(segments):
                faces.append((ra[i], ra[(i + 1) % segments], rb[0]))
        else:
            for i in range(segments):
                j = (i + 1) % segments
                faces.append((ra[i], ra[j], rb[j], rb[i]))
    if cap_bottom and len(rings[0]) > 1:
        c = len(verts)
        t = profile[0][1]
        verts.append((0.0, 0.0, t) if axis == "z" else (t, 0.0, 0.0))
        for i in range(segments):
            faces.append((rings[0][(i + 1) % segments], rings[0][i], c))
    if cap_top and len(rings[-1]) > 1:
        c = len(verts)
        t = profile[-1][1]
        verts.append((0.0, 0.0, t) if axis == "z" else (t, 0.0, 0.0))
        for i in range(segments):
            faces.append((rings[-1][i], rings[-1][(i + 1) % segments], c))
    return _mesh_obj(name, verts, faces)


def _flat_poly(name, pts2d, matrix=None):
    """Single polygon from 2D points (x, y), optionally transformed."""
    verts = [(p[0], p[1], 0.0) for p in pts2d]
    faces = [tuple(range(len(verts)))]
    obj = _mesh_obj(name, verts, faces)
    if matrix is not None:
        obj.data.transform(matrix)
    return obj


def _ribbon_3d(name, pts3, width):
    """Curved ribbon lying on a surface: pts3 = [(x, y, z)] centre-line."""
    n = len(pts3)
    verts = []
    for i, p in enumerate(pts3):
        prev = Vector(pts3[max(0, i - 1)])
        nxt = Vector(pts3[min(n - 1, i + 1)])
        tang = (nxt - prev)
        tang.z = 0.0
        if tang.length < 1e-8:
            tang = Vector((1.0, 0.0, 0.0))
        tang.normalize()
        nrm = Vector((-tang.y, tang.x, 0.0))
        verts.append((p[0] - nrm.x * width * 0.5,
                      p[1] - nrm.y * width * 0.5, p[2]))
        verts.append((p[0] + nrm.x * width * 0.5,
                      p[1] + nrm.y * width * 0.5, p[2]))
    faces = []
    for i in range(n - 1):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    return _mesh_obj(name, verts, faces)


def _curve_wire(name, pts, radius, mat, coll=None, cyclic=False):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 1
    cu.resolution_u = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (float(p[0]), float(p[1]), float(p[2]), 1.0)
    sp.use_cyclic_u = bool(cyclic)
    obj = bpy.data.objects.new(name, cu)
    _collect(obj, coll)
    if mat is not None:
        obj.data.materials.append(mat)
    return obj


def _text_obj(name, body, size, font_path, extrude=0.0006, bevel=0.0001,
              align_x="LEFT", align_y="TOP", coll=None, resolution=3):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    font = _font(font_path)
    if font is not None:
        cu.font = font
    cu.size = size
    cu.align_x = align_x
    cu.align_y = align_y
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 1
    cu.resolution_u = resolution
    cu.space_line = 1.16
    obj = bpy.data.objects.new(name, cu)
    _collect(obj, coll)
    return obj


# --- modifiers / scan processing ------------------------------------------

def _remesh_decimate(obj, voxel, target_tris, smooth=True):
    rm = obj.modifiers.new("SCAN_remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = voxel
    rm.use_smooth_shade = smooth
    _apply_mod(obj, rm.name)
    if len(obj.data.polygons) == 0:
        return obj
    cur = _obj_tris(obj)
    if cur > target_tris:
        dc = obj.modifiers.new("SCAN_decimate", "DECIMATE")
        dc.decimate_type = "COLLAPSE"
        dc.ratio = max(0.01, min(1.0, target_tris / float(cur)))
        dc.use_collapse_triangulate = True
        _apply_mod(obj, dc.name)
    _triangulate(obj)
    return obj


def _bevel(obj, width=0.006, segments=2, angle=42.0):
    m = obj.modifiers.new("SCAN_bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    _apply_mod(obj, m.name)


def _bounds(objs):
    mins = [1e18, 1e18, 1e18]
    maxs = [-1e18, -1e18, -1e18]
    for o in objs:
        if o.type != "MESH":
            continue
        for v in o.data.vertices:
            co = v.co
            for k in range(3):
                mins[k] = min(mins[k], co[k])
                maxs[k] = max(maxs[k], co[k])
    return Vector(mins), Vector(maxs)


def _mesh_transform(me, matrix):
    """Transform a mesh, including any shape-key blocks (Basis included)."""
    if getattr(me, "shape_keys", None) is not None:
        me.transform(matrix, shape_keys=True)
    else:
        me.transform(matrix)


def _normalise_parts(objs, height, fit="height"):
    mins, maxs = _bounds(objs)
    dim = maxs - mins
    if fit == "max":
        ref = max(dim.x, dim.y, dim.z)
    elif fit == "width":
        ref = dim.x
    else:
        ref = dim.z
    s = height / ref if ref > 1e-9 else height
    scale_m = Matrix.Scale(s, 4)
    for o in objs:
        _mesh_transform(o.data, scale_m)
    mins, maxs = _bounds(objs)
    shift = Vector((-(mins.x + maxs.x) * 0.5, -(mins.y + maxs.y) * 0.5, -mins.z))
    trans = Matrix.Translation(shift)
    for o in objs:
        _mesh_transform(o.data, trans)
    return maxs - mins


def _sample_surface(obj, count, rng, point_size):
    me = obj.data
    me.calc_loop_triangles()
    tris = me.loop_triangles
    if not tris:
        return None
    areas = [t.area for t in tris]
    total = sum(areas)
    if total <= 1e-12:
        return None
    cum = []
    acc = 0.0
    for a in areas:
        acc += a
        cum.append(acc)
    verts = []
    faces = []
    base_tri = ((0.0, 0.5, 0.0), (-0.45, -0.4, 0.0), (0.45, -0.4, 0.0))
    for _ in range(count):
        t = tris[bisect.bisect_left(cum, rng.random() * total)]
        u, v = rng.random(), rng.random()
        if u + v > 1.0:
            u, v = 1.0 - u, 1.0 - v
        w = 1.0 - u - v
        i0, i1, i2 = t.vertices
        p = (me.vertices[i0].co * w + me.vertices[i1].co * u
             + me.vertices[i2].co * v)
        n = t.normal
        size = point_size * rng.uniform(0.62, 1.35)
        off = n * (size * 0.45)
        for _k in range(2):
            rot = Euler((rng.random() * math.pi * 2.0,
                         rng.random() * math.pi * 2.0,
                         rng.random() * math.pi * 2.0)).to_matrix()
            start = len(verts)
            for bx, by, bz in base_tri:
                pv = rot @ Vector((bx, by, bz)) * size + p + off
                verts.append((pv.x, pv.y, pv.z))
            faces.append((start, start + 1, start + 2))
    return verts, faces


# ---------------------------------------------------------------------------
# plinth / halo / label / mount
# ---------------------------------------------------------------------------

def _make_plinth(name, sx, sy, h, paper_mat, coll):
    sx, sy = max(sx, 0.35), max(sy, 0.35)
    taper = 0.955
    bx, by = sx * taper * 0.5, sy * taper * 0.5
    tx, ty = sx * 0.5, sy * 0.5
    verts = [(-bx, -by, 0), (bx, -by, 0), (bx, by, 0), (-bx, by, 0),
             (-tx, -ty, h), (tx, -ty, h), (tx, ty, h), (-tx, ty, h)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
             (2, 6, 7, 3), (3, 7, 4, 0)]
    body = _mesh_obj(name, verts, faces, coll)
    _bevel(body, width=0.006, segments=2)
    _set_material(body, paper_mat)
    # top board (slightly overhanging) + shadow gap
    top_h = min(0.018, h * 0.09)
    cap = _prim_cube((0.0, 0.0, h - top_h * 0.5),
                     (sx * 1.012, sy * 1.012, top_h))
    cap.name = name + "_cap"
    _move_to(cap, coll)
    _bevel(cap, width=0.0035, segments=2)
    _set_material(cap, paper_mat)
    gap = _prim_cube((0.0, 0.0, h - top_h * 2.2),
                     (sx * 0.955, sy * 0.955, top_h * 0.9))
    gap.name = name + "_gap"
    _move_to(gap, coll)
    _set_material(gap, mat_ink(f"plinth_gap_{name}", "#141a20"))
    return [body, cap, gap]


def _make_halo(name, radius, z, color, coll):
    n = 48
    verts = [(0.0, 0.0, 0.0)]
    for i in range(n):
        a = 2.0 * math.pi * i / n
        verts.append((radius * math.cos(a), radius * math.sin(a), 0.0))
    faces = [(0, i, (i % n) + 1) for i in range(1, n + 1)]
    obj = _mesh_obj(name, verts, faces, coll)
    obj.location = (0.0, 0.0, z)
    _set_material(obj, mat_halo(color, radius))
    obj.visible_shadow = False
    return obj


def _make_label(name, loc, rot_x, lines, coll):
    mat_plate = mat_paper("label_plate", PALETTE["paper"], roughness=0.9,
                          edge_glow=0.22, emission=0.006, noise_scale=90.0)
    mat_ink_dark = mat_ink("label_ink", "#23272f")
    name_size = 0.050
    data_size = 0.0215
    t_name = _text_obj(name + "_name", lines[0], name_size, FONT_GEORGIA,
                       extrude=0.0, bevel=0.0, align_x="CENTER",
                       align_y="TOP", coll=coll, resolution=2)
    data_objs = []
    for i, txt in enumerate(lines[1:]):
        data_objs.append(_text_obj(f"{name}_data{i}", txt, data_size,
                                   FONT_CONSOLAS, extrude=0.0, bevel=0.0,
                                   align_x="LEFT", align_y="TOP", coll=coll,
                                   resolution=1))
    bpy.context.view_layer.update()
    name_w, name_h = t_name.dimensions.x, t_name.dimensions.y
    data_ws = [o.dimensions.x for o in data_objs]
    data_hs = [o.dimensions.y for o in data_objs]
    plate_w = max([0.30, name_w + 0.10] + [w + 0.085 for w in data_ws])
    plate_h = name_h + sum(data_hs) + 0.112
    plate_t = 0.006
    cm = bpy.data.objects.new(name + "_frame", None)
    cm.empty_display_type = "PLAIN_AXES"
    cm.empty_display_size = 0.1
    _collect(cm, coll)
    plate = _prim_cube((0.0, 0.0, 0.0), (plate_w, plate_t, plate_h))
    plate.name = name + "_plate"
    _move_to(plate, coll)
    _bevel(plate, width=0.0025, segments=2)
    _set_material(plate, mat_plate)
    rule = _prim_cube((0.0, plate_t * 0.5 + 0.0006,
                       plate_h * 0.5 - name_h - 0.046),
                      (plate_w * 0.62, 0.0014, 0.0026))
    rule.name = name + "_rule"
    _move_to(rule, coll)
    _set_material(rule, mat_ink_dark)
    bar = _prim_cube((0.0, plate_t * 0.5 + 0.0008, -plate_h * 0.5 + 0.020),
                     (plate_w * 0.28, 0.0010, 0.0022))
    bar.name = name + "_bar"
    _move_to(bar, coll)
    _set_material(bar, mat_emission(PALETTE["scan"], 2.2, "label_bar"))
    for o in [t_name] + data_objs:
        _set_material(o, mat_ink_dark)
    for o in [plate, rule, bar, t_name] + data_objs:
        o.parent = cm
        o.matrix_parent_inverse = Matrix.Identity(4)
    cm.location = Vector(loc)
    cm.rotation_euler = Euler((rot_x, 0.0, 0.0))
    t_name.location = (0.0, plate_t * 0.5 + 0.0014, plate_h * 0.5 - 0.030)
    t_name.rotation_euler = (math.pi * 0.5, 0.0, math.pi)
    z = plate_h * 0.5 - name_h - 0.062
    for o, dh in zip(data_objs, data_hs):
        o.location = (max(data_ws) * 0.5,
                      plate_t * 0.5 + 0.0010, z)
        o.rotation_euler = (math.pi * 0.5, 0.0, math.pi)
        z -= dh + 0.006
    # suspension filaments up out of frame
    mat_wire = mat_metal("label_wire")
    hw = plate_w * 0.5 - 0.035
    for side in (-1.0, 1.0):
        pts = [(side * hw, 0.004, plate_h * 0.5),
               (side * hw, 0.010, plate_h * 0.5 + 0.35),
               (side * (hw - 0.02), 0.018, plate_h * 0.5 + 0.92)]
        w = _curve_wire(name + f"_wire{int(side)}", pts, 0.0013, mat_wire)
        _move_to(w, coll)
        w.parent = cm
        w.matrix_parent_inverse = Matrix.Identity(4)
    return cm


def _make_wedge(name, bbox, loc, coll):
    """Paper wedge mount for a leaning slab specimen."""
    bw = Vector(bbox)
    half_x = bw.x * 0.30
    y_back = bw.y * 0.42
    y_front = -bw.y * 0.03
    h = bw.z * 0.50
    verts = [(-half_x, y_front, 0.0), (half_x, y_front, 0.0),
             (half_x, y_back, 0.0), (-half_x, y_back, 0.0),
             (-half_x, y_back, h), (half_x, y_back, h)]
    faces = [(0, 1, 2, 3), (0, 4, 5, 1), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2)]
    obj = _mesh_obj(name, verts, faces, coll)
    _bevel(obj, width=0.004, segments=1)
    _set_material(obj, mat_paper("wedge", "#e2dccd", edge_glow=0.25,
                                 emission=0.015))
    obj.location = Vector(loc)
    return obj


# ---------------------------------------------------------------------------
# assembly core
# ---------------------------------------------------------------------------

def _merge_style(name, style, kw):
    s = dict(DEFAULT_STYLE)
    s.update(SPECIMEN_STYLES.get(name, {}))
    if isinstance(style, dict):
        s.update(style)
    if kw:
        s.update(kw)
    return s


def _root_empty(name):
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.25
    return root


def _apply_root_transform(root, location, rotation, scale):
    if location is not None:
        root.location = Vector(location)
    if rotation is not None:
        root.rotation_euler = Euler(rotation, "XYZ")
    if scale is not None:
        if isinstance(scale, (int, float)):
            root.scale = (float(scale),) * 3
        else:
            root.scale = Vector(scale)
    bpy.context.view_layer.update()


def _parent_all(objs, root):
    for o in objs:
        if o is None:
            continue
        o.parent = root
        o.matrix_parent_inverse = Matrix.Identity(4)


def _random_for(name, seed):
    return random.Random((zlib.crc32(name.encode("utf-8"))
                          ^ (int(seed) * 7919)) & 0xFFFFFFFF)


def _scan_part_layers(part_obj, name, color, style, points_count, seed,
                      is_main=True):
    """Build the three hologram layers for one part.

    Consumes (deletes) the source mesh object; returns (objects, base_tris).
    """
    objs = []
    base_tris = _obj_tris(part_obj)
    # 1. sparse point cloud first (samples the unmodified base surface)
    if style["points"] and points_count > 0:
        rng = _random_for(name + "_points", seed)
        sample = _sample_surface(part_obj, points_count, rng,
                                 style["point_size"] * (1.0 if is_main else 0.72))
        if sample is not None:
            verts, faces = sample
            point_obj = _mesh_obj(name + "_points", verts, faces)
            _set_material(point_obj, mat_emission(color, style["point_strength"],
                                                  "points"))
            point_obj.visible_shadow = False
            objs.append(point_obj)
    # 2. wireframe copy
    if style["wire"]:
        me = part_obj.data.copy()
        wire_obj = bpy.data.objects.new(name + "_wire", me)
        _collect(wire_obj)
        if len(wire_obj.data.polygons) > 0 and style["wire_ratio"] < 0.995:
            dc = wire_obj.modifiers.new("SCAN_predecimate", "DECIMATE")
            dc.decimate_type = "COLLAPSE"
            dc.ratio = style["wire_ratio"]
            dc.use_collapse_triangulate = True
            _apply_mod(wire_obj, dc.name)
        thick = style["wire_thickness"] * (1.0 if is_main else 0.82)
        _set_material(wire_obj, mat_emission(color, style["wire_strength"],
                                             "wire"))
        wm = wire_obj.modifiers.new(WIRE_MOD, "WIREFRAME")
        wm.thickness = thick
        wm.use_replace = True
        wm.use_even_offset = True
        wm.use_relative_offset = False
        wm.use_boundary = True
        wm.use_crease = False
        wire_obj.visible_shadow = False
        objs.append(wire_obj)
    # 3. translucent shell (reuse the base object)
    if style["shell"]:
        _set_material(part_obj, mat_shell(color, style["shell_alpha"], "shell"))
        _smooth(part_obj)
        part_obj.visible_shadow = False
        part_obj.name = name + "_shell"
        objs.append(part_obj)
    else:
        _remove_obj(part_obj)
    return objs, base_tris


def _assemble_scan(name, parts, style, location=None, rotation=None,
                   scale=None, collection=None, link=True):
    """parts: list of (mesh_object, color, points_weight, is_main)."""
    style = dict(style)
    seed = style["seed"]
    scan_objs = [p[0] for p in parts]
    dim = _normalise_parts(scan_objs, style["height"], style["fit"])
    if style["triangulate"]:
        for o in scan_objs:
            _triangulate(o)
    weights = [max(0.0, p[2]) for p in parts]
    total_w = sum(weights) or 1.0
    budget = int(style["point_count"]) if style["points"] else 0
    coll = _new_collection(f"SPEC_{name}")
    root = _root_empty(f"SPEC_{name}")
    content = []
    base_tris = 0
    for idx, (obj, color, w, is_main) in enumerate(parts):
        pts = 0
        if budget > 0:
            if idx == len(parts) - 1:
                pts = budget - sum(int(round(budget * x / total_w))
                                   for x in weights[:-1])
            else:
                pts = int(round(budget * w / total_w))
        layers, tris = _scan_part_layers(obj, f"{name}_{idx}", color, style,
                                         pts, seed, is_main=is_main)
        base_tris += tris
        content.extend(layers)
    ph = style["plinth_h"]
    gap = style["plinth_gap"]
    z0 = (ph + gap) if style["plinth"] else 0.0
    for o in content:
        _mesh_transform(o.data, Matrix.Translation((0.0, 0.0, z0)))
    props = []
    if style["plinth"]:
        paper = mat_paper("plinth", "#d9d2c2", roughness=0.92, edge_glow=0.26,
                          emission=0.010, noise_scale=40.0)
        props += _make_plinth(f"{name}_plinth", dim.x + 0.34, dim.y + 0.34,
                              ph, paper, coll)
        if style["halo"]:
            radius = min(dim.x, dim.y) * 0.42 + 0.055
            props.append(_make_halo(f"{name}_halo", radius, ph + 0.0015,
                                    style["scan_color"], coll))
    if style["mount"] == "wedge":
        props.append(_make_wedge(f"{name}_wedge", dim,
                                 (0.0, z0 - gap, 0.0), coll))
    if style["label"] and style["label_lines"]:
        label_x = dim.x * 0.5 + 0.30
        if style["label_side"] == "left":
            label_x = -label_x
        label_z = z0 + dim.z * 0.44
        label_y = -dim.y * 0.10
        props.append(_make_label(f"{name}_label",
                                 (label_x, label_y, label_z),
                                 math.radians(10.0), style["label_lines"],
                                 coll))
    coll.objects.link(root)
    all_objs = content + props
    for o in all_objs:
        _move_to(o, coll)
    _parent_all(all_objs, root)
    _finish_collection(coll, collection, link)
    _apply_root_transform(root, location, rotation, scale)
    coll["specimen"] = name
    coll["kind"] = "specimen"
    coll["root"] = root.name
    coll["height"] = float(style["height"])
    coll["size"] = list(round(v, 4) for v in dim)
    coll["tris_base"] = int(base_tris)
    coll["points"] = int(budget)
    coll["scan_color"] = style["scan_color"]
    coll["style_json"] = json.dumps(
        {k: v for k, v in style.items()
         if isinstance(v, (str, int, float, bool, type(None)))},
        ensure_ascii=False)
    stats = measure(coll)
    coll["tris_wire"] = int(stats.get("wire", 0))
    coll["tris_total"] = int(stats.get("total", 0))
    root["specimen"] = name
    return coll


def _assemble_prop(name, objs, style, location=None, rotation=None, scale=None,
                   collection=None, link=True):
    objs = _convert_to_mesh(objs)
    _normalise_parts(objs, style["height"], style["fit"])
    dim = _bounds(objs)
    coll = _new_collection(f"PROP_{name}")
    root = _root_empty(f"PROP_{name}")
    for o in objs:
        _move_to(o, coll)
    coll.objects.link(root)
    _parent_all(objs, root)
    _finish_collection(coll, collection, link)
    _apply_root_transform(root, location, rotation, scale)
    coll["specimen"] = name
    coll["kind"] = "prop"
    coll["root"] = root.name
    coll["size"] = list(round(v, 4) for v in (dim[1] - dim[0]))
    coll["tris_base"] = sum(_obj_tris(o) for o in objs)
    coll["points"] = 0
    return coll


# ---------------------------------------------------------------------------
# public helpers
# ---------------------------------------------------------------------------

def root_of(coll):
    """Root Empty of a built collection (accepts Collection or Object)."""
    if isinstance(coll, bpy.types.Object):
        return coll
    rn = coll.get("root")
    root = bpy.data.objects.get(rn) if rn else None
    if root is None:
        for o in coll.objects:
            if o.type == "EMPTY":
                return o
    return root


def measure(coll):
    """Evaluated triangle counts of a built collection."""
    bpy.context.view_layer.update()
    try:
        dg = bpy.context.evaluated_depsgraph_get()
    except Exception:
        return {"base": 0, "wire": 0, "points": 0, "other": 0, "total": 0,
                "objects": 0}
    out = {"base": 0, "wire": 0, "points": 0, "other": 0, "total": 0,
           "objects": 0}
    for o in coll.all_objects:
        if o.type not in ("MESH", "FONT", "CURVE"):
            continue
        out["objects"] += 1
        tris = 0
        try:
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            tris = sum(max(0, len(p.vertices) - 2) for p in me.polygons)
            ev.to_mesh_clear()
        except Exception:
            if o.type == "MESH":
                tris = _obj_tris(o)
        nm = o.name
        if "_wire" in nm:
            out["wire"] += tris
        elif "_points" in nm:
            out["points"] += tris
        elif ("_shell" in nm or "_label" in nm or "_name" in nm
              or "_data" in nm):
            out["base"] += tris
        else:
            out["other"] += tris
        out["total"] += tris
    return out


def set_scan_params(coll, wire_thickness=None, wire_strength=None,
                    point_size=None, shell_alpha=None):
    """Retune the hologram layers after the fact (e.g. far shots need thicker
    wire + stronger points).  Safe to call with any subset of arguments."""
    for o in coll.all_objects:
        if o.type != "MESH":
            continue
        if "_wire" in o.name:
            for m in o.modifiers:
                if m.type == "WIREFRAME" and wire_thickness is not None:
                    m.thickness = wire_thickness
            if wire_strength is not None:
                for slot in o.material_slots:
                    mat = slot.material
                    if mat and mat.name.startswith("MAT_emit"):
                        for n in mat.node_tree.nodes:
                            if n.bl_idname == "ShaderNodeEmission":
                                n.inputs["Strength"].default_value = wire_strength
        elif "_points" in o.name and point_size is not None:
            me = o.data
            for poly in me.polygons:
                c = Vector((0.0, 0.0, 0.0))
                for vi in poly.vertices:
                    c += me.vertices[vi].co
                c /= len(poly.vertices)
                for vi in poly.vertices:
                    v = me.vertices[vi]
                    v.co = c + (v.co - c) * (point_size / 0.0032)
            me.update()
        elif "_shell" in o.name and shell_alpha is not None:
            for slot in o.material_slots:
                mat = slot.material
                if mat and mat.name.startswith("MAT_shell"):
                    for n in mat.node_tree.nodes:
                        if n.bl_idname == "ShaderNodeMath" and \
                                n.operation == "MULTIPLY_ADD":
                            n.inputs[1].default_value = shell_alpha * 2.4
                            n.inputs[2].default_value = shell_alpha * 0.45


def animate_flutter(obj, amp=0.055, speed=0.55, phase=0.0, yaw=7.0,
                    pitch=4.0, roll=3.5, tail=1.0, cycles=3, frame_start=1,
                    frame_end=None, fps=None, key_step=3):
    """Float + tail-wave animation for koinobori kites (and paper sheets).

    `obj` may be the Collection returned by build_koinobori or its root Empty.
    Writes keyframes for root location / rotation and for the body shape keys
    SWAY_A / SWAY_B.  All values derive from `phase`, so deterministic.

    Returns dict with animated object names and the frame range.
    """
    coll = obj if isinstance(obj, bpy.types.Collection) else None
    root = obj if isinstance(obj, bpy.types.Object) else root_of(obj)
    if root is None:
        raise ValueError("animate_flutter: no root object found")
    scene = bpy.context.scene
    fps = fps or scene.render.fps or 60
    period = 1.0 / max(speed, 1e-3)
    if frame_end is None:
        frame_end = frame_start + max(8, int(round(period * fps * cycles)))
    base_loc = root.location.copy()
    base_rot = root.rotation_euler.copy()
    lam = 1.0
    if coll is not None and "size" in coll and coll["size"]:
        lam = max(float(coll["size"][0]), 0.3)
    body = None
    if coll is not None:
        for o in coll.all_objects:
            if o.type == "MESH" and o.data.shape_keys:
                keys = o.data.shape_keys.key_blocks
                if "SWAY_A" in keys and "SWAY_B" in keys:
                    body = o
                    break
    frames = list(range(frame_start, frame_end + 1, max(1, key_step)))
    if frames[-1] != frame_end:
        frames.append(frame_end)
    for f in frames:
        t = (f - frame_start) / float(fps)
        ph = 2.0 * math.pi * t / period + phase
        root.location = base_loc + Vector(
            (math.sin(ph) * amp * lam * 0.35,
             math.sin(ph + 0.9) * amp * lam * 0.20,
             math.sin(ph) * amp * lam))
        root.rotation_euler = Euler((
            base_rot.x + math.radians(pitch) * math.sin(ph + 1.1),
            base_rot.y + math.radians(roll) * math.sin(ph + 0.4),
            base_rot.z + math.radians(yaw) * math.sin(ph * 0.5 + phase * 0.3),
        ))
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("rotation_euler", frame=f)
        if body is not None:
            keys = body.data.shape_keys.key_blocks
            s = math.sin(ph * 1.6)
            keys["SWAY_A"].value = max(0.0, s) * 0.10 * tail
            keys["SWAY_B"].value = max(0.0, -s) * 0.10 * tail
            keys["SWAY_A"].keyframe_insert("value", frame=f)
            keys["SWAY_B"].keyframe_insert("value", frame=f)
    return {"root": root.name,
            "body": body.name if body else None,
            "frames": [frame_start, frame_end],
            "period": period}


def animate_scan(coll, period=4.0, frame_start=1, frame_end=None, fps=None,
                 color=None, radius_scale=1.02, z0=None):
    """Travelling scan ring: a thin emissive ring sweeps up and down a specimen.

    The ring travels from the base of the *scan* (above the plinth gap) up to
    the top of the scan.  `z0` overrides that base height.

    Returns the ring object (parented to the specimen root, emissive).
    """
    root = root_of(coll)
    h = float(coll.get("height", 1.0))
    size = list(coll.get("size", (1.0, 1.0, 1.0)))
    color = color or str(coll.get("scan_color", PALETTE["scan"]))
    # encircle the widest part of the scan, but never shrink below a humanoid ring
    r = max(0.30 * h, 0.52 * max(float(size[0]), float(size[1]))) * radius_scale
    if z0 is None:
        try:
            _st = json.loads(str(coll.get("style_json", "{}")))
        except Exception:
            _st = {}
        z0 = (float(_st.get("plinth_h", 0.40)) + float(_st.get("plinth_gap", 0.10))) \
            if _st.get("plinth", True) else 0.0
    z0 = float(z0)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, radius=r, segments=48)
    me = bpy.data.meshes.new("scan_ring_" + coll.name)
    bm.to_mesh(me)
    bm.free()
    ring = bpy.data.objects.new("scan_ring_" + coll.name, me)
    _collect(ring, coll)
    _set_material(ring, mat_emission(color, 2.2, "scan_ring"))
    wm = ring.modifiers.new(WIRE_MOD, "WIREFRAME")
    wm.thickness = 0.006
    wm.use_replace = True
    ring.visible_shadow = False
    ring.parent = root
    ring.matrix_parent_inverse = Matrix.Identity(4)
    fps = fps or bpy.context.scene.render.fps or 60
    if frame_end is None:
        frame_end = frame_start + int(round(period * fps))
    for f in range(frame_start, frame_end + 1, 2):
        t = (f - frame_start) / float(fps)
        u = (t / period) % 1.0
        tri = 1.0 - abs(2.0 * u - 1.0)
        ring.location = (0.0, 0.0, z0 + tri * h)
        ring.keyframe_insert("location", frame=f)
    return ring


# ---------------------------------------------------------------------------
# specimen builders
# ---------------------------------------------------------------------------

def build_table(location=None, rotation=None, scale=None, style=None,
                collection=None, link=True, **kw):
    """Wooden table specimen (s06).  One cool-cyan scan part.

    Signature: build_table(location=None, rotation=None, scale=None,
                           style=None, collection=None, link=True, **style)
    Returns: bpy.types.Collection (root Empty "SPEC_table", base z=0).
    """
    st = _merge_style("table", style, kw)
    rng = _random_for("table", st["seed"])
    tw, td, tt = 1.41, 0.83, 0.060
    leg = 0.072
    top_z = 1.0 - tt * 0.5
    objs = []
    objs.append(_prim_cube((0.0, 0.0, top_z), (tw, td, tt)))
    for sy in (-1.0, 1.0):
        objs.append(_prim_cube(
            (0.0, sy * (td * 0.5 - 0.06), 0.79), (tw * 0.86, 0.035, 0.10)))
    for sx in (-1.0, 1.0):
        objs.append(_prim_cube(
            (sx * (tw * 0.5 - 0.12), 0.0, 0.79), (0.035, td * 0.72, 0.10)))
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            objs.append(_prim_cone(
                (sx * (tw * 0.5 - 0.13), sy * (td * 0.5 - 0.11), 0.42),
                leg * 0.84, leg, 0.84, vertices=4,
                rot=Euler((0.0, 0.0, math.radians(45.0)))))
    table = _join_meshes("table_scan", objs)
    _bevel(table, width=0.0055, segments=1)
    _triangulate(table)
    for v in table.data.vertices:
        v.co += Vector((rng.uniform(-0.0009, 0.0009),
                        rng.uniform(-0.0009, 0.0009),
                        rng.uniform(-0.0009, 0.0009)))
    table.data.update()
    parts = [(table, st["scan_color"], 1.0, True)]
    return _assemble_scan("table", parts, st, location, rotation, scale,
                          collection, link)


def build_eggplant(location=None, rotation=None, scale=None, style=None,
                   collection=None, link=True, **kw):
    """Aubergine specimen (s07): teardrop body, six-point star calyx, stem.

    Signature: build_eggplant(location=None, rotation=None, scale=None,
                              style=None, collection=None, link=True, **style)
    """
    st = _merge_style("eggplant", style, kw)
    body_profile = [
        (0.000, 0.000), (0.130, 0.008), (0.225, 0.048), (0.276, 0.135),
        (0.292, 0.300), (0.277, 0.465), (0.238, 0.620), (0.186, 0.760),
        (0.128, 0.870), (0.076, 0.942), (0.000, 0.975),
    ]
    body = _lathe("eggplant_body", body_profile, segments=22)
    _remesh_decimate(body, voxel=0.017, target_tris=270)
    calyx = []
    for i in range(6):
        a = math.radians(60.0 * i + 12.0)
        leaf = [(0.0, 0.0), (0.045, 0.014), (0.170, 0.034),
                (0.235, 0.007), (0.155, -0.020), (0.050, -0.031)]
        m = (Matrix.Translation((0.0, 0.0, 0.905))
             @ Matrix.Rotation(a, 4, "Z")
             @ Matrix.Rotation(math.radians(-32.0), 4, "Y"))
        calyx.append(_flat_poly(f"calyx{i}", leaf, m))
    stem = _lathe("eggplant_stem",
                  [(0.026, 0.0), (0.021, 0.052), (0.030, 0.108)],
                  segments=8, cap_top=True)
    stem.data.transform(Matrix.Translation((0.004, 0.0, 0.918))
                        @ Matrix.Rotation(math.radians(14.0), 4, "Y"))
    calyx_scan = _join_meshes("eggplant_calyx", calyx + [stem])
    _triangulate(calyx_scan)
    parts = [(body, st["scan_color"], 0.86, True),
             (calyx_scan, "#a9d8c2", 0.14, False)]
    return _assemble_scan("eggplant", parts, st, location, rotation, scale,
                          collection, link)


def _cat_parts():
    """Sitting cat, built at real-ish proportions (~0.55 m tall)."""
    objs = []
    objs.append(_prim_sphere((0.0, 0.030, 0.150), 0.135, 18, 12,
                             scale=(0.95, 1.02, 1.05)))
    objs.append(_prim_sphere((0.0, -0.010, 0.300), 0.105, 18, 12,
                             scale=(1.0, 1.05, 1.45),
                             rot=Euler((math.radians(-8.0), 0, 0))))
    objs.append(_prim_sphere((0.0, -0.035, 0.355), 0.088, 16, 10,
                             scale=(1.05, 0.95, 1.10)))
    objs.append(_prim_sphere((0.0, -0.045, 0.425), 0.086, 20, 14,
                             scale=(1.0, 0.95, 0.94)))
    objs.append(_prim_sphere((0.0, -0.118, 0.404), 0.036, 14, 10,
                             scale=(1.25, 0.85, 0.72)))
    for sx in (-1.0, 1.0):
        objs.append(_prim_cone((sx * 0.050, -0.040, 0.500), 0.040, 0.004, 0.095,
                               vertices=4,
                               rot=Euler((math.radians(-6.0), 0.0,
                                          math.radians(sx * -14.0)))))
    for sx in (-1.0, 1.0):
        objs += _capsule((sx * 0.048, -0.080, 0.300),
                         (sx * 0.048, -0.092, 0.030), 0.037, 0.029, verts=10)
        objs.append(_prim_sphere((sx * 0.048, -0.106, 0.022), 0.030, 12, 8,
                                 scale=(1.0, 1.35, 0.62)))
    for sx in (-1.0, 1.0):
        objs.append(_prim_sphere((sx * 0.085, -0.058, 0.024), 0.036, 12, 8,
                                 scale=(0.9, 1.5, 0.6)))
    tail_pts = []
    for i in range(9):
        u = i / 8.0
        a = math.radians(200.0 * u + 15.0)
        rr = 0.185 * (1.0 - 0.18 * u)
        tail_pts.append((rr * math.sin(a), 0.06 + rr * math.cos(a) * 0.75,
                         0.040 + 0.030 * u))
    for a, b in zip(tail_pts, tail_pts[1:]):
        objs += _capsule(a, b, 0.024, 0.017, verts=8)
    objs.append(_prim_sphere((0.0, -0.030, 0.372), 0.070, 14, 10,
                             scale=(1.15, 1.05, 0.75)))
    return objs


def build_cat(location=None, rotation=None, scale=None, style=None,
              collection=None, link=True, **kw):
    """Sitting cat scan (s09): wireframe cat, purr: 0.

    Signature: build_cat(location=None, rotation=None, scale=None,
                         style=None, collection=None, link=True, **style)
    """
    st = _merge_style("cat", style, kw)
    cat = _join_meshes("cat_scan", _cat_parts())
    _remesh_decimate(cat, voxel=0.0095, target_tris=400)
    parts = [(cat, st["scan_color"], 1.0, True)]
    return _assemble_scan("cat", parts, st, location, rotation, scale,
                          collection, link)


def _steak_parts():
    """Sirloin slab (s10): rounded-rect slab, cream fat cap along the lower
    edge of the top face, four char grill ridges.  Built face-up in XY (+Z)."""
    SX, SY, TH = 0.50, 0.34, 0.085
    N = 34
    n_exp = 3.2

    def prof(a, sx=SX, sy=SY):
        c, s = math.cos(a), math.sin(a)
        x = sx * math.copysign(abs(c) ** (2.0 / n_exp), c)
        y = sy * math.copysign(abs(s) ** (2.0 / n_exp), s)
        k = 1.0 + 0.028 * math.sin(5.0 * a + 0.7)
        return x * k, y * k

    verts, faces = [], []
    for i in range(N):
        x, y = prof(2.0 * math.pi * i / N)
        verts.append((x, y, -TH))
    for i in range(N):
        x, y = prof(2.0 * math.pi * i / N)
        verts.append((x * 0.995, y * 0.995, TH))
    for i in range(N):
        j = (i + 1) % N
        faces.append((i, j, N + j, N + i))
    faces.append(tuple(range(N - 1, -1, -1)))
    faces.append(tuple(range(N, 2 * N)))
    body = _mesh_obj("steak_body", verts, faces)
    _triangulate(body)
    _bevel(body, width=0.014, segments=2)
    _remesh_decimate(body, voxel=0.010, target_tris=340)

    # cream fat cap: a band of the top face along its lower (-Y) edge
    outer, inner = [], []
    for i in range(N):
        x, y = prof(2.0 * math.pi * i / N)
        if y < -0.155:
            outer.append((x * 0.988, y * 0.988, TH + 0.0016))
            inner.append((x * 0.795, y * 0.795, TH + 0.0016))
    fat_verts = outer + inner
    fat_faces = [(i, i + 1, len(outer) + i + 1, len(outer) + i)
                 for i in range(len(outer) - 1)]
    fat = _mesh_obj("steak_fat", fat_verts, fat_faces)

    # char grill ridges lying on the top face
    marks = []
    for k in range(4):
        xc = -0.285 + 0.188 * k
        t = min(1.0, abs(xc) / SX)
        ymax = SY * (1.0 - t ** n_exp) ** (1.0 / n_exp) - 0.030
        if ymax < 0.06:
            continue
        mv, mf = [], []
        steps = 6
        for s in range(steps + 1):
            yy = -ymax + 2.0 * ymax * s / steps
            mv.append((xc - 0.020, yy, TH + 0.0022))
            mv.append((xc + 0.020, yy, TH + 0.0022))
        for s in range(steps):
            mf.append((2 * s, 2 * s + 1, 2 * s + 3, 2 * s + 2))
        marks.append(_mesh_obj(f"steak_char{k}", mv, mf))
    char = _join_meshes("steak_char", marks)
    _triangulate(fat)
    _triangulate(char)
    return body, fat, char


def build_steak(location=None, rotation=None, scale=None, style=None,
                collection=None, link=True, **kw):
    """Mounted steak specimen (s10): slab leaning back, cream fat on front rim.

    Signature: build_steak(location=None, rotation=None, scale=None,
                           style=None, collection=None, link=True, **style)
    """
    st = _merge_style("steak", style, kw)
    body, fat, char = _steak_parts()
    tilt = Matrix.Rotation(math.radians(60.0), 4, "X")
    for o in (body, fat, char):
        o.data.transform(tilt)
    _triangulate(body)
    parts = [(body, st["scan_color"], 0.78, True),
             (fat, "#ffe6b8", 0.14, False),
             (char, "#6b3a24", 0.08, False)]
    return _assemble_scan("steak", parts, st, location, rotation, scale,
                          collection, link)


def _petal(name, centre, azimuth, tilt_deg, length, width):
    """Petal polygon, radiating outwards and tilted up by tilt_deg."""
    pts = [(0.0, -width * 0.35), (length * 0.28, -width * 0.5),
           (length * 0.72, -width * 0.34), (length, 0.0),
           (length * 0.66, width * 0.36), (length * 0.24, width * 0.5),
           (0.0, width * 0.32)]
    m = (Matrix.Translation(centre)
         @ Matrix.Rotation(azimuth, 4, "Z")
         @ Matrix.Rotation(math.radians(-tilt_deg), 4, "Y"))
    return _flat_poly(name, pts, m)


def build_flower(location=None, rotation=None, scale=None, style=None,
                 collection=None, link=True, **kw):
    """Warm flower specimen (s11): slim stem, two leaves, two petal rings.

    Signature: build_flower(location=None, rotation=None, scale=None,
                            style=None, collection=None, link=True, **style)
    """
    st = _merge_style("flower", style, kw)
    stem_pts = []
    for i in range(8):
        u = i / 7.0
        stem_pts.append((0.020 * math.sin(u * 2.6) + 0.010 * u,
                         0.008 * math.sin(u * 3.4), u * 0.505))
    stem_objs = []
    radii = [0.021 * (1.0 - 0.34 * (i / 7.0)) for i in range(8)]
    for i in range(7):
        stem_objs += _capsule(stem_pts[i], stem_pts[i + 1],
                              radii[i], radii[i + 1], verts=8)
    stem = _join_meshes("flower_stem", stem_objs)
    _remesh_decimate(stem, voxel=0.010, target_tris=170)
    leaves = []
    for i, (z, az, ln) in enumerate([(0.185, 1.9, 0.30), (0.300, -2.2, 0.26)]):
        leaf = [(0.0, 0.0), (ln * 0.30, ln * 0.16), (ln * 0.72, ln * 0.15),
                (ln, 0.0), (ln * 0.62, -ln * 0.10), (ln * 0.22, -ln * 0.12)]
        m = (Matrix.Translation((0.0, 0.0, z))
             @ Matrix.Rotation(az, 4, "Z")
             @ Matrix.Rotation(math.radians(38.0), 4, "Y"))
        leaves.append(_flat_poly(f"leaf{i}", leaf, m))
    leaf_obj = _join_meshes("flower_leaves", leaves)
    _triangulate(leaf_obj)
    centre = _prim_sphere((0.022, 0.008, 0.527), 0.058, 18, 12,
                          scale=(1.0, 1.0, 0.62))
    _remesh_decimate(centre, voxel=0.010, target_tris=90)
    petals = []
    for i in range(9):
        az = math.radians(40.0 * i)
        petals.append(_petal(f"petal_o{i}", (0.022, 0.008, 0.537), az,
                             24.0, 0.198, 0.078))
    for i in range(6):
        az = math.radians(60.0 * i + 26.0)
        petals.append(_petal(f"petal_i{i}", (0.022, 0.008, 0.562), az,
                             54.0, 0.118, 0.056))
    petal_obj = _join_meshes("flower_petals", petals)
    _triangulate(petal_obj)
    parts = [(stem, "#a7c48b", 0.20, True),
             (leaf_obj, "#a7c48b", 0.12, False),
             (centre, "#ffd28a", 0.16, False),
             (petal_obj, st["scan_color"], 0.52, False)]
    return _assemble_scan("flower", parts, st, location, rotation, scale,
                          collection, link)


def _human_joints(pose="stand"):
    """Joint dictionary for the human scan.  Units are metres (1.72 tall)."""
    if pose == "sit":
        return {
            "pelvis": (0.0, 0.04, 0.46), "waist": (0.0, 0.03, 0.68),
            "chest": (0.0, 0.01, 0.90),
            "neck": (0.0, 0.0, 1.14), "head": (0.0, -0.01, 1.30),
            "head_r": 0.105,
            "shoulder_l": (0.165, 0.01, 1.10), "shoulder_r": (-0.165, 0.01, 1.10),
            "elbow_l": (0.205, -0.02, 0.80), "elbow_r": (-0.205, -0.02, 0.80),
            "wrist_l": (0.185, -0.30, 0.56), "wrist_r": (-0.185, -0.30, 0.56),
            "hip_l": (0.085, 0.03, 0.44), "hip_r": (-0.085, 0.03, 0.44),
            "knee_l": (0.105, -0.36, 0.46), "knee_r": (-0.105, -0.36, 0.46),
            "ankle_l": (0.105, -0.38, 0.08), "ankle_r": (-0.105, -0.38, 0.08),
            "foot_l": (0.105, -0.50, 0.035), "foot_r": (-0.105, -0.50, 0.035),
        }
    return {
        "pelvis": (0.0, 0.0, 0.94), "waist": (0.0, 0.0, 1.12),
        "chest": (0.0, 0.0, 1.33),
        "neck": (0.0, 0.0, 1.50), "head": (0.0, -0.005, 1.62),
        "head_r": 0.105,
        "shoulder_l": (0.175, 0.0, 1.45), "shoulder_r": (-0.175, 0.0, 1.45),
        "elbow_l": (0.215, -0.005, 1.17), "elbow_r": (-0.215, -0.005, 1.17),
        "wrist_l": (0.230, -0.020, 0.91), "wrist_r": (-0.230, -0.020, 0.91),
        "hip_l": (0.108, 0.0, 0.94), "hip_r": (-0.108, 0.0, 0.94),
        "knee_l": (0.116, -0.005, 0.53), "knee_r": (-0.116, -0.005, 0.53),
        "ankle_l": (0.114, -0.020, 0.10), "ankle_r": (-0.114, -0.020, 0.10),
        "foot_l": (0.114, -0.135, 0.035), "foot_r": (-0.114, -0.135, 0.035),
    }


def build_human(location=None, rotation=None, scale=None, style=None,
                collection=None, link=True, pose="stand", **kw):
    """Human specimen (s12): light-made figure; pose='stand' | 'sit'.

    Signature: build_human(location=None, rotation=None, scale=None,
                           style=None, collection=None, link=True,
                           pose="stand", **style)
    """
    st = _merge_style("human", style, kw)
    j = _human_joints(pose)
    objs = []
    objs += _capsule(j["pelvis"], j["waist"], 0.134, 0.116, verts=14)
    objs += _capsule(j["waist"], j["chest"], 0.116, 0.152, verts=14)
    objs += _capsule(j["chest"], j["neck"], 0.150, 0.060, verts=12)
    objs.append(_prim_sphere(j["head"], j["head_r"], 20, 14,
                             scale=(1.0, 0.98, 1.08)))
    objs += _capsule(j["chest"], j["shoulder_l"], 0.096, 0.064, verts=10)
    objs += _capsule(j["chest"], j["shoulder_r"], 0.096, 0.064, verts=10)
    for side in ("l", "r"):
        objs += _capsule(j[f"shoulder_{side}"], j[f"elbow_{side}"],
                         0.050, 0.038, verts=10)
        objs += _capsule(j[f"elbow_{side}"], j[f"wrist_{side}"],
                         0.038, 0.027, verts=10)
        wx, wy, wz = j[f"wrist_{side}"]
        objs.append(_prim_sphere((wx, wy, wz - 0.050), 0.046, 12, 8,
                                 scale=(0.72, 0.95, 1.20)))
        objs += _capsule(j[f"hip_{side}"], j[f"knee_{side}"],
                         0.074, 0.054, verts=12)
        objs += _capsule(j[f"knee_{side}"], j[f"ankle_{side}"],
                         0.054, 0.036, verts=12)
        ax, ay, az = j[f"ankle_{side}"]
        if pose == "sit":
            objs.append(_prim_cube((ax, ay - 0.090, az - 0.020),
                                   (0.094, 0.215, 0.080)))
        else:
            objs.append(_prim_cube((ax, ay - 0.078, 0.048),
                                   (0.094, 0.225, 0.082)))
    human = _join_meshes("human_scan", objs)
    _remesh_decimate(human, voxel=0.019, target_tris=430)
    parts = [(human, st["scan_color"], 1.0, True)]
    return _assemble_scan("human", parts, st, location, rotation, scale,
                          collection, link)


# ---------------------------------------------------------------------------
# koinobori
# ---------------------------------------------------------------------------

_KOINOBORI_PROFILE = [(0.000, 0.145), (0.018, 0.158), (0.060, 0.155),
                      (0.140, 0.150), (0.240, 0.140), (0.360, 0.126),
                      (0.480, 0.110), (0.590, 0.090), (0.680, 0.064),
                      (0.745, 0.038), (0.780, 0.022)]


def _koinobori_radius(u):
    prof = _KOINOBORI_PROFILE
    if u <= prof[0][0]:
        return prof[0][1]
    if u >= prof[-1][0]:
        return prof[-1][1]
    for (u0, r0), (u1, r1) in zip(prof, prof[1:]):
        if u0 <= u <= u1:
            t = (u - u0) / max(u1 - u0, 1e-9)
            return r0 * (1.0 - t) + r1 * t
    return prof[-1][1]


def _koinobori_body(L):
    """Paper carp windsock along X (mouth at -X).  Returns body object with
    SWAY_A / SWAY_B shape keys used by animate_flutter()."""
    rings = [(r * L, (u - 0.5) * L) for u, r in _KOINOBORI_PROFILE]
    body = _lathe("koinobori_body", rings, segments=20, axis="x")
    mouth_rings = [(r * L, (u - 0.5) * L) for u, r in
                   [(0.008, 0.128), (0.030, 0.120), (0.055, 0.098)]]
    mouth = _lathe("koinobori_mouth", mouth_rings, segments=20, axis="x")
    # forked tail fluke, flat in the XZ plane
    tail_pts = [(0.280, 0.020), (0.395, 0.115), (0.452, 0.205),
                (0.410, 0.120), (0.392, 0.020), (0.410, -0.120),
                (0.452, -0.205), (0.395, -0.115), (0.280, -0.020)]
    tail = _mesh_obj("koinobori_tail",
                     [(x * L, 0.0, z * L) for x, z in tail_pts],
                     [tuple(range(len(tail_pts)))])
    # dorsal fin (top, from u .30 to .55)
    dorsal_pts = [((0.30 - 0.5) * L, 0.0, 0.128 * L),
                  ((0.40 - 0.5) * L, 0.0, 0.185 * L),
                  ((0.55 - 0.5) * L, 0.0, 0.120 * L),
                  ((0.50 - 0.5) * L, 0.0, 0.085 * L),
                  ((0.34 - 0.5) * L, 0.0, 0.090 * L)]
    dorsal = _mesh_obj("koinobori_dorsal", dorsal_pts,
                       [tuple(range(len(dorsal_pts)))])
    fins = []
    for side in (-1.0, 1.0):
        pts = [((0.26 - 0.5) * L, side * 0.125 * L, -0.010 * L),
               ((0.15 - 0.5) * L, side * 0.205 * L, -0.030 * L),
               ((0.10 - 0.5) * L, side * 0.170 * L, -0.075 * L),
               ((0.21 - 0.5) * L, side * 0.115 * L, -0.060 * L)]
        fins.append(_mesh_obj(f"koinobori_fin{int(side)}", pts,
                              [tuple(range(len(pts)))]))
    body = _join_meshes("koinobori_scan", [body, mouth, tail, dorsal] + fins)
    sol = body.modifiers.new("PAPER_thickness", "SOLIDIFY")
    sol.thickness = 0.0035 * L
    sol.offset = 0.0
    sol.use_rim = True
    body.shape_key_add(name="Basis", from_mix=False)
    for sgn in ("A", "B"):
        kb = body.shape_key_add(name=f"SWAY_{sgn}", from_mix=False)
        direction = 1.0 if sgn == "A" else -1.0
        for i, v in enumerate(body.data.vertices):
            x = v.co.x / L + 0.5
            w = max(0.0, (x - 0.55) / 0.45) ** 1.4
            kb.data[i].co.y += direction * 0.085 * L * w
    return body


def _koinobori_label_color(body_color):
    return PALETTE["ink"] if hex_luma(body_color) > 0.55 else "#f6efe2"


def _rgba_mix(hex_a, hex_b, t):
    a = [int(hex_a.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(hex_b.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{int(round(a[i] * (1 - t) + b[i] * t)):02x}"
                         for i in range(3))


def build_koinobori(color=None, label_text="", length=1.4, location=None,
                    rotation=None, scale=None, style=None, collection=None,
                    link=True, name=None, **kw):
    """Paper carp kite (koinobori): open mouth, forked tail, painted bands,
    model name + file printed on the flank.

    Signature: build_koinobori(color=None, label_text="", length=1.4,
                               location=None, rotation=None, scale=None,
                               style=None, collection=None, link=True,
                               name=None)
    `label_text` may contain "\\n" or " / " to split name and file
    ("kimi / table_2").  Total nose-to-tail length == `length`.
    Returns: Collection (root "PROP_koinobori"), lowest point at z=0.
    """
    color = color or PEER_COLORS["kimi"]
    if color in PEER_COLORS:            # convenience: peer name instead of hex
        color = PEER_COLORS[color]
    L = float(length)
    label = str(label_text or "")
    lines = [x.strip() for x in label.replace(" / ", "\n").split("\n")
             if x.strip()]
    if not lines:
        lines = ["peer", "unknown"]
    objs = []
    body = _koinobori_body(L)
    _set_material(body, mat_paper("koinobori_body", color, roughness=0.74,
                                  edge_glow=0.8, emission=0.035,
                                  noise_scale=90.0))
    objs.append(body)
    band_mat = mat_paper("koinobori_band", "#f4ead6", roughness=0.8,
                         edge_glow=0.45, emission=0.03)
    band_mat_dark = mat_paper("koinobori_band_dark",
                              _rgba_mix(color, "#2a2a33", 0.42),
                              roughness=0.8, edge_glow=0.45)
    for bi, (u, wdt, mat) in enumerate(
            [(0.155, 0.075, band_mat), (0.420, 0.105, band_mat_dark),
             (0.585, 0.048, band_mat_dark)]):
        u0, u1 = u - wdt * 0.5, u + wdt * 0.5
        rings = [(_koinobori_radius(u0) * L + 0.004 * L, (u0 - 0.5) * L),
                 (_koinobori_radius(u1) * L + 0.004 * L, (u1 - 0.5) * L)]
        band = _lathe(f"koinobori_band{bi}", rings, segments=20, axis="x")
        _set_material(band, mat)
        objs.append(band)
    eye_u = 0.255
    eye_r = _koinobori_radius(eye_u)
    for side in (-1.0, 1.0):
        ex = (eye_u - 0.5) * L
        ey = side * (eye_r * L)
        eye = _prim_sphere((ex, ey, 0.030 * L), 0.052 * L, 18, 12,
                           scale=(1.0, 0.30, 1.05))
        _set_material(eye, mat_paper("koinobori_eye", "#f6efe2", roughness=0.7,
                                     edge_glow=0.4, emission=0.05))
        pupil = _prim_sphere((ex, side * (eye_r * L + 0.012 * L),
                              0.030 * L), 0.023 * L, 14, 10,
                             scale=(1.0, 0.40, 1.0))
        _set_material(pupil, mat_ink("koinobori_pupil", "#1a1c22"))
        objs += [eye, pupil]
    if lines:
        tcol = _koinobori_label_color(color)
        tx = -0.02 * L
        ty = -(_koinobori_radius(0.45) * L + 0.006 * L)
        t1 = _text_obj("koinobori_name", lines[0].upper(), 0.064 * L,
                       FONT_GEORGIA, extrude=0.0, bevel=0.0,
                       align_x="CENTER", align_y="TOP", resolution=1)
        t1.location = (tx, ty, 0.046 * L)
        t1.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
        _set_material(t1, mat_ink("koinobori_paint", tcol))
        objs.append(t1)
        if len(lines) > 1:
            t2 = _text_obj("koinobori_file", lines[1], 0.038 * L,
                           FONT_CONSOLAS, extrude=0.0, bevel=0.0,
                           align_x="CENTER", align_y="TOP", resolution=1)
            t2.location = (tx, ty - 0.0015 * L, -0.012 * L)
            t2.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
            _set_material(t2, mat_ink("koinobori_paint_file", tcol))
            objs.append(t2)
    # normalise: base at z=0, centre x/y on origin
    mins, maxs = _bounds([o for o in objs if o.type == "MESH"])
    bpy.context.view_layer.update()
    for o in objs:
        if o.type == "FONT":
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                mins = Vector((min(mins.x, w.x), min(mins.y, w.y),
                               min(mins.z, w.z)))
                maxs = Vector((max(maxs.x, w.x), max(maxs.y, w.y),
                               max(maxs.z, w.z)))
    shift = Vector((-(mins.x + maxs.x) * 0.5, -(mins.y + maxs.y) * 0.5,
                    -mins.z))
    for o in objs:
        if o.type == "MESH":
            _mesh_transform(o.data, Matrix.Translation(shift))
        else:
            o.location += shift
    dim = Vector((maxs.x - mins.x, maxs.y - mins.y, maxs.z - mins.z))
    coll = _new_collection(f"PROP_{name or 'koinobori'}")
    root = _root_empty(f"PROP_{name or 'koinobori'}")
    for o in objs:
        _move_to(o, coll)
    coll.objects.link(root)
    _parent_all(objs, root)
    _finish_collection(coll, collection, link)
    _apply_root_transform(root, location, rotation, scale)
    coll["specimen"] = "koinobori"
    coll["kind"] = "prop"
    coll["root"] = root.name
    coll["length"] = L
    coll["size"] = list(round(v, 4) for v in dim)
    coll["peer_color"] = color
    coll["label"] = " / ".join(lines)
    coll["points"] = 0
    coll["tris_base"] = sum(_obj_tris(o) for o in objs if o.type == "MESH")
    root["specimen"] = "koinobori"
    return coll


# ---------------------------------------------------------------------------
# props: bucket / tomato / index sheet
# ---------------------------------------------------------------------------

def build_bucket(location=None, rotation=None, scale=None, style=None,
                 collection=None, link=True, fill=0.0, **kw):
    """Paper bucket (s17 MERGE).  fill in 0..1 adds glowing archive scraps.

    Signature: build_bucket(location=None, rotation=None, scale=None,
                            style=None, collection=None, link=True, fill=0.0)
    """
    st = _merge_style("bucket", style, kw)
    st["height"] = 1.0
    H = 1.0
    bot_r, top_r = 0.330, 0.445
    wall = [(bot_r, 0.0), (bot_r * 1.02, 0.02), (top_r * 0.98, H * 0.97),
            (top_r, H)]
    bucket = _lathe("bucket_wall", wall, segments=26, cap_bottom=True)
    sol = bucket.modifiers.new("PAPER_thickness", "SOLIDIFY")
    sol.thickness = 0.010
    sol.offset = 0.0
    sol.use_rim = True
    _set_material(bucket, mat_paper("bucket", "#e8e1d2", roughness=0.9,
                                    edge_glow=0.55, emission=0.02,
                                    noise_scale=60.0))
    objs = [bucket]
    objs.append(_curve_wire("bucket_rim", [
        (top_r * math.cos(a), top_r * math.sin(a), H)
        for a in [2.0 * math.pi * i / 28 for i in range(28)]],
        0.010, mat_paper("bucket_rim", "#d9d0bd", roughness=0.85,
                         edge_glow=0.4), cyclic=True))
    objs.append(_curve_wire("bucket_handle", [
        (-top_r * 0.92, 0.0, H * 0.985),
        (-top_r * 0.70, 0.0, H * 1.075),
        (0.0, 0.0, H * 1.115),
        (top_r * 0.70, 0.0, H * 1.075),
        (top_r * 0.92, 0.0, H * 0.985),
    ], 0.0075, mat_metal("bucket_handle_wire")))
    if fill > 0.0:
        level = min(1.0, max(0.0, fill)) * H * 0.86
        r = bot_r + (top_r - bot_r) * (level / H)
        disc = _lathe("bucket_fill", [(0.0, level), (r * 0.97, level)],
                      segments=26)
        _set_material(disc, mat_emission("#ffd28a", 1.6, "bucket_fill"))
        objs.append(disc)
        rng = _random_for("bucket_fill", 7)
        for i in range(7):
            a = rng.uniform(0.0, math.pi * 2.0)
            rr = rng.uniform(0.0, r * 0.7)
            zz = level + rng.uniform(0.01, 0.10)
            scrap = _flat_poly(f"bucket_scrap{i}", [
                (-0.045, -0.030), (0.050, -0.024), (0.038, 0.034),
                (-0.030, 0.028)],
                Matrix.Translation((rr * math.cos(a), rr * math.sin(a), zz))
                @ Matrix.Rotation(rng.uniform(0, math.pi), 4, "Z")
                @ Matrix.Rotation(rng.uniform(-0.9, 0.9), 4, "X"))
            _set_material(scrap, mat_paper(f"bucket_scrap{i}", "#efe8d8",
                                           roughness=0.9, edge_glow=0.6))
            objs.append(scrap)
    return _assemble_prop("bucket", objs, st, location, rotation, scale,
                          collection, link)


def build_tomato_paper(location=None, rotation=None, scale=None, style=None,
                       collection=None, link=True, **kw):
    """Papercraft tomato (s21 dawn): pleated paper sphere + sepals + stem.

    Signature: build_tomato_paper(location=None, rotation=None, scale=None,
                                  style=None, collection=None, link=True)
    """
    st = _merge_style("tomato", style, kw)
    body = _prim_sphere((0.0, 0.0, 0.46), 0.46, 22, 14,
                        scale=(1.0, 1.0, 0.86))
    for v in body.data.vertices:
        theta = math.atan2(v.co.y, v.co.x)
        rr = math.hypot(v.co.x, v.co.y)
        pleat = 1.0 + 0.030 * math.cos(6.0 * theta)
        v.co.x *= pleat
        v.co.y *= pleat
        v.co.z += 0.012 * math.cos(6.0 * theta) * (1.0 - min(1.0, rr / 0.5))
    body.data.update()
    _triangulate(body)
    _set_material(body, mat_paper("tomato_paper", "#cf5a44", roughness=0.78,
                                  edge_glow=0.75, emission=0.04,
                                  noise_scale=50.0))
    objs = [body]
    sepal_mat = mat_paper("tomato_sepal", "#7c9a58", roughness=0.82,
                          edge_glow=0.5)
    for i in range(6):
        a = math.radians(60.0 * i + 12.0)
        m = (Matrix.Translation((0.0, 0.0, 0.86))
             @ Matrix.Rotation(a, 4, "Z")
             @ Matrix.Rotation(math.radians(34.0), 4, "Y"))
        sepal = _flat_poly(f"tomato_sepal{i}", [
            (0.0, 0.0), (0.10, 0.030), (0.235, 0.028), (0.205, -0.010),
            (0.105, -0.030)], m)
        _set_material(sepal, sepal_mat)
        objs.append(sepal)
    stem = _lathe("tomato_stem", [(0.045, 0.0), (0.034, 0.055), (0.042, 0.112)],
                  segments=8, cap_top=True)
    stem.data.transform(Matrix.Translation((0.0, 0.0, 0.862))
                        @ Matrix.Rotation(math.radians(10.0), 4, "Y"))
    _set_material(stem, mat_paper("tomato_stem_mat", "#6b7a48",
                                  roughness=0.85, edge_glow=0.4))
    objs.append(stem)
    return _assemble_prop("tomato_paper", objs, st, location, rotation, scale,
                          collection, link)


def _default_index_text():
    rows = [
        ("0001", "table_2", "kimi", "0.31"),
        ("0002", "eggplant_3", "qwen", "0.28"),
        ("0003", "cat_2", "mimo", "0.22"),
        ("0004", "steak_2", "glm", "0.19"),
        ("0005", "flower_2", "kimi", "0.26"),
        ("0006", "human_9", "doubao", "0.13"),
        ("0007", "piece", "minimax", "0.11"),
        ("0008", "dope", "hy4", "0.09"),
        ("0009", "love", "ernie", "0.08"),
        ("0010", "asked_again", "step", "0.07"),
        ("0011", "her_again", "longcat", "0.06"),
        ("0012", "merged", "merged", "--"),
        ("0013", "?", "?", "--"),
    ]
    out = [f"{'FILE':<4}{'NAME':<15}{'WRITER':<12}{'SIM':>5}"]
    for no, name, writer, sim in rows:
        out.append(f"{no:<4}{name:<15}{writer:<12}{sim:>5}")
    return "\n".join(out)


def build_index_sheet(text=None, location=None, rotation=None, scale=None,
                      style=None, collection=None, link=True, height=1.0,
                      width_ratio=0.74, hang=True, **kw):
    """Giant suspended paper index sheet (s02; also reads as s14 typewriter page).

    Signature: build_index_sheet(text=None, location=None, rotation=None,
                                 scale=None, style=None, collection=None,
                                 link=True, height=1.0, width_ratio=0.74,
                                 hang=True)
    `text` may be a multi-line string or list of lines; None -> default index.
    Scale it up 2.5-3x in the scene for the "giant" sheet of s02.
    Returns: Collection (root "PROP_index_sheet"), base z=0.
    """
    st = _merge_style("index_sheet", style, kw)
    H = float(height)
    W = H * float(width_ratio)
    nx, nz = 14, 18
    verts = []
    for j in range(nz + 1):
        for i in range(nx + 1):
            u = i / nx * 2.0 - 1.0
            v = j / nz * 2.0 - 1.0
            x = u * W * 0.5
            z = (v * 0.5 + 0.5) * H
            curl = (0.030 * H * (abs(u) ** 4.0)
                    + 0.022 * H * (abs(v) ** 4.0)
                    + 0.006 * H * math.sin(u * 3.2 + 0.4) * abs(v))
            verts.append((x, curl, z))
    faces = []
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    sheet = _mesh_obj("index_sheet_paper", verts, faces)
    sol = sheet.modifiers.new("PAPER_thickness", "SOLIDIFY")
    sol.thickness = 0.0022 * H
    sol.offset = 0.0
    sol.use_rim = True
    _set_material(sheet, mat_paper("index_sheet", "#ece8de", roughness=0.9,
                                   edge_glow=1.0, emission=0.035,
                                   noise_scale=45.0))
    objs = [sheet]
    mat_ink_dark = mat_ink("index_ink", "#2a2f37")
    title = _text_obj("index_title", "INDEX  /  ~/memory/you/", 0.030 * H,
                      FONT_GEORGIA, extrude=0.0, bevel=0.0,
                      align_x="LEFT", align_y="TOP", resolution=2)
    title.location = (-W * 0.41, -0.006 * H, H * 0.955)
    title.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
    _set_material(title, mat_ink_dark)
    objs.append(title)
    rule = _prim_cube((0.0, -0.004 * H, H * 0.925),
                      (W * 0.82, 0.0012, 0.0018 * H))
    _set_material(rule, mat_ink_dark)
    objs.append(rule)
    if isinstance(text, (list, tuple)):
        body_text = "\n".join(str(t) for t in text)
    elif text is None:
        body_text = _default_index_text()
    else:
        body_text = str(text)
    n_lines = max(1, len(body_text.split("\n")))
    size = min(0.0165 * H, (H * 0.80) / (n_lines * 1.16))
    index = _text_obj("index_body", body_text, size, FONT_CONSOLAS,
                      extrude=0.0, bevel=0.0, align_x="LEFT",
                      align_y="TOP", resolution=1)
    index.location = (-W * 0.41, -0.006 * H, H * 0.895)
    index.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
    _set_material(index, mat_ink_dark)
    objs.append(index)
    if hang:
        wire = mat_metal("index_wire", "#46505a")
        for side in (-1.0, 1.0):
            pts = [(side * W * 0.42, 0.0, H * 0.99),
                   (side * W * 0.43, 0.01 * H, H * 1.16),
                   (side * W * 0.40, 0.03 * H, H * 1.40)]
            objs.append(_curve_wire(f"index_hang{int(side)}", pts,
                                    0.0012 * H, wire))
    objs = _convert_to_mesh(objs)
    mins, maxs = _bounds(objs)
    shift = Vector((-(mins.x + maxs.x) * 0.5, -(mins.y + maxs.y) * 0.5, -mins.z))
    for o in objs:
        o.data.transform(Matrix.Translation(shift))
    dim = maxs - mins
    coll = _new_collection("PROP_index_sheet")
    root = _root_empty("PROP_index_sheet")
    for o in objs:
        _move_to(o, coll)
    coll.objects.link(root)
    _parent_all(objs, root)
    _finish_collection(coll, collection, link)
    _apply_root_transform(root, location, rotation, scale)
    coll["specimen"] = "index_sheet"
    coll["kind"] = "prop"
    coll["root"] = root.name
    coll["size"] = list(round(v, 4) for v in dim)
    coll["tris_base"] = sum(_obj_tris(o) for o in objs)
    return coll
