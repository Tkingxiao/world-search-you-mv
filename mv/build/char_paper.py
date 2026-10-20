"""char_paper.py - 2.5D paper-doll character for the world.search(you) MV.

The character is NEVER modelled or sculpted in Blender. She is the official galgame
illustration printed on an alpha card: one subdivided quad, a UV-offset material that
switches expressions inside a packed atlas, a Simple Deform BEND for paper softness and
a 2 mm Solidify so that edge-on she collapses to a glowing line.

Public API
----------
EXPRESSIONS                      -> ("angry", "cheerful", ..., "starry")  8 expressions
EXTRA_POSES                      -> ("maid",)  lift-skirt / reach pose
ALL_POSES                        -> EXPRESSIONS + EXTRA_POSES
build_character(name='fish', expr='cheerful', height=1.75, location=(0, 0, 0),
                split_head=False) -> ctrl
set_expression(ctrl, expr, frame=None, flash=0)   hard cut (CONSTANT interpolation)
set_bend(ctrl, degrees, lateral=None, frame=None) paper bend / lateral curl
set_edge_glow(ctrl, color=None, strength=None, frame=None)
add_alpha_edge(ctrl, thickness_mm=2.0)            (re)create the 2 mm paper edge
set_flash(ctrl, amount, frame=None)               white anime flash on an expression cut
set_fog(ctrl, color=None, density=None)           aerial perspective for the card
set_backface(ctrl, mode='art')                    'art' = double sided print, 'paper' = blank paper
anchor_world(ctrl, which='face', expr=None)       world-space feet / head / face anchor
clear_character(ctrl)                             remove object + data

ctrl keys: root, card, mat, uv_mapping_node, image_node, bsdf, output, image,
           head, head_card, bend_x, bend_z, solidify, rim_mat, paper_mat, flash_value,
           expr, height, px_per_m, card_w, card_h, card_left, card_bottom,
           set_expression, set_bend, set_edge_glow, add_alpha_edge, set_flash,
           set_backface, anchor

10-line usage example
---------------------
    import sys; sys.path.append(r"<root>/mv/build")
    import char_paper as cp
    ctrl = cp.build_character(name="fish", expr="cheerful", height=1.75, location=(0, 0, -1.2))
    ctrl["root"].rotation_euler[2] = 0.35            # yaw: art faces -Y by default
    ctrl["set_bend"](3.0)                            # soft paper curl, feet stay planted
    ctrl["set_expression"]("confused", frame=120)    # hard cut at frame 120
    ctrl["set_expression"]("serious", frame=150, flash=2)
    face = ctrl["anchor"]("face")                    # aim the camera at her eyes
"""
import json
import math
import os

import bpy
from mathutils import Vector

# ----------------------------------------------------------------------------- paths
_HERE = os.path.dirname(os.path.abspath(__file__))
MV = os.path.abspath(os.path.join(_HERE, ".."))
ASSET_DIR = os.path.join(MV, "assets", "char")
ATLAS_PNG = os.path.join(ASSET_DIR, "expr_atlas.png")
ATLAS_JSON = os.path.join(ASSET_DIR, "expr_atlas.json")

with open(ATLAS_JSON, encoding="utf-8") as _f:
    ATLAS = json.load(_f)

EXPRESSIONS = tuple(ATLAS["order"][:8])
MAID = "maid"
EXTRA_POSES = tuple(k for k in ATLAS["order"] if k not in EXPRESSIONS)
ALL_POSES = EXPRESSIONS + EXTRA_POSES

# aliases so shot scripts can use the wording of TREATMENT / shots.json
ALIASES = {
    "sad": "shy", "cry": "frightened", "crying": "frightened", "scared": "frightened",
    "surprised": "frightened", "shock": "frightened", "happy": "cheerful",
    "smile": "cheerful", "laugh": "cheerful", "sigh": "exasperated",
    "annoyed": "exasperated", "blush": "shy", "embarrassed": "shy",
    "wow": "starry", "sparkle": "starry", "neutral": "serious", "stern": "serious",
    "lift": "maid", "lift_skirt": "maid", "reach": "maid", "maid_left": "maid",
}

