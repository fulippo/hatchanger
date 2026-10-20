"""
HatChanger top hat: a raised canopy wall for a heated chamber (Voron 2.4 250 / 300 / 350).

The wall stands on the top extrusions with the same 20 mm footprint, so its top is a printed
"2020": top face 20 mm wide with a T-slot on top, one on the outer face and one on the inner face
(roll-in / spring T-nuts: panel clips, LED bars, tube guides... clamp on it as on the frame). The
stock top panel sits on it.

Pieces (each fits a 250 bed or larger), separated by FOAM_GAP for closed-cell foam strips:
  tophat_<size>_corner        x4  L, ARM x ARM
  tophat_<size>_centre        x2  left / right side
  tophat_<size>_centre_front  x1  "HatChanger" plaque
  tophat_<size>_centre_rear   x1  bowden exits (8 holes, TPU grommets)
  tophat_grommet_tpu / tophat_plug_tpu   (all sizes)

  python3 cad/tophat/source/tophat.py                    # every size, both patterns
  python3 cad/tophat/source/tophat.py --size 300         # one size
  python3 cad/tophat/source/tophat.py --pattern voronoi  # voronoi panels (files *_voronoi)
  -> cad/tophat/stl/<size>/, cad/tophat/step/<size>/ (grommet and plug in cad/tophat/stl/, step/)
Each piece is screwed to the frame's top slot (M3 x 10 + roll-in T-nut) through its foot: the
screw sits in a counterbore that opens into the outer tray, reached with the short arm of an L-key.

Frame: x, y = 0 on the frame centre, front outer edge y = -F/2 (-230 on a 300); z = 0 on top of the extrusions.
"""
import argparse, math
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import cadquery as cq
from shapely.geometry import Polygon, box as sbox, Point
from shapely.ops import unary_union


@dataclass
class C:
    size: int = 300             # Voron 2.4 build size: 250, 300, 350
    W: float = 20.0             # wall = extrusion width
    H: float = 85.0             # height (the panel sits on top): tube arcs peak at ~60
    ARM: float = 120.0          # corner arm length from the outer corner
    FOAM_GAP: float = 2.5       # gap between pieces for a foam strip
    top_chamfer: float = 1.0
    corner_chamfer: float = 2.0
    # printed 2020 slots (top band = the top 20 mm)
    slot_open: float = 6.2
    slot_lip: float = 1.8
    slot_cav: float = 11.0
    slot_depth: float = 6.1
    # frame screws
    screw_d: float = 3.4
    counterbore_d: float = 6.5  # M3 head; the counterbore opens into the tray (L-key from outside)
    floor: float = 5.0
    corner_screw: float = 60.0  # from the outer corner, on each arm
    centre_screw: float = 15.0  # from each end of a centre (clear of the front letters)
    # outer panel
    corner_border: float = 20.0 # plain column at the corners (the vertical extrusion's footprint)
    panel_z0: float = 7.0
    panel_gap_top: float = 4.0  # below the top band
    panel_r: float = 3.0
    panel_depth: float = 14.0   # the panel is a tray in the outer face (rib tops): the wall is
                                #   hollowed from the outside like the canopy, the inner side
                                #   stays flat. Centres print lying on it; the corners print
                                #   upright, the tray's roof slopes at 45°
    cell_depth: float = 2.5     # honeycomb cells in the tray floor: 3.5 mm skin behind them
    fillet_top: float = 12.0    # tray floor -> top band: brace for the skin
    fillet_bottom: float = 8.0  # tray floor -> foot
    pitch: float = 22.0         # hex pitch
    rib: float = 3.0
    pattern: str = "hex"        # hex | voronoi
    # front plaque
    text: str = "HatChanger"
    font: str = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
    text_h: float = 22.0
    text_relief: float = 4.0    # letters stand this far off the tray floor
    # rear bowden exits
    hole_d: float = 12.0
    hole_cols: tuple = (-36.0, -12.0, 12.0, 36.0)
    hole_rows: tuple = (35.0, 51.0)

    @property
    def F(self): return self.size + 160.0     # frame outer size: horizontals (size + 120) + 2 x 20
    @property
    def h(self): return self.F / 2
    @property
    def LC(self): return self.F - 2 * self.ARM - 2 * self.FOAM_GAP
    @property
    def panel_z1(self): return self.H - self.W - self.panel_gap_top


