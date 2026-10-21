"""
HatChanger v0.42, filament-cutter variant (FilamATrix), Galileo 2 (G2E) integration.

Parts
  front_body_hatchanger : the FilamATrix G2E front body (cutter insert, after-gears sensor, arm
                   clearance) with our top: raised flat interface pad, 2 dowel pins beside the
                   filament hole, 2 magnets at the front, cone socket
                   for the stinger, pocket for the pin half of the magnetic pogo connector (hat ID). Stock G2E board mount (any board that fits it).
  hat            : ECAS04 on top, continuous 4x2 bowden through it (the stinger), V-ridge rails
                   with a tapered nose, pad half of the pogo connector + ID resistor; locates on
                   the dowels.
  stinger_gauge  : jig that sets how far the bowden sticks out of the hat.
  hat_rack       : V-channel dock (lower + upper 45 deg lips) bolted to the top extrusion.
  hat_rack_spacer_<L> : optional block between rack and extrusion, moves the rack L mm towards
                   the chamber centre (12 and 17 mm, for M3x20 / M3x25 screws).

Frames
  G2E STEP frame : as in "Galileo 2 Extruder.step" (Z up, +Y towards the motor/rear).
                   Filament axis = (0, 0.4). front_body_hatchanger is exported in this frame so it
                   drops straight into the G2E / Stealthburner assembly.
  part frame     : cartridge + dock: origin on the filament axis at the interface plane.

Numbers extracted from the G2E STEP (front_body):
  nip (16 mm drive gear / MR115 idler contact line) ....... z = 100.25
  upper 2.1 guide ......................................... z = 102.7 .. 108.7
  cone into PTFE seat ..................................... z = 108.7 .. 109.8
  PTFE seat 4.3 (friction fit), stock top .................. z = 109.8 .. 129.7
  body top at the axis (5 deg sloped face) ................. z ~ 129.9
  cable_cover top (x >= 11.7, y 0..13) ..................... z = 130.3
  cable_chain anchor (y >= 12.6) ........................... z <= 132.3
"""
from dataclasses import dataclass, replace
from pathlib import Path
import math
import cadquery as cq

AXIS_Y = 0.4          # filament axis Y in the G2E STEP frame
NIP_Z = 100.25
SEAT_BOTTOM_Z = 109.82


