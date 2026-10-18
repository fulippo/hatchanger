# CAD

## Parts

| Part | Qty | What it does |
|---|---|---|
| `front_body_hatchanger` | 1 | Replaces the Galileo 2 `front_body`. Built on the FilamATrix G2E front body: its bottom half holds the upper blade guide (M3 heat-set insert), the filament channel, the after-gears sensor (19.85 mm below the gears) and the cutting-arm clearance. The top is the hat interface: a flat pad, two dowel pins at the front, two magnets at the back, the cone socket and a lead-in into the gears. FilamATrix's pre-gear sensor isn't used: its pocket is filled solid. |
| `main_body_hatchanger_cw2` | 1 (Clockwork 2 instead of `front_body_hatchanger`) | Replaces the Clockwork 2 `main_body`. Built on the FilamATrix CW2 dual-switch main body (both D2F sensors kept). Same hat interface, raised 5.5 mm so the pad clears the CW2 latch, and a 40 mm stinger. The hat and rack prints are the G2E ones; only the bowden is set longer. See [Clockwork 2](#clockwork-2). |
| `stinger_gauge_cw2` | 1 (Clockwork 2) | `stinger_gauge` for the 40 mm CW2 stinger. |
| `hat` | 1 per lane | Printed in one piece, faceted so it prints upside down without supports. ECAS04 on top. The bowden runs straight through and ends 20.5 mm below the hat, inside a printed cone and sleeve that seat in the head. Magnets underneath (to the head) and in the front face (to the rack), plus V-ridge side rails with a tapered nose. |
| `hat_rack` | 1 per lane | V-channel bolted to the top front extrusion. The hat's rails slide between a lower and an upper 45° lip on each side wall (1.2 mm of vertical play, flared mouth). Two magnet pairs snap the hat against the plate. |
| `hat_rack_spacer_12` / `_17` | optional | Moves a rack 12 or 17 mm off the extrusion, towards the chamber, if the head can't reach far enough. |
| `stinger_gauge` | 1 | Assembly jig that sets how far the bowden sticks out of each hat. |
| `ptfe_rail_clamp` / `_4x` | optional | Holds 8 (or 4) bowden tubes side by side, vertical, just outside the frame, on top of a 2020 extrusion. Guides the tubes and keeps them apart; it doesn't grip them. |

## Clockwork 2

`main_body_hatchanger_cw2` puts the HatChanger interface on the FilamATrix Clockwork 2 main body.
The hat, rack and spacer prints are the same as for Galileo 2. Only the bowden is set
longer: 40 mm below the hat instead of 20.48, with `stinger_gauge_cw2`. A hat moves between a
G2E and a CW2 head by re-setting its tube with the other gauge.

What changes compared with `front_body_hatchanger`:

- **The interface is 5.5 mm higher** (z 136.3 in the CW2 frame vs 130.8). The CW2 latch rises to
  z 130.93 behind the axis, under the -X magnet. The pad bridges over it with 0.4 mm of
  clearance, and the latch still slides in from the back before the motor plate. The hat-ID
  wire channel has 1.2 mm of floor above the latch.
- **40 mm stinger.** The CW2 gears are 50.0 mm below the hat (30.6 on G2E). With the G2E
  stinger, a docked hat would leave 32.5 mm of bare filament hanging below the bowden, enough
  to curve it. The 4.6 mm seat therefore runs down to z 95.8, 9.5 mm above the nip as on G2E,
  which leaves about 13 mm bare, the same as on G2E. The stock ECAS pocket and the 4.2 mm PTFE
  channel are filled. The CW2 M3x20 next to the channel (z 114.9) passes 0.06 mm from the tube,
  as it does from the stock PTFE.
- **Only the after-gears sensor stays.** It sits 10.12 mm below the nip. The pre-gear D2F
  pocket, its ball channel and its M2 holes are filled with the No_Switch body's material,
  because the seat now runs through it.
- **Docked hats hang about 19.5 mm lower** (40 mm of bowden + 13 mm of filament), so
  `z_clear` / `z_clear_loaded` grow by about that much, and so does the print-height limit for a
  change (see the CW2 values in `hatchanger.cfg`).

Print it on its front face, like the stock CW2 main body. The pad grows up from the bed, so it
needs no supports.

Build:

```sh
python cad/source/hatchanger_cad.py --extruder cw2 \
    --filamatrix FilamATrix/CAD/Stealthburner_FilamATrix.step \
    --cw2-stl FilamATrix/STLs/Clockwork2/main_body_clockwork2_dual_switch.stl
```

The first run reads the ~220 MB FilamATrix assembly and caches its CW2 parts in a `cw2_cache/`
folder next to it. Later runs can pass that folder to `--filamatrix`.

OCC meshes a few stock faces low on the CW2 body with gaps. Below z 86.77, where nothing
changed, the STL therefore uses FilamATrix's own CW2 STL, joined to the new top with manifold3d
(`pip install manifold3d trimesh`). The STEP is built entirely from the B-rep.
