# HatChanger — Bill of Materials

Stealthburner + Galileo 2 with the FilamATrix filament cutter. Quantities for **5 lanes** (T0–T4).
The only HatChanger part on the toolhead is `front_body_hatchanger`, built on the FilamATrix G2E front body (stock G2E toolhead board mount).

## Toolhead (once)

| Qty | Item | Specification / notes |
|---:|---|---|
| 1 | `front_body_hatchanger` | Printed ABS/ASA. Replaces the G2E `front_body` (and FilamATrix's `front_body_g2e`). The +X wall in front of the toolhead board is 1 mm thinner than stock, so an SB2209 doesn't touch it |
| 2 | Dowel pin 3×8 mm | ISO 8734 / DIN 6325, hardened, m6. Press in after drilling the holes to 3.0 mm |
| 1 | 2-pin magnetic pogo connector, 2.54 mm pitch, pin half | Body 15.4 × 4.05 × 4.13 mm, 18.32 mm over the mounting ears (keep them), 1.4 mm tails, pins 1.0 mm proud. Holds the hat down with its built-in magnets and carries the hat ID. Another connector works if you set the `pogo_*` sizes in `hatchanger_cad.py` and rebuild |
| 2 | Magnet Ø6×3 mm, axial, N42SH | Front of the pad, facing the hat's bottom magnets. High-temp grade (150 °C) for chamber heat; standard N grades are rated to 80 °C |
| 1 | M1.4×5 self-tapping screw | −X ear of the pin half. The +X ear isn't screwed: the rear body's M3 screw ends right under it |
| 1 | Omron D2F switch, pin plunger | After-gears filament sensor (D2F or D2F-5, no lever), FilamATrix's +X pocket. Genuine Omron from DigiKey/Mouser or a clone |
| 1 | Steel ball 5.5 mm | Sensor ball; 304 stainless is fine |
| 2 | M2×10 self-tapping screw | Hold the D2F (as in FilamATrix) |
| 1 | M3 heat-set insert, D5 × L4 | In the bottom of `front_body_hatchanger`: upper filament guide at the blade |
| — | FilamATrix cutter, G2E version | From the [FilamATrix BOM](https://github.com/thunderkeys/FilamATrix#bill-of-materials): `[a]_cutting_arm_g2e`, `[a]_knife_holder` (or `_olfa`), `rear_body_g2e`, the Stealthburner printhead front + rear for your hotend (with its own heat-set inserts, one of them the lower blade guide), `beefy_depressor` + mount, #4 hobby blade or OLFA KB4-F/5, 0.5×4×25 spring, M2.5×16, M3 screws and inserts as listed there. **Not** their `front_body_g2e`: `front_body_hatchanger` replaces it |
| — | 2-wire lead | Switch → an IO input on the toolhead board (COM + NC or NO) |

## Hat (per lane)

| Per lane | ×5 | Item | Specification / notes |
|---:|---:|---|---|
| 1 | 5 | `hat` | Printed ABS/ASA |
| 1 | 5 | ECAS04 bowden coupler | Genuine Bondtech Push-fit ECAS 4 mm; generic clones also work |
| 4 | 20 | Magnet Ø6×3 mm, axial, N42SH | 2 in the bottom, at the front (to the head), 2 in the front face (rack snap). High-temp grade (150 °C) for chamber heat; standard N grades are rated to 80 °C |
| 1 | 5 | 2-pin magnetic pogo connector, 2.54 mm pitch, pad half | Mates with the head's pin half: holds the hat down and carries the hat ID |
| 2 | 10 | M1.4×5 self-tapping screw | Both ears of the pad half |
| (1) | (5) | Resistor, one value per lane | Hat ID (optional, `hatchanger_id.cfg`): soldered across the pad half's tails. 1/4 W axial or 1206 SMD |
| ~1 m | ~5 m | PTFE 4×2 mm bowden | One continuous tube from spool/buffer, through the hat, ending 20.5 mm below it as the stinger. Length depends on spool location |

## Hat rack (per lane)

| Per lane | ×5 | Item | Specification / notes |
|---:|---:|---|---|
| 1 | 5 | `hat_rack` | Printed ABS/ASA |
| 2 | 10 | Magnet Ø6×3 mm, axial, N42SH | Snap magnets in the plate, 0.5 mm below the face, facing the hat's front-face magnets. Push them out from the back through the Ø1 eject holes (pin or paper clip) |
| 2 | 10 | M3×8 socket head screw | ISO 4762 / DIN 912. Heads sit fully recessed in counterbores, left and right of the bowden tube |
| (1) | (5) | `hat_rack_spacer_12` or `_17` | Optional, printed ABS/ASA. Moves the rack 12 / 17 mm off the extrusion. With it, use M3×20 (12) or M3×25 (17) instead of M3×8 |
| 2 | 10 | M3 roll-in T-nut for 2020 | Standard Voron part, top front extrusion |

## PTFE rail clamp (once, optional, 8 tubes or 4 with `_4x`)

| Qty | Item | Specification / notes |
|---:|---|---|
| 1 | `ptfe_rail_clamp` | Printed ABS/ASA, one piece. Foot on top of a 2020 extrusion, tubes vertical outside the frame |
| 2 | M3×12 socket head screw | ISO 4762 / DIN 912. Foot into the T-nuts |
| 2 | M3 roll-in T-nut for 2020 | Standard Voron part |

## Printed parts

| Qty | Part | Orientation / post-processing | Est. g |
|---:|---|---|---:|
| 1 | `front_body_hatchanger` | As FilamATrix's `front_body_g2e` (front face on the bed). The sensor pocket comes with a break-away support already in the model: don't add slicer supports there. The roof of the connector pocket is an 18.5 mm bridge. Drill dowel holes to 3.0 mm, check that a hat's cone drops into its socket and lifts out freely, and check that the 5.5 mm ball rolls freely in its channel | ~25 |
| 5 | `hat` | Upside down as exported: ECAS end on the bed, stinger sleeve pointing up, no supports. All facets are 45° or less; the only overhangs are the 1.2 mm ECAS seat ring, and the horizontal magnet holes. The interface face is a top surface: ironing helps. | ~19 |
| 5 | `hat_rack` | Upright, flat bottom on the bed, no supports | ~38 |
| (5) | `hat_rack_spacer_12` or `_17` | On its side, as exported (key and groove are vertical sections), no supports | ~30 / ~43 |
| 1 | `stinger_gauge` | Flat face on the bed, as exported. Assembly jig, one is enough | ~3 |
| (1) | `ptfe_rail_clamp` | As exported: foot on the bed, bores vertical, no supports | ~19 |
| (1) | `ptfe_rail_clamp_4x` | 4-tube version, same orientation | ~12 |
| (1 set) | `tophat_*` | Optional heated-chamber top hat: parts, hardware and orientation in [TOPHAT.md](TOPHAT.md) | ~1000 |

About **85 g of ABS/ASA** (without spacers) in total (model volume × 1.05 g/cm³ × 0.7 fill factor; use your slicer's figure). Voron print settings: 0.4 nozzle, 0.2 layers, 4 walls, 5 top/bottom, 40 % infill.

## Tools

- 3.0 mm drill or reamer for the dowel holes
- Screwdriver for the M2 screws
- Soldering iron with a heat-set insert tip
- PTFE cutter (the G2E repo's `g2_ptfe_cutting_tool` works)
- High-temp epoxy for the magnets and the pogo connector halves
- Vise or arbor press for the dowels

## Assembly notes

- **Magnets:** glue every magnet with epoxy around the sides and press it **flush** with its face against a flat plate (glass) until the glue sets.
- **Pogo connector:** it sits 0.1 mm below the face in both halves, so it never holds the hat off the pad; the pins stay pressed 0.8 mm. Both halves rest on the pocket floor on their ears (the model assumes the ears are flush with the back of the body), so no plate is needed: drop each half in, check that its face is just below the surface (a straight edge across the pocket must not touch it), and screw it through the ears (Ø1.2 pilots, 4 mm deep): one screw on −X in the head, two in the hat. Add a little epoxy around the sides of the head half.
  1. **Orientation first.** Its magnets make the connector polarised: mated one way round it snaps together, the other way it pushes apart. Snap the two halves together, mark the +X end of both, and keep every pad half the same way round in every hat.
  2. **Head:** solder two thin wires (~30 AWG) to the pin half's tails, lay them in the slot behind the pocket and out of the channel on the +X side (behind the cable cover), then glue the pin half in, pins up.
  3. **Hat:** solder the hat's resistor across the pad half's tails (an axial one lies along X in the cavity above them, leads bent down), push it in resistor first, pads down, and glue it.
  4. With a hat seated, measure between the two head wires: you should read the hat's resistor.
- **Magnet polarity:** mark one face of every magnet before gluing. Glue one reference hat first (bottom and front-face magnets) and use it to orient the toolhead and every rack, so all hats attract in the same orientation. Glue the two front-face magnets of a hat with the same face outward, and check that a hat snaps flat against its rack before the glue sets.
- **Stinger:**
  1. Cut the bowden end square and lightly chamfer its outer edge. Push it down through the ECAS, the hat and the sleeve.
  2. Stand the hat on the `stinger_gauge` (it has a pocket for the cone) and push until the tube bottoms in the gauge; the ECAS then holds it 20.5 mm below the hat (about 3.5 mm of bare tube below the sleeve).
- **Stinger fit in the head:** the tube must slide freely in the 4.6 mm seat of `front_body_hatchanger`. Tune `seat_d` in `hatchanger_cad.py` for your printer.
- **Cone socket in the head:** the cone fits with 0.1 mm per side (`cone_clear`) and the tail bore below it with 0.3 mm (`cone_tail_clear`), so only the cone locates. The socket prints as a horizontal hole (front face on the bed), so check it with a printed hat: its cone should drop in under its own weight and lift out without sticking, with no wobble once seated. If it binds, raise `cone_clear` by 0.05 and reprint the front body; if it wobbles, lower it. The mouth (Ø8.4) can't grow: it is 0.9 mm from the connector pocket.
- **Grab test by hand:** with the hat off the head, set the stinger with the gauge and let the filament hang out of it by the docked length (~13 mm). Push the stinger slowly into the seat: the tip should slide down the 20° lead-in into the Ø2.1 hole without being pushed back into the tube. If it still stubs, check the tip itself (a blob or a hooked string catches anywhere) before blaming the geometry.
- **Filament drift while docked:** there is no filament brake; friction in the bowden holds the tip in place. If your spool holder pulls filament back (tensioned spool, respooler), check that the tip stays put after a hat has been docked for a while.
- **Cutter:** build the FilamATrix G2E cutter as in their [manual](https://armoredturtle.xyz/manual.html?manual=filamatrix), using `front_body_hatchanger` in place of their `front_body_g2e`. Melt the D5×L4 M3 insert into the bottom of the front body (the Ø4.6 pocket on the filament axis): it is the upper blade guide, so set it flush and square. Cut the hotend PTFE (2 mm ID) with their jig for your hotend. Mount the depressor pin on the gantry (the rear is clear of the racks on the front extrusion) and calibrate `cut_x_touch` / `cut_x_cut` / `cut_y` with `HAT_CUT`.
- **Filament sensor:** FilamATrix's after-gears pocket on the +X side. It comes with a break-away support printed inside (a separate body of thin horizontal layers, as in FilamATrix): pull it out with pliers and clean the pocket first. Drop the 5.5 mm ball into its channel, slide the D2F in plunger-first and fix it with the two M2×10 self-tapping screws. They go in from the front face: the heads sit in Ø4.2 counterbores, the screws thread into the front wall (Ø1.8 pilot) and pass through the switch's mounting holes. Solder two wires (COM + NC or NO). Test with `QUERY_FILAMENT_SENSOR SENSOR=hat_toolhead` by pushing filament through by hand.
- **Macros:** `variable_nip_to_sensor` is 19.85 and `variable_nip_to_cut` 38.35. Measure `variable_nozzle_to_nip` on your hotend (gear contact line to nozzle tip, along the filament).
- **PTFE rail clamp:** drop the T-nuts into the top slot of the extrusion, set the foot on top with the block over the outer edge and fix it with the two M3×12. Cut each tube square, chamfer its edge lightly and push it through its bore with a slight twist: it should slide through freely (4.50 mm bores, no friction band). If it doesn't, ream the bore with a 4.5 mm drill, or rebuild with a larger `BORE_D`. The tubes pass 5 mm outside the extrusion face (`OUTSET`): place the clamp between two panel clips, or raise `OUTSET` if your clips stick out further.
- **Reused parts:** the rest of the Galileo 2 and the Stealthburner are stock, apart from the FilamATrix parts above.
