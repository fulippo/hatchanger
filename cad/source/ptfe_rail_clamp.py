"""
HatChanger - PTFE rail clamp
============================
One printed piece that holds up to 8 PTFE tubes side by side, VERTICAL (90 deg to the
top face of the extrusion), just outside the frame. Anchored to the top face of a 2020
extrusion (Voron 2.4 frame) with 2x M3 screws into T-nuts.

The foot sits on the extrusion top face; a block overhangs the outer face and carries
one vertical bore per lane. The tubes slide in from the top or the bottom. Each bore has
a short tighter band in the middle (GRIP_D) that holds the tube by friction; set GRIP_D =
BORE_D for a plain sliding fit.

Printed vertical holes come out ~0.1-0.3 mm SMALLER than drawn (printer and slicer
dependent), so the drawn sizes are larger than the tube: BORE_D slides freely, GRIP_D
prints at about the tube size. v1 drew the band at 3.95 mm: it printed ~3.8 and the
tube stuck halfway; v2 (bore 4.40, band 4.10) was still too tight on the prototype printer,
and v3 (4.60 / 4.30) only moved the problem: since v4 there is no band, every bore is a plain
4.50 mm (the tubes are guided, not clamped). To bring a band back, tune it with the test strip:
    python cad/source/ptfe_rail_clamp.py --grip-test
(one bore per GRIP_D in GRIP_TEST, labelled with the hundredths: "10" = 4.10 mm). Use the
largest size that still holds the tube in place by itself (4.60 = no band, plain bore).
The tubes pass OUTSET mm outside the extrusion's outer face, clear of a side panel and
its clips, and continue below the rail (no part of the clamp is below Z=0).

Usage:
    python cad/source/ptfe_rail_clamp.py [--lanes N] [--grip D] [--out DIR]
    python cad/source/ptfe_rail_clamp.py --grip-test [--out DIR]
Outputs STEP and watertight STL to ./out. The STL is in print orientation, which is
also the mounting orientation: foot on the bed, bores vertical.

Coordinates: X = along extrusion, Y = into the frame (outer face of the extrusion at
Y = -10), Z = up, Z = 0 = extrusion top face. Tubes are parallel to Z.
"""
import cadquery as cq

# ---------------- parameters ----------------
LANES        = 8      # number of tubes (1..8 tested)
PTFE_OD      = 4.0    # PTFE outer diameter
PITCH        = 7.0    # lane spacing (centre to centre)
BORE_D       = 4.50   # plain bore, the same over the whole height (drawn; prints ~4.2-4.3)
GRIP_D       = BORE_D # friction band in the middle of each bore: OFF since v4 (= BORE_D).
                      #   = BORE_D to disable. Tune with --grip-test
GRIP_TEST    = [4.10, 4.20, 4.30, 4.40, 4.50, 4.60]   # band sizes on the test strip
GRIP_BAND    = 4.0    # length of the friction band
HEIGHT       = 20.0   # block height above the rail (guided length of tube)
OUTSET       = 5.0    # extrusion outer face -> tube wall (room for a 3 mm panel + clips)
WALL         = 2.4    # material outside the tube
FOOT_T       = 4.0    # foot thickness on top of the extrusion
FOOT_IN      = 10.0   # foot reaches to Y = +10 (full 2020 width)
BLOCK_BACK   = -5.0   # block spans from its outer face to this Y (over the rail)
SCREW_GAP    = 5.0    # last tube wall -> screw centre
END_MARGIN   = 4.5    # screw centre -> part end
M3_CLEAR     = 3.4
ENTRY_CHAMF  = 0.8    # chamfer on the bore mouths

LABELS       = True
LABEL_SIZE   = 3.2
LABEL_DEPTH  = 0.4

# ---------------- derived ----------------
R        = PTFE_OD / 2
TUBE_Y   = -10 - OUTSET - R          # tube axis
OUT_Y    = TUBE_Y - R - WALL         # outer face of the block


def set_lanes(n):
    global LANES, array_half, screw_x, LENGTH, lane_xs
    LANES = n
    array_half = (LANES - 1) * PITCH / 2
    screw_x = array_half + R + SCREW_GAP
    LENGTH = 2 * (screw_x + END_MARGIN)
    lane_xs = [-array_half + i * PITCH for i in range(LANES)]


set_lanes(LANES)


def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY", origin=((x0 + x1) / 2, (y0 + y1) / 2, z0))
            .box(x1 - x0, y1 - y0, z1 - z0, centered=(True, True, False)))


