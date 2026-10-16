# HatChanger — Bill of Materials

Stealthburner + Galileo 2 with the FilamATrix filament cutter. Quantities for **5 lanes** (T0–T4).
The only HatChanger part on the toolhead is `front_body_hatchanger`, built on the FilamATrix G2E front body (stock G2E toolhead board mount).
Prices checked September 2026 at the sources linked at the bottom, converted roughly to €, VAT and shipping excluded.

## Toolhead (once)

| Qty | Item | Specification / notes | € each | € total |
|---:|---|---|---:|---:|
| 1 | `front_body_hatchanger` | Printed ABS/ASA. Replaces the G2E `front_body` (and FilamATrix's `front_body_g2e`). The +X wall in front of the toolhead board is 1 mm thinner than stock, so an SB2209 doesn't touch it | — | — |
| 2 | Dowel pin 3×8 mm | ISO 8734 / DIN 6325, hardened, m6. Press in after drilling the holes to 3.0 mm | 0.15 | 0.30 |
| 2 | Magnet Ø6×3 mm, axial, N42SH | High-temp grade (150 °C) for chamber heat; standard N grades are rated to 80 °C | 0.55 | 1.10 |
| 1 | Omron D2F switch, pin plunger | After-gears filament sensor (D2F or D2F-5, no lever), FilamATrix's +X pocket. Price not checked: genuine Omron from DigiKey/Mouser, clones are cheaper | — | — |
| 1 | Steel ball 5.5 mm | Sensor ball; 304 stainless is fine. Sold in packs (50 for about $11) | 0.20 | 0.20 |
| 2 | M2×10 self-tapping screw | Hold the D2F (as in FilamATrix) | 0.05 | 0.10 |
| 1 | M3 heat-set insert, D5 × L4 | In the bottom of `front_body_hatchanger`: upper filament guide at the blade | 0.10 | 0.10 |
| — | FilamATrix cutter, G2E version | From the [FilamATrix BOM](https://github.com/thunderkeys/FilamATrix#bill-of-materials): `[a]_cutting_arm_g2e`, `[a]_knife_holder` (or `_olfa`), `rear_body_g2e`, the Stealthburner printhead front + rear for your hotend (with its own heat-set inserts, one of them the lower blade guide), `beefy_depressor` + mount, #4 hobby blade or OLFA KB4-F/5, 0.5×4×25 spring, M2.5×16, M3 screws and inserts as listed there. **Not** their `front_body_g2e`: `front_body_hatchanger` replaces it | — | — |
| — | 2-wire lead | Switch → an IO input on the toolhead board (COM + NC or NO) | — | — |
| — | 2 thin wires (hat ID) | ~30 AWG, from under the two head magnets, through the channel in the pad, out on the +X side behind the cable cover, to the hat-ID reader | — | — |
| 1 | Hat-ID reader (optional) | ADS1115 breakout module + 10k divider, see [Hat ID](HAT_ID.md) | — | — |
| — | 4-wire lead | Reader → SB2209 USB `I2C` header (5V, GND, SCL, SDA) | — | — |

## Hat (per lane)

| Per lane | ×5 | Item | Specification / notes | € each | € ×5 |
|---:|---:|---|---|---:|---:|
| 1 | 5 | `hat` | Printed ABS/ASA | — | — |
| 1 | 5 | ECAS04 bowden coupler | Genuine Bondtech Push-fit ECAS 4 mm; generic clones are a few cents each | 1.50 | 7.50 |
| 4 | 20 | Magnet Ø6×3 mm, axial, N42SH | 2 in the bottom (head, also the ID contacts: keep the nickel plating), 2 in the front face (rack snap) | 0.55 | 11.00 |
| 1 | 5 | Resistor, ¼ W axial, 1 % | Hat ID: a different value per lane (lane 0–5: 1k, 2.2k, 4.7k, 10k, 22k, 47k), in the slot at the back of the hat, leads under the two bottom magnets | 0.02 | 0.10 |
| ~1 m | ~5 m | PTFE 4×2 mm bowden | One continuous tube from spool/buffer, through the hat, ending 20.5 mm below it as the stinger. Length depends on spool location | 3.00 | 15.00 |

## Hat rack (per lane)

| Per lane | ×5 | Item | Specification / notes | € each | € ×5 |
|---:|---:|---|---|---:|---:|
| 1 | 5 | `hat_rack` | Printed ABS/ASA | — | — |
| 2 | 10 | Magnet Ø6×3 mm, axial, N42SH | Snap magnets in the plate, 0.5 mm below the face, facing the hat's front-face magnets. Push them out from the back through the Ø1 eject holes (pin or paper clip) | 0.55 | 5.50 |
| 2 | 10 | M3×8 socket head screw | ISO 4762 / DIN 912. Heads sit fully recessed in counterbores, left and right of the bowden tube | 0.05 | 0.50 |
| (1) | (5) | `hat_rack_spacer_12` or `_17` | Optional, printed ABS/ASA. Moves the rack 12 / 17 mm off the extrusion. With it, use M3×20 (12) or M3×25 (17) instead of M3×8 | — | — |
| 2 | 10 | M3 roll-in T-nut for 2020 | Standard Voron part, top front extrusion | 0.10 | 1.00 |

## PTFE rail clamp (once, optional, 8 tubes or 4 with `_4x`)

| Qty | Item | Specification / notes | € each | € total |
|---:|---|---|---:|---:|
| 1 | `ptfe_rail_clamp` | Printed ABS/ASA, one piece. Foot on top of a 2020 extrusion, tubes vertical outside the frame | — | — |
| 2 | M3×12 socket head screw | ISO 4762 / DIN 912. Foot into the T-nuts | 0.05 | 0.10 |
| 2 | M3 roll-in T-nut for 2020 | Standard Voron part | 0.10 | 0.20 |

## Printed parts

| Qty | Part | Orientation / post-processing | Est. g |
|---:|---|---|---:|
| 1 | `front_body_hatchanger` | As FilamATrix's `front_body_g2e` (front face on the bed). The sensor pocket comes with a break-away support already in the model: don't add slicer supports there. Drill dowel holes to 3.0 mm, check that a hat's cone drops into its socket and lifts out freely, and check that the 5.5 mm ball rolls freely in its channel | ~25 |
| 5 | `hat` | Upside down as exported: ECAS end on the bed, stinger sleeve pointing up, no supports. All facets are 45° or less; the only overhangs are the 1.2 mm ECAS seat ring, the resistor slot roof (a short bridge) and the horizontal magnet holes. The interface face is a top surface: ironing helps. | ~19 |
| 5 | `hat_rack` | Upright, flat bottom on the bed, no supports | ~38 |
| (5) | `hat_rack_spacer_12` or `_17` | On its side, as exported (key and groove are vertical sections), no supports | ~30 / ~43 |
| 1 | `stinger_gauge` | Flat face on the bed, as exported. Assembly jig, one is enough | ~3 |
| (1) | `ptfe_rail_clamp` | As exported: foot on the bed, bores vertical, no supports | ~19 |
| (1) | `ptfe_rail_clamp_4x` | 4-tube version, same orientation | ~12 |

About **85 g of ABS/ASA** (without spacers) in total (model volume × 1.05 g/cm³ × 0.7 fill factor; use your slicer's figure), about €2 of filament. Voron print settings: 0.4 nozzle, 0.2 layers, 4 walls, 5 top/bottom, 40 % infill.

## Cost summary

| | € |
|---|---:|
| Toolhead (once, excluding the D2F switch and the FilamATrix parts) | 1.80 |
| Each lane, including 1 m bowden | 7.95 |
| PTFE rail clamp (optional) | 0.30 |
| Filament | 2.00 |
| **Total, 5 lanes with new bowden** | **~44 + switch** |
| **Total, 5 lanes reusing your tubes** | **~29 + switch** |

## Tools

- 3.0 mm drill or reamer for the dowel holes
- Screwdriver for the M2 screws
- Soldering iron with a heat-set insert tip
- PTFE cutter (the G2E repo's `g2_ptfe_cutting_tool` works)
- High-temp epoxy for the magnets
- Vise or arbor press for the dowels

## Assembly notes

- **Hat ID contacts:** the two bottom magnets of each hat and the two pad magnets of the head double as electrical contacts, so their faces must touch across the interface:
  1. Hat: slide the resistor into the slot in the back face (it sits above the magnets). From each end, a 1.0 mm slit runs down through the back wall into a magnet pocket, open at the back and at the bottom: lay each lead into its slit from behind (no threading), bend the end flat against the pocket ceiling from the bottom side and trim it to ~3 mm. Glue the magnet in on top of it with epoxy around the sides, and press it **flush** with the bottom face against a flat plate (glass) until the glue sets. The lead is trapped between the magnet and the pocket (0.7 mm deeper than the magnet, for the 0.6 mm lead). A drop of glue in the slot keeps the resistor from rattling.
  2. Head: push two thin wires into the channel opening on the +X side of the pad and along the channel that runs behind the magnet pockets (2.4 × 2.2 mm); each wire drops into its pocket through a small notch at the floor, strip ~4 mm, lay each end flat on a magnet pocket floor (the head pockets are 0.5 mm deeper than the magnet: 26–30 AWG, squashed flat) and glue the magnets flush the same way.
  3. Check with a multimeter between the two head wires with a hat seated: you should read the hat's resistor. Then connect them to the reader and run `HAT_ID`.
- **Magnet polarity:** mark one face of every magnet before gluing. Glue one reference hat first (bottom and front-face magnets) and use it to orient every other hat, the toolhead and every rack, so all hats attract in the same orientation. Glue the two front-face magnets of a hat with the same face outward, and check that a hat snaps flat against its rack before the glue sets.
- **Stinger:**
  1. Cut the bowden end square and lightly chamfer its outer edge. Push it down through the ECAS, the hat and the sleeve.
  2. Stand the hat on the `stinger_gauge` (it has a pocket for the cone) and push until the tube bottoms in the gauge; the ECAS then holds it 20.5 mm below the hat (about 3.5 mm of bare tube below the sleeve).
- **Stinger fit in the head:** the tube must slide freely in the 4.6 mm seat of `front_body_hatchanger`. Tune `seat_d` in `hatchanger_cad.py` for your printer.
- **Cone socket in the head:** the cone fits with 0.1 mm per side (`cone_clear`) and the tail bore below it with 0.3 mm (`cone_tail_clear`), so only the cone locates. The socket prints as a horizontal hole (front face on the bed), so check it with a printed hat: its cone should drop in under its own weight and lift out without sticking, with no wobble once seated. If it binds, raise `cone_clear` by 0.05 and reprint the front body; if it wobbles, lower it. The mouth (Ø8.4) can't grow: it is 0.8 mm from the magnet pockets.
- **Grab test by hand:** with the hat off the head, set the stinger with the gauge and let the filament hang out of it by the docked length (~13 mm). Push the stinger slowly into the seat: the tip should slide down the 20° lead-in into the Ø2.1 hole without being pushed back into the tube. If it still stubs, check the tip itself (a blob or a hooked string catches anywhere) before blaming the geometry.
- **Filament drift while docked:** there is no filament brake; friction in the bowden holds the tip in place. If your spool holder pulls filament back (tensioned spool, respooler), check that the tip stays put after a hat has been docked for a while.
- **Cutter:** build the FilamATrix G2E cutter as in their [manual](https://armoredturtle.xyz/manual.html?manual=filamatrix), using `front_body_hatchanger` in place of their `front_body_g2e`. Melt the D5×L4 M3 insert into the bottom of the front body (the Ø4.6 pocket on the filament axis): it is the upper blade guide, so set it flush and square. Cut the hotend PTFE (2 mm ID) with their jig for your hotend. Mount the depressor pin on the gantry (the rear is clear of the racks on the front extrusion) and calibrate `cut_x_touch` / `cut_x_cut` / `cut_y` with `HAT_CUT`.
- **Filament sensor:** FilamATrix's after-gears pocket on the +X side. It comes with a break-away support printed inside (a separate body of thin horizontal layers, as in FilamATrix): pull it out with pliers and clean the pocket first. Drop the 5.5 mm ball into its channel, slide the D2F in plunger-first and fix it with the two M2×10 self-tapping screws. They go in from the front face: the heads sit in Ø4.2 counterbores, the screws thread into the front wall (Ø1.8 pilot) and pass through the switch's mounting holes. Solder two wires (COM + NC or NO). Test with `QUERY_FILAMENT_SENSOR SENSOR=hat_toolhead` by pushing filament through by hand.
- **Macros:** `variable_nip_to_sensor` is 19.85 and `variable_nip_to_cut` 38.35. Measure `variable_nozzle_to_nip` on your hotend (gear contact line to nozzle tip, along the filament).
- **PTFE rail clamp:** drop the T-nuts into the top slot of the extrusion, set the foot on top with the block over the outer edge and fix it with the two M3×12. Cut each tube square, chamfer its edge lightly and push it through its bore with a slight twist: it should slide through freely (4.50 mm bores, no friction band). If it doesn't, ream the bore with a 4.5 mm drill, or rebuild with a larger `BORE_D`. The tubes pass 5 mm outside the extrusion face (`OUTSET`): place the clamp between two panel clips, or raise `OUTSET` if your clips stick out further.
- **Reused parts:** the rest of the Galileo 2 and the Stealthburner are stock, apart from the FilamATrix parts above.

## Price sources

- ECAS04: [Bondtech, Push-fit ECAS 4 mm](https://www.bondtech.se/product/push-fit-ecas-4mm/), [3DJake](https://www.3djake.com/bondtech/push-fit-ecas)
- N42SH 6×3 magnet: [K&J Magnetics D42SH](https://www.kjmagnetics.com/d42sh-neodymium-high-temp-disc-magnet) (closest imperial size, 1/4" × 1/8")
- PTFE tube: [Hotend.eu](https://www.hotend.eu/ptfe-tubes)
- 5.5 mm steel balls: [50 pcs, 304 stainless (eBay)](https://www.ebay.com/itm/157089518424)
- D2F switch: [Omron D2F-5 at DigiKey](https://www.digikey.com/en/products/detail/omron-electronics-inc-emc-div/D2F-5/8593136)