PALETTE = {
    "paper": "#ece8de", "ink": "#0a2230", "cyan": "#38c9ff",
    "coral": "#ff6b4a", "gold": "#ffd28a", "blue": "#4d6bfe",
}

CELL_W = ATLAS["grid"]["cell_w"]
CELL_H = ATLAS["grid"]["cell_h"]
ANCHOR_X = ATLAS["expressions"][EXPRESSIONS[0]]["feet_anchor_px_in_cell"][0]
ANCHOR_Y = ATLAS["expressions"][EXPRESSIONS[0]]["feet_anchor_px_in_cell"][1]
REF_PX = float(ATLAS["height_ref_px"])
IMAGE_W = ATLAS["image"]["width"]
IMAGE_H = ATLAS["image"]["height"]
FEET_UV_MESH = ATLAS["mapping"]["feet_uv_mesh"]

ATLAS_IMAGE_NAME = "expr_atlas.png"
COLLECTION_NAME = "CHAR"


# ----------------------------------------------------------------------------- colour
def _srgb_to_linear(c):
    c = max(0.0, min(1.0, float(c)))
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h, alpha=1.0):
    """'#38c9ff' -> linear RGBA tuple (Blender node colours are linear)."""
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (_srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b), alpha)


# ----------------------------------------------------------------------------- lookup
def _resolve(expr):
    if expr is None:
        raise ValueError("expr is None")
    key = str(expr).strip().lower().replace(" ", "_").replace("-", "_")
    key = ALIASES.get(key, key)
    if key not in ALL_POSES:
        raise ValueError(f"unknown expression {expr!r}; valid: {list(ALL_POSES)} "
                         f"(aliases: {sorted(ALIASES)})")
    return key


def _entry(expr):
    key = _resolve(expr)
    if key in ATLAS["expressions"]:
        return ATLAS["expressions"][key]
    return ATLAS["extras"][key]


def mapping_for(expr):
    """{'scale': (su, sv), 'location': (lu, lv)} for the Mapping node (from the atlas JSON)."""
    m = _entry(expr)["mapping"]
    return (tuple(m["scale"]), tuple(m["location"]))


# ----------------------------------------------------------------------------- assets
def atlas_image():
    """The atlas image datablock (sRGB, straight alpha)."""
    img = bpy.data.images.get(ATLAS_IMAGE_NAME)
    if img is None:
        img = bpy.data.images.load(ATLAS_PNG, check_existing=True)
        img.name = ATLAS_IMAGE_NAME
    img.colorspace_settings.name = "sRGB"
    img.alpha_mode = "STRAIGHT"
    return img


def _collection(name=COLLECTION_NAME):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


# ----------------------------------------------------------------------------- material
def _new_material(name):
    mat = bpy.data.materials.get(name)
    if mat is not None:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return mat


