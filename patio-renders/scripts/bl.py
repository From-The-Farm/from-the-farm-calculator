"""Small helpers for building meshes / node trees with the bpy module."""
import bpy, bmesh, math, random
import numpy as np
from mathutils import Vector, Matrix, Euler
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
import mapbox_earcut as earcut

# ------------------------------------------------------------------ collections / objects
def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c

def obj(name, me, collection=None, mat=None):
    o = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(o)
    if mat is not None:
        if isinstance(mat, (list, tuple)):
            for m in mat: me.materials.append(m)
        else:
            me.materials.append(mat)
    return o

def mesh(name, verts, faces, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    me.update()
    if smooth:
        me.shade_smooth()
    return me

def face_attr(me, name, values, kind='FLOAT'):
    a = me.attributes.new(name=name, type=kind, domain='FACE')
    if kind == 'FLOAT':
        a.data.foreach_set('value', np.asarray(values, dtype=np.float32))
    elif kind == 'FLOAT_VECTOR':
        a.data.foreach_set('vector', np.asarray(values, dtype=np.float32).ravel())
    elif kind == 'INT':
        a.data.foreach_set('value', np.asarray(values, dtype=np.int32))
    return a

def set_material_indices(me, idx):
    me.polygons.foreach_set('material_index', np.asarray(idx, dtype=np.int32))

# ------------------------------------------------------------------ 2D polygon -> 3D
def ring_ccw(poly):
    poly = orient(poly, 1.0)
    pts = list(poly.exterior.coords)[:-1]
    return pts

def inset_ring(pts, d):
    n = len(pts)
    out = []
    for i in range(n):
        p = Vector(pts[i - 1]); v = Vector(pts[i]); q = Vector(pts[(i + 1) % n])
        d1 = (v - p); d2 = (q - v)
        if d1.length < 1e-9 or d2.length < 1e-9:
            out.append(v.copy()); continue
        d1.normalize(); d2.normalize()
        n1 = Vector((-d1.y, d1.x)); n2 = Vector((-d2.y, d2.x))
        den = 1.0 + n1.dot(n2)
        den = max(den, 0.25)
        out.append(v + (n1 + n2) * (d / den))
    return out

class MeshBuilder:
    """Accumulates verts/faces (+ per-face attributes) for one big mesh."""
    def __init__(self):
        self.v = []; self.f = []; self.fa = []; self.mi = []
    def add_face(self, idx, mi=0, **attrs):
        self.f.append(idx); self.mi.append(mi); self.fa.append(attrs if attrs else None)
    def vert(self, p):
        self.v.append(tuple(p)); return len(self.v) - 1
    def build(self, name, attr_kinds=None, smooth=False):
        me = mesh(name, self.v, self.f, smooth)
        if len(me.polygons) != len(self.f):
            raise RuntimeError('face count changed during validate: %d -> %d' % (len(self.f), len(me.polygons)))
        set_material_indices(me, self.mi)
        keys = {}
        for a in self.fa:
            if a:
                for k, v in a.items():
                    if k not in keys: keys[k] = v
        for k, sample in keys.items():
            kind = (attr_kinds or {}).get(k, 'FLOAT')
            dflt = (0.0, 0.0, 0.0) if kind == 'FLOAT_VECTOR' else 0.0
            vals = [(a.get(k, dflt) if a else dflt) for a in self.fa]
            face_attr(me, k, vals, kind)
        return me

    def prism(self, pts, z0, z1, ch=0.0, mi=0, side_mi=None, bottom=False, **attrs):
        """Extruded CCW ring pts (list of xy) from z0..z1 with a 45deg chamfer ch on the top edge."""
        n = len(pts)
        if side_mi is None: side_mi = mi
        if ch > 0:
            top = inset_ring(pts, ch)
            T = [self.vert((p[0], p[1], z1)) for p in top]
            M = [self.vert((p[0], p[1], z1 - ch)) for p in pts]
        else:
            T = [self.vert((p[0], p[1], z1)) for p in pts]
            M = T
        B = [self.vert((p[0], p[1], z0)) for p in pts]
        self.add_face(T, mi, **attrs)
        for i in range(n):
            j = (i + 1) % n
            if ch > 0:
                self.add_face([M[i], M[j], T[j], T[i]], mi, **attrs)
            self.add_face([B[i], B[j], M[j], M[i]], side_mi, **attrs)
        if bottom:
            self.add_face(list(reversed(B)), side_mi, **attrs)

    def poly_prism(self, poly, z0, z1, ch=0.0, mi=0, simplify=0.0015, **attrs):
        if poly.is_empty: return
        polys = [poly] if poly.geom_type == 'Polygon' else [g for g in poly.geoms if g.geom_type == 'Polygon']
        for p in polys:
            if p.area < 1e-6: continue
            if simplify: p = p.simplify(simplify, preserve_topology=True)
            if p.interiors:
                self.flat_poly(p, z1, mi, **attrs)   # holes: flat top only
                continue
            self.prism(ring_ccw(p), z0, z1, ch, mi, **attrs)

    def flat_poly(self, poly, z, mi=0, **attrs):
        """Triangulated (earcut) flat polygon, holes allowed."""
        polys = [poly] if poly.geom_type == 'Polygon' else [g for g in poly.geoms if g.geom_type == 'Polygon']
        for p in polys:
            p = orient(p, 1.0)
            rings = [list(p.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in p.interiors]
            flat = np.array([c for r in rings for c in r], dtype=np.float64)
            ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
            tri = earcut.triangulate_float64(flat, ends).reshape(-1, 3)
            base = len(self.v)
            for c in flat: self.v.append((c[0], c[1], z))
            for t in tri:
                self.add_face([base + int(t[0]), base + int(t[1]), base + int(t[2])], mi, **attrs)

    def box(self, x0, y0, z0, x1, y1, z1, mi=0, **attrs):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        self.prism(pts, z0, z1, 0.0, mi, bottom=True, **attrs)

def bevel_box_mesh(name, sx, sy, sz, bevel=0.01, segments=2, origin_bottom=True):
    """Box of size (sx,sy,sz) centered in XY, sitting on z=0 if origin_bottom, with beveled edges."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx; v.co.y *= sy; v.co.z *= sz
        if origin_bottom: v.co.z += sz / 2
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(bevel, min(sx, sy, sz) * 0.45), segments=segments,
                        profile=0.5, affect='EDGES', clamp_overlap=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = segments > 1
    return me

def join_meshes(name, parts):
    """parts: list of (mesh, matrix, material_index). Returns a single mesh (materials by index)."""
    bm = bmesh.new()
    for me, mat, mi in parts:
        tmp = bmesh.new(); tmp.from_mesh(me)
        bmesh.ops.transform(tmp, matrix=mat, verts=tmp.verts)
        for f in tmp.faces: f.material_index = mi
        me2 = bpy.data.meshes.new('_tmp'); tmp.to_mesh(me2); tmp.free()
        bm.from_mesh(me2); bpy.data.meshes.remove(me2)
    out = bpy.data.meshes.new(name); bm.to_mesh(out); bm.free()
    return out

# ------------------------------------------------------------------ node helpers
class NT:
    """Terse node-tree builder."""
    def __init__(self, tree):
        self.t = tree; self.x = 0
    def n(self, type, *inputs, **kw):
        """kw starting lowercase -> node property; Uppercase -> input socket (underscores = spaces)."""
        node = self.t.nodes.new(type)
        for k, v in kw.items():
            if k[0].islower():
                setattr(node, k, v)
        for i, v in enumerate(inputs):
            if v is None: continue
            self.inp(node, i, v)
        for k, v in kw.items():
            if not k[0].islower():
                self.inp(node, k.replace('_', ' '), v)
        return node
    def inp(self, node, key, v):
        sock = node.inputs[key]
        if isinstance(v, bpy.types.NodeSocket):
            self.t.links.new(v, sock)
        elif isinstance(v, bpy.types.Node):
            self.t.links.new(v.outputs[0], sock)
        else:
            try:
                sock.default_value = v
            except (TypeError, ValueError):
                if isinstance(v, (int, float)) and hasattr(sock.default_value, '__len__'):
                    n = len(sock.default_value)
                    sock.default_value = [v] * n if n != 4 else [v, v, v, 1.0]
                elif hasattr(v, '__len__') and len(v) == 3 and len(sock.default_value) == 4:
                    sock.default_value = (*v, 1.0)
                else:
                    raise
    def link(self, a, b):
        self.t.links.new(a, b)
    # math shortcuts
    def math(self, op, a, b=None, c=None, clamp=False):
        m = self.n('ShaderNodeMath', operation=op, use_clamp=clamp) if self.t.bl_idname == 'ShaderNodeTree' else self.n('ShaderNodeMath', operation=op, use_clamp=clamp)
        self.inp(m, 0, a)
        if b is not None: self.inp(m, 1, b)
        if c is not None: self.inp(m, 2, c)
        return m.outputs[0]
    def vmath(self, op, a, b=None, c=None, out=0):
        m = self.n('ShaderNodeVectorMath', operation=op)
        self.inp(m, 0, a)
        if b is not None: self.inp(m, 1, b)
        if c is not None: self.inp(m, 2, c)
        return m.outputs[out]
    def mix(self, fac, a, b, blend='MIX', dtype='RGBA'):
        m = self.n('ShaderNodeMix', data_type=dtype, blend_type=blend)
        if dtype == 'RGBA':
            self.inp(m, 'Factor', fac); self.inp(m, 6, a); self.inp(m, 7, b)
            return m.outputs[2]
        elif dtype == 'FLOAT':
            self.inp(m, 'Factor', fac); self.inp(m, 2, a); self.inp(m, 3, b)
            return m.outputs[0]
        else:
            self.inp(m, 'Factor', fac); self.inp(m, 4, a); self.inp(m, 5, b)
            return m.outputs[1]

def new_material(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    return m, NT(nt)

def principled(nt, **kw):
    """kw keys are Principled BSDF input names with spaces replaced by _ ."""
    b = nt.n('ShaderNodeBsdfPrincipled')
    for k, v in kw.items():
        nt.inp(b, k.replace('_', ' '), v)
    return b

def finish(nt, shader, disp=None):
    out = nt.n('ShaderNodeOutputMaterial', target='ALL')
    nt.link(shader.outputs[0] if isinstance(shader, bpy.types.Node) else shader, out.inputs['Surface'])
    if disp is not None:
        nt.link(disp, out.inputs['Displacement'])
    return out

# ------------------------------------------------------------------ extra builders
def prism_holes(mb, poly, z0, z1, mi=0, **attrs):
    """Extrude a shapely polygon that may contain holes (earcut top/bottom + walls)."""
    polys = [poly] if poly.geom_type == 'Polygon' else [g for g in poly.geoms if g.geom_type == 'Polygon']
    for p in polys:
        p = orient(p, 1.0)
        rings = [list(p.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in p.interiors]
        flat = np.array([c for r in rings for c in r], dtype=np.float64)
        ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
        tri = earcut.triangulate_float64(flat, ends).reshape(-1, 3)
        base_t = len(mb.v)
        for c in flat: mb.v.append((c[0], c[1], z1))
        base_b = len(mb.v)
        for c in flat: mb.v.append((c[0], c[1], z0))
        for t in tri:
            mb.add_face([base_t + int(t[0]), base_t + int(t[1]), base_t + int(t[2])], mi, **attrs)
            mb.add_face([base_b + int(t[2]), base_b + int(t[1]), base_b + int(t[0])], mi, **attrs)
        start = 0
        for r in rings:
            n = len(r)
            for i in range(n):
                a = start + i; b = start + (i + 1) % n
                mb.add_face([base_b + a, base_b + b, base_t + b, base_t + a], mi, **attrs)
            start += n

def rrect(cx, cy, w, h, r, seg=6):
    """rounded rectangle polygon (shapely)"""
    from shapely.geometry import box
    return box(cx - w / 2 + r, cy - h / 2 + r, cx + w / 2 - r, cy + h / 2 - r).buffer(r, quad_segs=seg)

def cylinder_mesh(name, r, h, seg=32, r_top=None, cap=True, smooth=True, z0=0.0):
    r_top = r if r_top is None else r_top
    verts = []; faces = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append((r * math.cos(a), r * math.sin(a), z0))
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append((r_top * math.cos(a), r_top * math.sin(a), z0 + h))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((i, j, seg + j, seg + i))
    if cap:
        faces.append(tuple(range(seg - 1, -1, -1)))
        faces.append(tuple(range(seg, 2 * seg)))
    me = mesh(name, verts, faces)
    if smooth:
        for p in me.polygons: p.use_smooth = len(p.vertices) == 4
    return me

def place(o, loc=(0, 0, 0), rot=(0, 0, 0), scale=None):
    o.location = loc; o.rotation_euler = rot
    if scale is not None: o.scale = scale
    return o

def box_obj(name, x0, y0, z0, x1, y1, z1, mat, collection=None, bevel=0.0, seg=1):
    """Axis-aligned box object with its origin at the box centre (object coords centred)."""
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    me = bevel_box_mesh(name, sx, sy, sz, bevel=bevel, segments=seg, origin_bottom=False) if bevel > 0 else bevel_box_mesh(name, sx, sy, sz, bevel=0, segments=1, origin_bottom=False)
    o = obj(name, me, collection, mat)
    o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    return o

def member(name, p0, p1, w, d, mat, collection=None, up=(0, 0, 1), bevel=0.004):
    """Timber member from p0 to p1 (centre line), width w (horizontal), depth d (vertical-ish).
    Local X runs along the member (grain)."""
    p0 = Vector(p0); p1 = Vector(p1)
    L = (p1 - p0).length
    me = bevel_box_mesh(name, L, w, d, bevel=bevel, segments=1, origin_bottom=False)
    o = obj(name, me, collection, mat)
    x = (p1 - p0).normalized()
    upv = Vector(up)
    y = upv.cross(x)
    if y.length < 1e-6: y = Vector((0, 1, 0)).cross(x)
    y.normalize(); z = x.cross(y)
    M = Matrix((x, y, z)).transposed()
    o.matrix_world = Matrix.Translation((p0 + p1) / 2) @ M.to_4x4()
    return o

def extrude_profile_x(mb, prof, xa, xb, mi=0, cap=True, **attrs):
    """prof: list of (y,z) CCW (seen from +X). Extruded from x=xa to x=xb into MeshBuilder."""
    n = len(prof)
    A = [mb.vert((xa, y, z)) for y, z in prof]
    B = [mb.vert((xb, y, z)) for y, z in prof]
    for i in range(n):
        j = (i + 1) % n
        mb.add_face([A[i], A[j], B[j], B[i]], mi, **attrs)
    if cap:
        mb.add_face(list(reversed(A)), mi, **attrs)
        mb.add_face(B, mi, **attrs)

def obox(mb, center, ax, ay, az, sx, sy, sz, mi=0, **attrs):
    """Oriented box: axes ax, ay, az (unit Vectors) with full sizes sx, sy, sz."""
    c = Vector(center); ax = Vector(ax) * (sx / 2); ay = Vector(ay) * (sy / 2); az = Vector(az) * (sz / 2)
    P = [c - ax - ay - az, c + ax - ay - az, c + ax + ay - az, c - ax + ay - az,
         c - ax - ay + az, c + ax - ay + az, c + ax + ay + az, c - ax + ay + az]
    I = [mb.vert(p) for p in P]
    for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        mb.add_face([I[k] for k in f], mi, **attrs)

def curve_tube(name, pts, radius, mat, collection=None, res=12):
    cd = bpy.data.curves.new(name, 'CURVE'); cd.dimensions = '3D'
    cd.bevel_depth = radius; cd.bevel_resolution = 4; cd.resolution_u = res
    cd.use_fill_caps = True
    sp = cd.splines.new('POLY' if len(pts) == 2 else 'BEZIER')
    if sp.type == 'POLY':
        sp.points.add(len(pts) - 1)
        for p, q in zip(sp.points, pts): p.co = (*q, 1.0)
    else:
        sp.bezier_points.add(len(pts) - 1)
        for bp, q in zip(sp.bezier_points, pts):
            bp.co = q; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, cd)
    (collection or bpy.context.scene.collection).objects.link(o)
    cd.materials.append(mat)
    return o
