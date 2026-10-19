# Top hat (heated chamber)

The bowden tube of the loaded hat follows the toolhead, and its arc rises about 60 mm above the
top extrusions (docked, and at max Z). The top hat raises the stock top panel so the chamber stays
closed: an 85 mm wall standing on the top extrusions, with the tubes leaving through grommets in
the rear wall.

![Top hat](images/tophat_3q.png)

## Design

- **Same footprint as the frame.** The wall is 20 mm wide, right on top of the top extrusions,
  so the inside of the chamber is unchanged and the stock top panel sits on top of it.
- **A printed 2020 on top.** The top 20 mm of the wall has T-slots on the top, outer and inner
  faces (6.2 mm opening, 6.1 mm deep). Panel clips, LED bars, tube guides and anything else you
  clamp on a top extrusion fit here, with roll-in or spring T-nuts. The outer slot wraps around
  the corners; the side slots are interrupted for 12 mm at each frame screw. The walls between
  the slots are thin, as on a real 2020, so clamp light parts.
- **Foam gaps.** The pieces are 2.5 mm apart: fill each joint with a 3 mm closed-cell foam strip.
  Foam tape also goes under the wall (on the extrusion) and under the panel.
- **Screwed to the frame.** Two M3 × 10 screws per piece into roll-in T-nuts in the frame's top
  slots. Each screw drops down a 7 mm shaft from the printed top slot and is tightened through
  the slot with a long 2.5 mm hex key (at least 90 mm).
- **Bowden exits at the back.** The rear centre has 8 holes of 12 mm (2 rows of 4, 35 and 51 mm
  above the frame) with TPU grommets: 4.3 mm bore and a 3.8 mm lip that seals on the 4 mm PTFE
  while letting it slide. Unused holes take the blank plug.
- **Voron style.** Recessed panels with a honeycomb (or voronoi) pattern, chamfered edges, a
  plain 20 mm column at each corner over the vertical extrusion, "HatChanger" on the front.

| Front | Rear |
|---|---|
| ![Front](images/tophat_front.png) | ![Rear](images/tophat_rear.png) |

| Corner (honeycomb) | Corner (voronoi) |
|---|---|
| ![Corner](images/tophat_corner.png) | ![Voronoi](images/tophat_voronoi.png) |

![Wall profile](images/tophat_profile.png)

## Parts

All pieces fit a 300 mm bed. Print in ASA/ABS, upright (bottom on the bed), no supports, 4 walls,
15–20 % infill (the infill is the insulation). About 0.9 kg of filament for the walls.

| Part | Qty | Where |
|---|---:|---|
| `tophat_corner` | 4 | Corners: one design, rotated (120 × 120 × 85 mm) |
| `tophat_centre` | 2 | Left and right sides (215 × 20 × 85 mm) |
| `tophat_centre_front` | 1 | Front, "HatChanger" plaque |
| `tophat_centre_rear` | 1 | Rear, bowden exits |
| `tophat_grommet_tpu` | 1 per tube | TPU 95A, in the rear holes, flange outside |
| `tophat_plug_tpu` | 1 per unused hole | TPU 95A |

The `_voronoi` files are the same pieces with a voronoi pattern instead of the honeycomb.

## Hardware

| Qty | Item |
|---:|---|
| 16 | M3 × 10 socket head screw |
| 16 | M3 roll-in (spring) T-nut for 2020, in the frame's top slots |
| ~4 m | 3 mm closed-cell foam tape, 10–20 mm wide (joints, under the wall, under the panel) |
| – | T-nuts for the printed slots as needed (panel clips etc.) |
| 1 | Long 2.5 mm hex key, ≥ 90 mm (ball end helps) |

## Fitting

1. Put foam tape on the top face of the top extrusions, leaving the slot open where the screws go.
2. Drop a roll-in T-nut into the frame's top slot under each screw shaft.
3. Place the corners, then the centres, with a foam strip in each 2.5 mm joint.
4. Drop an M3 × 10 down each shaft (through the printed top slot) and tighten with the long key.
5. Push the grommets into the rear holes from outside, thread the bowdens through them.
6. Foam tape on top of the wall, then the top panel, held with panel clips in the printed top slot.

## Rebuilding

```
python3 cad/source/tophat.py                     # honeycomb -> cad/stl, cad/step
python3 cad/source/tophat.py --pattern voronoi   # *_voronoi files
python3 cad/source/tophat.py --height 95         # taller wall
```

Everything else (corner arm length, foam gap, slot dimensions, text, hole layout, pattern pitch)
is in the `C` dataclass at the top of the source.