@dataclass
class P:
    # ---- interface ----------------------------------------------------------------------
    z_if: float = 130.8            # interface plane in G2E frame (just above the sloped top)
    pad_x: float = 11.2            # pad half-width (cable_cover starts at x = 11.7)
    pad_y0: float = -7.4           # pad Y range in G2E frame (chain anchor starts at 12.6)
    pad_y1: float = 12.0
    pad_depth: float = 2.5         # how far the pad block reaches into the stock body
    seat_d: float = 4.6            # stinger must slide freely; horizontal hole in print (body lies on its back)
    seat_cone_d: float = 8.4       # funnel mouth: catches a filament tip up to ~4 mm off-axis
    seat_cone_h: float = 4.0       # funnel depth (~25 deg half-angle: tips slide in, don't stub)
    seat_exit_angle: float = 20.0  # half-angle of the lead-in from the seat into the stock 2.1 hole
                                   # (stock: 45 deg). 20 keeps 0.8 mm to the gear pockets; <18 breaks in
    magnet_d: float = 6.0          # 6x3, SH/UH grade
    magnet_h: float = 3.0
    magnet_fit: float = 0.1
    magnet_xy: tuple = (7.0, -4.0) # (+-x, y) rel. filament axis. v0.34 (pogo): at the FRONT, where the
                                   #   dowels were: ~15 mm of lever about the hat's back edge, the one it
                                   #   tips about when a steep bowden pulls. No wires: the ID is on the pogo.
                                   #   (v0.30-v0.33: (7, 5), at the back, as the ID contacts:
                                   #   reach them from the cable side and the hat can hold the ID resistor
    # hat ID: the two interface magnet pairs are the contacts (nickel plating), a resistor in the hat
    # bridges its two magnets, the head reads it through its two magnets
    id_contacts: bool = True
    head_wire_gap: float = 0.5     # head magnet pockets this much deeper than the magnet: room for the
                                   #   stripped wire end (26-30 AWG, flattened) under the magnet
    hat_wire_gap: float = 0.7      # hat magnet pockets: room for the resistor lead (0.6 mm on 1/4 W).
                                   #   Every magnet is glued FLUSH with the face (pressed against a flat
                                   #   plate while the glue sets) so the faces touch across the interface
    # wire channel in the front body: runs BEHIND the two magnet pockets (not under them) from -X to
    # the +X side of the pad, opens into each pocket only through a small notch at the floor (the
    # wire end is laid under the magnet from there), and exits on the +X
    # side (behind the cable cover) with the same section
    head_wire_y: float = 9.0       # channel centre, y rel. axis (pockets reach 8.05)
    head_wire_w: float = 2.4
    head_wire_z: tuple = (-3.6, -1.4)  # z range rel. interface plane (1.4 mm roof under the face)
    head_wire_notch: float = 2.0   # notch into each pocket: width (x), floor to 0.6 above it
    id_slot_x: float = 6.5         # resistor slot in the hat: open on the back face, ABOVE the magnet
    id_slot_y0: float = 3.4        #   pockets (their walls stay whole), x +-id_slot_x, from y0 to the
    id_slot_z: tuple = (4.3, 6.8)  #   back face; 1/4 W axial resistor: body ~2.3 x 6.3
    id_lead_d: float = 1.0         # lead slit width: one per magnet pocket, from the slot down through the
    id_lead_x: float = 5.6         #   pocket, open at the back and bottom faces, at this |x|
    # hat ID through a 2-pin MAGNETIC pogo connector (v0.33): pin half in the head, pad half in the
    # hat, behind the cone socket, long axis along X. Its own magnets replace the two 6x3 interface
    # magnets (and their pockets, wire channel, resistor slot); the hat's resistor is soldered to the
    # pad half's tails. False = v0.32: the magnets are the contacts (id_contacts); also set
    # magnet_xy = (7, 5) and pin_xy = (7, -4) for that layout.
    pogo: bool = True
    pogo_l: float = 18.32          # connector length WITH its mounting ears (kept: glue area, and
                                   #   the pocket is cut full length so the ears can sit anywhere in Z)
    pogo_body_l: float = 15.4      # body length without the ears
    pogo_w: float = 4.05           # body width (Y)
    pogo_h: float = 4.13           # body height, face to back (without pins / tails)
    pogo_tail: float = 1.4         # solder tails below the back
    pogo_pitch: float = 2.54       # 2 pins, +-pitch/2 about the centre
    pogo_clear: float = 0.2        # pocket clearance per side (X, Y). v0.35: 0.2 (0.1 was too tight with
                                   #   the slicer seam on the hat's vertical pocket walls)
    pogo_recess: float = 0.1       # pocket floor this much deeper than the body height. The connector
                                   #   rests on its ears (pogo_ear_z), not on the floor, so this only
                                   #   keeps the body and the lip round its magnets clear of it
    # ear screws: Ø1.6 holes in the ears, 1.5 mm in from each ear tip. The ears are taken to be flush
    # with the back of the body, so they rest on the pocket floor and the pilot starts there.
    pogo_ear_hole_inset: float = 1.5   # hole centre from the ear's outer end. The ear ends are round,
                                       #   concentric with the hole: ear width = 2 x this
    pogo_screw_pilot: float = 1.2      # self-tapping M1.4 (PA/PB 1.4) into the print
    pogo_screw_depth: float = 4.0      # pilot depth below the pocket floor -> M1.4 x 5
    pogo_head_screws: tuple = (-1, 1)  # head: both ears (v0.40). Hat: both sides
    pogo_head_screw_depth_px: float = 1.7  # head +X pilot: short, the bore for the rear body's M3x50 is ~1.9 below
                                           #   (and its insert): an M1.4 x 3 there, x 5 on -X
    pogo_cone_wall: float = 0.9    # wall between the head pocket and the cone socket mouth
    pogo_tail_x: float = 3.0       # tail / solder-joint room under the connector: +-x, full width,
    # head: break-away support in the connector pocket (as FilamATrix's in the D2F pocket). The body
    # prints front face down, so the pocket's back wall is an ~19 mm bridge. 0.4 mm plates on a
    # pogo_sup_pitch grid (constant X, plus one at the face end tying them together) stand on the
    # pocket's front wall and stop pogo_sup_gap short of every other wall, the rings and the ceiling.
    pogo_support: bool = True
    pogo_sup_t: float = 0.4
    pogo_sup_pitch: float = 2.0
    pogo_sup_gap: float = 0.4
    pogo_head_tail_x: float = 5.0  #   (head, v0.39: +-5, to the edge of the +X M3 insert; the hat is hollow)
    pogo_tail_room: float = 0.8    #   pogo_tail + this deep
    pogo_wire_slot: float = 1.4    # head: wire slot behind the pocket (Y), from the tails up to the
                                   #   head_wire_z channel, which runs out on the +X side as before
    pogo_hat_wall: float = 1.5     # hat: wall behind the pocket; the hat grows at the back to make it
    # hat: above the pocket floor the whole connector outline is hollow (tails, solder joints, ID
    # resistor), except a boss under each ear's screw hole. The pad half rests on its ears there.
    pogo_res_h: float = 3.0        # cavity height above the tails
    pogo_ear_z: float = 0.9        # head and hat: the connector rests on its ears, on rings round the screw
                                   #   holes that stand this far proud of the pocket floor. 0.9 puts its face
                                   #   flush with the interface (v0.39; v0.36-v0.38: 0.8 in the hat only,
                                   #   0.1 below the face)
    pogo_cap_r: float = 1.2        # radius of the raised part of each boss (0.6 wall to the pilot): a
                                   #   plastic lip round the connector's magnets, under the body next to
                                   #   each ear, sits on anything wider (v0.38; v0.37 raised the full 1.75)
    pogo_boss_r: float = 1.75      # ear bosses round the screw holes: fill the ear ends (r 1.7), 1.15 wall to the pilot
    pin_d: float = 3.0             # steel dowel pins, 3x8 (ISO 8734 m6)
    pin_hole_press: float = 2.95   # press fit in the body (tune)
    pin_depth: float = 4.2         # a cavity sits ~5 mm under the +X pin: do not go deeper
    pin_protrusion: float = 3.8    # -> 3x8 mm steel dowel
    pin_hole_extra: float = 0.5    # hat dowel holes are this much deeper than the pin protrusion
    pin_xy: tuple = (7.0, 2.1)     # (+-x, y) relative to the filament axis. v0.34: beside the filament hole,
                                   #   between the front magnets and the pogo pocket (v0.30-v0.33: (7, -4))

    # ---- FilamATrix base (v0.29) -----------------------------------------------------------
    # The front body is built on the FilamATrix G2E front body (GPL-3.0, thunderkeys), taken from
    # "Stealthburner_FilamATrix.step": M3 heat-set insert at the bottom (upper blade guide of the
    # cutter), printed 2.1 filament channel, after-gears D2F sensor (+X, ball at z 80.4), cutting
    # arm clearance on -X. Its pre-gear sensor and ECAS top are filled and replaced by our seat.
    fmx_name: str = "front_body_ECAS_coupler_front_body_ECAS_coupler:1"
    fmx_offset: tuple = (0.13, 0.20, 0.0)   # the body sits 0.13/0.20 mm off the G2E frame in the
                                            #   FilamATrix assembly; this puts it back on the axis
    fmx_fill_r: float = 5.3        # solid cylinder around the axis from fmx_fill_z1 to the top,
    fmx_fill_z0: float = 108.9     #   then our seat is re-cut (stops at the switch pocket, x -5.35).
    fmx_fill_z1: float = 110.4     #   Below z1 only x <= fmx_fill_x: the idler bearing cover
    fmx_fill_x: float = 1.8        #   reaches up to z 110.25 at x >= 1.9
    fmx_fill_y1: float = 5.15      # fill clipped at this y (rel. axis): the back face is at 5.2 there, and the
                                   #   r 5.3 cylinder left a 0.1 mm sliver standing out of it (gear side)
    # FilamATrix's pre-gear switch (not used: the hat sits there) is filled with the stock G2E
    # body's material inside these boxes: its pocket and M2 screw holes on -X, and the slot through
    # the front wall at z ~118-120
    fmx_fill_boxes: tuple = ((-18.6, -3.4, -8.5, 1.5, 108.5, 122.2),
                             (-4.0, 18.0, -8.5, -2.5, 117.0, 121.0))
    sensor_z: float = 80.4         # FilamATrix after-gears sensor ball centre -> nip_to_sensor 19.85
    # D2F screws: FilamATrix has Ø4 head-clearance holes through the front wall and threads the M2x10
    # into the wall behind the switch. Here the holes are closed again and re-cut as a counterbore
    # (head flush in the front face) + Ø1.8 pilot through the front wall, as in the v0.2x bodies.
    sw_cb: bool = True
    sw_screw_xz: tuple = ((11.55, 79.10), (11.55, 85.60))   # D2F mounting holes, 6.5 mm pitch
    sw_front_y: float = -8.0       # front face
    sw_pocket_front_y: float = -2.68   # switch pocket front wall (switch face)
    sw_cb_d: float = 4.2           # head counterbore
    sw_cb_depth: float = 1.8
    sw_pilot_d: float = 1.8        # self-tapping thread in the front wall
    sw_plug_r: float = 2.7         # plug for FilamATrix's ~Ø5 screw-head holes
    # the +X wall in front of the toolhead board (stock G2E shape) touches the SB2209: thin it by
    # board_relief on its inner (-X) side
    board_relief: float = 1.0
    # (x0, x1, y0, y1, z0, z1, shift dz): the material within board_relief of a face looking towards
    # -X goes, measured along (1, 0, dz). Lower part: horizontal (follows the floor fillet, flush at the
    # bottom). Upper part: along the top slope (dz = its gradient), so the slope itself is untouched and
    # the wall runs into it without a step or a cusp at the corner.
    board_relief_boxes: tuple = ((21.0, 35.0, -8.5, 2.0, 75.0, 100.0, 0.0),
                                 (15.5, 35.0, -8.5, 2.0, 100.0, 125.0, -0.807))
    board_relief_edge_y: float = -0.1

    # ---- stinger spine (clip-on stiffener for the stinger) ---------------------------------
    spine_groove_r: float = 2.0     # = PTFE radius: grips without play
    spine_back_t: float = 1.2       # material behind the tube
    spine_lip_t: float = 0.75       # side wall / lip thickness at the tube centreline
    spine_opening: float = 3.7      # clip opening (< 4.0 tube), chosen with the coupon test
    spine: bool = True              # add the spine pocket (hat) and keyed slot (front body)
    spine_in_hat: float = 4.0       # spine length pressed into the hat bottom
    spine_below: float = 17.0       # spine length below the hat (stinger: 20.5)
    spine_pocket_clear: float = 0.1 # press fit in the hat (vertical pocket prints ~0.1 small)
    spine_slot_clear: float = 0.3   # spine slot clearance in the stinger gauge (sets the stinger)
    spine_head_clear: float = 0.5   # keyed slot in the front body: clearance per side
    spine_mouth_x: float = 1.0      # extra width per side at the top of the head slot (magnets limit it)
    spine_mouth_back: float = 1.5   # extra depth towards the back at the top of the head slot
    spine_mouth_h: float = 3.0      # height of the tapered lead-in
    spine_floor_h: float = 3.4      # slot floor lofted down into the seat over this height
    spine_chamfer: float = 0.4      # long outer edges and top end of the spine
    spine_barb_h: float = 0.25      # snap barbs on the lips (hat end): the lips flex in to pass
    spine_barb_z: tuple = (0.6, 1.9)  # barb band, measured down from the spine's top end
    spine_barb_y: tuple = (-0.6, 0.6) # barb band across the lip (tube centre = 0)
    spine_undercut: float = 0.4     # depth of the matching grooves in the hat pocket walls
    # spine retention: "tslot" (v0.25) = T-head slid in from the hat's back face, locked by the tube;
    # "barb" = the old press-in with snap barbs
    spine_lock: str = "tslot"
    spine_wing_x: float = 3.8       # T-head half width (spine body is +-2.75): ~1 mm shelf per side
    spine_wing_y0: float = 0.5      # front edge of the wings (y; tube axis = 0). It is also the stop
                                    #   that centres the groove on the tube axis
    spine_wing_h: float = 1.9       # wing height at the top end of the spine
    spine_tslot_clear: float = 0.15 # sliding clearance per side in the T-slot
    # stinger style: "hat" (v0.28) = cone + tail printed in one piece with the hat (the hat prints
    # upside down, ECAS end on the bed); "cone" (v0.27) = the same cone + tail as a separate part
    # with a T-head in the hat's T-slot; "spine" = the long clip-on spine in a loose keyed slot (v0.25).
    # "hat" and "cone" use the same front body socket.
    stinger_style: str = "hat"
    cone_d0: float = 8.2            # cone diameter at the hat face (socket mouth 8.4: magnets 5.0 from axis)
    cone_d1: float = 6.0            # cone diameter at its tip (wall ~0.9 around the tube bore)
    cone_len: float = 6.0           # cone length below the hat face (~10.5 deg half-angle)
    cone_clear: float = 0.1         # socket <-> cone, radial (tune: the socket prints as a horizontal hole)
    cone_depth_extra: float = 0.3   # socket deeper than the cone: the hat face lands first (no wedging)
    cone_seat_angle: float = 30.0   # half-angle of the lead from the socket bottom into the 4.6 seat
    cone_tip_chamfer: float = 0.4   # outer chamfer at the sleeve's tip
    sleeve_tip_lead: float = 0.0    # inner chamfer there: 0 = flat (with both, the 0.8 wall ended in a
                                    #   knife edge that prints badly; the tube goes in from the top anyway)
    cone_tail: float = 17.0         # closed sleeve continues at cone_d1 down to this far below the hat
                                    #   face (= spine_below): keeps the tube straight, also when docked
    cone_tail_clear: float = 0.3    # radial clearance of the tail bore: only the cone locates
    coupon_openings: tuple = (3.5, 3.6, 3.7)
    coupon_len: float = 10.0

    # ---- cartridge --------------------------------------------------------------------
    ptfe_od: float = 4.0
    tube_bore: float = 4.4         # continuous bowden passes through the hat (prints ~4.1: slides)
    stinger_gap: float = 0.5       # bowden end stops this far above the seat bottom
    cart_w: float = 22.0           # X  (footprint must stay inside the front_body pad)
    cart_d: float = 18.0           # Y
    cart_r: float = 3.0            # footprint corner radius (hat_facets = False)
    # faceted (Voron-style) hat: chamfered footprint and a faceted, octagonal top instead of the round
    # neck. All facets stay <= 45 deg, so the hat still prints upside down without supports.
    hat_facets: bool = True
    cart_chamfer: float = 2.0      # 45 deg corner chamfer of the footprint
    top_w: float = 16.0            # octagonal top (ECAS seat): width (x) ...
    top_d: float = 14.0            #   ... depth (y) ...
    top_chamfer: float = 2.5       #   ... and corner chamfer
    cart_h: float = 16.0           # interface plane -> ECAS seating face
    neck_d: float = 15.0           # round collar that carries the ECAS (collet flange is 10.45)
    neck_blend: float = 3.0        # height of the base -> neck loft
    # one-piece hat (stinger_style "hat") prints upside down: the base -> neck loft and the rail
    # tops become overhangs, so the loft runs to the top face (<=45 deg on the sides, ~51 at the
    # rounded corners) and the rail tops get a 45 deg slope instead of the flat top
    neck_d_flip: float = 16.0
    bottom_chamfer: float = 0.6
    pin_hole_clear: float = 3.4    # prints ~3.1-3.25: free sliding fit on a 3 mm dowel
    pin_slot_len: float = 1.2      # extra length of the slotted hole along X
    pin_lead_in: float = 0.6       # lead-in cone on both dowel holes: radial growth at the hat face.
                                   #   v0.34: 0.6 (mouth 4.6) keeps ~0.7 mm to the magnet and the pogo pocket
                                   #   (v0.26-v0.33: 1.3)
                                   #   (mouth 6.0: ~0.4 mm of wall left to the bottom chamfer on the
                                   #   -X side; v0.25: 1.0)
    pin_lead_depth: float = 1.5    # cone height (v0.25: 1.0, 45 deg). Leaves 2.3 mm of straight bore
                                   #   on the 3.8 mm protrusion (v0.25: 2.8)
    # flange = 45 deg wedge rail: self-centres in the dock and prints without supports
    flange_z: float = 6.0          # wedge root (bottom) height
    flange_w: float = 3.0          # protrusion per side; wedge height = flange_w
    flange_top: float = 12.0       # top of the base block (room for 2 back magnets). The rail is a 90 deg
                                   #   V ridge: 45 deg under (rack lower lip) and over (rack upper lip),
                                   #   apex at flange_z + flange_w; flange_top = flange_z + 2 flange_w
    rail_nose: float = 1.0         # leading end of the rails (the end that enters the rack): every face
    rail_nose_len: float = 3.0     #   of the V ridge set in by rail_nose, tapering out over rail_nose_len
    # ECAS04 pocket copied from the G2E front_body_ECAS_coupler (z relative to seating face)
    ecas_d: float = 8.35
    ecas_groove_d: float = 8.7
    ecas_groove_z: tuple = (-3.0, -2.4)
    ecas_bore_depth: float = 6.0   # 8.35 bore depth below the seating face
    ecas_top_chamfer: float = 0.4
    tube_lead_d: float = 6.0       # 45 deg funnel from the ECAS pocket floor into the tube bore
                                   # (the ECAS body still seats on the 6.0-8.35 ring)
    gauge_wall: float = 4.0        # stinger length gauge: wall around the blind hole

    # ---- dock -------------------------------------------------------------------------
    # hat rack = open V-cradle: gravity + 45 deg lips locate X and Z, a magnet pair snaps Y
    c_x: float = 0.8               # hat body / rail tips <-> cradle walls (no contact)
    lip_t: float = 1.5             # lip below the V root: rack bottom = flange_z - lip_t = 4.5,
                                   #   flat and support-free, clears the G2E chain anchor when lifted
    wall_top: float = 1.0          # side walls rise this much above the rail top
    rail_wall: float = 3.0
    lift: float = 0.6              # head rises this much above the seat to slide in/out
                                   #   (v0.31: = channel_play / 2, the middle of the channel)
    # V-channel (v0.31): each side wall carries a lower 45 deg lip under the rail AND an upper 45 deg
    # lip over it, so the rail (a 90 deg V ridge) runs in a closed V groove. The hat can only rise
    # channel_play above its seat and can't tilt up (bowden pull, pickup push); at either end of the
    # play one V face centres it in X. Replaces the dock pin as the Z lock (the hat's pin bore is a
    # vertical slot now).
    channel: bool = True
    channel_play: float = 1.2      # vertical travel of the hat in the channel (seat -> upper stop)
    channel_lip_t: float = 2.0     # upper lip thickness above its 45 deg underside, at the inner edge
    channel_flare: float = 1.2     # open end: both V faces open by this much (vertical, also X at the apex)
    channel_flare_len: float = 4.0 #   ... tapering to the nominal groove over this length
    # top retainer (v0.2x, superseded by `channel`): a lip on each side wall over the hat's rails
    retain: bool = False           # off since v0.24
    retain_gap: float = 1.0        # clearance above the rail top when the hat is lifted by `lift`
    retain_flat: float = 0.5       # width of the flat underside over the rail's outer edge
    retain_x: float = 12.0         # lip inner edge (|x|); hat body above the rails is |x| <= ~11
    retain_t: float = 1.6          # lip thickness above its sloped underside
    retain_lead: float = 1.5       # 45 deg lead-in on the lip underside at the open end
    snap_face: str = "front"       # hat face that carries the rack snap magnets: "front" (-Y) or
                                   # "back" (+Y). It is the face that enters the rack first.
    snap_magnet_z: float = 8.2     # snap magnet centres (hat frame); same height as in the rack
    snap_magnet_x: float = 5.8     # two magnets at +-x: stop the hat rocking/yawing in the rack
                                   #   (4.2 until v0.23; moved out to make room for the dock pin bore)
    # dock pin: a 3x8 steel dowel pressed through the rack plate, pointing at the hat along the slide
    # direction; it enters a bore in the hat's snap face as the hat slides home and locks it in X
    # (and yaw) while docked. v0.31: the bore is a VERTICAL SLOT, channel_play long between centres,
    # so the hat keeps its channel play in Z with the pin in: the channel locks Z now.
    # v0.32: OFF by default. The V-channel centres the hat in X at either end of its play and holds
    # yaw over the full rail length; Y is the snap magnets' job. True = pin + slot (as v0.31).
    dock_pin: bool = False
    dock_pin_z: float = 8.2        # = snap_magnet_z: between the two snap magnets, x = 0
    dock_pin_protrusion: float = 3.0
    dock_pin_press: float = 2.95   # through hole in the plate (press fit; drill to 3.0 if too tight)
    dock_pin_bore: float = 3.4     # bore in the hat (prints ~3.1-3.25: free on a 3 mm pin)
    dock_pin_bore_extra: float = 0.5   # bore this much deeper than the pin protrudes
    dock_pin_chamfer: float = 0.5  # 45 deg mouth on the bore: catches the pin ~1 mm off (with the slack)
    snap_recess_hat: float = 0.2   # magnet face below the hat face
    snap_recess_rack: float = 0.5  # magnet face below the rack plate face (softer snap)
    # optional artwork engraved on the chamber-facing side of the rack plate (e.g. the official
    # Voron logo SVG from the Voron repos). Box is centred between the wall tops and the screw line.
    logo_svg: str = ""            # path to an SVG; "" = no logo
    logo_w: float = 28.0          # max width of the artwork (mm)
    logo_h: float = 16.0          # max height of the artwork (mm)
    logo_depth: float = 0.6       # engraving depth (3 layers at 0.2)
    snap_eject_d: float = 1.0      # hole from the back of the plate to push the rack magnet out (pin or paper clip)
    plate_t: float = 6.0
    ext_bottom: float = 28.0
    ext_size: float = 20.0
    screw_d: float = 3.4          # 2x M3x8 SHCS (ISO 4762) + M3 roll-in T-nuts into the 2020 slot
    screw_head_d: float = 6.2     # counterbore for the 5.5 mm socket head
    screw_head_h: float = 3.2     # head fully recessed (3.0 mm head + 0.2)
    screw_x: float = 12.0         # +-X: off the bowden tube axis so a hex key can reach them
    key_w: float = 5.8
    key_h: float = 1.5
    # hat_rack_spacer: moves the rack this far off the extrusion, towards the chamber centre.
    # It only fills the volume the extrusion itself used to occupy (z >= ext_bottom), so it adds
    # nothing the head could hit. Screws become M3x(8 + L): 12 -> M3x20, 17 -> M3x25.
    spacer_lens: tuple = (12.0, 17.0)
    # back braces: triangular ribs behind the plate, under the extrusion. Docking pushes the hat
    # into the plate low down; the plate would pivot about the extrusion's bottom edge, which puts
    # the layer lines at z = ext_bottom in tension. The ribs' top edges bear on the extrusion (or
    # spacer) underside instead. The head stays >= 2 mm below the rack bottom behind the plate.
    brace: bool = False            # ribs off: the rack is sturdy enough without them (True = v0.20-v0.21 ribs)
    brace_d: float = 20.0          # depth behind the plate (<= extrusion width), 40 deg underside
    brace_t: float = 3.0           # rib thickness
    brace_gap: float = 0.2         # rib top below the extrusion underside: the plate still seats flat
    # rack styling (cosmetic only; False = plain v0.20 geometry)
    rack_style: bool = True
    rack_corner_r: float = 6.0     # plate top corners
    rack_cove_r: float = 4.0       # cove between wall top and plate front
    key_clear: float = 0.2        # rack key <-> spacer groove, per side
    entry_chamfer: float = 1.2

    @property
    def stinger_len(self):
        return self.z_if - SEAT_BOTTOM_Z - self.stinger_gap

    @property
    def if_to_nip(self):
        return self.z_if - NIP_Z


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_z(d, z0, h, x=0.0, y=0.0):
    return cq.Workplane("XY").circle(d / 2).extrude(h).translate((x, y, z0))