def _fog_chain(nt, color_out, target_socket, color=None, tag="Fog"):
    """Aerial perspective for EEVEE-Next: blended surfaces are composited *after* the
    volumetric pass, so the card would otherwise never be fogged.  Mixes the surface
    colour toward the fog colour with 1 - exp(-density * view_distance) - the same
    transmittance the volume uses.  density 0 (default) disables it."""
    nodes, links = nt.nodes, nt.links
    cam = nodes.new("ShaderNodeCameraData")
    cam.name = f"{tag}_Camera"
    cam.location = (-460, -420)
    dens = nodes.new("ShaderNodeValue")
    dens.name = f"{tag}_Density"
    dens.location = (-660, -560)
    dens.outputs[0].default_value = 0.0
    m1 = nodes.new("ShaderNodeMath")
    m1.name = f"{tag}_Depth"
    m1.operation = "MULTIPLY"
    m1.location = (-460, -560)
    links.new(cam.outputs["View Distance"], m1.inputs[0])
    links.new(dens.outputs[0], m1.inputs[1])
    m2 = nodes.new("ShaderNodeMath")
    m2.name = f"{tag}_Neg"
    m2.operation = "MULTIPLY"
    m2.inputs[1].default_value = -1.0
    m2.location = (-280, -560)
    links.new(m1.outputs[0], m2.inputs[0])
    m3 = nodes.new("ShaderNodeMath")
    m3.name = f"{tag}_Transmit"
    m3.operation = "EXPONENT"
    m3.location = (-100, -560)
    links.new(m2.outputs[0], m3.inputs[0])
    m4 = nodes.new("ShaderNodeMath")
    m4.name = f"{tag}_Factor"
    m4.operation = "SUBTRACT"
    m4.inputs[0].default_value = 1.0
    m4.location = (70, -560)
    links.new(m3.outputs[0], m4.inputs[1])
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = f"{tag}_Mix"
    mix.blend_type = "MIX"
    mix.location = (120, -120)
    mix.inputs["Color2"].default_value = hex_to_linear(color or "#123039")
    links.new(m4.outputs[0], mix.inputs["Fac"])
    links.new(color_out, mix.inputs["Color1"])
    links.new(mix.outputs["Color"], target_socket)
    return mix


