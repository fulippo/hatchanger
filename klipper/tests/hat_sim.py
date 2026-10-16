# Test-only Klipper extra: simulates the HatChanger after-gears sensor in Klipper batch mode
# (no MCU, no real switch). Never install this on a printer.
#
# It registers itself as "filament_switch_sensor hat_toolhead", so the macros read it exactly
# like the real sensor. Model, in the frame of a hat seated on the head (0 = gear nip, + = down):
#   - each hat has a filament tip position; a docked hat hangs its tip at grip_margin;
#   - extruder moves move the tip of the hat on the head when the tip is in the gears (>= 0);
#   - filament_detected = tip of the hat on the head >= nip_to_sensor.
# Extruder moves are attributed when the sensor is read and when the macros change state
# (HAT_SIM_SETTLE, called from the test's state_hook), using the state from before the change:
# moves made while the head is empty, or during the synced dock/pickup Z moves, don't move a tip.
#
# [hat_sim]
# grip_margin: 3.0
# nip_to_sensor: 19.85
# initial_tips: 36.35, 3.0    # per hat lane; the hat on the head at start uses its entry


class SimSensor:
    def __init__(self, sim):
        self.sim = sim

    def get_status(self, eventtime):
        self.sim.settle()
        return {"filament_detected": self.sim.detected(), "enabled": True}


class HatSim:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.grip = config.getfloat("grip_margin", 3.0)
        self.sensor = config.getfloat("nip_to_sensor", 19.85)
        self.tips = [float(t) for t in config.get("initial_tips", "3.0, 3.0").split(",")]
        self.reads = 0
        self.lane = None          # hat on the head as of the last settle
        self.last_e = None
        self.printer.add_object("filament_switch_sensor hat_toolhead", SimSensor(self))
        # Batch mode has no thermistor: report every heater at its target, so code that polls the
        # temperature itself (AFC waits for the extruder) doesn't wait forever.
        self.printer.register_event_handler("klippy:connect", self._fake_heaters)
        gcode = self.printer.lookup_object("gcode")
        gcode.register_command("HAT_SIM_SETTLE", self.cmd_SETTLE)
        gcode.register_command("HAT_SIM_STATUS", self.cmd_STATUS)
        gcode.register_command("HAT_SIM_SET_TIP", self.cmd_SET_TIP)
        gcode.register_command("HAT_SIM_NOTE", self.cmd_NOTE)

    def _fake_heaters(self):
        for heater in self.printer.lookup_object("heaters").heaters.values():
            heater.get_temp = (lambda h: lambda eventtime: (h.target_temp, h.target_temp))(heater)

    def _state_lane(self):
        st = self.printer.lookup_object("gcode_macro _HAT_STATE").variables
        return int(st.get("lane", -1))

    def _e(self):
        return self.printer.lookup_object("toolhead").get_position()[3]

    def settle(self):
        e = self._e()
        if self.lane is None:
            self.lane, self.last_e = self._state_lane(), e
            return
        de, self.last_e = e - self.last_e, e
        if self.lane >= 0 and self.tips[self.lane] >= 0:
            self.tips[self.lane] = max(self.tips[self.lane] + de, -50.0)
        new = self._state_lane()
        if new != self.lane:
            if self.lane >= 0:
                self.tips[self.lane] = self.grip   # docked: hangs grip_margin below the nip
            self.lane = new

    def detected(self):
        return self.lane is not None and self.lane >= 0 and self.tips[self.lane] >= self.sensor

    def cmd_SETTLE(self, gcmd):
        self.settle()

    def cmd_NOTE(self, gcmd):
        # RESPOND output doesn't reach the log in batch mode; this does
        gcmd.respond_info(gcmd.get("MSG", ""))

    def cmd_SET_TIP(self, gcmd):
        # e.g. TIP=-100: the hat's filament is out of reach of the gears, the next grab fails
        self.settle()
        self.tips[gcmd.get_int("LANE")] = gcmd.get_float("TIP")

    def cmd_STATUS(self, gcmd):
        self.settle()
        gcmd.respond_info("HAT_SIM: head %s tips %s detected %s" % (
            self.lane, ["%.2f" % t for t in self.tips], self.detected()))


def load_config(config):
    return HatSim(config)