# ======================================================================================
def pogo_yc(p: P) -> float:
    """Y (rel. the filament axis) of the pogo connector centre: just behind the cone socket mouth."""
    return p.cone_d0 / 2 + p.cone_clear + p.pogo_cone_wall + p.pogo_clear + p.pogo_w / 2


def hat_back_ext(p: P) -> float:
    """How far the hat's back face moves back so the pogo pocket keeps pogo_hat_wall behind it."""
    if not p.pogo:
        return 0.0
    return max(0.0, pogo_yc(p) + p.pogo_w / 2 + p.pogo_clear + p.pogo_hat_wall - p.cart_d / 2)


def pogo_pocket(p: P, z_face: float, down: int, y_axis: float = 0.0, tail_x: float = None) -> cq.Workplane:
    """Connector pocket + tail room, from the face plane z_face into the part (down = -1: into the
    head below the face; +1: into the hat above it). Cut 1 mm past the face."""
    d = p.pogo_h + p.pogo_recess
    t = p.pogo_tail + p.pogo_tail_room
    a, b = sorted((z_face - down * 1.0, z_face + down * d))
    cut = pogo_outline(p, a, b, y_axis)
    yc, hw = y_axis + pogo_yc(p), p.pogo_w / 2 + p.pogo_clear
    a, b = sorted((z_face + down * (d - 0.01), z_face + down * (d + t)))
    tx = p.pogo_tail_x if tail_x is None else tail_x
    return cut.union(box(-tx, tx, yc - hw, yc + hw, a, b))


def pogo_outline(p: P, z0: float, z1: float, y_axis: float = 0.0) -> cq.Workplane:
    """The connector's outline grown by pogo_clear (body + round-ended ears), from z0 to z1."""
    yc = y_axis + pogo_yc(p)
    c = p.pogo_clear
    bl, hw = p.pogo_body_l / 2 + c, p.pogo_w / 2 + c
    xe = p.pogo_l / 2 - p.pogo_ear_hole_inset           # ear hole centre (|x|)
    re = p.pogo_ear_hole_inset + c                       # round ear end
    cut = box(-bl, bl, yc - hw, yc + hw, z0, z1)
    for sx in (-1, 1):                                  # ears: straight from the body, round end
        x0, x1 = sorted((sx * (bl - 0.5), sx * xe))
        cut = cut.union(box(x0, x1, yc - re, yc + re, z0, z1))
        cut = cut.union(cyl_z(2 * re, z0, z1 - z0, x=sx * xe, y=yc))
    return cut


def pogo_head_support(p: P) -> cq.Workplane:
    """Break-away support for the head's connector pocket (G2E frame), see pogo_support."""
    ay, g, t = AXIS_Y, p.pogo_sup_gap, p.pogo_sup_t
    ztop = p.z_if - 0.2
    zf = p.z_if - p.pogo_h - p.pogo_recess
    zb = zf - p.pogo_tail - p.pogo_tail_room
    yc, hw = ay + pogo_yc(p), p.pogo_w / 2 + p.pogo_clear
    room = pogo_outline(p, zf, ztop, ay).union(
        box(-p.pogo_head_tail_x, p.pogo_head_tail_x, yc - hw, yc + hw, zb, zf + 0.01))
    # keep only what stays inside the pocket when moved g towards the ceiling (+Y), +-X and the
    # floor (-Z): a g gap there, none at the front wall (-Y), where the plates stand
    reg = room
    for v in ((0, g, 0), (g, 0, 0), (-g, 0, 0), (0, 0, -g)):
        reg = reg.intersect(room.translate((-v[0], -v[1], -v[2])))
    xe = p.pogo_l / 2 - p.pogo_ear_hole_inset
    for sx in (-1, 1):                                    # clear of the rings
        reg = reg.cut(cyl_z(2 * (p.pogo_cap_r + g), zb - 1, (zf + p.pogo_ear_z + g) - (zb - 1),
                            x=sx * xe, y=yc))
    xl = p.pogo_l / 2 + 1
    comb = box(-xl, xl, yc - hw - 1, yc + hw + 1, ztop - t, ztop)        # tie plate at the face end
    n = int(xl / p.pogo_sup_pitch) + 1
    for i in range(-n, n + 1):
        x = i * p.pogo_sup_pitch
        comb = comb.union(box(x - t / 2, x + t / 2, yc - hw - 1, yc + hw + 1, zb - 1, ztop))
    return reg.intersect(comb).translate((0, -0.05, 0))      # 0.05 into the front wall: fused


def pogo_screws(p: P, z_face: float, down: int, sides, y_axis: float = 0.0,
                raise_: float = 0.0) -> cq.Workplane:
    """Pilot holes for the ear screws, from the pocket floor (less raise_, towards the face)
    pogo_screw_depth into the part."""
    x = p.pogo_l / 2 - p.pogo_ear_hole_inset
    zf = z_face + down * (p.pogo_h + p.pogo_recess - raise_)
    z0 = zf - 0.01 if down > 0 else zf - p.pogo_screw_depth
    w = cq.Workplane("XY")
    for s in sides:
        w = w.add(cyl_z(p.pogo_screw_pilot, z0, p.pogo_screw_depth + 0.01, x=s * x,
                        y=y_axis + pogo_yc(p)).val())
    return w.combine()


def load_g2_part(step_path, suffix):
    """Return (shape, all_parts) for the first G2E STEP part whose name ends with suffix."""
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFDoc import XCAFDoc_DocumentTool
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDF import TDF_LabelSequence, TDF_Label
    from OCP.TDataStd import TDataStd_Name
    from OCP.TopLoc import TopLoc_Location

    doc = TDocStd_Document(TCollection_ExtendedString("g2"))
    r = STEPCAFControl_Reader(); r.SetNameMode(True)
    r.ReadFile(str(step_path)); r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def name(l):
        a = TDataStd_Name()
        return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), a) else "?"

    parts = []

    def walk(l, loc, nm):
        if st.IsReference_s(l):
            ref = TDF_Label(); st.GetReferredShape_s(l, ref)
            walk(ref, loc.Multiplied(st.GetLocation_s(l)), name(l)); return
        if st.IsAssembly_s(l):
            seq = TDF_LabelSequence(); st.GetComponents_s(l, seq)
            for i in range(1, seq.Length() + 1):
                walk(seq.Value(i), loc, nm)
            return
        parts.append((nm, cq.Shape.cast(st.GetShape_s(l).Moved(loc))))

    roots = TDF_LabelSequence(); st.GetFreeShapes(roots)
    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i), TopLoc_Location(), name(roots.Value(i)))
    target = next(s for n, s in parts if n == suffix)
    return target, parts


def load_fmx_body(path, p: P) -> cq.Shape:
    """FilamATrix front body on the G2E frame. `path` = Stealthburner_FilamATrix.step (slow: a
    ~220 MB assembly) or a .brep cached from it by a previous build."""
    path = Path(path)
    if path.suffix.lower() == ".brep":
        s = cq.Shape.importBrep(str(path))
    else:
        s, _ = load_g2_part(path, p.fmx_name)
        s = s.moved(cq.Location(cq.Vector(*p.fmx_offset)))
        cache = path.with_name("filamatrix_front_body.brep")
        try:
            s.exportBrep(str(cache)); print(f"cached the FilamATrix front body in {cache}")
        except OSError:
            pass
    return s


