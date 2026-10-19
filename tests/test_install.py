#!/usr/bin/env python3
"""Tests for install.sh / scripts/cfgtool.py, on fake printer homes (no printer needed).

    python3 tests/test_install.py          # or: python3 -m unittest tests/test_install.py

Each test builds a throwaway HOME with ~/printer_data/config and ~/klipper/klippy/extras,
runs install.sh in it and checks what changed. --check runs against a fake Moonraker.
"""
import hashlib
import http.server
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
INSTALL = REPO / "install.sh"
CFGTOOL = REPO / "scripts" / "cfgtool.py"

PRINTER_CFG = """[include mainsail.cfg]
[include AFC/*.cfg]
[respond]

[printer]
kinematics: corexy

#*# <---------------------- SAVE_CONFIG ---------------------->
#*# DO NOT EDIT THIS BLOCK OR BELOW. The contents are auto-generated.
#*#
#*# [extruder]
#*# pid_kp = 26.1
"""
# The parts of AFC's own AFC.cfg / AFC_Macro_Vars.cfg the installer reads (as AFC ships them)
AFC_CFG = """[AFC]
VarFile: ../printer_data/config/AFC/AFC.var   # Path to the variables file
tool_cut: True                  # Enable Cut macro.
tool_cut_cmd: AFC_CUT           # Cut macro name.
park: True                      # Enable Park.
park_cmd: AFC_PARK              # Park macro name.
poop: True                      # Enable Poop.
poop_cmd: AFC_POOP              # Poop macro name.
kick: True                      # Enable Kick.
kick_cmd: AFC_KICK              # Kick macro name.
wipe: True                      # Enable Wipe.
wipe_cmd: AFC_BRUSH             # Wipe macro name.
form_tip: False                 # Enable Tip Form.
"""
MACRO_VARS = """[gcode_macro _AFC_POOP_VARS]
variable_purge_loc_xy             : -99, -99    # (x,y) Location of where to purge
gcode:
[gcode_macro _AFC_KICK_VARS]
variable_kick_start_loc           : -99,-99,5  # Location to move before kick
gcode:
[gcode_macro _AFC_BRUSH_VARS]
variable_brush_loc                : -99,-99,-1  # Position of the center of the brush
gcode:
"""


def tree_hash(root: pathlib.Path, skip=(".hatchanger-",)) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if any(s in rel for s in skip) or rel.startswith("printer_data/config/hatchanger/"):
            continue
        if p.is_symlink():
            out[rel] = "link:" + os.readlink(p)
        elif p.is_file():
            out[rel] = hashlib.md5(p.read_bytes()).hexdigest()
    return out