def slot_poly(c: C):
    """2020 slot section: (u across the opening, d depth from the surface)."""
    o, l, cav, d = c.slot_open / 2, c.slot_lip, c.slot_cav / 2, c.slot_depth
    b = cav - (d - l - 1.2)
    return [(-o, -1), (o, -1), (o, l), (cav, l), (cav, l + 1.2), (b, d), (-b, d), (-cav, l + 1.2), (-cav, l), (-o, l)]


def prism_x(pts_yz, x0, x1):
    """Extrude a polygon given in (y, z) along x from x0 to x1."""
    w = cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts_yz).close().extrude(x1 - x0)
    return w.val()


def slots_front(c: C, x0, x1, top_from=None, inner_from=None, outer_from=None, breaks=()):
    """Cutters for the three slots of a front-side wall between x0 and x1 (outer face y = -h)."""
    h, H, W = c.h, c.H, c.W
    sp = slot_poly(c)
    yc, zc = -h + W / 2, H - W / 2
    top = [(yc + u, H - d) for u, d in sp]
    outer = [(-h + d, zc + u) for u, d in sp]
    inner = [(-h + W - d, zc + u) for u, d in sp]
    cuts = [prism_x(top, top_from if top_from is not None else x0 - 1, x1 + 1)]
    def segs(a, b):
        out, s = [], a
        for x in sorted(breaks):
            out.append((s, x - 6)); s = x + 6
        out.append((s, b)); return [(p, q) for p, q in out if q > p]
    for poly, start in ((outer, outer_from), (inner, inner_from)):
        for p, q in segs(start if start is not None else x0 - 1, x1 + 1):
            cuts.append(prism_x(poly, p, q))
    return cuts


def screws_front(c: C, xs):
    """Frame screws: a hole through the foot (floor thick) and a counterbore from above that opens
    into the tray, so the head is reached from outside with an L-key."""
    h, W = c.h, c.W
    out = []
    for x in xs:
        out.append(cq.Solid.makeCylinder(c.screw_d / 2, c.floor + 2, cq.Vector(x, -h + W / 2, -1)))
        out.append(cq.Solid.makeCylinder(c.counterbore_d / 2, c.panel_z0 + c.fillet_bottom, cq.Vector(x, -h + W / 2, c.floor)))
    return out


def xz_prism(poly: Polygon, y_out, y_in):
    """Polygon in (x, z) on the outer face, cut from y_out (outside) to y_in."""
    pts = list(poly.exterior.coords)[:-1]
    w = cq.Workplane("XZ", origin=(0, y_in, 0)).polyline(pts).close().extrude(y_in - y_out)
    s = w.val()
    for hole in poly.interiors:
        hw = cq.Workplane("XZ", origin=(0, y_in, 0)).polyline(list(hole.coords)[:-1]).close().extrude(y_in - y_out)
        s = s.cut(hw.val())
    return s


def rrect(x0, x1, z0, z1, r):
    return sbox(x0 + r, z0 + r, x1 - r, z1 - r).buffer(r, resolution=8)


def cells(c: C, x0, x1, z0, z1, keep_out=None, seed=1, open_ends=(False, False)):
    """Pocket polygons for a panel (x0..x1, z0..z1) on the outer face. The pattern is the same
    for every piece of a side: centred on the side (x = 0) and mirror-symmetric, so it runs on
    across the joints (open_ends: the panel runs out through that end of the piece) and all the
    corners are the same part."""
    inner = sbox(x0 - 1 if open_ends[0] else x0 + c.rib, z0 + c.rib,
                 x1 + 1 if open_ends[1] else x1 - c.rib, z1 - c.rib)
    xm, zm = 0.0, (z0 + z1) / 2
    p = c.pitch
    rp = p * math.sqrt(3) / 2
    if c.pattern == "hex":
        r = (p - c.rib) / math.sqrt(3)
        polys = []
        for j in range(-4, 5):
            for k in range(-20, 21):
                cx = xm + k * p + (p / 2 if j % 2 else 0); cz = zm + j * rp
                hx = Polygon([(cx + r * math.cos(math.radians(90 + 60 * q)), cz + r * math.sin(math.radians(90 + 60 * q)))
                              for q in range(6)])
                polys.append(hx)
    else:
        from scipy.spatial import Voronoi
        rng = np.random.default_rng(seed)
        pts = []
        for j in range(-6, 7):
            for k in range(0, 25):                 # one half, mirrored: symmetric about x = 0
                cx = k * p + (p / 2 if j % 2 else 0); cz = zm + j * rp
                dx, dz = rng.uniform(-0.28, 0.28) * p, rng.uniform(-0.28, 0.28) * rp
                if cx == 0:
                    pts.append((0.0, cz + dz))
                else:
                    pts += [(cx + dx, cz + dz), (-(cx + dx), cz + dz)]
        pts = np.array(pts)
        vor = Voronoi(pts)
        polys = []
        for i, reg in enumerate(vor.point_region):
            rv = vor.regions[reg]
            if -1 in rv or not rv:
                continue
            cell = Polygon(vor.vertices[rv])
            if cell.is_valid and cell.area > 1:
                polys.append(cell.buffer(-c.rib / 2 - 1.2, join_style=2).buffer(1.2, resolution=6))
    out = []
    for hx in polys:
        q = hx.intersection(inner)
        if keep_out is not None:
            q = q.difference(keep_out)
        for g in getattr(q, "geoms", [q]):
            if not g.is_empty and g.geom_type == "Polygon" and g.area > 10:
                b = g.bounds                        # a cell cut by a joint: keep it whatever its width
                at_end = (open_ends[0] and b[0] < x0 + 0.01) or (open_ends[1] and b[2] > x1 - 0.01)
                if not at_end:
                    g = g.buffer(-0.6).buffer(0.6, resolution=4)   # no knife edges where a cell is clipped
                if not g.is_empty and g.geom_type == "Polygon" and g.area > 2 and \
                        (at_end or not g.buffer(-3.0).is_empty):  # (no slivers narrower than 6 mm)
                    out.append(g)
    return out