def seat_exit_tool(p: P) -> cq.Workplane:
    """Cone from the seat (slightly above its bottom) to just below the stock 2.1 hole diameter,
    so the cone crosses the stock bore instead of sharing faces with it."""
    ta = math.tan(math.radians(p.seat_exit_angle))
    top_z, top_r = SEAT_BOTTOM_Z + 0.3, p.seat_d / 2 + 0.3 * ta
    bot_r = 0.95                                          # < 1.05 stock bore radius
    bot_z = top_z - (top_r - bot_r) / ta
    return (cq.Workplane("XY").workplane(offset=bot_z).center(0, AXIS_Y).circle(bot_r)
            .workplane(offset=top_z - bot_z).circle(top_r).loft())


def front_body_hatchanger(p: P, stock: cq.Shape, g2_body: cq.Shape = None) -> cq.Workplane:
    """`stock` = the FilamATrix front body, already moved onto the G2E frame (load_fmx_body).
    `g2_body` = the stock G2E front_body, used to fill FilamATrix's unused pre-gear switch pocket."""
    ay = AXIS_Y
    body = cq.Workplane("XY").add(stock)
    if g2_body is not None:
        for x0, x1, y0, y1, z0, z1 in p.fmx_fill_boxes:
            body = body.union(cq.Workplane("XY").add(g2_body).intersect(box(x0, x1, y0, y1, z0, z1)),
                              clean=False)
    # 0. close FilamATrix's pre-gear sensor ball channel, its PTFE seat and ECAS pocket around the
    #    axis; our seat, socket and lead-in are cut again below
    fill = cyl_z(2 * p.fmx_fill_r, p.fmx_fill_z1, p.z_if + 2 - p.fmx_fill_z1, y=ay)
    low = cyl_z(2 * p.fmx_fill_r, p.fmx_fill_z0, p.fmx_fill_z1 - p.fmx_fill_z0 + 0.01, y=ay)
    low = low.intersect(box(-p.fmx_fill_r - 1, p.fmx_fill_x, ay - p.fmx_fill_r - 1, ay + p.fmx_fill_r + 1,
                            p.fmx_fill_z0 - 1, p.fmx_fill_z1 + 1))
    clip = box(-20, 20, -20, ay + p.fmx_fill_y1, p.fmx_fill_z0 - 1, p.z_if + 3)
    body = body.union(fill.union(low).intersect(clip), clean=False)

    # 1. flat interface pad (built inside the same print layers as the body: no supports)
    pad = box(-p.pad_x, p.pad_x, p.pad_y0, p.pad_y1, p.z_if - p.pad_depth - 1.0, p.z_if)
    body = body.union(pad, clean=False)
    # trim anything of the stock top that pokes above the interface plane inside the pad
    body = body.cut(box(-p.pad_x, p.pad_x, p.pad_y0, p.pad_y1, p.z_if, p.z_if + 5), clean=False)

    # 2. PTFE seat extended to the interface plane + lead-in cone
    body = body.cut(cyl_z(p.seat_d, SEAT_BOTTOM_Z, p.z_if - SEAT_BOTTOM_Z + 1, y=ay), clean=False)
    if cone_style(p):
        body = body.cut(cone_socket_tool(p), clean=False)
    else:
        h = p.seat_cone_h
        cone = (cq.Workplane("XY").workplane(offset=p.z_if - h).center(0, ay)
                .circle(p.seat_d / 2).workplane(offset=h + 0.01).circle(p.seat_cone_d / 2).loft())
        body = body.cut(cone, clean=False)
    # seat exit: shallow cone down into the stock 2.1 hole, so a curved filament tip landing
    # off-centre is steered in instead of stubbing on the stock 45 deg step (bowden friction is
    # all that holds the filament in the hat, so it gets pushed back up otherwise)
    body = body.cut(seat_exit_tool(p), clean=False)

    # 2b. D2F screws: close FilamATrix's through holes, cut counterbore + pilot
    if p.sw_cb:
        y0, y1 = p.sw_front_y, p.sw_pocket_front_y
        for x, z in p.sw_screw_xz:
            # FilamATrix's hole is ~Ø5 through the whole wall: plug it flush with both faces
            plug = cq.Workplane("XZ").circle(p.sw_plug_r).extrude(-(y1 - y0)).translate((x, y0, z))
            body = body.union(plug, clean=False)
            cb = cq.Workplane("XZ").circle(p.sw_cb_d / 2).extrude(-(p.sw_cb_depth + 0.5)).translate((x, y0 - 0.5, z))
            pilot = cq.Workplane("XZ").circle(p.sw_pilot_d / 2).extrude(-(y1 - y0 + 0.4)).translate((x, y0 - 0.2, z))
            body = body.cut(cb.union(pilot), clean=False)

    # 3. magnets and dowel pins
    mx, my = p.magnet_xy
    px, py = p.pin_xy
    mdepth = p.magnet_h + (p.head_wire_gap if p.id_contacts and not p.pogo else 0.1)
    for s in (-1, 1):
        body = body.cut(cyl_z(p.magnet_d + p.magnet_fit, p.z_if - mdepth,
                              mdepth + 1, x=s * mx, y=ay + my), clean=False)
        body = body.cut(cyl_z(p.pin_hole_press, p.z_if - p.pin_depth, p.pin_depth + 1,
                              x=s * px, y=ay + py), clean=False)
    if p.pogo:
        # pin half, pins up, face pogo_recess below the pad. The two wires leave the tails through a
        # slot behind the pocket, rise to the head_wire_z channel and run out on the +X side
        # (behind the cable cover), like the v0.32 magnet wires.
        # it rests on its ears, on a ring round each screw hole pogo_ear_z proud of the floor (as in
        # the hat); the body and the lip round its magnets hang clear of the floor
        cut = pogo_pocket(p, p.z_if, -1, ay, tail_x=p.pogo_head_tail_x)
        yb = ay + pogo_yc(p) + p.pogo_w / 2 + p.pogo_clear
        zb = p.z_if - p.pogo_h - p.pogo_recess - p.pogo_tail - p.pogo_tail_room
        c0, c1 = p.head_wire_z
        ws = p.pogo_wire_slot
        cut = cut.union(box(-p.pogo_tail_x, p.pogo_tail_x, yb - 0.01, yb + ws, zb, p.z_if + c1))
        cut = cut.union(box(-p.pogo_tail_x, p.pad_x + 2, yb - 0.01, yb + ws, p.z_if + c0, p.z_if + c1))
        body = body.cut(cut, clean=False)
        xe = p.pogo_l / 2 - p.pogo_ear_hole_inset
        zf = p.z_if - p.pogo_h - p.pogo_recess
        for sx in (-1, 1):
            body = body.union(cyl_z(2 * p.pogo_cap_r, zf - 0.01, p.pogo_ear_z + 0.01, x=sx * xe,
                                    y=ay + pogo_yc(p)), clean=False)
        if p.pogo_support:
            body = body.union(pogo_head_support(p), clean=False)
        for sx in p.pogo_head_screws:
            q = p if sx < 0 else replace(p, pogo_screw_depth=p.pogo_head_screw_depth_px)
            body = body.cut(pogo_screws(q, p.z_if, -1, (sx,), ay, raise_=p.pogo_ear_z), clean=False)
    elif p.id_contacts:
        zf = p.z_if - mdepth                     # magnet pocket floor
        yc = ay + p.head_wire_y
        w, (c0, c1) = p.head_wire_w, p.head_wire_z
        rp = (p.magnet_d + p.magnet_fit) / 2      # starts flush with the -X pocket's outer tangent
        ch = box(-mx - rp, p.pad_x + 2, yc - w / 2, yc + w / 2, p.z_if + c0, p.z_if + c1)
        for s in (-1, 1):                        # notch from the channel into the pocket, at the floor
            n = p.head_wire_notch
            ch = ch.union(box(s * mx - n / 2, s * mx + n / 2, ay + my, yc, zf - 0.01, zf + 0.6))
        body = body.cut(ch, clean=False)
    if p.spine and not cone_style(p):
        body = body.cut(spine_slot_tool(p), clean=False)
    if p.board_relief > 0:
        cut = None
        for x0, x1, y0, y1, z0, z1, dz in p.board_relief_boxes:
            r = p.board_relief
            wall = body.intersect(box(x0 - 2 * r, x1, y0, y1, z0 - 2 * r, z1 + 2 * r))
            inner = wall.cut(wall.translate((r, 0, dz * r)))
            inner = inner.union(wall.intersect(box(max(x0, 21.0), x1, p.board_relief_edge_y, y1, z0, z1)))
            inner = inner.intersect(box(x0, x1, y0, y1, z0, z1))
            cut = inner if cut is None else cut.union(inner)
        body = body.cut(cut, clean=False)
    # NOTE: clean=False everywhere - OCC face merging breaks this imported solid
    return body


def spine_section(p: P, opening: float, length: float) -> cq.Workplane:
    """Clip-on spine: its cross-section extruded along Z (the tube axis) over `length`.
    Tube centred on the origin, flat back towards +Y. The groove wraps the tube past its
    centreline; the lips spring open to let the 4 mm tube in through `opening`."""
    r = p.spine_groove_r
    half_w = r + p.spine_lip_t
    y_tip = -math.sqrt(max(r * r - (opening / 2) ** 2, 0.0))   # where the opening meets the groove
    y_back = r + p.spine_back_t
    body = box(-half_w, half_w, y_tip, y_back, 0, length)
    body = body.cut(cyl_z(2 * r, -1, length + 2))
    return body.cut(box(-opening / 2, opening / 2, y_tip - 1, 0, -1, length + 1))


def _spine_envelope(p: P, grow: float, z0: float, z1: float) -> cq.Workplane:
    """Box around the spine cross-section, grown by `grow`, from z0 to z1 (hat frame)."""
    r = p.spine_groove_r
    hw = r + p.spine_lip_t
    y_tip = -math.sqrt(max(r * r - (p.spine_opening / 2) ** 2, 0.0))
    return box(-hw - grow, hw + grow, y_tip - grow, r + p.spine_back_t + grow, z0, z1)


def spine_tslot_tool(p: P) -> cq.Workplane:
    """T-slot in the hat bottom for the spine (hat frame). The spine slides in from the back face
    (+Y) along a channel as wide as its body; its T-head (wings) runs in a wider chamber above a
    shelf and stops against the chamber's front wall, which puts the groove on the tube axis.
    Then the tube is pushed down through it: the groove wraps the tube (opening 3.7 < 4.0), so the
    spine can't slide back out, and the wings sit on the shelves, so it can't be pulled down."""
    c = p.spine_tslot_clear
    hd = p.cart_d / 2
    r = p.spine_groove_r
    hw = r + p.spine_lip_t
    y_tip = -math.sqrt(max(r * r - (p.spine_opening / 2) ** 2, 0.0))
    top = p.spine_in_hat + c
    channel = box(-hw - c, hw + c, y_tip - 2 * c, hd + 1, -1, top)       # body: tube -> back face
    z_shelf = p.spine_in_hat - p.spine_wing_h - c
    chamber = box(-p.spine_wing_x - c, p.spine_wing_x + c, p.spine_wing_y0 - c, hd + 1, z_shelf, top)
    return channel.union(chamber)


