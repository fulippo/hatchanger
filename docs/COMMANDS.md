# Commands

| Command | What it does |
|---|---|
| `HAT_CHANGE LANE=n` / `Tn` | Full change: dock the current hat, pick up lane n, load, purge, return. Does nothing if lane n is already loaded. |
| `HAT_START LANE=n` | `START_PRINT` hook: lane n on the head and loaded before the start purge. `TEMP=t` heats first; `STUB=0/1` overrides `start_stub`. |
| `HAT_PICKUP LANE=n` | Pick up lane n (docking the current hat first) and load it. `TO_NOZZLE=0` stops after the grab check; `STUB=0` leaves the cut stub for your own purge; `MIN_TEMP=` overrides `min_melt_temp` once. |
| `HAT_DOCK` | Cut (if the sensor sees filament), unload and dock the hat on the head. `CUT=0` skips the cut for a hat that isn't loaded to the nozzle; `RELEASE=mm` overrides `release_margin`. |
| `HAT_STATUS` | Shows which hat the macros think is on the head, whether it is loaded, what the sensor reads and the nozzle temperature. |
| `HAT_SET_STATE LANE= LOADED=` | Corrects the state after moving a hat by hand (`LANE=-1`: head empty). Nothing moves. |
| `HAT_CUT` | Presses the cutting arm and comes back (calibration). |
| `HAT_CAL_DOCK LANE=n STEP=0..3` | Hat on the head: walks the dock approach in stages; `STEP=0` backs out. |
| `HAT_CAL_PICKUP LANE=n GAP=5` | Empty head: stops `GAP` mm under a docked hat, for jogging the dock position. |
| `HAT_TEST_LANE LANE=n COUNT=10` | Repeated pickups and drop-offs of one lane, without loading the nozzle. `DWELL=s` between cycles. |
| `HAT_TEST_ALL COUNT=5` | The same for every lane in turn (`LANES=1,0` to choose). |

`HAT_PICKUP`, `HAT_DOCK` and the test commands accept `DRY=1`: the same movements without
turning the extruder (pull the filament out of the hats first).

## Change sequence in detail

**Drop-off (`HAT_DOCK`)**

1. If the sensor sees filament, the head presses the cutting arm against its pin. The filament
   is cut about 38 mm below the extruder gears.
2. The head slides the hat into its rack's channel up to the plate (the last few millimetres
   slowly) and sets it on the lower lips. The filament is still in the gears.
3. The extruder pulls the cut end up until the sensor clears, then moves it a fixed distance to
   just below the gears, where it is still gripped. This happens in the rack on purpose: the
   bowden drags on the filament and pulls the hat up, and the rack's upper lips hold it down
   whatever the bowden's angle (the head's magnets alone don't, at a steep angle).
   If this step fails, the head stays in the rack under the hat and every HatChanger command
   refuses to move. Fix the cause, then run `HAT_DOCK` again: it finishes from step 3.
4. The head moves down while the extruder reverses by the same amount. The filament stays still
   in the hat, the magnets let go and the tip slides out of the gears.

**Pickup (`HAT_PICKUP`)**

1. If another hat is on the head, it is docked first. Then the extruder pushes some filament
   forward and back with the head empty: if the sensor sees filament, a hat is on the head after
   all and the pickup stops before moving.
2. The head rises under the hat with the extruder turning in sync with Z for the whole rise, so
   the gears catch the hanging filament as the hat seats on the head.
3. The head lifts the hat off the lower lips (mid-channel) and slides it out of the rack.
4. The extruder pushes until the sensor sees filament, which confirms the grab.
5. The extruder loads the new filament to just above the blade, short of the stub left by the
   last cut, so nothing comes out of the nozzle in place. The stub (about 43 mm) is then pushed
   out by the purge macro or, without one, at `load_park_xy`.