def tray_section(c: C):
    """(y, z) outline of the tray: flat floor, fillets up to the top band and down to the foot."""
    h = c.h
    yo, yf = -h - 1, -h + c.panel_depth
    z0, z1, rt, rb = c.panel_z0, c.panel_z1, c.fillet_top, c.fillet_bottom
    pts = [(yo, z1), (yf - rt, z1)]
    pts += [(yf - rt + rt * math.sin(a), z1 - rt + rt * math.cos(a))
            for a in np.linspace(0, math.pi / 2, 13)[1:]]
    pts += [(yf - rb + rb * math.cos(a), z0 + rb - rb * math.sin(a))
            for a in np.linspace(0, math.pi / 2, 9)[:-1]]
    pts += [(yf - rb, z0), (yo, z0)]
    return pts


def tray_pocket(c: C, g: Polygon, roof=False):
    """The tray: the polygon (x, z) cut to the filleted section, or (roof) also ∩ the polygon
    swept inwards and down at 45°, so its roof slopes down at 45° from the outer face
    (printable upright). g must be convex in z (it is: rectangles, rounded rectangles)."""
    h = c.h
    y0, y1 = -h - 1, -h + c.panel_depth
    b = g.bounds
    straight = xz_prism(g, y0, y1).intersect(prism_x(tray_section(c), b[0] - 1, b[2] + 1))
    if not roof:
        return straight
    lift = 1                                       # the roof starts sloping at the outer face
    pts = [cq.Vector(x, y0, z + lift) for x, z in list(g.exterior.coords)[:-1]]
    face = cq.Face.makeFromWires(cq.Wire.makePolygon(pts, close=True))
    L = y1 - y0
    oblique = cq.Solid.extrudeLinear(face, cq.Vector(0, L, -L))
    return straight.intersect(oblique)


def panel_front(c: C, x0, x1, keep_out=None, seed=1, roof=False, solid=None, open_ends=(True, True)):
    """Cutters for a patterned panel on the outer face of a front-side wall between x0 and x1.
    open_ends: the tray runs out through that end (a joint) instead of stopping at a border."""
    h = c.h
    z0, z1 = c.panel_z0, c.panel_z1
    ext = 3 * c.panel_r
    tray = rrect(x0 - (ext if open_ends[0] else 0), x1 + (ext if open_ends[1] else 0), z0, z1, c.panel_r)
    tray = tray.intersection(sbox(x0 - 1, z0 - 1, x1 + 1, z1 + 1))   # keep_out clears the cells, solid the tray
    if solid is not None:
        tray = tray.difference(solid)
    tools = []
    for g in getattr(tray, "geoms", [tray]):
        if g.geom_type == "Polygon" and g.area > 20:
            tools.append(tray_pocket(c, g, roof))
    # honeycomb on the flat floor only (the fillets stay whole)
    for g in cells(c, x0, x1, z0 + c.fillet_bottom - c.rib, z1 - c.fillet_top + c.rib, keep_out, seed, open_ends):
        tools.append(xz_prism(g, -h - 1, -h + c.panel_depth + c.cell_depth))
    return tools