def stinger_spine(p: P, in_place: bool = False) -> cq.Workplane:
    """Stiffener behind the stinger. Its top end snaps into the hat pocket (barbs on the lips,
    undercuts in the pocket); once the tube is pushed through its groove the lips can't flex
    inward any more, so the barbs are locked. In place: hat frame (tube axis at x=y=0,
    interface plane z=0, back +Y). Otherwise laid on its flat back for printing."""
    L = p.spine_in_hat + p.spine_below
    r = p.spine_groove_r
    hw = r + p.spine_lip_t
    yb = r + p.spine_back_t
    w = spine_section(p, p.spine_opening, L)
    ch = p.spine_chamfer
    w = w.edges("|Z and >Y").chamfer(ch)                       # long back edges (bed side)
    w = w.faces(">Z").edges("not %CIRCLE").chamfer(ch)         # top end: lead into the pocket
    w = w.cut(cq.Workplane("XY").workplane(offset=L - ch).circle(r)       # groove entry
              .workplane(offset=ch + 0.01).circle(r + ch).loft())
    # 45 deg lead-in on the back edge of the bottom (tip) end, plus small chamfers round it
    wedge = (cq.Workplane("YZ").polyline([(yb - 2.2, -1), (yb + 1, -1), (yb + 1, 2.2)]).close()
             .extrude(20).translate((-10, 0, 0)))
    w = w.cut(wedge)
    for sx in (-1, 1):
        w = w.cut(cq.Workplane("XZ").polyline([(sx * (hw - ch), -0.01), (sx * (hw + 1), -0.01),
                                               (sx * (hw + 1), ch + 1)]).close()
                  .extrude(-(yb + 2)).translate((0, -2, 0)))
    if p.spine_lock == "tslot":
        # T-head: wings at the top end, back face flush with the spine's back (prints on the bed)
        wings = box(-p.spine_wing_x, p.spine_wing_x, p.spine_wing_y0, yb, L - p.spine_wing_h, L)
        wings = wings.edges("|Y").chamfer(0.3)
        wings = wings.cut(cq.Workplane("XY").circle(r).extrude(L + 2).translate((0, 0, -1)))
        w = w.union(wings)
    # snap barbs on both lips: ramp towards the top (insertion), 45 deg catch below
    z_lo, z_hi = L - p.spine_barb_z[1], L - p.spine_barb_z[0]
    h = p.spine_barb_h
    y0, y1 = p.spine_barb_y
    for sx in ((-1, 1) if p.spine_lock == "barb" else ()):
        prof = [(sx * hw, z_lo), (sx * (hw + h), z_lo + h), (sx * (hw + h), z_lo + h + 0.2),
                (sx * hw, z_hi)]
        barb = (cq.Workplane("XZ").polyline([(x - sx * 0.05, z) if i in (0, 3) else (x, z)
                                             for i, (x, z) in enumerate(prof)]).close()
                .extrude(-(y1 - y0)).translate((0, y0, 0)))
        w = w.union(barb)
    if in_place:
        return w.translate((0, 0, -p.spine_below))
    w = w.rotate((0, 0, 0), (1, 0, 0), -90)                 # back (+Y) -> down (-Z)
    bb = w.val().BoundingBox()
    return w.translate((-bb.xmin, -bb.ymin, -bb.zmin))


def cone_style(p: P) -> bool:
    """Cone socket in the front body (separate cone or one-piece hat)."""
    return p.spine and p.stinger_style in ("cone", "hat")


def stinger_sleeve(p: P) -> cq.Workplane:
    """Solid cone + tail below the hat face (hat frame), without the bore."""
    cone = (cq.Workplane("XY").workplane(offset=-p.cone_len).circle(p.cone_d1 / 2)
            .workplane(offset=p.cone_len + 0.01).circle(p.cone_d0 / 2).loft())
    if p.cone_tail > p.cone_len:
        cone = cone.union(cyl_z(p.cone_d1, -p.cone_tail, p.cone_tail - p.cone_len + 0.01))
    return cone.faces("<Z").edges().chamfer(p.cone_tip_chamfer)


def cone_socket_tool(p: P) -> cq.Workplane:
    """Conical socket for the stinger cone in the front body (G2E frame): the cone grown by
    cone_clear, cone_depth_extra deeper than the cone, then a cone_seat_angle lead down into the
    seat. The hat face lands on the pad before the cone bottoms out, so the face sets Z and tilt
    and the cone only centres X/Y; a pressed-in printed taper this shallow would wedge."""
    c, zt = p.cone_clear, p.z_if
    r0, r1 = p.cone_d0 / 2 + c, p.cone_d1 / 2 + c
    k = (r0 - r1) / p.cone_len                                     # radius change per mm
    zb = zt - p.cone_len - p.cone_depth_extra
    rb = r1 - k * p.cone_depth_extra
    sock = (cq.Workplane("XY").workplane(offset=zb).center(0, AXIS_Y).circle(rb)
            .workplane(offset=zt + 1 - zb).circle(r0 + k).loft())
    rs = p.seat_d / 2 - 0.05
    if p.cone_tail > p.cone_len:
        rt = p.cone_d1 / 2 + p.cone_tail_clear
        zt_b = zt - p.cone_tail - p.cone_depth_extra
        sock = sock.union(cyl_z(2 * rt, zt_b, zb - zt_b + 0.5, y=AXIS_Y))
        zb, rb = zt_b, rt
    hl = (rb - rs) / math.tan(math.radians(p.cone_seat_angle))
    lead = (cq.Workplane("XY").workplane(offset=zb - hl).center(0, AXIS_Y).circle(rs)
            .workplane(offset=hl + 0.01).circle(rb).loft())
    return sock.union(lead)


def stinger_cone(p: P, in_place: bool = False) -> cq.Workplane:
    """Cone stinger sleeve. Top: the spine's T-head and C-section, slid into the hat's T-slot from
    the back face and locked by the tube (as the v0.25 spine). Below the hat face: a closed cone
    around the tube that seats in the front body socket. In place: hat frame (tube axis at x=y=0,
    interface plane z=0). Otherwise standing on its tip for printing (bore vertical)."""
    Lh = p.spine_in_hat
    r = p.spine_groove_r
    yb = r + p.spine_back_t
    ch = p.spine_chamfer
    head = spine_section(p, p.spine_opening, Lh)
    head = head.edges("|Z and >Y").chamfer(ch)
    head = head.faces(">Z").edges("not %CIRCLE").chamfer(ch)
    head = head.cut(cq.Workplane("XY").workplane(offset=Lh - ch).circle(r)
                    .workplane(offset=ch + 0.01).circle(r + ch).loft())
    wings = box(-p.spine_wing_x, p.spine_wing_x, p.spine_wing_y0, yb, Lh - p.spine_wing_h, Lh)
    wings = wings.edges("|Y").chamfer(0.3)
    wings = wings.cut(cq.Workplane("XY").circle(r).extrude(Lh + 2).translate((0, 0, -1)))
    cone = (cq.Workplane("XY").workplane(offset=-p.cone_len).circle(p.cone_d1 / 2)
            .workplane(offset=p.cone_len).circle(p.cone_d0 / 2).loft())
    if p.cone_tail > p.cone_len:
        cone = cone.union(cyl_z(p.cone_d1, -p.cone_tail, p.cone_tail - p.cone_len + 0.01))
    cone = cone.faces("<Z").edges().chamfer(p.cone_tip_chamfer)
    w = cone.union(head).union(wings)
    zl = -max(p.cone_len, p.cone_tail)
    w = w.cut(cyl_z(p.tube_bore, zl - 1, -zl + 1.2))                     # closed bore in the sleeve
    w = w.cut(cq.Workplane("XY").workplane(offset=zl - 0.01).circle(p.tube_bore / 2 + 0.4)
              .workplane(offset=0.41).circle(p.tube_bore / 2).loft())     # lead-in for the tube
    if in_place:
        return w
    bb = w.val().BoundingBox()
    return w.translate((0, 0, -bb.zmin))                # tip on the bed, bore vertical


def spine_slot_tool(p: P) -> cq.Workplane:
    """Keyed slot for the spine in the front body (G2E frame). Loose straight part plus a
    tapered lead-in, so the spine finds it even when the head is a little off. The front side
    of the mouth is not grown: the seat funnel already opens there, and the magnets are close."""
    c = p.spine_head_clear
    zt = p.z_if
    slot = _spine_envelope(p, c, -p.spine_below - c, 1.0).translate((0, AXIS_Y, zt))
    r = p.spine_groove_r
    hw = r + p.spine_lip_t + c
    y0 = -math.sqrt(max(r * r - (p.spine_opening / 2) ** 2, 0.0)) - c
    y1 = r + p.spine_back_t + c
    gx, gb, h = p.spine_mouth_x, p.spine_mouth_back, p.spine_mouth_h
    bot = cq.Workplane("XY").workplane(offset=zt - h).center(0, AXIS_Y + (y0 + y1) / 2).rect(2 * hw, y1 - y0)
    mouth = (bot.workplane(offset=h + 0.01).center(0, gb / 2)
             .rect(2 * (hw + gx), y1 - y0 + gb).loft())
    # funnel floor: the slot is wider than the seat, so a curved tip could land on a flat floor
    # here. Loft the slot outline down into the seat (removes material only between the two).
    zf = zt - p.spine_below - c
    floor = (cq.Workplane("XY").workplane(offset=zf - p.spine_floor_h).center(0, AXIS_Y)
             .circle(p.seat_d / 2 - 0.1)
             .workplane(offset=p.spine_floor_h + 0.01).center(0, (y0 + y1) / 2).rect(2 * hw, y1 - y0)
             .loft())
    return slot.union(mouth).union(floor)


def spine_clip_coupon(p: P) -> cq.Workplane:
    """Fit test for the spine clip: one piece per opening in coupon_openings, laid on its flat
    back with the groove up. Piece n has n notches on its +X side."""
    hw = p.spine_groove_r + p.spine_lip_t
    pitch = 2 * hw + 4.0
    out = None
    for i, o in enumerate(p.coupon_openings):
        w = spine_section(p, o, p.coupon_len)
        for k in range(i + 1):
            z = 1.5 + k * 1.4
            w = w.cut(box(hw - 0.4, hw + 1, -5, 5, z, z + 0.6))
        w = w.rotate((0, 0, 0), (1, 0, 0), -90)         # back (+Y) -> down (-Z)
        bb = w.val().BoundingBox()
        w = w.translate((i * pitch - (bb.xmin + bb.xmax) / 2, -bb.ymin, -bb.zmin))
        out = w if out is None else out.union(w)
    return out


def dowel_pins(p: P):
    px, py = p.pin_xy
    w = cq.Workplane("XY")
    for s in (-1, 1):
        w = w.add(cyl_z(p.pin_d, p.z_if - p.pin_depth, p.pin_depth + p.pin_protrusion,
                        x=s * px, y=AXIS_Y + py).val())
    return w


# ======================================================================================
def _octagon(w: float, d: float, c: float, z: float) -> cq.Wire:
    """Rectangle w x d with 45 deg corner chamfers c, in the plane z, centred on the axis."""
    x, y = w / 2, d / 2
    pts = [(x - c, -y), (x, -y + c), (x, y - c), (x - c, y), (-x + c, y), (-x, y - c), (-x, -y + c), (-x + c, -y)]
    return cq.Wire.makePolygon([cq.Vector(a, b, z) for a, b in pts], close=True)


def _footprint(p: P, z: float) -> cq.Wire:
    e = hat_back_ext(p)                       # pogo: the back face moves back by e
    if p.hat_facets:
        return _octagon(p.cart_w, p.cart_d + e, p.cart_chamfer, z).translate((0, e / 2, 0))
    sk = cq.Sketch().rect(p.cart_w, p.cart_d).vertices().fillet(p.cart_r)
    return sk._faces.Faces()[0].outerWire().translate((0, 0, z))


def hat_flipped(p: P) -> bool:
    return p.spine and p.stinger_style == "hat"