def _make_art_material(name, glow_color=None):
    """Printed-paper material: atlas colour, straight alpha, dithered-free blended alpha,
    backface culled (the 2 mm solidify supplies the back surface), white-flash emission."""
    mat = _new_material(name)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    out = nodes.new("ShaderNodeOutputMaterial")
    out.name = "Output"
    out.location = (620, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.name = "Principled"
    bsdf.location = (300, 0)
    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.name = "UV"
    texcoord.location = (-620, 0)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.name = "UV_Mapping"
    mapping.vector_type = "POINT"
    mapping.location = (-420, 0)
    img_node = nodes.new("ShaderNodeTexImage")
    img_node.name = "Atlas"
    img_node.location = (-200, 0)
    img_node.image = atlas_image()
    img_node.extension = "CLIP"          # never sample the neighbouring cell
    img_node.interpolation = "Linear"
    links.new(texcoord.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], img_node.inputs["Vector"])
    _fog_chain(nt, img_node.outputs["Color"], bsdf.inputs["Base Color"], tag="Fog")
    links.new(img_node.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.62
    bsdf.inputs["Specular IOR Level"].default_value = 0.32
    bsdf.inputs["IOR"].default_value = 1.45
    bsdf.inputs["Metallic"].default_value = 0.0
    # anime white flash on expression cuts: emission strength driven by a keyframeable Value
    flash = nodes.new("ShaderNodeValue")
    flash.name = "Flash"
    flash.location = (-200, -320)
    flash.outputs[0].default_value = 0.0
    flash_mul = nodes.new("ShaderNodeMath")
    flash_mul.name = "Flash_Strength"
    flash_mul.operation = "MULTIPLY"
    flash_mul.inputs[1].default_value = 5.0
    flash_mul.location = (60, -320)
    links.new(flash.outputs[0], flash_mul.inputs[0])
    links.new(flash_mul.outputs[0], bsdf.inputs["Emission Strength"])
    bsdf.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    # EEVEE-Next: blended transparency -> crisp anti-aliased alpha; transparent shadow
    mat.surface_render_method = "BLENDED"
    mat.use_transparent_shadow = True
    mat.use_backface_culling = True
    return mat


def _make_paper_material(name):
    """Blank paper back side (the reverse of the print)."""
    mat = _new_material(name)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.name = "Principled"
    bsdf.location = (100, 0)
    bsdf.inputs["Base Color"].default_value = hex_to_linear(PALETTE["paper"])
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    paper_rgb = nodes.new("ShaderNodeRGB")
    paper_rgb.name = "Paper_Color"
    paper_rgb.location = (-260, 60)
    paper_rgb.outputs[0].default_value = hex_to_linear(PALETTE["paper"])
    _fog_chain(nt, paper_rgb.outputs[0], bsdf.inputs["Base Color"], tag="Fog")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparent_shadow = True
    mat.use_backface_culling = True
    return mat


def _make_rim_material(name, color=None, strength=1.0):
    """Emissive paper edge: 2 mm strip that makes edge-on read as a glowing line.

    The strip must be *invisible* while the card faces the camera - seen from the front it is
    only ~1 px wide and would draw a straight vertical line floating outside the artwork -
    and it must *not* turn black either, so the gate drives a Mix Shader toward Transparent
    instead of only dimming the emission.  Only when the strip turns toward the camera
    (|N.V| -> 1, i.e. the card is near edge-on) does it light up and read as a line.
    Layer Weight 'Facing' = 1 - |N.V|, so the gate is (1 - Facing)^6."""
    mat = _new_material(name)
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    out = nodes.new("ShaderNodeOutputMaterial")
    out.name = "Output"
    out.location = (560, 0)
    emit = nodes.new("ShaderNodeEmission")
    emit.name = "Emission"
    emit.location = (300, 120)
    edge_col = nodes.new("ShaderNodeRGB")
    edge_col.name = "Edge_Color"
    edge_col.location = (-200, 120)
    edge_col.outputs[0].default_value = hex_to_linear(color or PALETTE["cyan"])
    _fog_chain(nt, edge_col.outputs[0], emit.inputs["Color"], tag="Fog")
    val = nodes.new("ShaderNodeValue")
    val.name = "Rim_Strength"
    val.location = (120, -160)
    val.outputs[0].default_value = float(strength)
    links.new(val.outputs[0], emit.inputs["Strength"])
    # Edge-on gate: the rim is a 2 mm strip that runs around the *card rectangle* (not around
    # the art silhouette), so head-on it is seen from its side and shows up as a 1 px vertical
    # line floating beside the artwork.  Gate it by how edge-on the CARD is: |cos| between the
    # view ray and the card's front normal (0,-1,0), in object space so the root empty's yaw
    # counts.  gate = (1 - |cos|)^4 -> 0 at yaw 0, ~0 at yaw 35, 0.5 at yaw 80, 1 at yaw 90.
    geo = nodes.new("ShaderNodeNewGeometry")
    geo.name = "Rim_Geom"
    geo.location = (-620, -300)
    vt = nodes.new("ShaderNodeVectorTransform")
    vt.name = "Rim_ViewToObject"
    vt.vector_type = "VECTOR"
    vt.convert_from = "WORLD"
    vt.convert_to = "OBJECT"
    vt.location = (-440, -300)
    links.new(geo.outputs["Incoming"], vt.inputs["Vector"])
    dot = nodes.new("ShaderNodeVectorMath")
    dot.name = "Rim_Dot"
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (0.0, -1.0, 0.0)
    dot.location = (-260, -300)
    links.new(vt.outputs["Vector"], dot.inputs[0])
    ab = nodes.new("ShaderNodeMath")
    ab.name = "Rim_Abs"
    ab.operation = "ABSOLUTE"
    ab.location = (-80, -300)
    links.new(dot.outputs["Value"], ab.inputs[0])
    inv = nodes.new("ShaderNodeMath")
    inv.name = "Rim_InvFacing"
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    inv.location = (80, -300)
    links.new(ab.outputs[0], inv.inputs[1])
    pw = nodes.new("ShaderNodeMath")
    pw.name = "Rim_Power"
    pw.operation = "POWER"
    pw.inputs[1].default_value = 4.0
    pw.location = (220, -380)
    links.new(inv.outputs[0], pw.inputs[0])
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    transparent.name = "Rim_Transparent"
    transparent.location = (300, -200)
    mix = nodes.new("ShaderNodeMixShader")
    mix.name = "Rim_Mix"
    mix.location = (430, 0)
    links.new(pw.outputs[0], mix.inputs["Fac"])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(emit.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"    # alpha-gated: never a black line
    mat.use_transparent_shadow = False
    mat.use_backface_culling = False
    return mat


# ----------------------------------------------------------------------------- mesh
def _grid_mesh(name, x0, x1, z0, z1, u0, u1, v0, v1, nx=24, nz=64):
    """Flat card in the XZ plane, normal -Y, UV rectangle (u0..u1, v0..v1)."""
    verts, uvs = [], []
    for j in range(nz + 1):
        tz = j / nz
        z = z0 + (z1 - z0) * tz
        v = v0 + (v1 - v0) * tz
        for i in range(nx + 1):
            tx = i / nx
            verts.append((x0 + (x1 - x0) * tx, 0.0, z))
            uvs.append((u0 + (u1 - u0) * tx, v))
    faces = []
    for j in range(nz):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + 1 + nx + 1, a + nx + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.validate()
    layer = me.uv_layers.new(name="UVMap")
    loops = me.loops
    for poly in me.polygons:
        for li in poly.loop_indices:
            layer.data[li].uv = uvs[loops[li].vertex_index]
    return me


def _add_bend(obj, name, axis="X", angle=0.0):
    mod = obj.modifiers.new(name, "SIMPLE_DEFORM")
    mod.deform_method = "BEND"
    mod.deform_axis = axis
    mod.angle = math.radians(angle)
    mod.origin = None
    return mod


def _add_edge(obj, thickness_mm=2.0, rim=True):
    mod = obj.modifiers.new("Paper_Edge", "SOLIDIFY")
    mod.thickness = thickness_mm / 1000.0
    mod.offset = -1.0           # keep the printed face at y=0, thickness grows away from camera
    mod.use_rim = rim
    mod.use_even_offset = True
    mod.use_quality_normals = True
    mod.material_offset = 0     # back faces keep the art material (double sided print)
    mod.material_offset_rim = 2  # rim faces -> emissive paper edge
    return mod


# ----------------------------------------------------------------------------- animation helpers
def _fcurves(id_data):
    ad = getattr(id_data, "animation_data", None)
    if not ad or not ad.action:
        return []
    act = ad.action
    try:
        fcs = list(act.fcurves)
        if fcs:
            return fcs
    except Exception:
        pass
    out = []
    try:  # layered actions (Blender 4.4+)
        slot = getattr(ad, "action_slot", None)
        for layer in act.layers:
            for strip in layer.strips:
                cb = strip.channelbag(slot)
                if cb is not None:
                    out.extend(cb.fcurves)
    except Exception:
        pass
    return out


def _set_constant(id_data, data_path_contains):
    for fc in _fcurves(id_data):
        if data_path_contains in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


# ----------------------------------------------------------------------------- ctrl methods
def set_expression(ctrl, expr, frame=None, flash=0):
    """Hard-cut to another expression (Mapping scale+location). Keyframed CONSTANT, so the
    atlas window jumps between cells instead of sliding across them."""
    key = _resolve(expr)
    scale, loc = mapping_for(key)
    mapping = ctrl["uv_mapping_node"]
    mapping.inputs["Scale"].default_value = (scale[0], scale[1], 1.0)
    mapping.inputs["Location"].default_value = (loc[0], loc[1], 0.0)
    if frame is not None:
        mapping.inputs["Scale"].keyframe_insert("default_value", frame=frame)
        mapping.inputs["Location"].keyframe_insert("default_value", frame=frame)
        _set_constant(ctrl["mat"].node_tree, 'UV_Mapping')
    ctrl["expr"] = key
    if flash and frame is not None:
        set_flash(ctrl, 1.0, frame)
        set_flash(ctrl, 0.0, frame + int(flash))
    return key


def set_bend(ctrl, degrees, lateral=None, frame=None):
    """Simple Deform BEND around X: the card curls backwards (away from the -Y camera),
    the feet row at z=0 stays planted. `lateral` curls the sides back around Z."""
    bx = ctrl["bend_x"]
    bx.angle = math.radians(float(degrees))
    if frame is not None:
        bx.keyframe_insert("angle", frame=frame)
    if lateral is not None:
        bz = ctrl["bend_z"]
        bz.angle = math.radians(float(lateral))
        if frame is not None:
            bz.keyframe_insert("angle", frame=frame)
    for mod in ctrl.get("head_bends", ()):
        mod.angle = math.radians(float(degrees))
        if frame is not None:
            mod.keyframe_insert("angle", frame=frame)


def set_edge_glow(ctrl, color=None, strength=None, frame=None):
    """Colour / power of the 2 mm emissive paper edge (0.3 mm glowing edge look)."""
    if color is not None:
        if isinstance(color, str):
            col = hex_to_linear(color)
        else:
            col = tuple(color) + (1.0,) if len(color) == 3 else tuple(color)
        ctrl["rim_mat"].node_tree.nodes["Edge_Color"].outputs[0].default_value = col
    if strength is not None:
        val = ctrl["rim_mat"].node_tree.nodes["Rim_Strength"].outputs[0]
        val.default_value = float(strength)
        if frame is not None:
            val.keyframe_insert("default_value", frame=frame)


def set_fog(ctrl, color=None, density=None):
    """Aerial perspective for the card (EEVEE-Next does not fog blended surfaces).
    Call once per shot with the shot's fog density; density 0 switches it off.
    color should be the fog's *scattered* colour (what the haze looks like at her depth)."""
    for mat in (ctrl["mat"], ctrl["paper_mat"], ctrl["rim_mat"]):
        nt = mat.node_tree
        if density is not None:
            nt.nodes["Fog_Density"].outputs[0].default_value = float(density)
        if color is not None:
            col = hex_to_linear(color) if isinstance(color, str) else tuple(color)
            nt.nodes["Fog_Mix"].inputs["Color2"].default_value = (
                tuple(col) + (1.0,) if len(col) == 3 else tuple(col))


def add_alpha_edge(ctrl, thickness_mm=2.0):
    """(Re)create the 2 mm paper edge; makes the card a solid object so an edge-on view
    collapses to a line instead of disappearing."""
    card = ctrl["card"]
    for mod in list(card.modifiers):
        if mod.name == "Paper_Edge":
            card.modifiers.remove(mod)
    mod = _add_edge(card, thickness_mm)
    ctrl["solidify"] = mod
    if ctrl.get("head_card") is not None:
        head = ctrl["head_card"]
        for m in list(head.modifiers):
            if m.name == "Paper_Edge":
                head.modifiers.remove(m)
        _add_edge(head, thickness_mm, rim=False)  # no rim on the neck cut
    return mod


def set_flash(ctrl, amount, frame=None):
    """White emission flash (anime expression switch). amount 0..1, 1 = blown out."""
    val = ctrl["flash_value"].outputs[0]
    val.default_value = float(amount)
    if frame is not None:
        val.keyframe_insert("default_value", frame=frame)


def set_backface(ctrl, mode="art", color=None):
    """'art'   = double sided print (default): from behind you see the mirrored art.
    'paper' = blank paper reverse: from behind she is a pale paper silhouette."""
    mod = ctrl.get("solidify")
    if mod is None:
        raise RuntimeError("no paper edge yet; call add_alpha_edge() first")
    mode = str(mode).lower()
    if mode == "art":
        mod.material_offset = 0
    elif mode == "paper":
        mod.material_offset = 1
    else:
        raise ValueError("mode must be 'art' or 'paper'")
    if color is not None and mode == "paper":
        bsdf = ctrl["paper_mat"].node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (
            hex_to_linear(color) if isinstance(color, str) else tuple(color))


def anchor_world(ctrl, which="face", expr=None):
    """World-space position of 'feet', 'head' or 'face' anchor for an expression
    (defaults to the current one). Lets a camera script aim at her eyes exactly."""
    key = _resolve(expr) if expr is not None else ctrl["expr"]
    e = _entry(key)
    px, py = e[{"feet": "feet_anchor_px_in_cell", "head": "head_anchor_px_in_cell",
                "face": "face_anchor_px_in_cell"}[which]]
    col, row = e["cell"]
    atlas_u = (col * CELL_W + px) / IMAGE_W
    atlas_v = 1.0 - (row * CELL_H + py) / IMAGE_H
    scale, loc = mapping_for(key)
    u = (atlas_u - loc[0]) / scale[0]
    v = (atlas_v - loc[1]) / scale[1]
    local = Vector((ctrl["card_left"] + u * ctrl["card_w"], 0.0,
                    ctrl["card_bottom"] + v * ctrl["card_h"]))
    return ctrl["card"].matrix_world @ local


def clear_character(ctrl):
    """Delete the character (objects, mesh data and the materials it owns)."""
    objs = [ctrl.get("head_card"), ctrl.get("card"), ctrl.get("head"), ctrl.get("root")]
    mats = [ctrl.get("mat"), ctrl.get("paper_mat"), ctrl.get("rim_mat")]
    for o in objs:
        if o is not None and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    for m in mats:
        if m is not None and m.name in bpy.data.materials:
            bpy.data.materials.remove(m)


# ----------------------------------------------------------------------------- builder
def build_character(name="fish", expr="cheerful", height=1.75, location=(0, 0, 0),
                    split_head=False, **opts):
    """Build the paper-doll character. Returns the ctrl dict described in the module docstring.

    height      on-screen height in metres of the alpha bbox of the reference expression
                (art keeps its native scale, so individual expressions differ by +-2 %).
    location    world position of the FEET anchor (the card's local z=0).
    split_head  separate head card on a neck pivot for head tilts (default False; the cut
                runs through her hair, so keep tilts small, <= ~5 deg).
    opts: yaw=0.0, bend=0.0, bend_lateral=0.0, edge_mm=2.0, glow=PALETTE['cyan'],
          glow_strength=1.5, backface='art', head_split=0.80, head_overlap=0.02,
          nx=24, nz=64, collection=COLLECTION_NAME
    """
    scene = bpy.context.scene
    coll = _collection(opts.get("collection", COLLECTION_NAME))
    key = _resolve(expr)
    s = float(height) / REF_PX

    card_w = CELL_W * s
    card_h = CELL_H * s
    card_left = -ANCHOR_X * s
    card_bottom = -(CELL_H - ANCHOR_Y) * s
    top = ANCHOR_Y * s

    # ---------------------------------------------------------------- materials
    mat = _make_art_material(f"{name}_paper")
    paper_mat = _make_paper_material(f"{name}_paper_back")
    rim_mat = _make_rim_material(f"{name}_edge", opts.get("glow", PALETTE["cyan"]),
                                 opts.get("glow_strength", 1.0))
    # ---------------------------------------------------------------- root empty
    root = bpy.data.objects.new(f"{name}_root", None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.25
    root.location = location
    root.rotation_euler = (0.0, 0.0, math.radians(float(opts.get("yaw", 0.0))))
    coll.objects.link(root)

    nx, nz = int(opts.get("nx", 24)), int(opts.get("nz", 64))
    head_split = float(opts.get("head_split", 0.80))
    head_overlap = float(opts.get("head_overlap", 0.02))
    cut_z = float(height) * head_split
    ov = float(height) * head_overlap

    def v_at(z):
        return (z - card_bottom) / card_h

    # ---------------------------------------------------------------- card mesh(es)
    head = head_card = None
    if not split_head:
        me = _grid_mesh(f"{name}_card", card_left, card_left + card_w, card_bottom, top,
                        0.0, 1.0, 0.0, 1.0, nx, nz)
        card = bpy.data.objects.new(f"{name}_card", me)
        coll.objects.link(card)
        card.parent = root
        card.location = (0.0, 0.0, 0.0)
        parts = [(card, "body")]
    else:
        body_me = _grid_mesh(f"{name}_body", card_left, card_left + card_w, card_bottom,
                             cut_z + ov, 0.0, 1.0, 0.0, v_at(cut_z + ov), nx, nz // 2 + 1)
        card = bpy.data.objects.new(f"{name}_body", body_me)
        coll.objects.link(card)
        card.parent = root
        head_me = _grid_mesh(f"{name}_head", card_left, card_left + card_w, cut_z - ov, top,
                             0.0, 1.0, v_at(cut_z - ov), 1.0, nx, nz // 2 + 1)
        head_card = bpy.data.objects.new(f"{name}_head", head_me)
        coll.objects.link(head_card)
        head = bpy.data.objects.new(f"{name}_neck", None)
        head.empty_display_type = "PLAIN_AXES"
        head.empty_display_size = 0.08
        coll.objects.link(head)
        head.parent = root
        head.location = (0.0, 0.0, cut_z)
        head_card.parent = head
        head_card.location = (0.0, -0.0015, -cut_z)   # origin back at the feet, 1.5 mm in front
        parts = [(card, "body"), (head_card, "head")]

    for obj, _ in parts:
        obj.data.materials.append(mat)
        obj.data.materials.append(paper_mat)
        obj.data.materials.append(rim_mat)

    # ---------------------------------------------------------------- modifiers
    bend_x = _add_bend(card, "Bend_X", "X", opts.get("bend", 0.0))
    bend_z = _add_bend(card, "Bend_Z", "Z", opts.get("bend_lateral", 0.0))
    solidify = _add_edge(card, float(opts.get("edge_mm", 2.0)), rim=True)
    head_bends = []
    if head_card is not None:
        head_bends.append(_add_bend(head_card, "Bend_X", "X", opts.get("bend", 0.0)))
        head_bends.append(_add_bend(head_card, "Bend_Z", "Z", opts.get("bend_lateral", 0.0)))
        _add_edge(head_card, float(opts.get("edge_mm", 2.0)), rim=False)

    if opts.get("backface", "art") != "art":
        set_backface({"solidify": solidify, "paper_mat": paper_mat}, opts["backface"])

    # ---------------------------------------------------------------- ctrl
    ctrl = {
        "name": name,
        "root": root, "card": card, "head": head, "head_card": head_card,
        "mat": mat, "paper_mat": paper_mat, "rim_mat": rim_mat,
        "image": atlas_image(),
        "uv_mapping_node": mat.node_tree.nodes["UV_Mapping"],
        "image_node": mat.node_tree.nodes["Atlas"],
        "bsdf": mat.node_tree.nodes["Principled"],
        "output": mat.node_tree.nodes["Output"],
        "flash_value": mat.node_tree.nodes["Flash"],
        "bend_x": bend_x, "bend_z": bend_z, "head_bends": head_bends,
        "solidify": solidify,
        "expr": key, "height": float(height), "px_per_m": 1.0 / s,
        "card_w": card_w, "card_h": card_h,
        "card_left": card_left, "card_bottom": card_bottom,
        "split_head": bool(split_head),
        "set_expression": lambda e, frame=None, flash=0: set_expression(ctrl, e, frame, flash),
        "set_bend": lambda deg, lateral=None, frame=None: set_bend(ctrl, deg, lateral, frame),
        "set_edge_glow": lambda color=None, strength=None, frame=None: set_edge_glow(
            ctrl, color, strength, frame),
        "add_alpha_edge": lambda thickness_mm=2.0: add_alpha_edge(ctrl, thickness_mm),
        "set_flash": lambda amount, frame=None: set_flash(ctrl, amount, frame),
        "set_backface": lambda mode="art", color=None: set_backface(ctrl, mode, color),
        "set_fog": lambda color=None, density=None: set_fog(ctrl, color, density),
        "anchor": lambda which="face", expr=None: anchor_world(ctrl, which, expr),
    }
    set_expression(ctrl, key)
    return ctrl


__all__ = ["EXPRESSIONS", "EXTRA_POSES", "ALL_POSES", "ALIASES", "PALETTE",
           "build_character", "set_expression", "set_bend", "set_edge_glow",
           "add_alpha_edge", "set_flash", "set_backface", "set_fog", "anchor_world",
           "clear_character", "mapping_for", "atlas_image", "hex_to_linear"]
