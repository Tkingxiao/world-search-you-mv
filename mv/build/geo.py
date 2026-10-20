"""geo.py - fast bmesh geometry builder (one object, many primitives, per-face materials).
Avoids bpy.ops per-object cost: thousands of primitives in one mesh in <1s.
"""
import bpy, bmesh, math
from mathutils import Matrix, Vector, Euler


class Geo:
    def __init__(self, name='geo'):
        self.bm = bmesh.new()
        self.mats = []
        self.name = name

    def _mi(self, mat):
        if mat is None:
            return 0
        for i, m in enumerate(self.mats):
            if m == mat:
                return i
        self.mats.append(mat)
        return len(self.mats) - 1

    def _tag(self, faces, mat):
        mi = self._mi(mat)
        for f in faces:
            f.material_index = mi

    def _new_faces(self, before):
        return [f for f in self.bm.faces if f.index not in before]

    def box(self, dims=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), mat=None):
        m = Matrix.LocRotScale(Vector(loc), Euler(rot), Vector((dims[0], dims[1], dims[2])))
        before = set(f.index for f in self.bm.faces)
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self.bm.faces.ensure_lookup_table()
        self._tag([f for f in self.bm.faces if f.index not in before], mat)

    def plane(self, size=1.0, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, sx=1.0, sy=1.0):
        m = Matrix.LocRotScale(Vector(loc), Euler(rot), Vector((size * sx, size * sy, 1)))
        before = set(f.index for f in self.bm.faces)
        bmesh.ops.create_grid(self.bm, x_segments=1, y_segments=1, size=0.5, matrix=m)
        self.bm.faces.ensure_lookup_table()
        self._tag([f for f in self.bm.faces if f.index not in before], mat)

    def cylinder(self, r=0.1, h=1.0, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, seg=12):
        m = Matrix.LocRotScale(Vector(loc), Euler(rot), Vector((1, 1, 1)))
        before = set(f.index for f in self.bm.faces)
        bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                              radius1=r, radius2=r, depth=h, matrix=m)
        self.bm.faces.ensure_lookup_table()
        self._tag([f for f in self.bm.faces if f.index not in before], mat)

    def sphere(self, r=0.1, loc=(0, 0, 0), mat=None, subdiv=1):
        m = Matrix.LocRotScale(Vector(loc), Euler((0, 0, 0)), Vector((r, r, r)))
        before = set(f.index for f in self.bm.faces)
        bmesh.ops.create_icosphere(self.bm, subdivisions=subdiv, radius=1.0, matrix=m)
        self.bm.faces.ensure_lookup_table()
        self._tag([f for f in self.bm.faces if f.index not in before], mat)

    def build(self, parent=None, mat_slots=True):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.collection.objects.link(ob)
        if mat_slots:
            for m in self.mats:
                me.materials.append(m)
        if parent:
            ob.parent = parent
        return ob

    def to_mesh(self):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        return me


def obj_from_bm(bm, name, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    return ob


def merge_objects(objs, name, keep_mats=True):
    """Merge simple mesh objects into one (objects must share no shape keys)."""
    import bmesh
    bm = bmesh.new()
    mats = []
    for ob in objs:
        me = ob.data
        for m in me.materials:
            if m not in mats:
                mats.append(m)
        tmp = bm.from_mesh(me) if False else None
        # transform verts into world space of target (identity)
        mw = ob.matrix_world
        sub = bmesh.new()
        sub.from_mesh(me)
        bmesh.ops.transform(sub, matrix=mw, verts=sub.verts)
        # remap material indices
        for f in sub.faces:
            m = me.materials[f.material_index] if me.materials else None
            f.material_index = mats.index(m) if m in mats else 0
        tmp_me = bpy.data.meshes.new('tmp')
        sub.to_mesh(tmp_me)
        sub.free()
        bm.from_mesh(tmp_me)
        bpy.data.meshes.remove(tmp_me)
    return obj_from_bm(bm, name, mats)


def join(mesh_objs, name):
    """bpy.ops.object.join fast path (context override)."""
    ctx = bpy.context.copy()
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in mesh_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    bpy.ops.object.join()
    ob = bpy.context.object
    ob.name = name
    return ob