def _footprint_offset(p: P, d: float, z: float) -> cq.Wire:
    if p.hat_facets:                          # mitred offset: the chamfer leg grows by d (2 - sqrt 2)
        return _octagon(p.cart_w + 2 * d, p.cart_d + 2 * d, p.cart_chamfer + d * (2 - math.sqrt(2)), z)
    sk = cq.Sketch().rect(p.cart_w + 2 * d, p.cart_d + 2 * d).vertices().fillet(p.cart_r + d)
    return sk._faces.Faces()[0].outerWire().translate((0, 0, z))


def _rail_profile(p: P, inset: float = 0.0):
    """Right-hand rail cross-section in XZ (x, z): a 90 deg V ridge, 45 deg below (rests on the
    rack's lower lip) and 45 deg above (runs under its upper lip), apex at (hw + w, z0 + w).
    `inset` moves every exposed face in by that much (the tapered nose)."""
    hw = p.cart_w / 2
    x_in = hw - p.cart_r - 0.5                 # buried in the body, also at the rounded corners
    z0, zt, w, n = p.flange_z, p.flange_top, p.flange_w, inset
    xu = hw + 2 * w + z0 - zt                  # where the upper face meets the base top (= hw)
    return [(x_in, z0 + n), (hw, z0 + n), (hw + w - n, z0 + w), (xu, zt - n), (x_in, zt - n)]


def _rail_wire(p: P, inset: float, y: float) -> cq.Wire:
    return cq.Wire.makePolygon([cq.Vector(x, y, z) for x, z in _rail_profile(p, inset)], close=True)


def _rail(p: P, length: float, y_front: float, nose_front: bool = True):
    """Both rails from y_front to y_front + length. With p.rail_nose the end that enters the rack
    (y_front if nose_front, else the far end) is lofted from the inset profile to the full one."""
    L, n = p.rail_nose_len, p.rail_nose
    y1 = y_front + length
    if n <= 0 or L <= 0:
        r = cq.Workplane().add(cq.Solid.makeLoft([_rail_wire(p, 0, y_front), _rail_wire(p, 0, y1)], True))
    else:
        ya, yb = (y_front, y_front + L) if nose_front else (y1, y1 - L)
        nose = cq.Solid.makeLoft([_rail_wire(p, n, ya), _rail_wire(p, 0, yb)], True)
        rest = cq.Solid.makeLoft([_rail_wire(p, 0, yb), _rail_wire(p, 0, y1 if nose_front else y_front)], True)
        r = cq.Workplane().add(nose).union(cq.Workplane().add(rest))
    return r.union(r.mirror("YZ"))


def cartridge(p: P) -> cq.Workplane:
    hd = p.cart_d / 2
    flip = hat_flipped(p)
    T = p.cart_h
    zb = p.flange_top
    zn, nd = (T, p.neck_d_flip) if flip else (p.flange_top + p.neck_blend, p.neck_d)

    base = cq.Workplane("XY").add(cq.Solid.extrudeLinear(
        cq.Face.makeFromWires(_footprint(p, 0)), cq.Vector(0, 0, zb)))
    top = (_octagon(p.top_w, p.top_d, p.top_chamfer, zn) if p.hat_facets
           else cq.Wire.makeCircle(nd / 2, cq.Vector(0, 0, zn), cq.Vector(0, 0, 1)))
    blend = cq.Workplane("XY").add(cq.Solid.makeLoft([_footprint(p, zb), top], True))
    body = base.union(blend)
    if T - zn > 0.01:
        body = body.union(cyl_z(nd, zn, T - zn) if not p.hat_facets else
                          cq.Workplane("XY").add(cq.Solid.extrudeLinear(
                              cq.Face.makeFromWires(_octagon(p.top_w, p.top_d, p.top_chamfer, zn)),
                              cq.Vector(0, 0, T - zn))))
    if flip:
        body = body.faces(">Z").edges().chamfer(0.4)          # bed edge (elephant's foot)
    else:
        body = body.faces(">Z").edges().fillet(0.8)
    body = body.faces("<Z").edges().chamfer(p.bottom_chamfer)

    lead = "<Y" if p.snap_face == "front" else ">Y"            # the end that enters the rack first
    rails = _rail(p, p.cart_d, -hd, nose_front=(lead == "<Y"))
    if flip:
        # upside-down print: clip the rails with a 45 deg frustum hanging from the base top, so
        # every downward face of the rail tops (the flat top, also at the rounded corners) is
        # 45 deg. The rack slot keeps the flat-top profile: old racks still fit.
        g = p.flange_top - p.flange_z
        fr = cq.Workplane("XY").add(cq.Solid.makeLoft(
            [_footprint_offset(p, g, p.flange_z), _footprint(p, p.flange_top)]))
        rails = rails.intersect(fr)
        sy = -1 if lead == "<Y" else 1                          # dock entry lead-in, in plan
        for sx in (-1, 1):
            tri = (cq.Workplane("XY").polyline([(sx * (p.cart_w / 2 + p.flange_w - 0.8), sy * hd),
                                                (sx * (p.cart_w / 2 + p.flange_w + 1), sy * hd),
                                                (sx * (p.cart_w / 2 + p.flange_w + 1), sy * (hd - 1.8))])
                   .close().extrude(20).translate((0, 0, -2)))
            rails = rails.cut(tri)
    elif p.rail_nose <= 0:
        rails = rails.edges(f"|Z and {lead}").chamfer(0.8)
    body = body.union(rails)
    if flip:
        body = body.union(stinger_sleeve(p))

    # filament path: one continuous 4x2 bowden, held by the ECAS04 on top, runs straight
    # through the hat and sticks out of the bottom as the stinger
    zlo = -max(p.cone_len, p.cone_tail) - 1 if flip else -1
    body = body.cut(cyl_z(p.tube_bore, zlo, T + 1 - zlo))
    if flip and p.sleeve_tip_lead > 0:                        # inner chamfer at the sleeve's tip
        zl = zlo + 1
        c = p.sleeve_tip_lead
        body = body.cut(cq.Workplane("XY").workplane(offset=zl - 0.01).circle(p.tube_bore / 2 + c)
                        .workplane(offset=c + 0.01).circle(p.tube_bore / 2).loft())
    body = body.cut(cyl_z(p.ecas_d, T - p.ecas_bore_depth, p.ecas_bore_depth + 1))
    h = (p.tube_lead_d - p.tube_bore) / 2                     # lead-in so a tube pushed down
    zf = T - p.ecas_bore_depth                                # through the ECAS finds the bore
    body = body.cut(cq.Workplane("XY").workplane(offset=zf - h).circle(p.tube_bore / 2)
                    .workplane(offset=h + 0.01).circle(p.tube_lead_d / 2).loft())
    g0, g1 = p.ecas_groove_z
    body = body.cut(cyl_z(p.ecas_groove_d, T + g0, g1 - g0))
    c = p.ecas_top_chamfer
    body = body.cut(cq.Workplane("XY").workplane(offset=T - c).circle(p.ecas_d / 2)
                    .workplane(offset=c + 0.01).circle(p.ecas_d / 2 + c).loft())

    mx, my = p.magnet_xy
    px, py = p.pin_xy
    hp = p.pin_protrusion + p.pin_hole_extra
    mdepth = p.magnet_h + (p.hat_wire_gap if p.id_contacts and not p.pogo else 0.1)
    if p.pogo:
        # pad half, pads down, face pogo_recess above the hat face; the resistor sits in a cavity
        # above the tails, soldered across them
        zf = p.pogo_h + p.pogo_recess                         # pocket floor
        xe = p.pogo_l / 2 - p.pogo_ear_hole_inset
        cav = pogo_outline(p, zf - 0.01, zf + p.pogo_tail + p.pogo_res_h)
        for sx in (-1, 1):                                    # keep a boss under each ear's screw
            cav = cav.cut(cyl_z(2 * p.pogo_boss_r, zf - 1, p.pogo_tail + p.pogo_res_h + 2,
                                x=sx * xe, y=pogo_yc(p)))
        body = body.cut(pogo_pocket(p, 0.0, 1).union(cav))
        if p.pogo_ear_z > 0:                                  # raise the whole bosses towards the face
            for sx in (-1, 1):
                body = body.union(cyl_z(2 * p.pogo_cap_r, zf - p.pogo_ear_z, p.pogo_ear_z + 0.01,
                                        x=sx * xe, y=pogo_yc(p)))
        body = body.cut(pogo_screws(p, 0.0, 1, (-1, 1), raise_=p.pogo_ear_z))
    for s in (-1, 1):
        body = body.cut(cyl_z(p.magnet_d + p.magnet_fit, -1, mdepth + 1, x=s * mx, y=my))
    if p.id_contacts and not p.pogo:                                          # resistor slot from the back face
        z0, z1 = p.id_slot_z
        # stadium profile (round ends) seen from the back, run in Y from id_slot_y0 out of the back face
        slot = (cq.Workplane("XZ").center(0, (z0 + z1) / 2).slot2D(2 * p.id_slot_x, z1 - z0)
                .extrude(-(hd + 1 - p.id_slot_y0)).translate((0, p.id_slot_y0, 0)))
        body = body.cut(slot)
        for s in (-1, 1):            # lead slits: from the slot down into each pocket, open at the back
            w = p.id_lead_d / 2          #   face and the bottom face, so a lead is laid in, not threaded
            body = body.cut(box(s * p.id_lead_x - w, s * p.id_lead_x + w, my, hd + 1, -1, z0 + 0.2))
    body = body.cut(cyl_z(p.pin_hole_clear, -1, hp + 1, x=-px, y=py))
    body = body.cut(cq.Workplane("XY").center(px, py)
                    .slot2D(p.pin_hole_clear + p.pin_slot_len, p.pin_hole_clear).extrude(hp + 1)
                    .translate((0, 0, -1)))
    for x in (-px, px):
        body = body.cut(cq.Workplane("XY").workplane(offset=-0.01).center(x, py)
                        .circle(p.pin_hole_clear / 2 + p.pin_lead_in)
                        .workplane(offset=p.pin_lead_depth).circle(p.pin_hole_clear / 2).loft())

    if flip:
        pass                                              # stinger is part of the hat
    elif p.spine and p.spine_lock == "tslot":
        body = body.cut(spine_tslot_tool(p))
    elif p.spine:                                         # pocket for the spine top + undercuts
        body = body.cut(_spine_envelope(p, p.spine_pocket_clear, -1, p.spine_in_hat))
        hw = p.spine_groove_r + p.spine_lip_t + p.spine_pocket_clear
        zb0 = p.spine_in_hat - p.spine_barb_z[1] - 0.2
        zb1 = p.spine_in_hat - p.spine_barb_z[0] + 0.2
        y0, y1 = p.spine_barb_y
        for sx in (-1, 1):
            x0, x1 = sorted((sx * (hw - 0.1), sx * (hw + p.spine_undercut)))
            body = body.cut(box(x0, x1, y0 - 0.2, y1 + 0.2, zb0, zb1))
    # rack snap magnets in the face that enters the rack first (snap_face), pair with the plate
    depth = p.magnet_h + p.snap_recess_hat + 0.1
    y_start = hd - depth if p.snap_face == "back" else -hd - 1.0   # pocket from the chosen face
    for sx in (-1, 1):
        body = body.cut(cq.Workplane("XZ").circle((p.magnet_d + p.magnet_fit) / 2)
                        .extrude(-(depth + 1))
                        .translate((sx * p.snap_magnet_x, y_start, p.snap_magnet_z)))
    if p.dock_pin:
        # bore for the rack's dock pin, in the same face as the snap magnets, with a 45 deg mouth.
        # With the V-channel it is a vertical slot: seated (hat at 0) the pin sits at the top end,
        # at the upper stop (hat channel_play up) at the bottom end, so it never takes Z load.
        depth = p.dock_pin_protrusion + p.dock_pin_bore_extra
        d, ch = p.dock_pin_bore, p.dock_pin_chamfer
        v = p.channel_play if p.channel else 0.0
        zc = p.dock_pin_z - v / 2

        def stadium(dia, z):                    # in XY, long axis along Y, at height z
            w = cq.Workplane("XY").workplane(offset=z)
            return w.slot2D(dia + v, dia, 90) if v > 0 else w.circle(dia / 2)
        bore = stadium(d, -0.5).extrude(depth + 0.5)
        mouth = stadium(d + 2 * ch, -0.01).workplane(offset=ch).slot2D(d + v, d, 90).loft() if v > 0 else \
            stadium(d + 2 * ch, -0.01).workplane(offset=ch).circle(d / 2).loft()
        # +Z (into the hat) -> +Y, the slot's long axis (Y) -> Z; then onto the front face
        tool = bore.union(mouth).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -hd, zc))
        if p.snap_face != "front":
            tool = tool.mirror("XZ")
        body = body.cut(tool)
    return body


