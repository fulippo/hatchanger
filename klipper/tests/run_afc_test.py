#!/usr/bin/env python3
"""HatChanger + AFC integration test in Klipper batch mode (no printer, no MCU).

Runs the real hatchanger.cfg macros, the real AFC-Klipper-Add-On and AFC_HatChanger.py in
klippy, with hat_sim.py standing in for the after-gears sensor, and plays afc_test.gcode.

Setup (once):
  git clone https://github.com/Klipper3d/klipper && cd klipper
  printf 'CONFIG_MACH_LINUX=y\\n' > .config && make olddefconfig && make   # -> out/klipper.dict
  python3 -m venv venv && venv/bin/pip install -r scripts/klippy-requirements.txt
  git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On ../AFC
  ln -sf $PWD/../AFC/extras/*.py klippy/extras/

Run:
  venv/bin/python <hatchanger>/klipper/tests/run_afc_test.py --klipper <klipper dir>
  (--extruder g2e / cw2 to run one extruder profile only; default: both)
"""
import argparse
import http.server
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent
CFG = HERE.parent / "config"
EXTRAS = HERE.parent / "extras"


def cfg_value(path: pathlib.Path, key: str, default: float) -> float:
    m = re.search(rf"^variable_{key}:\s*([-0-9.]+)", path.read_text(), re.M)
    return float(m.group(1)) if m else default


def strip_section(text: str, name: str) -> str:
    """Remove [name] and its body (up to the next section header)."""
    out, skip = [], False
    for line in text.splitlines(keepends=True):
        m = re.match(r"^\[([^\]]+)\]", line)
        if m:
            skip = m.group(1).strip() == name
        if not skip:
            out.append(line)
    return "".join(out)


class FakeMoonraker(http.server.BaseHTTPRequestHandler):
    """Just enough of Moonraker for AFC: empty database, no Spoolman, every POST accepted."""
    def _reply(self, result):
        body = json.dumps({"result": result}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/server/config"):
            self._reply({"orig": {}})
        elif self.path.startswith("/server/database/item"):
            self._reply({"value": {}})
        else:
            self._reply({})

    posts = []

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0)).decode()
        FakeMoonraker.posts.append(body)
        self._reply({})

    def log_message(self, *a):
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--klipper", required=True, type=pathlib.Path,
                    help="Klipper checkout with AFC's extras linked into klippy/extras")
    ap.add_argument("--dict", type=pathlib.Path, default=None,
                    help="MCU dictionary (default: <klipper>/out/klipper.dict)")
    ap.add_argument("--keep", action="store_true", help="keep the temp dir")
    ap.add_argument("--extruder", choices=["g2e", "cw2", "all"], default="all",
                    help="extruder profile(s) to run the scenarios with (extruder_<name>.cfg)")
    args = ap.parse_args()
    kl = args.klipper.resolve()
    mcu_dict = (args.dict or kl / "out" / "klipper.dict").resolve()
    extras = kl / "klippy" / "extras"
    if not (extras / "AFC.py").exists():
        sys.exit(f"AFC's extras are not linked into {extras}")

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeMoonraker)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    links = [(extras / "AFC_HatChanger.py", EXTRAS / "AFC_HatChanger.py"),
             (extras / "hat_sim.py", HERE / "hat_sim.py")]
    for dst, src in links:
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        dst.symlink_to(src)
    # (scenario, expected AFC cut_total updates): any error ends a Klipper batch run, so a
    # scenario that triggers one on purpose must be last in its file or in a file of its own
    scenarios = [("afc_test.gcode", 3), ("afc_test_eject.gcode", 0)]
    ok = True
    profiles = ["g2e", "cw2"] if args.extruder == "all" else [args.extruder]
    try:
        for ext in profiles:
            print(f"\n##### extruder profile: {ext}")
            for name, want_cuts in scenarios:
                ok &= run_scenario(kl, mcu_dict, server, name, want_cuts, args.keep, ext)
    finally:
        (extras / "hat_sim.py").unlink()
    print("\nPASS" if ok else "\nFAIL")
    return 0 if ok else 1


