# Installation

## 1. Print and assemble

Print-ready STL files are in [`cad/stl`](../cad/stl) and STEP files in [`cad/step`](../cad/step).
The [bill of materials](BOM.md) has the hardware list, print orientations and assembly notes.
Print in ABS/ASA with Voron settings: 0.2 mm layers, 4 walls, 40 % infill.

Build the FilamATrix cutter from
[its manual](https://armoredturtle.xyz/manual.html?manual=filamatrix), using
`front_body_hatchanger` in place of `front_body_g2e`. The hotend's PTFE liner must be cut to
FilamATrix's length for your hotend.

## 2. Install the macros

```sh
cd ~ && wget -q https://github.com/fulippo/hatchanger/releases/latest/download/hatchanger.zip \
  && unzip -oq hatchanger.zip -d hatchanger && rm hatchanger.zip
bash hatchanger/install.sh
```

This installs the latest release (see [Release or git clone](#release-or-git-clone)).

The installer asks whether to run under [AFC](AFC.md) (only if AFC is installed). Then it:

- **Links the macros.** `hatchanger.cfg` is linked from `~/printer_data/config/hatchanger/` into
  the repo, so updates reach it.
- **Copies the lane file once.** `hatchanger_tools.cfg` (the `T0`, `T1`, … macros) or, under
  AFC, `hatchanger_afc.cfg` (the lanes). Edit it when you add racks.
- **Creates `hatchanger_user.cfg`** for your machine's values. It's included last, so anything
  set there overrides the repo's defaults, and the installer never overwrites it. A hand-made
  install (`hatchanger*.cfg` copies) is migrated: options that differ from the repo move there,
  and the old files are kept as `*.hatchanger-<date>`.
- **Adds one marked include block to `printer.cfg`**, and comments out old HatChanger includes.
- **Registers `hatchanger` with Moonraker's update manager**, so it updates from
  Mainsail/Fluidd: from new releases for a release install, or from your branch for a git
  clone.
- **Under AFC:** links the AFC unit into Klipper, turns off AFC's cut, park and tip forming, and
  offers to disable the AFC hardware files for a unit you don't have.

Every file it edits is backed up first. `./hatchanger/install.sh --help` lists the options
(`--afc`, `--standalone`, `-y`, …).

After restarting Klipper, the installer runs `./hatchanger/install.sh --check`, which reports
anything that didn't start cleanly. You can run it at any time.

You need `[respond]` in your config (the installer warns if it's missing). If you already have a
`[save_variables]` section, the installer keeps using it.

Set `switch_pin` in `hatchanger_user.cfg` to the input your D2F is wired to.

### Uninstall

```sh
./hatchanger/install.sh --uninstall
```

This removes the include block, the links and the update-manager entry. Under AFC it also
restores the `AFC.cfg` values it changed and re-enables the AFC files it disabled. If the
install migrated a hand-made one, it offers to put that back. Your `hatchanger_user.cfg` and
lane file stay unless you add `--purge`.

### Release or git clone

The installer looks at how `~/hatchanger` got there and registers the matching update type with
Moonraker:

- **Release zip (recommended).** `hatchanger.zip` from a GitHub release holds only what the
  printer needs: the installer, the Klipper config, the AFC unit and the docs, with no STL or
  STEP files. Moonraker (`type: zip`) offers each new release in the update manager and restarts
  Klipper after installing it. Add `--beta` to the installer to get pre-releases too. Each
  release also carries `hatchanger-stl-<version>.zip` with the print files of that version.
- **Git clone.** `git clone https://github.com/fulippo/hatchanger.git` then
  `./hatchanger/install.sh`. Moonraker (`type: git_repo`) follows the branch you have checked
  out, commit by commit, including the CAD files. Use this to test a branch before it's released.

To switch from a git clone to releases, move the clone out of the way (`mv ~/hatchanger
~/hatchanger-git`), unpack the release zip as above and run its `install.sh`. It relinks the
config files and rewrites the update-manager entry. Moonraker won't manage a release folder that
sits inside a git repository.

## 3. Calibrate

Every value marked MEASURE or CALIBRATE in `_HAT_CFG` must match your machine. Set them in
`hatchanger_user.cfg`, where they are listed commented out:

| Value | How to find it |
|---|---|
| `lane_x`, `dock_y_in`, `dock_z` | With an empty head and a hat in the rack, run `HAT_CAL_PICKUP LANE=0` (stops `GAP` mm, default 5, under the hat) and jog up until the hat seats. With a hat on the head, `HAT_CAL_DOCK LANE=0 STEP=1..3` walks the docking in stages so you can check each one; `STEP=0` backs out. For `dock_z`, go to `STEP=3` and jog down 0.1 mm at a time until the rails touch the lips. |
| `cut_x_touch`, `cut_x_cut`, `cut_y` | Jog towards the depressor pin and note where the arm first touches it and where it is fully pressed. Check with `HAT_CUT`. |
| `nozzle_to_nip` | Distance along the filament from the gear contact line to the nozzle tip. Only used to push the cut stub out of the nozzle. |
| `min_melt_temp` | Lowest nozzle temperature that melts every filament you load. Loading refuses to run below it. |
| `load_park_xy`, `load_park_z` | Where the head pushes the cut stub out when no purge macro follows (`HAT_PICKUP` on its own, or `purge_macro` empty). `[]` = where the head is. |

Lanes need about 40 mm between them so the head can pass the neighbouring stingers.

Then tell the macros what is on the head, e.g. `HAT_SET_STATE LANE=-1 LOADED=0` for an empty
head. The state is saved and restored at every restart; `HAT_STATUS` shows it next to what the
sensor reads.

## 4. Test

Home, run `QUAD_GANTRY_LEVEL` and heat the nozzle. Then:

```
HAT_TEST_LANE LANE=0 COUNT=10 DRY=1    ; movements only, no filament
HAT_TEST_LANE LANE=0 COUNT=10          ; with filament, no loading to the nozzle
HAT_TEST_ALL COUNT=5                   ; every lane in turn (LANES=1,0 to choose)
```

## 5. Print

In the slicer, use `T0`, `T1`, … as tool changes. Each one runs `HAT_CHANGE` (under AFC, AFC's
tool change, which calls the same macros). Set `purge_macro` in `_HAT_CFG` (for example a purge
bucket or Blobifier macro) to purge after each load. The purge also pushes out the cut stub left
in the hotend (about 43 mm of the old filament), so make it that much longer than the colour
change alone needs.

So that the start purge runs with the right filament, pass the first tool to `START_PRINT`
(`INITIAL_TOOL=[initial_tool]` in the slicer's start G-code) and call
`HAT_START LANE={params.INITIAL_TOOL|default(-1)}` after homing, `QUAD_GANTRY_LEVEL` and
heating, before the purge. The slicer's first `T<n>` then finds that lane already loaded and
does nothing. `start_stub` in `_HAT_CFG` chooses who pushes out the cut stub after that change.

With a hat on the head, the clearance below the racks limits the maximum print height (about
175 mm on the prototype).