def stinger(p: P, above: float = 15.0):
    """The bowden tube end: stinger_len below the hat, through it, `above` mm out of the ECAS."""
    L = p.stinger_len + p.cart_h + above
    return (cq.Workplane("XY").circle(p.ptfe_od / 2).circle(1.0).extrude(L)
            .translate((0, 0, -p.stinger_len)))


def stinger_gauge(p: P) -> cq.Workplane:
    """Assembly jig: stand the hat on it, push the bowden down until it bottoms, the ECAS
    locks it at exactly stinger_len. Top face = the hat's interface plane."""
    hd, w = p.stinger_len, p.tube_bore / 2 + p.gauge_wall
    g = cq.Workplane("XY").rect(p.cart_w, p.cart_d).extrude(3.0).translate((0, 0, -3.0))
    g = g.union(cyl_z(2 * w, -hd - 3.0, hd))
    g = g.cut(cyl_z(p.tube_bore, -hd, hd + 1))
    g = g.cut(cq.Workplane("XY").workplane(offset=-0.8).circle(p.tube_bore / 2)
              .workplane(offset=0.81).circle(p.tube_bore / 2 + 0.8).loft())
    if cone_style(p):                             # room for the cone, fitted before gauging
        g = g.union(cyl_z(p.cone_d0 + 2 * (p.gauge_wall - 1), -p.cone_len - 2, p.cone_len + 2))
        c = p.spine_slot_clear
        g = g.cut(cq.Workplane("XY").workplane(offset=-p.cone_len - 0.5).circle(p.cone_d1 / 2 + c)
                  .workplane(offset=p.cone_len + 1.5).circle(p.cone_d0 / 2 + c).loft())
        if p.cone_tail > p.cone_len:
            g = g.cut(cyl_z(p.cone_d1 + 2 * c, -p.cone_tail - 0.5, p.cone_tail))
    elif p.spine:                                 # room for the spine, fitted before gauging
        g = g.cut(_spine_envelope(p, p.spine_slot_clear, -(p.spine_below + 0.5), 1.0))
    return g.mirror("XY")                         # print orientation: hat face on the bed


# ======================================================================================
def svg_solid(svg_path: str, w: float, h: float, depth: float) -> cq.Workplane:
    """SVG artwork -> solid in the XY plane, centred on the origin, fitted inside w x h,
    extruded +Z by depth. Filled paths use even-odd rule (holes in letters work)."""
    import svgelements as se
    svg = se.SVG.parse(svg_path)
    loops = []
    for el in svg.elements():
        if not isinstance(el, se.Shape) or el.fill is None or el.fill.value is None:
            continue
        path = se.Path(el)
        for sub in path.as_subpaths():
            sp = se.Path(sub)
            n = max(24, int(sp.length(error=1e-3) / 0.2)) if sp.length(error=1e-3) > 0 else 0
            pts = [sp.point(i / n) for i in range(n)] if n else []
            pts = [(q.x, -q.y) for q in pts if q is not None]          # SVG y points down
            if len(pts) >= 3:
                loops.append(pts)
    if not loops:
        raise ValueError(f"no filled paths found in {svg_path}")
    xs = [x for l in loops for x, _ in l]; ys = [y for l in loops for _, y in l]
    k = min(w / (max(xs) - min(xs)), h / (max(ys) - min(ys)))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    acc = None
    for l in loops:
        pl = [((x - cx) * k, (y - cy) * k) for x, y in l]
        try:
            sol = cq.Workplane("XY").polyline(pl).close().extrude(depth).val()
        except Exception:
            continue
        # even-odd fill: symmetric difference of all closed subpaths
        acc = sol if acc is None else acc.fuse(sol).cut(acc.intersect(sol))
    return cq.Workplane("XY").add(acc)


def _rack_outer(p: P) -> float:
    """Half-width of the hat rack (outer face of the side walls)."""
    return p.cart_w / 2 + p.flange_w + p.c_x + p.rail_wall


def _rack_key(p: P, ow: float, y0: float, grow: float = 0.0, extra: float = 0.0) -> cq.Workplane:
    """Anti-rotation key for the 2020 slot, on the face at y = y0, pointing +Y.
    45 deg underside so it prints upright without supports. grow/extra enlarge it into a groove."""
    zc = p.ext_bottom + p.ext_size / 2
    kz0, kz1, kh = zc - p.key_w / 2 - grow, zc + p.key_w / 2 + grow, p.key_h + extra
    return (cq.Workplane("YZ").polyline([(0, kz0), (kh, kz0 + kh), (kh, kz1), (0, kz1)]).close()
            .extrude(2 * ow).translate((-ow, y0, 0)))


def rack_spacer(p: P, length: float) -> cq.Workplane:
    """Block between the hat rack's plate and the top extrusion: moves the rack `length` mm away
    from the extrusion, towards the chamber centre. Same footprint as the extrusion face behind
    the rack, so it only fills volume the extrusion already occupied relative to the head.
    Front: groove for the rack's key. Back: its own key into the 2020 slot. The rack's two M3
    screws pass straight through (M3x(8 + length)). Drawn in the rack frame."""
    ow = _rack_outer(p)
    y0 = p.cart_d / 2 + p.plate_t                  # rack plate back face
    z0, z1 = p.ext_bottom, p.ext_bottom + p.ext_size
    zc = (z0 + z1) / 2
    s = box(-ow, ow, y0, y0 + length, z0, z1)
    s = s.edges("|Y").chamfer(0.6)
    # groove: key profile + clearance, a bit deeper than the key; the profile keeps its 45 deg
    # underside, so the groove roof prints fine with the block on its side
    s = s.cut(_rack_key(p, ow + 1, y0 - 0.01, grow=p.key_clear, extra=p.key_clear + 0.01))
    s = s.union(_rack_key(p, ow, y0 + length))
    for sx in (-1, 1):
        s = s.cut(cq.Workplane("XZ").circle(p.screw_d / 2).extrude(-(length + p.key_h + 2))
                  .translate((sx * p.screw_x, y0 - 1, zc)))
    return s


def _soften(w: cq.Workplane, pred, r: float, chamfer: bool = False) -> cq.Workplane:
    """Fillet (or chamfer) the edges of w that match pred(edge). Cosmetic only: if OCC can't
    build it, or the result isn't a single valid solid, w comes back unchanged."""
    edges = [e for e in w.edges().vals() if pred(e)]
    if not edges:
        return w
    try:
        sel = w.newObject(edges)
        out = sel.chamfer(r) if chamfer else sel.fillet(r)
        v = out.val()
        if v.isValid() and len(out.solids().vals()) == 1:
            return cq.Workplane().add(v)
    except Exception:
        pass
    print(f"note: rack edge softening r={r} skipped ({len(edges)} edges)")
    return w


def _edir(e):
    """Unit direction of a straight edge (None for curves)."""
    if e.geomType() != "LINE":
        return None
    d = e.endPoint() - e.startPoint()
    return d.normalized() if d.Length > 1e-6 else None