class FakeHome:
    def __init__(self, afc=True, hand_made=True, unit_name="Turtle_1", blobifier=True):
        self.home = pathlib.Path(tempfile.mkdtemp(prefix="hc_home_"))
        self.cfg = self.home / "printer_data" / "config"
        self.extras = self.home / "klipper" / "klippy" / "extras"
        self.extras.mkdir(parents=True)
        (self.home / "klipper" / ".git" / "info").mkdir(parents=True)
        (self.home / "klipper" / ".git" / "info" / "exclude").write_text("something/else\n")
        self.cfg.mkdir(parents=True)
        (self.cfg / "printer.cfg").write_text(PRINTER_CFG)
        (self.cfg / "moonraker.conf").write_text("[server]\nhost: 0.0.0.0\n")
        if hand_made:   # an install made by copying the files by hand, with your own values
            hc = (REPO / "klipper/config/hatchanger.cfg").read_text()
            (self.cfg / "hatchanger.cfg").write_text(
                hc.replace("variable_dock_z: 244.5", "variable_dock_z: 243.9"))
            hid = (REPO / "klipper/config/hatchanger_id.cfg").read_text()
            (self.cfg / "hatchanger_id.cfg").write_text(hid.replace("i2c_mcu: EBB", "i2c_mcu: sb2209"))
            with open(self.cfg / "printer.cfg", "r+") as f:
                t = f.read().replace("[respond]", "[include hatchanger.cfg]\n[include hatchanger_id.cfg]\n[respond]")
                f.seek(0); f.write(t); f.truncate()
        if blobifier:
            (self.cfg / "blobifier.cfg").write_text("[gcode_macro BLOBIFIER]\ngcode:\n  G4\n")
        if afc:
            (self.extras / "AFC.py").write_text("# AFC\n")
            a = self.cfg / "AFC"
            a.mkdir()
            (a / "AFC.cfg").write_text(AFC_CFG)
            (a / "AFC_Macro_Vars.cfg").write_text(MACRO_VARS)
            (a / "AFC_Hardware.cfg").write_text("[AFC_extruder extruder]\npin_tool_start: Unknown\n")
            (a / f"AFC_{unit_name}.cfg").write_text(f"[AFC_BoxTurtle {unit_name}]\nhub: Turtle_1\n")
        self.before = tree_hash(self.home)

    def run(self, *args, stdin="", check=True):
        env = dict(os.environ, HOME=str(self.home))
        r = subprocess.run(["bash", str(INSTALL), "--no-restart", *args], env=env, input=stdin,
                           capture_output=True, text=True, timeout=120)
        if check and r.returncode != 0:
            raise AssertionError(f"install.sh {args} failed ({r.returncode}):\n{r.stdout}\n{r.stderr}")
        return r.stdout + r.stderr

    def text(self, rel):
        return (self.cfg / rel).read_text()

    def cleanup(self):
        shutil.rmtree(self.home, ignore_errors=True)


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.h = None

    def tearDown(self):
        if self.h:
            self.h.cleanup()

    def test_syntax(self):
        subprocess.run(["bash", "-n", str(INSTALL)], check=True)
        subprocess.run([sys.executable, "-m", "py_compile", str(CFGTOOL)], check=True)

    def test_help(self):
        out = subprocess.run(["bash", str(INSTALL), "--help"], capture_output=True, text=True).stdout
        self.assertIn("--uninstall", out)
        self.assertNotIn("set -euo", out)

    def test_afc_install_migrates_and_fixes_afc(self):
        self.h = h = FakeHome(unit_name="Hatchanger")       # unit renamed in AFC's installer
        out = h.run("-y", "--hat-id")
        # migration of the hand-made install
        user = h.text("hatchanger/hatchanger_user.cfg")
        self.assertIn("variable_dock_z: 243.9", user)
        self.assertIn("i2c_mcu: sb2209", user)
        self.assertNotIn("variable_dock_y_in", user)          # unchanged values aren't copied
        self.assertTrue((h.cfg / "hatchanger" / "hatchanger.cfg").is_symlink())
        self.assertTrue((h.cfg / "hatchanger" / "hatchanger_afc.cfg").is_file())
        self.assertFalse((h.cfg / "hatchanger.cfg").exists())
        # printer.cfg: block before SAVE_CONFIG, old includes commented
        p = h.text("printer.cfg")
        self.assertLess(p.index("[include hatchanger/hatchanger_afc.cfg]"), p.index("#*# <----"))
        self.assertIn("# [include hatchanger.cfg]", p)
        self.assertNotIn("hatchanger_tools.cfg", p)
        # AFC: unit files disabled whatever their name, placeholder macros fixed
        self.assertTrue((h.cfg / "AFC" / "AFC_Hatchanger.cfg.disabled").exists())
        self.assertTrue((h.cfg / "AFC" / "AFC_Hardware.cfg.disabled").exists())
        a = h.text("AFC/AFC.cfg")
        for line in ("tool_cut: False", "park: False", "poop: True", "poop_cmd: BLOBIFIER",
                     "kick: False", "wipe: False"):
            self.assertIn(line, a)
        self.assertEqual((h.cfg / "AFC" / "AFC.var.unit").read_text().strip(), "{}")
        self.assertTrue((h.extras / "AFC_HatChanger.py").is_symlink())
        self.assertIn("klippy/extras/AFC_HatChanger.py",
                      (h.home / "klipper/.git/info/exclude").read_text())
        self.assertIn("[update_manager hatchanger]", h.text("moonraker.conf"))
        self.assertIn("Done", out)

    def test_rerun_changes_nothing(self):
        self.h = h = FakeHome()
        h.run("-y", "--hat-id")
        first = tree_hash(h.home, skip=(".hatchanger-",))
        out = h.run("-y", "--hat-id")
        self.assertEqual(first, tree_hash(h.home, skip=(".hatchanger-",)))
        self.assertIn("already up to date", out)

    def test_uninstall_restores_everything(self):
        self.h = h = FakeHome()
        h.run("-y", "--hat-id")
        # answers: restore the hand-made install, re-enable both AFC files
        h.run("--uninstall", stdin="y\ny\ny\n")
        self.assertEqual(h.before, tree_hash(h.home))

    def test_uninstall_purge(self):
        self.h = h = FakeHome(hand_made=False)
        h.run("-y", "--no-hat-id")
        h.run("--uninstall", "--purge", "-y")
        self.assertFalse((h.cfg / "hatchanger").exists())
        self.assertNotIn("HatChanger", h.text("printer.cfg"))

    def test_no_purge_macro_turns_poop_off(self):
        self.h = h = FakeHome(blobifier=False)
        out = h.run("-y", "--no-hat-id")
        a = h.text("AFC/AFC.cfg")
        self.assertIn("poop: False", a)
        self.assertIn("poop_cmd: AFC_POOP", a)
        self.assertIn("load_park_xy", out)

    def test_standalone_without_afc_explains(self):
        self.h = h = FakeHome(afc=False, hand_made=False)
        out = h.run("-y", "--no-hat-id")
        self.assertIn("not installed", out)
        self.assertIn("install-afc.sh", out)
        self.assertIn("[include hatchanger/hatchanger_tools.cfg]", h.text("printer.cfg"))

    def test_afc_flag_without_afc_fails(self):
        self.h = h = FakeHome(afc=False, hand_made=False)
        out = h.run("-y", "--afc", check=False)
        self.assertIn("not installed", out)
        self.assertNotIn("HatChanger", h.text("printer.cfg"))

    def test_git_clone_registers_git_repo(self):
        self.h = h = FakeHome(afc=False, hand_made=False)
        h.run("-y", "--no-hat-id")
        m = h.text("moonraker.conf")
        self.assertIn("type: git_repo", m)
        self.assertIn("primary_branch:", m)

    def test_release_zip_install_registers_zip(self):
        self.h = h = FakeHome(afc=False, hand_made=False)
        dist = h.home / "dist"
        subprocess.run([sys.executable, str(REPO / "scripts" / "release_zip.py"), "--version", "v9.9.9",
                        "--out", str(dist)], check=True, capture_output=True)
        import zipfile
        with zipfile.ZipFile(dist / "hatchanger.zip") as z:
            names = z.namelist()
            self.assertIn("release_info.json", names)
            self.assertIn("install.sh", names)
            self.assertFalse([n for n in names if n.startswith(("cad/", "tests/", "klipper/tests/"))])
            info = json.loads(z.read("release_info.json"))
            self.assertEqual((info["project_owner"], info["project_name"], info["version"]),
                             ("fulippo", "hatchanger", "v9.9.9"))
            z.extractall(h.home / "hatchanger")
        with zipfile.ZipFile(dist / "hatchanger-stl-v9.9.9.zip") as z:
            self.assertTrue(all(n.endswith(".stl") for n in z.namelist()))
        env = dict(os.environ, HOME=str(h.home))
        r = subprocess.run(["bash", str(h.home / "hatchanger" / "install.sh"), "--no-restart", "-y",
                            "--no-hat-id", "--beta"], env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        m = h.text("moonraker.conf")
        for line in ("type: zip", "channel: beta", "repo: fulippo/hatchanger",
                     f"path: {h.home / 'hatchanger'}", "managed_services: klipper"):
            self.assertIn(line, m)
        self.assertNotIn("primary_branch", m)
        self.assertEqual(os.readlink(h.cfg / "hatchanger" / "hatchanger.cfg"),
                         str(h.home / "hatchanger" / "klipper" / "config" / "hatchanger.cfg"))
        self.assertIn("release zips (beta)", r.stdout)

    def test_existing_save_variables_kept(self):
        self.h = h = FakeHome(afc=False, hand_made=False)
        with open(h.cfg / "printer.cfg", "a") as f:
            f.write("\n[save_variables]\nfilename: ~/printer_data/config/variables.cfg\n")
        h.run("-y", "--no-hat-id", "--standalone")
        self.assertIn("filename: ~/printer_data/config/variables.cfg",
                      h.text("hatchanger/hatchanger_user.cfg"))


# ---------------------------------------------------------------------------- --check -------
class FakeMoonraker(http.server.BaseHTTPRequestHandler):
    info = {"state": "ready", "state_message": "Printer is ready"}
    status = {}
    store = []

    def _reply(self, result):
        b = json.dumps({"result": result}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/printer/info"):
            self._reply(self.info)
        elif self.path.startswith("/printer/objects/list"):
            self._reply({"objects": list(self.status)})
        elif self.path.startswith("/printer/objects/query"):
            self._reply({"status": self.status})
        elif self.path.startswith("/server/gcode_store"):
            self._reply({"gcode_store": self.store})
        else:
            self._reply({})

    def log_message(self, *a):
        pass


def good_status():
    return {
        "configfile": {"warnings": [], "settings": {
            "afc": {"tool_cut": False, "park": False, "poop": True, "poop_cmd": "BLOBIFIER",
                    "kick": False, "wipe": False, "form_tip": False},
            "gcode_macro blobifier": {}}},
        "gcode_macro _HAT_STATE": {"lane": 1, "loaded": 1},
        "gcode_macro _HAT_CFG": {},
        "AFC": {"units": ["HatChanger HatChanger_1"], "current_load": "hat1", "error_state": False},
        "AFC_HatChanger HatChanger_1": {"lanes": ["hat0", "hat1"], "hat_on_head": 1, "hat_loaded": True},
        "AFC_lane hat0": {"unit": "HatChanger_1", "map": "T0", "tool_loaded": False},
        "AFC_lane hat1": {"unit": "HatChanger_1", "map": "T1", "tool_loaded": True},
        "gcode_macro _AFC_POOP_VARS": {"purge_loc_xy": [-99, -99]},
    }


class CheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeMoonraker)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.srv.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def check(self, status, info=None, store=()):
        FakeMoonraker.status = status
        FakeMoonraker.info = info or {"state": "ready"}
        FakeMoonraker.store = list(store)
        r = subprocess.run([sys.executable, str(CFGTOOL), "check", "--moonraker", self.url,
                            "--expect-afc"], capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout

    def test_good(self):
        rc, out = self.check(good_status())
        self.assertEqual(rc, 0, out)
        self.assertIn("all good", out)

    def test_klipper_error(self):
        rc, out = self.check({}, info={"state": "error", "state_message":
                                       "Unknown is not valid for pin_tool_start in [AFC_extruder extruder]"})
        self.assertEqual(rc, 1)
        self.assertIn("pin_tool_start", out)

    def test_placeholder_poop(self):
        st = good_status()
        st["configfile"]["settings"]["afc"]["poop_cmd"] = "AFC_POOP"
        rc, out = self.check(st)
        self.assertEqual(rc, 1)
        self.assertIn("purge_loc_xy is still -99", out)

    def test_extra_boxturtle_unit(self):
        st = good_status()
        st["AFC"]["units"].append("BoxTurtle Hatchanger")
        rc, out = self.check(st)
        self.assertIn("other units: BoxTurtle Hatchanger", out)

    def test_out_of_sync(self):
        st = good_status()
        st["AFC"]["current_load"] = None
        rc, out = self.check(st)
        self.assertIn("AFC_HATCHANGER_SYNC", out)

    def test_console_errors(self):
        rc, out = self.check(good_status(), store=[
            {"message": "// Klipper state: Ready"},
            {"message": "!! Error: /home/biqu/printer_data/config/AFC/AFC.var.unit file not found"}])
        self.assertIn("AFC.var.unit", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