def bore_cutter(bores=None, height=None):
    """Vertical bores: sliding fit, friction band in the middle, chamfered mouths.
    bores: [(x, grip_d)], default one per lane at GRIP_D."""
    if bores is None:
        bores = [(x, GRIP_D) for x in lane_xs]
    HEIGHT_ = HEIGHT if height is None else height
    rb = BORE_D / 2
    zg0 = (HEIGHT_ - GRIP_BAND) / 2
    solid = None
    for x, grip in bores:
        rg = min(grip, BORE_D) / 2
        lower = cq.Workplane("XY").center(x, TUBE_Y).circle(rb).extrude(zg0)
        band = (cq.Workplane("XY", origin=(0, 0, zg0)).center(x, TUBE_Y)
                .circle(rg).extrude(GRIP_BAND))
        upper = (cq.Workplane("XY", origin=(0, 0, zg0 + GRIP_BAND)).center(x, TUBE_Y)
                 .circle(rb).extrude(HEIGHT_ - zg0 - GRIP_BAND))
        bore = lower.union(band).union(upper)
        if rg < rb:   # 45 deg steps into the band so the tube end doesn't catch
            for z0, d in ((zg0, 1), (zg0 + GRIP_BAND, -1)):
                c = cq.Solid.makeCone(rb, rg, rb - rg, cq.Vector(x, TUBE_Y, z0),
                                      cq.Vector(0, 0, d))
                bore = bore.union(cq.Workplane().add(c))
        for z0, d in ((0, 1), (HEIGHT_, -1)):
            c = cq.Solid.makeCone(rb + ENTRY_CHAMF, rb, ENTRY_CHAMF,
                                  cq.Vector(x, TUBE_Y, z0), cq.Vector(0, 0, d))
            bore = bore.union(cq.Workplane().add(c))
        solid = bore if solid is None else solid.union(bore)
    return solid


def make_clamp():
    L2 = LENGTH / 2
    foot = box(-L2, L2, OUT_Y, FOOT_IN, 0, FOOT_T)
    block = box(-L2, L2, OUT_Y, BLOCK_BACK, 0, HEIGHT)
    part = foot.union(block).edges("|Z").fillet(1.5)
    # 45 deg gusset between foot and block on the inner side
    gusset = (cq.Workplane("YZ", origin=(-L2, 0, 0))
              .polyline([(BLOCK_BACK, FOOT_T), (BLOCK_BACK + 4, FOOT_T),
                         (BLOCK_BACK, FOOT_T + 4)])
              .close().extrude(LENGTH))
    part = part.union(gusset)
    part = part.cut(bore_cutter())
    frame = (cq.Workplane("XY", origin=(0, 0, -1))
             .pushPoints([(-screw_x, 0), (screw_x, 0)])
             .circle(M3_CLEAR / 2).extrude(FOOT_T + 2))
    part = part.cut(frame)
    if LABELS:
        # lane numbers on the top face, inboard of each bore
        y_lab = (TUBE_Y + BORE_D / 2 + ENTRY_CHAMF + BLOCK_BACK) / 2
        for i, x in enumerate(lane_xs):
            wp = cq.Workplane("XY", origin=(x, y_lab, HEIGHT - LABEL_DEPTH))
            part = part.cut(wp.text(str(i + 1), LABEL_SIZE, LABEL_DEPTH + 1, kind="bold",
                                    halign="center", valign="center"))
    return part


def make_grip_test():
    """Short strip with one bore per GRIP_TEST size, labelled with the hundredths."""
    h, pitch, margin = 12.0, 8.0, 4.0
    n = len(GRIP_TEST)
    xs = [(i - (n - 1) / 2) * pitch for i in range(n)]
    L2 = (n - 1) * pitch / 2 + margin
    y0, y1 = -R - WALL, R + WALL + 5.0
    part = box(-L2, L2, y0, y1, 0, h).edges("|Z").fillet(1.0)
    global TUBE_Y
    keep, TUBE_Y = TUBE_Y, 0.0
    try:
        part = part.cut(bore_cutter([(x, d) for x, d in zip(xs, GRIP_TEST)], height=h))
    finally:
        TUBE_Y = keep
    for x, d in zip(xs, GRIP_TEST):
        wp = cq.Workplane("XY", origin=(x, R + WALL / 2 + 2.6, h - LABEL_DEPTH))
        part = part.cut(wp.text(f"{round(d * 100) % 100:02d}", 2.6, LABEL_DEPTH + 1,
                                kind="bold", halign="center", valign="center"))
    return part


def export(part, out, name):
    import os
    os.makedirs(out, exist_ok=True)
    step = os.path.join(out, f"{name}.step")
    stl = os.path.join(out, f"{name}.stl")
    cq.exporters.export(part, step)
    cq.exporters.export(part, stl, tolerance=0.01, angularTolerance=0.1)
    try:
        import trimesh
        t = trimesh.load(stl)
        t.merge_vertices(); t.export(stl)
        if not t.is_watertight:
            print(f"WARNING: {stl} is not watertight")
    except ImportError:
        print("trimesh not installed: STL written without the final clean-up")


def build(out, lanes):
    set_lanes(lanes)
    tag = "" if LANES == 8 else f"_{LANES}x"
    clamp = make_clamp()
    export(clamp, out, f"ptfe_rail_clamp{tag}")
    print(f"lanes={LANES} length={LENGTH:.1f} height above rail={HEIGHT} "
          f"tube axis {-TUBE_Y - 10:.1f} mm outside the extrusion face, "
          f"overhang {-OUT_Y - 10:.1f} mm, screw spacing={2*screw_x:.1f}")
    return clamp


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--lanes", type=int, default=LANES)
    ap.add_argument("--grip", type=float, default=GRIP_D, help="friction band diameter")
    ap.add_argument("--grip-test", action="store_true", help="build the GRIP_D test strip")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    GRIP_D = a.grip
    if a.grip_test:
        export(make_grip_test(), a.out, "ptfe_grip_test")
        print("grip test: bores " + ", ".join(f"{d:.2f}" for d in GRIP_TEST))
    else:
        build(a.out, a.lanes)