def dock(p: P) -> cq.Workplane:
    """Hat rack. v0.31 (p.channel): closed V-channel, a lower and an upper 45 deg lip per side
    wall around the hat's V-ridge rails: the hat slides in, can rise only channel_play and can't
    tilt up; whichever lip it bears on centres it in X. Flared mouth at the open end. Without
    p.channel: the open V-cradle (lower lips only). A magnet pair between the hat's snap face and
    the plate snaps it to a repeatable Y.
    Styling (p.rack_style) echoes the hat: rounded plate corners, coves where the walls meet
    the plate, softened outer edges; none of it touches a functional surface."""
    hd = p.cart_d / 2
    hw = p.cart_w / 2
    z0, w = p.flange_z, p.flange_w
    xw = hw + w + p.c_x                        # inner face of the side walls
    ow = xw + p.rail_wall
    zb = z0 - p.lip_t                          # bottom of the lips
    zt = p.flange_top + p.wall_top
    yf, yb = -hd, hd                           # hat back face touches the plate
    xl = hw + p.c_x                            # lip edge (never touches the hat body)
    yp = yb + p.plate_t                        # plate back face
    top = p.ext_bottom + p.ext_size
    zc = p.ext_bottom + p.ext_size / 2
    st = p.rack_style
    # right lip + wall in XZ; the V line is z = z0 + (x - hw), i.e. the rail underside
    zlow = lambda x: z0 + (x - hw)                          # lower lip face (rail underside, seated)
    if p.channel:
        # closed V groove: lower 45 deg lip under the rail, upper 45 deg lip over it, channel_play
        # higher than the rail's upper face. The groove bottom (apex) stays inside the wall.
        v = p.channel_play
        zup = lambda x: z0 + 2 * w + v - (x - hw)           # upper lip face
        xa, za = hw + w + v / 2, z0 + w + v / 2             # groove apex
        xi = xl                                             # both lips end hw + c_x from the axis
        zi = zup(xi)
        zt = max(zt, zi + p.channel_lip_t)
        assert xa < xw, "groove apex reaches the wall face: raise c_x or lower channel_play"
        prof = [(xl, zb), (ow, zb), (ow, zt), (xi, zt), (xi, zi), (xa, za), (xl, zlow(xl))]
    elif p.retain:
        # top retainer: underside flat at zr over the rail's outer edge, then 45 deg up to the
        # lip edge (prints upright without supports: only a retain_flat-wide flat overhang)
        zr = p.flange_top + p.lift + p.retain_gap
        xf = hw + w - p.retain_flat
        xi = p.retain_x
        zi = zr + (xf - xi)                    # underside height at the lip edge
        zt = zi + p.retain_t
        prof = [(xl, zb), (ow, zb), (ow, zt), (xi, zt), (xi, zi), (xf, zr), (xw, zr),
                (xw, z0 + (xw - hw)), (xl, z0 + (xl - hw))]
    else:
        xi = xw
        prof = [(xl, zb), (ow, zb), (ow, zt), (xw, zt), (xw, z0 + (xw - hw)), (xl, z0 + (xl - hw))]
    side = (cq.Workplane("XZ").polyline(prof).close().extrude(-(yb - yf))
            .translate((0, yf, 0)))
    if p.retain:
        # lead-in at the open end: the lip underside rises 45 deg towards the entrance, so a
        # hat coming in a little high is guided down instead of hitting the lip's face
        L = p.retain_lead
        wedge = (cq.Workplane("YZ").polyline([(yf - 1, zr - 1), (yf + L, zr), (yf + L, zr + 0.01),
                                              (yf - 1, zr + L + 1)]).close()
                 .extrude(ow - xi + 2).translate((xi - 1, 0, 0)))
        side = side.cut(wedge.intersect(box(xi - 1, xw, yf - 1, yf + L, zr - 1, zt + 1)))
    if p.channel and p.channel_flare > 0:
        # flared mouth: at the open end both groove faces open by channel_flare (and the apex moves
        # out by as much), tapering to the nominal groove over channel_flare_len. A hat arriving a
        # little high, low or off in X is steered into the channel instead of hitting a lip face.
        x0 = xl - 2.0

        def cav(s, y):
            return cq.Wire.makePolygon([cq.Vector(x0, y, zlow(x0) - s), cq.Vector(xa + s, y, za),
                                        cq.Vector(x0, y, zup(x0) + s)], close=True)
        L = p.channel_flare_len
        mouth = cq.Workplane().add(cq.Solid.makeLoft(
            [cav(p.channel_flare * (1 + 0.5 / L), yf - 0.5), cav(0.0, yf + L)], True))
        side = side.cut(mouth)
    if not st:
        side = side.faces("<Y").edges("|X").chamfer(0.8)
    d = side.union(side.mirror("YZ"))
    # back plate: in XZ, top corners rounded like the hat's footprint
    sk = cq.Workplane("XZ").center(0, (zb + top) / 2).rect(2 * ow, top - zb)
    plate = sk.extrude(-p.plate_t).translate((0, yb, 0))
    if st:
        plate = plate.edges("|Y").edges(">Z").fillet(p.rack_corner_r)
    # anti-rotation key into the 2020 slot (or the spacer's groove)
    d = d.union(plate).union(_rack_key(p, ow, yp))
    if st:
        # coves where each side wall meets the plate (outside the hat's path: |x| >= xw)
        R = p.rack_cove_r
        for sx in (-1, 1):
            x0 = xi if sx > 0 else -ow
            cove = (box(x0, x0 + (ow - xi), yb - R, yb, zt, zt + R)
                    .cut(cq.Workplane("YZ").circle(R).extrude(ow - xi + 2)
                         .translate((x0 - 1, yb - R, zt + R))))
            d = d.union(cove)
    if p.brace:
        # rib: 1 mm into the plate, foot 2 mm above the bed (no knife-edge at the bed corner)
        zr, z1 = p.ext_bottom - p.brace_gap, zb + 2.0
        for x in (-(ow - p.brace_t / 2), 0.0, ow - p.brace_t / 2):
            rib = (cq.Workplane("YZ").polyline([(yp - 1, z1), (yp - 1, zr), (yp + p.brace_d, zr),
                                                (yp, z1)]).close()
                   .extrude(p.brace_t).translate((x - p.brace_t / 2, 0, 0)))
            d = d.union(rib)
    if st:
        e = 0.01
        P = lambda g: [v.toTuple() for v in g.Vertices()]
        # 1. bed edge: 0.4 chamfer all round the outside of the footprint (elephant's foot)
        d = _soften(d, lambda g: all(abs(z - zb) < e for _, _, z in P(g)) and (
            all(abs(abs(x) - ow) < e for x, _, _ in P(g)) or all(abs(y - yp) < e for _, y, _ in P(g))
            or all(abs(y - yf) < e and abs(x) >= xl - e for x, y, _ in P(g))), 0.4, chamfer=True)
        # 2. one continuous rounded silhouette per side: wall top edge -> cove -> plate side
        #    edge -> plate top corner -> plate top edge (all tangent: a single fillet chain)
        def outline(g):
            pts = P(g)
            side_ = all(abs(abs(x) - ow) < e for x, _, _ in pts) and all(y <= yb + e for _, y, _ in pts) \
                and all(z >= zt - e for _, _, z in pts)
            topc = all(abs(y - yb) < e for _, y, _ in pts) and all(z >= top - p.rack_corner_r - e for _, _, z in pts)
            return side_ or topc
        d = _soften(d, outline, 1.0)
        # 3. open end of each wall: round its top and outer edges (the nose)
        if p.channel:
            d = _soften(d, lambda g: all(abs(y - yf) < e for _, y, _ in P(g)) and (
                all(abs(z - zt) < e for _, _, z in P(g)) or
                (all(abs(abs(x) - ow) < e for x, _, _ in P(g)) and all(z > zb + 0.3 for _, _, z in P(g)))), 1.0)
        else:
            d = _soften(d, lambda g: all(abs(y - yf) < e for _, y, _ in P(g)) and all(z > zb + 0.3 for _, _, z in P(g))
                        and all(abs(x) >= xw - e for x, _, _ in P(g))
                        and not all(abs(abs(x) - xw) < e for x, _, _ in P(g)), 1.0)
        # 4. rib tips
        d = _soften(d, lambda g: (v := _edir(g)) is not None and abs(v.x) > 0.99
                    and abs(g.Center().y - (yp + p.brace_d)) < 0.05, 0.6, chamfer=True)
    depth = p.magnet_h + p.snap_recess_rack + 0.1
    for sx in (-1, 1):
        x = sx * p.snap_magnet_x
        d = d.cut(cq.Workplane("XZ").circle((p.magnet_d + p.magnet_fit) / 2).extrude(-depth)
                  .translate((x, yb, p.snap_magnet_z)))
        d = d.cut(cq.Workplane("XZ").circle(p.snap_eject_d / 2).extrude(-(p.plate_t + p.key_h + 1))
                  .translate((x, yb, p.snap_magnet_z)))       # magnet eject hole, open at the back
    if p.dock_pin:
        # through hole for the 3x8 dowel: pressed in from the front until it sticks out
        # dock_pin_protrusion; through, so it can be pushed out from behind
        d = d.cut(cq.Workplane().add(cq.Solid.makeCylinder(
            p.dock_pin_press / 2, p.plate_t + 2, cq.Vector(0, yb - 1, p.dock_pin_z), cq.Vector(0, 1, 0))))
    if p.logo_svg:
        # clear band on the plate front: from the wall tops to just under the mounting screws
        z_lo, z_hi = zt, zc - 4.0
        logo = svg_solid(p.logo_svg, min(p.logo_w, 2 * ow - 4), min(p.logo_h, z_hi - z_lo - 2),
                         p.logo_depth + 0.2)
        # XY artwork -> plate front (normal -Y): rotate so artwork X stays X and Y becomes Z
        logo = logo.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, yb + p.logo_depth, (z_lo + z_hi) / 2))
        d = d.cut(logo)
    for sx in (-1, 1):
        d = d.cut(cq.Workplane("XZ").circle(p.screw_d / 2).extrude(-(p.plate_t + p.key_h + 2))
                  .translate((sx * p.screw_x, yb - 1, zc)))
        d = d.cut(cq.Workplane("XZ").circle(p.screw_head_d / 2).extrude(-(p.screw_head_h + 1))
                  .translate((sx * p.screw_x, yb - 1, zc)))           # counterbore from the front
        if st:   # 0.6 mm 45 deg lead-in on the counterbore mouth
            r0 = p.screw_head_d / 2
            d = d.cut(cq.Solid.makeCone(r0 + 0.6, r0, 0.6, cq.Vector(sx * p.screw_x, yb - 0.001, zc),
                                        cq.Vector(0, 1, 0)))
    return d


# ======================================================================================
def export_stl(w, path, deflection=0.01, angle=0.1):
    """Watertight STL export. The official G2E STEP has cone and planar faces that OCC's mesher
    skips (the plain exporter left ~3300 open edges and ~0.8 % of the surface missing). Converting
    to NURBS first and meshing at 0.01 mm triangulates every face; the only leftover is a
    zero-length seam edge, removed with the degenerate triangles."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.IMeshTools import IMeshTools_Parameters
    from OCP.StlAPI import StlAPI_Writer
    shape = w.val() if hasattr(w, "val") else w
    sh = BRepBuilderAPI_NurbsConvert(shape.wrapped, True).Shape()
    prm = IMeshTools_Parameters()
    prm.Deflection, prm.Angle, prm.InParallel, prm.AllowQualityDecrease = deflection, angle, True, True
    BRepMesh_IncrementalMesh(sh, prm)
    wr = StlAPI_Writer(); wr.ASCIIMode = False; wr.Write(sh, str(path))
    try:
        import trimesh
        t = trimesh.load(str(path))
        t.update_faces(t.nondegenerate_faces()); t.merge_vertices(); t.remove_unreferenced_vertices()
        if not t.is_watertight:
            print(f"WARNING: {path} is not watertight")
        t.export(str(path))
    except ImportError:
        print("trimesh not installed: STL written without the final clean-up")


def build(g2_step, fmx, out="out", p: P = P()):
    out = Path(out); out.mkdir(exist_ok=True)
    g2_body, g2parts = load_g2_part(g2_step, "front_body:1")
    fmx_body = load_fmx_body(fmx, p)

    def export(name, w):
        cq.exporters.export(w, str(out / f"{name}.step"))
        export_stl(w, out / f"{name}.stl")

    parts = {"hat": cartridge(p), "hat_rack": dock(p), "stinger_gauge": stinger_gauge(p)}
    for L in p.spacer_lens:
        # print on its side: +X face down, so the key and groove profiles are vertical sections
        sp = rack_spacer(p, L).rotate((0, 0, 0), (0, 1, 0), 90)
        bb = sp.val().BoundingBox()
        parts[f"hat_rack_spacer_{L:g}"] = sp.translate((-bb.xmin, -bb.ymin, -bb.zmin))
    if hat_flipped(p):
        pass
    elif cone_style(p):
        parts["stinger_cone"] = stinger_cone(p)
    elif p.spine:
        parts["stinger_spine"] = stinger_spine(p)
    fb = front_body_hatchanger(p, fmx_body, g2_body)
    parts["front_body_hatchanger"] = fb
    for n, w in parts.items():
        if n == "hat" and hat_flipped(p):   # print orientation: ECAS end on the bed
            w = w.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, p.cart_h))
        export(n, w)

    to_g2 = (0, AXIS_Y, p.z_if)                      # part frame -> G2E frame
    skip = ("front_body", "ECAS", "cable_chain_3", "Collet")
    asm = cq.Assembly(name="g2e_hatchanger")
    for i, (n, s) in enumerate(g2parts):
        if any(k in n for k in skip):
            continue
        asm.add(s, name=f"{i:03d}_{n}".replace(":", "_").replace("/", "_"),
                color=cq.Color(0.35, 0.35, 0.38))
    asm.add(fb, name="front_body_hatchanger", color=cq.Color(0.1, 0.1, 0.1))
    asm.add(dowel_pins(p), name="dowels", color=cq.Color(0.8, 0.8, 0.85))
    asm.add(parts["hat"].translate(to_g2), name="cartridge", color=cq.Color(0.95, 0.4, 0.1))
    asm.add(stinger(p).translate(to_g2), name="stinger", color=cq.Color(0.97, 0.97, 0.97))
    rack = parts["hat_rack"]
    if p.snap_face == "front":          # rack faces the hat's front face (e.g. front extrusion)
        rack = rack.rotate((0, 0, 0), (0, 0, 1), 180)
    asm.add(rack.translate(to_g2), name="dock", color=cq.Color(0.6, 0.6, 0.7))
    asm.export(str(out / "g2e_hatchanger_assembly.step"))

    print(f"interface plane z = {p.z_if:.2f}  -> nip {p.if_to_nip:.2f} mm below it")
    print(f"stinger: bowden sticks out {p.stinger_len:.1f} mm below the hat (set it with stinger_gauge)")
    print(f"sensor {NIP_Z - p.sensor_z:.2f} mm below the nip (macro nip_to_sensor)")
    return parts, g2parts, fb


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Build the HatChanger parts")
    ap.add_argument("g2_step", nargs="?",
                    default="Galileo2/galileo2_extruder/cad/Galileo 2 Extruder.step",
                    help="path to the official 'Galileo 2 Extruder.step' (used for the assembly)")
    ap.add_argument("--filamatrix", default="FilamATrix/CAD/Stealthburner_FilamATrix.step",
                    help="FilamATrix 'Stealthburner_FilamATrix.step' (unzipped from the repo's CAD "
                         "folder), or the filamatrix_front_body.brep a previous build cached next to it")
    ap.add_argument("--logo", default="", help="SVG engraved on the chamber side of the hat rack")
    ap.add_argument("--out", default="out", help="output directory")
    a = ap.parse_args()
    build(a.g2_step, a.filamatrix, a.out, P(logo_svg=a.logo))
