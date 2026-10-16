# HatChanger unit for the Armored Turtle AFC-Klipper-Add-On
#
# Copyright (C) 2026 Filippo Pisano
#
# This file may be distributed under the terms of the GNU GPLv3 license.
#
# HatChanger has one extruder and one hotend. Each lane is a passive hat (ECAS + bowden end)
# that waits in a rack on the gantry; a lane "load" is a hat pickup, a lane "unload" is a hat
# drop-off. There are no lane motors and no lane sensors.
#
# AFC owns everything above the hardware: T<n> mapping, Spoolman, lane colours/materials,
# the poop/wipe/kick hooks, pause/resume and the UI. The HatChanger Klipper macros
# (hatchanger.cfg) stay the only thing that moves the machine:
#
#   AFC TOOL_LOAD   -> unit_load_lane()   -> HAT_PICKUP LANE=<hat> STUB=0|1
#   AFC TOOL_UNLOAD -> unit_unload_lane() -> HAT_DOCK
#
# AFC skips its own load/unload moves, cut, park and tip forming for these lanes: HAT_DOCK cuts
# with the FilamATrix arm (_HAT_CFG cut_*), never AFC_CUT. Each HAT_DOCK cut still counts in AFC's
# blade statistics (cut_total, tool_cut_threshold warning).
#
# AFC's "pre-extruder sensor" (tool_start) has no pin here: HatChanger's only toolhead sensor is
# after the gears and belongs to the macros. The unit reports it as "filament at the gears" = a
# hat is seated on the head (HatChanger state), so the AFC panel shows Detected / Empty sensibly.
#
# Source of truth: the HatChanger state (_HAT_STATE / save_variables: which hat is on the head,
# whether it is loaded to the nozzle). AFC's "lane loaded in toolhead" is derived from it:
#   - at PREP (startup) for every lane,
#   - every time the macros change their state (hatchanger_afc.cfg sets _HAT_CFG state_hook to
#     AFC_HATCHANGER_SYNC), so HAT_PICKUP / HAT_DOCK / HAT_SET_STATE run by hand keep AFC in step,
#   - on demand: AFC_HATCHANGER_SYNC UNIT=<unit>.
#
# Lanes: [AFC_lane <name>] with  unit: <unit name>:<n>  (n = 1 for the first hat, i.e. hat lane 0
# in _HAT_CFG lane_x) and  hub: direct. No pins.
#
# Install: symlink this file into klipper/klippy/extras/ next to AFC's files (see docs/AFC.md).

from __future__ import annotations

import traceback
from configparser import Error as error
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from configfile import ConfigWrapper
    from gcode import GCodeCommand
    from extras.AFC_lane import AFCLane
    from extras.AFC_extruder import AFCExtruder

try: from extras.AFC_utils import ERROR_STR
except: raise error("Error when trying to import AFC_utils.ERROR_STR\n{trace}".format(
    trace=traceback.format_exc()))

try: from extras.AFC_unit import afcUnit
except: raise error(ERROR_STR.format(import_lib="AFC_unit", trace=traceback.format_exc()))

try: from extras.AFC_lane import AFCLaneState, AFCMoveWarning
except: raise error(ERROR_STR.format(import_lib="AFC_lane", trace=traceback.format_exc()))

try: from extras.AFC import State
except: raise error(ERROR_STR.format(import_lib="AFC", trace=traceback.format_exc()))