def run_scenario(kl, mcu_dict, server, name, want_cuts, keep, extruder="g2e") -> bool:
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="hatchanger_afc_"))
    FakeMoonraker.posts = []
    hc = (CFG / "hatchanger.cfg").read_text()
    hc = strip_section(hc, "filament_switch_sensor hat_toolhead")        # hat_sim replaces it
    hc = hc.replace("~/printer_data/config/hatchanger_vars.cfg", str(tmp / "vars.cfg"))
    (tmp / "hatchanger.cfg").write_text(hc)
    (tmp / "hatchanger_afc.cfg").write_text((CFG / "hatchanger_afc.cfg").read_text())
    profile = CFG / f"extruder_{extruder}.cfg"
    (tmp / "hatchanger_extruder.cfg").write_text(profile.read_text())
    # the simulator's geometry follows the profile: sensor distance, and the loaded hat's tip
    # where a load leaves it (stub_gap above the blade)
    hcfg = CFG / "hatchanger.cfg"
    sensor = cfg_value(profile, "nip_to_sensor", cfg_value(hcfg, "nip_to_sensor", 19.85))
    loaded = (cfg_value(profile, "nip_to_cut", cfg_value(hcfg, "nip_to_cut", 38.35))
              - cfg_value(hcfg, "stub_gap", 2.0))
    test = (HERE / "afc_test_printer.cfg").read_text().replace("{TMP}", str(tmp)) \
        .replace("{PORT}", str(server.server_address[1]))
    test = re.sub(r"^nip_to_sensor: .*$", f"nip_to_sensor: {sensor:g}", test, flags=re.M)
    test = re.sub(r"^initial_tips: [-0-9.]+,", f"initial_tips: {loaded:g},", test, flags=re.M)
    (tmp / "test.cfg").write_text(test)
    # hatchanger_afc.cfg BEFORE AFC's [AFC] section on purpose: the unit must cope with it
    (tmp / "printer.cfg").write_text(
        "[include hatchanger.cfg]\n[include hatchanger_extruder.cfg]\n"
        "[include hatchanger_afc.cfg]\n[include test.cfg]\n")
    # hat 0 on the head, loaded to the nozzle
    (tmp / "vars.cfg").write_text("[Variables]\nhat_lane = 0\nhat_loaded = 1\n")
    (tmp / "AFC.var.unit").write_text("{}")             # AFC's lane state file (installer creates it)

    # klippy's log thread is non-daemon and keeps batch mode alive after the gcode ends
    launcher = tmp / "launch.py"
    launcher.write_text(
        "import runpy, sys, threading\n"
        "_init = threading.Thread.__init__\n"
        "def _daemon(self, *a, **k):\n"
        "    _init(self, *a, **k)\n"
        "    self.daemon = True\n"
        "threading.Thread.__init__ = _daemon\n"
        "sys.argv = sys.argv[1:]\n"
        "sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0])\n"
        "runpy.run_path(sys.argv[0], run_name='__main__')\n")
    cmd = [sys.executable, str(launcher), str(kl / "klippy" / "klippy.py"), str(tmp / "printer.cfg"),
           "-i", str(HERE / name), "-o", str(tmp / "out.serial"),
           "-d", str(mcu_dict), "-l", str(tmp / "klippy.log"), "-v"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:   # klippy idles forever after a config error
        pass

    print(f"=== {name}")
    log = (tmp / "klippy.log").read_text() if (tmp / "klippy.log").exists() else ""
    if "Config error" in log:
        print(log[log.find("Config error") - 2000:])
        print(f"logs in {tmp}")
        return False
    log = log[log.find("Running full garbage collection"):]       # skip the config dump
    expects = sum(1 for l in (HERE / name).read_text().splitlines() if l.startswith("EXPECT"))
    for line in log.splitlines():
        if re.search(r"EXPECT|HAT_SIM|TEST_POOP|TEST DONE|could not|nothing to eject"
                     r"|Internal error|Config error|HatChanger_1:|Unknown command", line):
            print(line[:220])
    passed = log.count("EXPECT ok")
    from urllib.parse import parse_qs
    cuts = sum(1 for b in FakeMoonraker.posts
               if parse_qs(b).get("key", [""])[0].endswith("cut_total"))
    print(f"AFC cut_total updates: {cuts} (expected {want_cuts})")
    failed = ("EXPECT failed" in log or "Internal error" in log or "Unknown command" in log
              or "HATCHANGER AFC TEST DONE" not in log or passed != expects or cuts != want_cuts)
    print(f"{passed}/{expects} checks passed")
    if failed or keep:
        print(f"logs in {tmp}")
    return not failed


if __name__ == "__main__":
    sys.exit(main())