def mirror_diag(s):
    """x <-> y (front arm -> left arm)."""
    return s.mirror(cq.Vector(1, -1, 0), cq.Vector(0, 0, 0))


def body(c: C, footprint):
    s = cq.Workplane("XY").polyline(footprint).close().extrude(c.H)
    s = s.edges(">Z").chamfer(c.top_chamfer)
    return s.val()


def cut_all(s, tools):
    for t in tools:
        s = s.cut(t)
    return s.clean()


def corner(c: C):
    """Front-left corner, both arms."""
    h, W, A, k = c.h, c.W, c.ARM, c.corner_chamfer
    fp = [(-h + k, -h), (-h + A, -h), (-h + A, -h + W), (-h + W, -h + W), (-h + W, -h + A), (-h, -h + A), (-h, -h + k)]
    s = body(c, fp)
    xs = -h + c.corner_screw
    arm = slots_front(c, -h, -h + A, top_from=-h + W / 2 - c.slot_cav / 2, inner_from=-h + W - c.slot_depth,
                      outer_from=-h - 1)
    arm += screws_front(c, (xs,))
    arm += panel_front(c, -h + c.corner_border, -h + A, roof=True, open_ends=(False, True))
    tools = arm + [mirror_diag(t) for t in arm]
    return cut_all(s, tools)


def centre(c: C, kind="plain"):
    h, W, L = c.h, c.W, c.LC
    fp = [(-L / 2, -h), (L / 2, -h), (L / 2, -h + W), (-L / 2, -h + W)]
    s = body(c, fp)
    xs = (-L / 2 + c.centre_screw, L / 2 - c.centre_screw)
    tools = slots_front(c, -L / 2, L / 2) + screws_front(c, xs)
    keep, extra, add = None, [], []
    x0, x1 = -L / 2, L / 2
    post = []                                      # cut after the bosses are added
    if kind == "front":
        # letters standing on the tray floor
        yt, dt = -h + c.panel_depth + 0.3, c.text_relief + 0.3
        txt = (cq.Workplane("XZ", origin=(0, yt, 0))
               .text(c.text, c.text_h, dt, fontPath=c.font, halign="center", valign="center"))
        tb = txt.val().BoundingBox()
        room = (x1 - x0) - 2 * c.rib - 12 - 8          # margins + at least a rib each side
        if tb.xlen > room:                              # short centre (250): smaller letters
            txt = (cq.Workplane("XZ", origin=(0, yt, 0))
                   .text(c.text, c.text_h * room / tb.xlen, dt, fontPath=c.font,
                         halign="center", valign="center"))
            tb = txt.val().BoundingBox()
        zc = (c.panel_z0 + c.panel_z1) / 2
        txt = txt.translate((0, 0, zc - (tb.zmin + tb.zmax) / 2))
        tb = txt.val().BoundingBox()
        keep = rrect(tb.xmin - 6, tb.xmax + 6, c.panel_z0, c.panel_z1, 2.0)   # no cells behind the text
        add.append(txt.val())
    if kind == "rear":
        # full-depth bosses: the grommets need the whole 20 mm
        zs, xs_h = c.hole_rows, c.hole_cols
        rb = c.hole_d / 2 + 4.5                   # (not tangent to the tray edge at z 61)
        keep = unary_union([Point(x, z).buffer(rb + c.rib) for z in zs for x in xs_h])
        bosses = unary_union([Point(x, z).buffer(rb, resolution=16) for z in zs for x in xs_h])
        for z in zs:
            for x in xs_h:
                hole = cq.Solid.makeCylinder(c.hole_d / 2, W + 2, cq.Vector(x, -h - 1, z), cq.Vector(0, 1, 0))
                mouth = cq.Solid.makeCone(c.hole_d / 2 + 1.2, c.hole_d / 2, 1.2,
                                          cq.Vector(x, -h - 0.01, z), cq.Vector(0, 1, 0))
                for t_ in (hole, mouth):           # turn the seam away from the mesh's other edges
                    post.append(t_.rotate(cq.Vector(x, 0, z), cq.Vector(x, 1, z), 37))
    tools += panel_front(c, x0, x1, keep, solid=bosses if kind == "rear" else None) + extra
    s = cut_all(s, tools)
    if add:
        s = s.fuse(*add, glue=False).clean()
    return cut_all(s, post)