class afcHatChanger(afcUnit):
    CFG_MACRO   = "gcode_macro _HAT_CFG"
    STATE_MACRO = "gcode_macro _HAT_STATE"

    def __init__(self, config: ConfigWrapper) -> None:
        # Load AFC (and AFC_spool) BEFORE afcUnit registers this unit's klippy:connect handler.
        # Lanes register their per-lane commands (SET_MATERIAL, SET_COLOR, SET_SPOOL_ID, ...) when
        # the unit connects, and AFC_spool only listens for that once its own connect handler has
        # run: with [AFC_HatChanger] parsed before [AFC] those commands were never registered.
        config.get_printer().load_object(config, "AFC")
        super().__init__(config)
        self.type = config.get("type", "HatChanger")
        # No lane motors: AFC_lane must not look for a drive stepper.
        self.stepperless_drive = True
        # With the hat-ID reader (hatchanger_id.cfg) check the hat on the head after every
        # pickup and drop-off. Ignored when HAT_ID_CHECK isn't defined.
        self.hat_id_check: bool = config.getboolean("hat_id_check", True)
        # STUB=0 leaves the ~43 mm cut stub in the nozzle for AFC's poop_cmd to push out.
        # auto = 0 when AFC poop is enabled, else 1 (HatChanger pushes it out at load_park_xy).
        self.stub_mode: str = config.get("leave_stub_for_poop", "auto").lower()
        if self.stub_mode not in ("auto", "true", "false"):
            raise error(f"[{config.get_name()}] leave_stub_for_poop must be auto, true or false")

        self.logo       = '<span class=success--text>HatChanger Ready</span>\n'
        self.logo_error = '<span class=error--text>HatChanger Not Ready</span>\n'

        self._operation_active = False   # True while AFC runs a hat load/unload
        self._ready = False
        self._sensor_timer = None

        self.gcode.register_mux_command("AFC_HATCHANGER_SYNC", "UNIT", self.name,
                                        self.cmd_AFC_HATCHANGER_SYNC,
                                        desc=self.cmd_AFC_HATCHANGER_SYNC_help)

    # ------------------------------------------------------------------ setup -----------------
    def handle_connect(self) -> None:
        super().handle_connect()
        for lane in self.lanes.values():
            self._mark_present(lane)

    def handle_ready(self) -> None:
        super().handle_ready()
        cfg = self._macro_vars(self.CFG_MACRO)
        if cfg is None:
            self.logger.error(f"{self.name}: [{self.CFG_MACRO}] not found. Include hatchanger.cfg "
                              "before hatchanger_afc.cfg")
            return
        n_hats = len(cfg.get("lane_x", []))
        for lane in self.lanes.values():
            idx = self.hat_lane(lane)
            if idx < 0 or idx >= n_hats:
                self.logger.error(
                    f"{lane.name}: unit index {lane.index} maps to hat lane {idx}, but _HAT_CFG "
                    f"lane_x has {n_hats} lane(s). Use unit: {self.name}:1 for hat lane 0.")
        self._sensor_timer = self.reactor.register_timer(self._update_presensor,
                                                         self.reactor.NOW)
        if not cfg.get("state_hook"):
            self.logger.info(f"{self.name}: _HAT_CFG state_hook is empty, AFC is only resynced "
                             "at PREP and by AFC_HATCHANGER_SYNC")
        self._ready = True

    # ------------------------------------------------------------------ helpers ---------------
    def hat_lane(self, lane: AFCLane) -> int:
        """AFC unit index 1..n -> HatChanger lane 0..n-1."""
        return int(getattr(lane, "index", 0)) - 1

    def _macro_vars(self, name: str) -> Optional[dict]:
        obj = self.printer.lookup_object(name, None)
        return None if obj is None else obj.variables

    def _hat_state(self, from_disk: bool=False) -> tuple[int, bool]:
        """(hat lane on the head or -1, loaded to the nozzle). from_disk reads save_variables:
        at startup _HAT_STATE is restored from it by a delayed_gcode that may not have run yet."""
        if from_disk:
            sv = self.printer.lookup_object("save_variables", None)
            if sv is not None:
                v = sv.allVariables
                if "hat_lane" in v:
                    lane = int(v.get("hat_lane", -1))
                    return lane, lane >= 0 and bool(int(v.get("hat_loaded", 0)))
        st = self._macro_vars(self.STATE_MACRO) or {}
        lane = int(st.get("lane", -1))
        return lane, lane >= 0 and bool(int(st.get("loaded", 0)))

    def _extruders(self):
        return {id(l.extruder_obj): l.extruder_obj for l in self.lanes.values()
                if getattr(l, "extruder_obj", None) is not None}.values()

    def _update_presensor(self, eventtime=None):
        """AFC tool_start ('pre-extruder sensor') = a hat is seated on the head."""
        hat, _ = self._hat_state()
        for ex in self._extruders():
            if ex.tool_start is None:          # never override a real sensor pin
                ex.tool_start_state = hat >= 0
        return (eventtime or self.reactor.monotonic()) + 0.5

    def _sensor_detected(self) -> bool:
        cfg = self._macro_vars(self.CFG_MACRO) or {}
        sens = self.printer.lookup_object(
            "filament_switch_sensor " + str(cfg.get("sensor", "hat_toolhead")), None)
        if sens is None:
            return False
        return bool(sens.get_status(self.reactor.monotonic()).get("filament_detected"))

    def _leave_stub(self) -> bool:
        if self.stub_mode == "auto":
            return bool(self.afc.poop)
        return self.stub_mode == "true"

    def _mark_present(self, lane: AFCLane) -> None:
        # Passive hats have no sensors: every configured lane is treated as a hat with filament
        # waiting in its rack. Spool data comes from AFC (UI / Spoolman).
        lane.prep_state = True
        lane._load_state = True
        lane.loaded_to_hub = True

    def _run(self, script: str) -> Optional[str]:
        """Run gcode; returns None on success or the error message."""
        try:
            self.gcode.run_script_from_command(script)
        except self.printer.command_error as e:
            return str(e)
        return None

    def _hat_id_check(self, hat: int) -> Optional[str]:
        if (self.hat_id_check
                and self.printer.lookup_object("gcode_macro HAT_ID_CHECK", None) is not None):
            return self._run(f"HAT_ID_CHECK LANE={hat}")
        return None

    def _set_afc_tooled(self, lane: AFCLane, tooled: bool) -> bool:
        """Make AFC's view of one lane match the hardware. Returns True if anything changed."""
        extruder = lane.extruder_obj
        if tooled:
            if lane.tool_loaded and extruder.lane_loaded == lane.name:
                return False
            lane.set_tool_loaded()
            self.afc.spool.set_active_spool(lane.spool_id)
            return True
        if not lane.tool_loaded and extruder.lane_loaded != lane.name:
            return False
        lane.tool_loaded = False
        if extruder.lane_loaded == lane.name:
            extruder.lane_loaded = None
            self.afc.spool.set_active_spool(None)
        lane.status = AFCLaneState.LOADED
        self.lane_tool_unloaded(lane)
        return True

    def sync_from_hatchanger(self, from_disk: bool=False) -> list[str]:
        hat, loaded = self._hat_state(from_disk)
        changed = []
        # Unload first, so a lane being marked loaded never sees a stale extruder.lane_loaded.
        for want in (False, True):
            for lane in self.lanes.values():
                tooled = loaded and self.hat_lane(lane) == hat
                if tooled == want and self._set_afc_tooled(lane, tooled):
                    changed.append(f"{lane.name} {'loaded' if tooled else 'unloaded'}")
        if changed:
            self.afc.save_vars()
        return changed

    # ------------------------------------------------------------------ AFC hooks -------------
    def system_Test(self, cur_lane: AFCLane, delay: float, assignTcmd: bool,
                    enable_movement: bool) -> bool:
        self._mark_present(cur_lane)
        hat, loaded = self._hat_state(from_disk=True)
        idx = self.hat_lane(cur_lane)
        tooled = loaded and idx == hat
        self._set_afc_tooled(cur_lane, tooled)

        if tooled:
            msg = "<span class=success--text>LOADED IN TOOLHEAD</span>"
            cur_lane.status = AFCLaneState.TOOLED
            self.lane_tool_loaded(cur_lane)
        elif idx == hat:
            msg = "<span class=success--text>HAT ON THE HEAD, NOT LOADED</span>"
            cur_lane.status = AFCLaneState.LOADED
            self.lane_loaded(cur_lane)
        else:
            msg = "<span class=success--text>DOCKED</span>"
            cur_lane.status = AFCLaneState.LOADED
            self.lane_loaded(cur_lane)
        self.lane_illuminate_spool(cur_lane)

        if assignTcmd:
            self.afc.function.TcmdAssign(cur_lane)
        cur_lane.send_lane_data()
        self.logger.raw('{lane_name} tool cmd: {tcmd:3} hat {hat} {msg}'.format(
            lane_name=cur_lane.name, tcmd=cur_lane.map, hat=idx, msg=msg))
        cur_lane.set_afc_prep_done()
        self.afc.save_vars()
        return True

    def unit_load_lane(self, cur_lane: AFCLane, cur_extruder: AFCExtruder) -> bool:
        hat = self.hat_lane(cur_lane)
        stub = 0 if self._leave_stub() else 1
        self._operation_active = True
        try:
            err = self._run(f"HAT_PICKUP LANE={hat} STUB={stub}")
            if err is None:
                err = self._hat_id_check(hat)
        finally:
            self._operation_active = False

        on_head, loaded = self._hat_state()
        if err is None and not (on_head == hat and loaded):
            err = (f"after HAT_PICKUP the HatChanger state is hat {on_head}, loaded {int(loaded)}"
                   f" (expected hat {hat} loaded)")
        if err is not None:
            msg = f"HatChanger could not load hat {hat}: {err}"
            msg += ("\nFix it by hand, then HAT_SET_STATE LANE=.. LOADED=.. (AFC follows)."
                    "\nIf the print is paused, RESUME continues it.")
            self.afc.error.handle_lane_failure(cur_lane, msg, pause=self.afc.function.in_print())
            return False

        cur_lane.loaded_to_hub = True
        cur_lane.status = AFCLaneState.TOOL_LOADED
        self.afc.save_vars()
        return True

    def unit_unload_lane(self, cur_lane: AFCLane, cur_extruder: AFCExtruder) -> bool:
        cur_lane.status = AFCLaneState.TOOL_UNLOADING
        cur_lane.disable_buffer()
        self._operation_active = True
        try:
            on_head, _ = self._hat_state()
            err = None
            will_cut = self._sensor_detected()   # HAT_DOCK cuts when the sensor sees filament
            if on_head >= 0:
                if on_head != self.hat_lane(cur_lane):
                    self.logger.info(f"{cur_lane.name}: AFC expected hat {self.hat_lane(cur_lane)}"
                                     f" on the head, HatChanger has hat {on_head}: docking that")
                err = self._run("HAT_DOCK")
                if err is None and will_cut:
                    cur_extruder.estats.increase_cut_total()
                if err is None:
                    err = self._hat_id_check(-1)
        finally:
            self._operation_active = False

        if err is None and self._hat_state()[0] >= 0:
            err = "after HAT_DOCK the HatChanger state still has a hat on the head"
        if err is not None:
            self.afc.error.handle_lane_failure(
                cur_lane, f"HatChanger could not dock: {err}",
                pause=self.afc.function.in_print())
            return False

        if self.afc.post_unload_macro is not None:
            self.gcode.run_script_from_command(self.afc.post_unload_macro)
        cur_lane.set_tool_unloaded(normal_toolchange=True)
        self._mark_present(cur_lane)
        cur_lane.status = AFCLaneState.LOADED
        self.afc.save_vars()
        return True

    # Hats can't be moved by AFC outside a hat change: no motor, no selector.
    def prep_load(self, lane: AFCLane) -> None:
        pass

    def prep_post_load(self, lane: AFCLane) -> None:
        pass

    def eject_lane(self, lane: AFCLane) -> None:
        """Mainsail shows an Eject button on every lane. A hat has no motor: there is nothing to
        eject. Refuse before AFC's LANE_UNLOAD goes on to forget the lane's spool and mark it
        not ready (it does that after this call)."""
        lane.status = AFCLaneState.TOOLED if lane.tool_loaded else AFCLaneState.LOADED
        self.afc.current_state = State.IDLE
        self.afc.save_vars()
        raise self.printer.command_error(
            f"{lane.name}: HatChanger hats are passive, there is nothing to eject. To change the "
            "spool, pull the filament out of the docked hat by hand, feed the new one in and set "
            "its spool / colour on the lane.")

    def lane_move(self, cur_lane: AFCLane, distance: float, speed_mode) -> None:
        self.logger.info(f"{cur_lane.name}: HatChanger lanes have no motor")

    def get_lane_reset_command(self, lane: AFCLane, dis: float) -> None:
        return None

    def move_to_hub(self, lane, dist, dir, use_homing=True, speed_mode=None,
                    assist_active=None) -> tuple[bool, float, AFCMoveWarning]:
        return True, 0, AFCMoveWarning.NONE

    def move_to_load(self, lane, dist, dir, use_homing=True, speed_mode=None
                     ) -> tuple[bool, float, AFCMoveWarning]:
        return True, 0, AFCMoveWarning.NONE

    def load_then_home(self, lane, distance, assist_active, endstop
                       ) -> tuple[bool, float, AFCMoveWarning]:
        return True, 0, AFCMoveWarning.NONE

    def calibration_lane_message(self) -> str:
        return "HatChanger lanes have no length to calibrate (use the HAT_CAL_* macros)"

    def calibrate_lane(self, cur_lane, tol):
        return False, self.calibration_lane_message(), 0

    def calibrate_bowden(self, cur_lane, dis, tol):
        return False, self.calibration_lane_message(), 0

    def calibrate_hub(self, cur_lane, tol):
        return False, self.calibration_lane_message(), 0

    # ------------------------------------------------------------------ gcode -----------------
    cmd_AFC_HATCHANGER_SYNC_help = ("Make AFC's loaded lane match the HatChanger state "
                                    "(run automatically through _HAT_CFG state_hook)")
    def cmd_AFC_HATCHANGER_SYNC(self, gcmd: GCodeCommand) -> None:
        """
        Make AFC's "lane loaded in toolhead" match what the HatChanger macros say is on the head.
        hatchanger_afc.cfg calls it after every HatChanger state change. Does nothing while AFC
        itself is loading or unloading a hat (AFC sets its state at the end of the change).

        Usage
        -----
        `AFC_HATCHANGER_SYNC UNIT=<unit> [QUIET=1]`
        """
        self._update_presensor()
        if self._operation_active or not self._ready:
            return
        changed = self.sync_from_hatchanger()
        hat, loaded = self._hat_state()
        if not gcmd.get_int("QUIET", 0):
            gcmd.respond_info(
                f"{self.name}: hat {hat if hat >= 0 else 'none'} on the head, "
                f"loaded {int(loaded)}; AFC {'updated: ' + ', '.join(changed) if changed else 'already in sync'}")
        elif changed:
            self.logger.info(f"{self.name}: AFC resynced from HatChanger: {', '.join(changed)}")

    def get_status(self, eventtime=None):
        response = super().get_status(eventtime)
        hat, loaded = self._hat_state()
        response["hat_on_head"] = hat
        response["hat_loaded"] = loaded
        return response


def load_config_prefix(config: ConfigWrapper):
    return afcHatChanger(config)
