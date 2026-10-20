# HatChanger with AFC

HatChanger can run as a unit of the Armored Turtle
[AFC-Klipper-Add-On](https://github.com/ArmoredTurtle/AFC-Klipper-Add-On), in place of a Box
Turtle. The work is split like this:

- **AFC** handles the T commands, the lane-to-tool mapping, Spoolman, lane colours and
  materials, the poop/wipe/kick hooks, pause/resume on errors, and the Mainsail/Fluidd AFC panel.
- **HatChanger's macros** still do every move. AFC's "load lane" becomes `HAT_PICKUP` and its
  "unload lane" becomes `HAT_DOCK`, called by `klipper/extras/AFC_HatChanger.py`.

Each hat is an AFC lane with no motor and no sensors. AFC's own cut, park, tip forming and
bowden moves are skipped for these lanes, because `HAT_DOCK` already cuts the filament.

## Install

1. **Install AFC** with its installer:

   ```sh
   cd ~ && git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
   cd AFC-Klipper-Add-On && ./install-afc.sh
   ```

   Its menu needs a unit type, and HatChanger isn't one of them. Answer like this
   (`./hatchanger/install.sh --afc-help` prints the same list):

   | Option | Set to | Why |
   |---|---|---|
   | T. Installation type | BoxTurtle (4-Lane) | any unit works: HatChanger's installer disables its files |
   | 3. Toolhead cutter | False | `HAT_DOCK` cuts with the FilamATrix |
   | 5. Kick / 6. Park / 8. Wipe | False | left on with placeholder positions, AFC refuses every tool change |
   | 9. Toolhead sensor | Sensor (pin left Unknown) | no TurtleNeck buffer |
   | B. Buffer type | None (press B until it says None) | otherwise it asks for buffer pins |
   | C. Unit name | anything | the HatChanger unit has its own name |

   Klipper shows an error (`Unknown is not valid for pin_tool_start`) until the next step has
   run. That's expected.
2. **Run HatChanger's installer:** `./hatchanger/install.sh --afc`. It:
   - links the macros and the unit driver (`AFC_HatChanger.py`) into Klipper;
   - copies `hatchanger_afc.cfg` (the lanes) into `~/printer_data/config/hatchanger/`;
   - writes the include block (without `hatchanger_tools.cfg`: AFC creates `T0`, `T1`, …);
   - sets `tool_cut`, `park` and `form_tip` to `False` in `AFC/AFC.cfg`, because `HAT_DOCK`
     cuts the filament;
   - points AFC's purge (`poop_cmd`) at your `purge_macro` (Blobifier) and turns off `kick`
     and `wipe` if their positions were never set: AFC refuses every tool change otherwise;
   - creates AFC's lane state file (`AFC.var.unit`) if it doesn't exist yet;
   - offers to disable the AFC unit files generated for a unit you don't have
     (`AFC_Hardware.cfg`, and the unit file whatever you named it: `AFC_Turtle_1.cfg`, …).
3. **Set one `[AFC_lane]` per hat** in `hatchanger/hatchanger_afc.cfg`. `unit: HatChanger_1:1`
   is hat lane 0 (the first X in `lane_x`), `:2` is hat lane 1, and so on.
4. **Purge.** The installer has set AFC's `poop_cmd` to your `purge_macro` (`BLOBIFIER`). If
   you have no purge macro it turned `poop` off instead: then HatChanger pushes the cut stub
   out at `load_park_xy`, so set that in `hatchanger_user.cfg`. The purge after a change also
   pushes out the cut stub, about 43 mm of the old filament (`nozzle_to_nip - nip_to_cut`):
   purge that much more than the colour change alone needs. The unit option
   `leave_stub_for_poop` overrides who pushes the stub out.
5. **Restart Klipper** (the installer offers to) and force-reload Mainsail (Ctrl+F5). The AFC
   panel needs Mainsail 2.15 or newer. At startup, `PREP` lists each lane as `DOCKED`,
   `HAT ON THE HEAD` or `LOADED IN TOOLHEAD`, based on the HatChanger state.
6. **Check.** After a restart the installer runs `./hatchanger/install.sh --check`. It asks
   Moonraker whether Klipper started, whether AFC loaded only the HatChanger unit, whether
   AFC and HatChanger agree on the loaded hat, whether any AFC macro would block a tool change,
   and lists the errors in the console since the restart. Run it again any time.

To go back to a Box Turtle (or plain AFC), run `./hatchanger/install.sh --uninstall`. It
puts back the `AFC.cfg` values and the AFC hardware files the install changed.

## Keeping AFC and HatChanger in step

HatChanger's state is the source of truth: which hat is on the head, and whether it is loaded
to the nozzle. AFC's "lane loaded in toolhead" follows it:

- **At startup:** `PREP` reads the state from `save_variables`.
- **On every state change:** `hatchanger_afc.cfg` sets `state_hook` in `_HAT_CFG`. So after
  `HAT_PICKUP`, `HAT_DOCK`, `HAT_SET_STATE` or `HAT_START` run by hand, AFC already shows the
  right lane.
- **On demand:** run `AFC_HATCHANGER_SYNC UNIT=HatChanger_1`.

If a change fails (a missed grab, a hat that didn't dock), AFC reports it and pauses the print.
Fix the hat by hand and tell HatChanger what is on the head with
`HAT_SET_STATE LANE=.. LOADED=..`; AFC follows. Then `RESUME`.

## Sensors and cutting under AFC

- **Pre-extruder sensor.** AFC's panel always shows a "pre-extruder sensor" for the
  extruder. HatChanger has no sensor before the gears: its D2F is after the gears and stays
  with the macros. The unit reports the pre-extruder sensor as **Detected while a hat is on
  the head** (its filament is at the gears) and **Empty with the head empty**, updated every
  half second and after every hat change.
- **Cutting.** AFC's own cut (`tool_cut`, `AFC_CUT`, `_AFC_CUT_TIP_VARS`) is off and unused.
  When AFC unloads a lane, the unit calls `HAT_DOCK`, which cuts with the FilamATrix arm using
  `cut_x_touch`, `cut_x_cut` and `cut_y` from `_HAT_CFG`. Each of those cuts is still counted
  in AFC's blade statistics, so AFC's `tool_cut_threshold` warning tells you when to change
  the blade. `HAT_CUT` and `HAT_DOCK` run by hand aren't counted.

## Lane buttons in Mainsail

Each lane card has **Load** / **Unload** (a hat pickup / drop-off) and **Eject**. Mainsail shows
Eject for every unit type, but a hat has no motor: there's nothing to eject. HatChanger refuses
it with a message and keeps the lane's spool, colour and material (AFC would otherwise forget
them). To change a spool, pull the filament out of the docked hat by hand, feed the new one in
and set the spool, colour or material on the lane.

## Unit options

```ini
[AFC_HatChanger HatChanger_1]
extruder: extruder
leave_stub_for_poop: auto   # auto | true | false (see step 5)
```

## START_PRINT

`HAT_START LANE={params.INITIAL_TOOL}` works the same as without AFC. It puts the first lane
on the head before the start purge, AFC follows through the hook, and the slicer's first
`T<n>` finds that lane already loaded.

## Limits

- **Print height.** AFC lifts the head by its `z_hop` before every unload, and `HAT_DOCK`
  refuses a loaded head above `dock_z - z_clear_loaded`. The maximum print height for a tool
  change is therefore that minus `z_hop`. Keep `z_hop` small in `AFC.cfg`.
- **No runout or endless spool yet.** The lanes have no sensors, and the after-gears sensor
  belongs to the HatChanger macros.
- **No AFC calibration.** The lanes have no motors, so `LANE_UNLOAD`, eject and AFC's
  calibration don't apply. Calibrate the dock with the `HAT_CAL_*` macros.

## Test

`klipper/tests/run_afc_test.py` runs the real `hatchanger.cfg`, AFC and `AFC_HatChanger.py` in
Klipper batch mode (no printer needed). A simulated after-gears sensor stands in for the D2F.
The test covers:

- startup sync;
- AFC tool changes both ways;
- a repeated `T` that does nothing;
- `HAT_DOCK`, `HAT_START` and `HAT_SET_STATE` by hand, with AFC following;
- `HAT_DOCK` finishing a dock that stopped with the hat set down in its rack;
- a failed grab reported by AFC.

The setup steps are at the top of the script.