def grommet(c: C, plug=False):
    L = c.W + 0.4
    g = (cq.Workplane("XY").circle(c.hole_d / 2).extrude(L)
         .union(cq.Workplane("XY").circle(c.hole_d / 2 + 2.5).extrude(1.6))
         .union(cq.Workplane("XY").workplane(offset=L).circle(c.hole_d / 2 + 0.7)
                .workplane(offset=1.4).circle(c.hole_d / 2 - 0.2).loft()))
    if not plug:
        g = g.cut(cq.Workplane("XY").workplane(offset=-1).circle(2.15).extrude(L + 5))
        g = g.union(cq.Workplane("XY").workplane(offset=0.4).circle(2.15).circle(1.9).extrude(0.8))
        for a in (0, 90):
            g = g.cut(cq.Workplane("XY").box(1.2, 30, 5).translate((0, 0, L + 0.6)).rotate((0, 0, 0), (0, 0, 1), a))
    else:
        g = g.cut(cq.Workplane("XY").workplane(offset=3).circle(c.hole_d / 2 - 1.6).extrude(L))   # hollow, squeezes in
    return g.val()


def rotz(s, a):
    return s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), a)


def pieces(c: C):
    return {"tophat_corner": corner(c), "tophat_centre": centre(c), "tophat_centre_front": centre(c, "front"),
            "tophat_centre_rear": centre(c, "rear"), "tophat_grommet_tpu": grommet(c), "tophat_plug_tpu": grommet(c, True)}


def assembly(p):
    """(shape, role) in place."""
    out = [(rotz(p["tophat_corner"], a), "corner") for a in (0, 90, 180, 270)]
    out += [(p["tophat_centre_front"], "front"), (rotz(p["tophat_centre_rear"], 180), "rear"),
            (rotz(p["tophat_centre"], 90), "side"), (rotz(p["tophat_centre"], 270), "side")]
    return out


def to_print(s, lay_flat=False):
    """Place a piece on the bed at the origin as printed: bottom down, or (lay_flat, the
    straight centres) lying on its flat inner face with the pattern up."""
    if lay_flat:
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90)
    b = s.BoundingBox()
    return s.moved(cq.Location(cq.Vector(-(b.xmin + b.xmax) / 2, -(b.ymin + b.ymax) / 2, -b.zmin)))


def export(c: C, stl_dir: Path, step_dir: Path, grommets=True):
    """Walls into <dir>/<size>/, grommet and plug into <dir>/."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hatchanger" / "source"))
    from hatchanger_cad import export_stl
    for d in (stl_dir, step_dir):
        (d / str(c.size)).mkdir(parents=True, exist_ok=True)
    suffix = "" if c.pattern == "hex" else f"_{c.pattern}"
    p = {}
    for n, s in pieces(c).items():
        if "tpu" in n:                 # the same for every size
            if grommets:
                p[n] = s
        else:
            p[n.replace("tophat_", f"tophat_{c.size}_") + suffix] = s
    for n, s in p.items():
        s2 = to_print(s, lay_flat="centre" in n)
        sub = "" if "tpu" in n else str(c.size)
        cq.exporters.export(cq.Workplane("XY").add(s2), str(step_dir / sub / f"{n}.step"))
        export_stl(s2, stl_dir / sub / f"{n}.stl", deflection=0.03)
        b = s2.BoundingBox()
        print(f"{n}: {b.xlen:.1f} x {b.ylen:.1f} x {b.zlen:.1f} mm, {s2.Volume() / 1000:.0f} cm3, valid {s2.isValid()}, "
              f"solids {len(s2.Solids())}")
    return p


SIZES = (250, 300, 350)

if __name__ == "__main__":
    here = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Build the HatChanger top hat (canopy walls + grommets)")
    ap.add_argument("--stl", default=str(here / "stl"))
    ap.add_argument("--step", default=str(here / "step"))
    ap.add_argument("--size", type=int, choices=SIZES, help="one build size (default: all)")
    ap.add_argument("--pattern", choices=["hex", "voronoi"], help="one pattern (default: both)")
    ap.add_argument("--height", type=float, default=C.H, help="wall height above the frame (mm)")
    a = ap.parse_args()
    first = True
    for size in ([a.size] if a.size else SIZES):
        for pattern in ([a.pattern] if a.pattern else ("hex", "voronoi")):
            c = C(size=size, pattern=pattern, H=a.height)
            print(f"--- {size} {pattern}: frame {c.F:g}, centre length {c.LC:.1f}, height {c.H:g}")
            export(c, Path(a.stl), Path(a.step), grommets=first)
            first = False
