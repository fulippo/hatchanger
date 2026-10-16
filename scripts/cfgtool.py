#!/usr/bin/env python3
"""Config-file edits for install.sh (HatChanger). Plain text edits, no Klipper needed.

  user-cfg      write hatchanger_user.cfg: your machine's values, kept across updates
  printer-block add / remove the HatChanger include block in printer.cfg
  moonraker     add / remove [update_manager hatchanger] in moonraker.conf
  afc-cfg       set the AFC.cfg options HatChanger needs: tool_cut / park / form_tip off,
                AFC_POOP / AFC_KICK / AFC_BRUSH with placeholder positions fixed;
                or --restore the values it changed
  purge-macro   print the effective _HAT_CFG purge_macro
  check         after a restart: ask Moonraker whether Klipper / AFC / HatChanger started cleanly
  save-vars     keep an existing [save_variables] file (hatchanger.cfg declares its own)

Every file is backed up next to itself (<name>.hatchanger-<timestamp>) before it changes.
"""
import argparse
import pathlib
import re
import shutil
import sys
import time

STAMP = time.strftime("%Y%m%d-%H%M%S")
BEGIN = "# >>> HatChanger (install.sh) >>>"
END = "# <<< HatChanger (install.sh) <<<"

# Options you calibrate or wire per machine. A fresh hatchanger_user.cfg lists them (commented,
# with the repo's values); a migration copies every option whose value differs from the repo.
USER_KEYS = {
    "filament_switch_sensor hat_toolhead": ["switch_pin"],
    "gcode_macro _HAT_CFG": [
        "variable_lane_x", "variable_dock_y_in", "variable_dock_y_front", "variable_dock_z",
        "variable_cut_x_touch", "variable_cut_x_cut", "variable_cut_y",
        "variable_nozzle_to_nip", "variable_load_park_xy", "variable_load_park_z",
        "variable_min_melt_temp", "variable_purge_macro", "variable_start_stub"],
    "ads1x1x hat_adc": ["i2c_mcu", "i2c_software_scl_pin", "i2c_software_sda_pin"],
    "gcode_macro _HAT_ID_CFG": ["variable_lane_ohms"],
}
# Sections whose single-line options are compared when migrating an old copy.
MIGRATE_SECTIONS = ["save_variables", "filament_switch_sensor hat_toolhead",
                    "gcode_macro _HAT_CFG", "ads1x1x hat_adc", "gcode_macro _HAT_ID_CFG"]


def backup(path: pathlib.Path) -> None:
    if path.exists():
        shutil.copy2(path, path.with_name(f"{path.name}.hatchanger-{STAMP}"))


def read_options(path: pathlib.Path) -> dict:
    """{section: {key: (value_without_comment, full_line)}} for single-line 'key: value' options.
    Indented lines (gcode bodies, continuations) are skipped."""
    out, sec = {}, None
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        m = re.match(r"^\[([^\]]+)\]", line)
        if m:
            sec = m.group(1).strip()
            out.setdefault(sec, {})
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*[:=]\s*(.*)$", line)
        if sec is not None and m:
            val = re.split(r"\s+[#;]", m.group(2), maxsplit=1)[0].strip()
            out[sec][m.group(1)] = (val, line.rstrip())
    return out


def cmd_user_cfg(a) -> int:
    out = pathlib.Path(a.out)
    if out.exists():
        print(f"  {out.name} exists, kept")
        return 0
    repo = {}
    for f in a.repo_cfg:
        for s, opts in read_options(pathlib.Path(f)).items():
            repo.setdefault(s, {}).update(opts)
    old = {}
    for f in a.old or []:
        for s, opts in read_options(pathlib.Path(f)).items():
            old.setdefault(s, {}).update(opts)

    lines = ["# HatChanger - YOUR machine's values. install.sh never overwrites this file, and",
             "# updates don't touch it. Included after hatchanger.cfg / hatchanger_id.cfg: an option",
             "# here replaces the same option there (Klipper merges sections with the same name).",
             ""]
    if old:
        lines += [f"# Migrated from your previous copies ({STAMP}): only the options that differ from",
                  "# the repo's files. Your old files are backed up as *.hatchanger-<date>.", ""]
        n = 0
        for sec in MIGRATE_SECTIONS:
            diff = [(k, v) for k, v in old.get(sec, {}).items()
                    if k not in repo.get(sec, {}) or repo[sec][k][0] != v[0]]
            if diff:
                lines.append(f"[{sec}]")
                lines += [full for _, (_, full) in diff]
                lines.append("")
                n += len(diff)
        print(f"  migrated {n} option(s) that differ from the repo into {out.name}")
    else:
        lines += ["# Fresh install: set the after-gears sensor pin, then calibrate (README, step 3).",
                  "# Uncomment what you change; the values shown are the repo's defaults.", ""]
        for sec, keys in USER_KEYS.items():
            if sec not in repo or (sec.startswith(("ads1x1x", "gcode_macro _HAT_ID")) and not a.hat_id):
                continue
            active = sec == "filament_switch_sensor hat_toolhead"
            lines.append(f"[{sec}]")
            for k in keys:
                if k in repo[sec]:
                    full = repo[sec][k][1]
                    lines.append(full if active else "#" + full)
            lines.append("")
    out.write_text("\n".join(lines))
    return 0


def cmd_printer_block(a) -> int:
    p = pathlib.Path(a.printer)
    if not p.exists():
        print(f"  {p} not found", file=sys.stderr)
        return 1
    text = p.read_text()
    # drop an existing block
    # (the block is written with one blank line on each side: removing it leaves one)
    new = re.sub(rf"\n*{re.escape(BEGIN)}.*?{re.escape(END)}\n*", "\n\n", text, flags=re.S)
    new = new.rstrip("\n") + "\n" if new.endswith("\n\n") else new
    # comment out hand-made includes of the HatChanger files
    tag = "  # replaced by the HatChanger block (install.sh)"
    if a.remove and a.uncomment_legacy:
        new, n_legacy = re.subn(rf"^# (\[include[^\]]*\]){re.escape(tag)}$", r"\1", new, flags=re.M)
    else:
        legacy = re.compile(r"^(\[include\s+[^\]]*hatchanger(_id|_afc|_tools|_user)?\.cfg\s*\])", re.M)
        new, n_legacy = legacy.subn(rf"# \1{tag}", new)
    if not a.remove:
        block = [BEGIN, "# managed by ~/hatchanger/install.sh: rerun it instead of editing here",
                 "[include hatchanger/hatchanger.cfg]"]
        if a.hat_id:
            block.append("[include hatchanger/hatchanger_id.cfg]")
        block.append("[include hatchanger/hatchanger_afc.cfg]" if a.mode == "afc"
                     else "[include hatchanger/hatchanger_tools.cfg]")
        block += ["[include hatchanger/hatchanger_user.cfg]", END]
        block = "\n".join(block) + "\n"
        marker = re.search(r"^#\*# <-+ SAVE_CONFIG -+>", new, re.M)
        if marker:
            new = new[:marker.start()].rstrip("\n") + "\n\n" + block + "\n" + new[marker.start():]
        else:
            new = new.rstrip("\n") + "\n\n" + block
    if new != text:
        backup(p)
        p.write_text(new)
        print(f"  printer.cfg: {'block removed' if a.remove else 'include block written'}"
              + (f", {n_legacy} old include(s) "
                 f"{'restored' if a.remove and a.uncomment_legacy else 'commented out'}"
                 if n_legacy else ""))
    else:
        print("  printer.cfg: already up to date")
    return 0


def cmd_moonraker(a) -> int:
    p = pathlib.Path(a.conf)
    if not p.exists():
        if not a.remove:
            print(f"  {p} not found: add the [update_manager hatchanger] section by hand (docs)")
        return 0
    text = p.read_text()
    sec = re.compile(r"\n?\[update_manager hatchanger\]\n(?:(?!\[).*\n?)*", re.M)
    new = sec.sub("\n", text).rstrip("\n") + "\n"
    if not a.remove:
        new += ("\n[update_manager hatchanger]\n"
                "type: git_repo\n"
                f"path: {a.repo}\n"
                f"origin: {a.origin}\n"
                f"primary_branch: {a.branch}\n"
                "managed_services: klipper\n")
    if new != text:
        backup(p)
        p.write_text(new)
        print(f"  moonraker.conf: [update_manager hatchanger] {'removed' if a.remove else 'written'}")
    else:
        print("  moonraker.conf: already up to date")
    return 0


def record(state, line: str) -> None:
    """Append one line to install.sh's state file (what the install changed, for --uninstall)."""
    if state:
        with open(state, "a") as fh:
            fh.write(line + "\n")


def cmd_afc_cfg(a) -> int:
    p = pathlib.Path(a.afc_cfg)
    if not p.exists():
        if not a.restore:
            print(f"  {p} not found: set tool_cut / park / form_tip to False in your AFC.cfg")
        return 0
    text, changed = p.read_text(), []
    if a.restore:
        # put back the values the install changed: lines "afc_cfg <key> <old value>"
        st = pathlib.Path(a.state) if a.state else None
        olds = {}
        if st and st.exists():
            for line in st.read_text().splitlines():
                parts = line.split(" ", 2)
                if len(parts) == 3 and parts[0] == "afc_cfg":
                    olds.setdefault(parts[1], parts[2])   # first record = the original value
        for key, val in olds.items():
            rx = re.compile(rf"^({key}\s*:\s*)(\S+)", re.M)
            m = rx.search(text)
            if m and m.group(2) != val:
                text = rx.sub(lambda mm: mm.group(1) + val, text, count=1)
                changed.append(f"{key}: {val}")
        if changed:
            backup(p)
            p.write_text(text)
            print(f"  AFC.cfg restored: {', '.join(changed)}")
        return 0
    def get(key):
        m = re.search(rf"^{key}\s*:\s*(\S+)", text, re.M)
        return m.group(1) if m else None

    def setv(key, val, why):
        nonlocal text
        rx = re.compile(rf"^({key}\s*:\s*)(\S+)", re.M)
        m = rx.search(text)
        if m and m.group(2) != val:
            record(a.state, f"afc_cfg {key} {m.group(2)}")
            text = rx.sub(lambda mm: mm.group(1) + val, text, count=1)
            changed.append(f"{key}: {val} ({why})")

    for key in ("tool_cut", "park", "form_tip"):
        if (get(key) or "false").lower() != "false":
            setv(key, "False", "HAT_DOCK cuts and parks")

    # AFC refuses every tool change while an enabled AFC_* macro still has its -99 placeholder
    # position (verify_macro_positions). Fix the ones HatChanger can decide for you.
    mv = read_options(pathlib.Path(a.macro_vars)) if a.macro_vars else {}

    def placeholder(section, var):
        v = mv.get(f"gcode_macro {section}", {}).get(var)
        return v is not None and re.sub(r"\s", "", v[0]).startswith("-99,-99")

    if (get("poop") or "").lower() == "true" and get("poop_cmd") == "AFC_POOP" \
            and placeholder("_AFC_POOP_VARS", "variable_purge_loc_xy"):
        if a.purge_macro:
            setv("poop_cmd", a.purge_macro, "your purge_macro; AFC_POOP has no purge position")
        else:
            setv("poop", "False", "AFC_POOP has no purge position; HatChanger pushes the stub out")
    if (get("kick") or "").lower() == "true" and get("kick_cmd") == "AFC_KICK" \
            and placeholder("_AFC_KICK_VARS", "variable_kick_start_loc"):
        setv("kick", "False", "no kick position set")
    if (get("wipe") or "").lower() == "true" and get("wipe_cmd") == "AFC_BRUSH" \
            and placeholder("_AFC_BRUSH_VARS", "variable_brush_loc"):
        setv("wipe", "False", "no brush position set")

    if changed:
        backup(p)
        p.write_text(text)
        print("  AFC.cfg: " + "\n           ".join(changed))
    else:
        print("  AFC.cfg: already set up for HatChanger")
    if (get("poop") or "").lower() != "true":
        print("  AFC.cfg: poop is off: HatChanger pushes the cut stub (~43 mm) out at load_park_xy.\n"
              "           Set load_park_xy in hatchanger_user.cfg (over a bucket / off the bed), or\n"
              "           it comes out wherever the head is.")
    return 0


def cmd_purge_macro(a) -> int:
    val = ""
    for f in a.files:
        opt = read_options(pathlib.Path(f)).get("gcode_macro _HAT_CFG", {}).get("variable_purge_macro")
        if opt:
            val = opt[0].strip("'\"")
    print(val)
    return 0


def _get(base: str, path: str, timeout: float = 5.0):
    import json
    import urllib.request
    with urllib.request.urlopen(base.rstrip("/") + path, timeout=timeout) as r:
        return json.load(r)["result"]


def cmd_check(a) -> int:
    """Read-only health check through Moonraker's HTTP API. Exit 0 = all good, 1 = problems."""
    import urllib.parse
    ok, warns = [], []

    def bad(msg):
        warns.append(msg)

    import time
    deadline = time.time() + a.wait
    while True:   # after a restart Moonraker / Klipper take a few seconds to come back
        try:
            info = _get(a.moonraker, "/printer/info")
            if info.get("state") != "startup" or time.time() > deadline:
                break
        except Exception as e:  # noqa: BLE001 - any connection problem is reported the same way
            if time.time() > deadline:
                print(f"  can't reach Moonraker at {a.moonraker} ({e}). Use --moonraker URL")
                return 1
        time.sleep(2)
    if a.wait:   # give PREP (AFC's startup, 2 s after ready) time to run
        time.sleep(min(a.wait, 6))
    state = info.get("state")
    if state != "ready":
        print(f"  Klipper is '{state}':\n    " + "\n    ".join(
            (info.get("state_message") or "").strip().splitlines()[:12]))
        print("  Fix that first (it's usually a config error), restart, then --check again.")
        return 1
    ok.append("Klipper is ready")

    objs = _get(a.moonraker, "/printer/objects/list")["objects"]
    names = ["configfile", "gcode_macro _HAT_STATE", "gcode_macro _HAT_CFG"]
    afc = "AFC" in objs
    units = [o for o in objs if o.startswith("AFC_HatChanger ")]
    lanes = [o for o in objs if o.startswith("AFC_lane ")]
    if afc:
        names += ["AFC"] + units + lanes + [
            "gcode_macro _AFC_POOP_VARS", "gcode_macro _AFC_KICK_VARS",
            "gcode_macro _AFC_BRUSH_VARS", "gcode_macro _AFC_PARK_VARS",
            "gcode_macro _AFC_CUT_TIP_VARS"]
    q = "&".join(urllib.parse.quote(n) for n in names if n in objs)
    st = _get(a.moonraker, "/printer/objects/query?" + q)["status"]

    if "gcode_macro _HAT_STATE" not in st:
        bad("HatChanger macros are not loaded: is the HatChanger include block in printer.cfg?")
    else:
        hs = st["gcode_macro _HAT_STATE"]
        lane = int(hs.get("lane", -1))
        ok.append(f"HatChanger loaded: hat {lane if lane >= 0 else 'none'} on the head, "
                  f"loaded {int(hs.get('loaded', 0))}")

    for w in (st.get("configfile", {}).get("warnings") or []):
        bad(f"config warning: {w.get('message', w)}")

    settings = st.get("configfile", {}).get("settings", {})
    if not afc:
        if a.expect_afc:
            bad("AFC is not loaded (no AFC object in Klipper): is AFC installed and included?")
        elif "gcode_macro t0" in settings:
            ok.append("standalone mode: T0 / T1 ... run HAT_CHANGE")
        else:
            bad("standalone mode but no T0 macro: include hatchanger/hatchanger_tools.cfg")
    else:
        if not units:
            bad("AFC is loaded but has no HatChanger unit: include hatchanger/hatchanger_afc.cfg")
        for u in units:
            us = st.get(u, {})
            ok.append(f"{u}: lanes {', '.join(us.get('lanes', [])) or 'none'}")
        other = [x for x in st.get("AFC", {}).get("units", []) if not x.startswith("HatChanger ")]
        if other:
            bad(f"AFC also loads other units: {', '.join(other)} (disable their AFC/*.cfg "
                "files, or rerun ./install.sh --afc)")
        for ln in lanes:
            ls = st.get(ln, {})
            if ls.get("unit") and not any(u.split(" ", 1)[1] == ls["unit"] for u in units):
                continue
            ok.append(f"  {ln.split(' ', 1)[1]}: {ls.get('map')} "
                      f"{'LOADED' if ls.get('tool_loaded') else 'docked'}")
        cur = st.get("AFC", {}).get("current_load")
        for u in units:
            hat, loaded = st[u].get("hat_on_head", -1), st[u].get("hat_loaded", False)
            want = f"hat{hat}" if loaded else None
            if (cur or None) != want and loaded:
                bad(f"AFC says '{cur}' is loaded but HatChanger has hat {hat} loaded: "
                    "run AFC_HATCHANGER_SYNC UNIT=" + u.split(" ", 1)[1])
        if st.get("AFC", {}).get("error_state"):
            bad("AFC is in error state: " + (st["AFC"].get("message", {}) or {}).get("message", ""))
        # the same placeholder test AFC runs before every tool change
        acfg = settings.get("afc", {})
        checks = [("tool_cut", "tool_cut_cmd", "AFC_CUT", "_AFC_CUT_TIP_VARS", "pin_loc_xy"),
                  ("park", "park_cmd", "AFC_PARK", "_AFC_PARK_VARS", "park_loc_xy"),
                  ("poop", "poop_cmd", "AFC_POOP", "_AFC_POOP_VARS", "purge_loc_xy"),
                  ("kick", "kick_cmd", "AFC_KICK", "_AFC_KICK_VARS", "kick_start_loc"),
                  ("wipe", "wipe_cmd", "AFC_BRUSH", "_AFC_BRUSH_VARS", "brush_loc")]
        for en, cmdk, dflt, mac, var in checks:
            if acfg.get(en) and str(acfg.get(cmdk, dflt)).upper() == dflt:
                v = st.get(f"gcode_macro {mac}", {}).get(var)
                if isinstance(v, (list, tuple)) and len(v) >= 2 and v[0] == -99 and v[1] == -99:
                    bad(f"AFC.cfg: {en} is on with {dflt}, but {var} is still -99: every tool change "
                        f"will be refused. Set {en}: False, or set {var} in AFC_Macro_Vars.cfg")
        for en in ("tool_cut", "park", "form_tip"):
            if acfg.get(en):
                bad(f"AFC.cfg: {en} is True: HatChanger's HAT_DOCK already cuts; set it to False")
        pc = str(acfg.get("poop_cmd", ""))
        if acfg.get("poop") and pc and f"gcode_macro {pc.lower()}" not in settings \
                and pc.upper() not in ("AFC_POOP",):
            bad(f"AFC.cfg: poop_cmd '{pc}' isn't a macro in your config")

    # errors printed to the console since the last restart
    try:
        store = _get(a.moonraker, "/server/gcode_store?count=300").get("gcode_store", [])
        start = max((i for i, g in enumerate(store) if "Klipper state: Ready" in g.get("message", "")
                     or "PREP" in g.get("message", "")[:8]), default=0)
        errs = [g["message"].strip() for g in store[start:]
                if g.get("message", "").lstrip().startswith(("!!", "Error")) or "error--text" in g.get("message", "")]
        for e in errs[-8:]:
            bad("console: " + re.sub(r"<[^>]+>", "", e).replace("\n", " ")[:200])
    except Exception:  # noqa: BLE001 - the console history is a bonus
        pass

    for line in ok:
        print("  ok   " + line)
    for line in warns:
        print("  !!   " + line)
    print("  all good" if not warns else f"  {len(warns)} problem(s)")
    return 0 if not warns else 1


def cmd_save_vars(a) -> int:
    """hatchanger.cfg declares [save_variables]. Klipper merges duplicate sections, so if the
    printer already has one, whichever is included last decides the file: pin the existing one
    in hatchanger_user.cfg (included last) so other macros keep their variables."""
    cfg_dir, user = pathlib.Path(a.cfg_dir), pathlib.Path(a.user_cfg)
    if "[save_variables]" in user.read_text():
        return 0
    found = None
    for f in sorted(cfg_dir.rglob("*.cfg")):
        rel = f.relative_to(cfg_dir).as_posix()
        if rel.startswith("hatchanger/") or ".hatchanger-" in f.name or "hatchanger" in f.name:
            continue
        opts = read_options(f).get("save_variables")
        if opts and "filename" in opts:
            found = (rel, opts["filename"][0])
            break
    if found is None:
        return 0
    with user.open("a") as fh:
        fh.write("\n# Your existing [save_variables] (from %s) stays in use: hatchanger.cfg declares one\n"
                 "# too, and this file is included last. HatChanger keeps hat_lane / hat_loaded there.\n"
                 "[save_variables]\nfilename: %s\n" % found)
    print(f"  [save_variables] from {found[0]} kept ({found[1]}): check HAT_STATUS after the restart")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("user-cfg")
    u.add_argument("--out", required=True)
    u.add_argument("--repo-cfg", nargs="+", required=True)
    u.add_argument("--old", nargs="*")
    u.add_argument("--hat-id", type=int, default=0)
    b = sub.add_parser("printer-block")
    b.add_argument("--printer", required=True)
    b.add_argument("--mode", choices=["afc", "standalone"], default="standalone")
    b.add_argument("--hat-id", type=int, default=0)
    b.add_argument("--remove", action="store_true")
    b.add_argument("--uncomment-legacy", action="store_true",
                   help="with --remove: restore the old includes the install commented out")
    m = sub.add_parser("moonraker")
    m.add_argument("--conf", required=True)
    m.add_argument("--repo", default="~/hatchanger")
    m.add_argument("--origin", default="https://github.com/fulippo/hatchanger.git")
    m.add_argument("--branch", default="main")
    m.add_argument("--remove", action="store_true")
    f = sub.add_parser("afc-cfg")
    f.add_argument("--afc-cfg", required=True)
    f.add_argument("--state", help="install.sh state file: record (or, with --restore, read) changes")
    f.add_argument("--restore", action="store_true", help="put back the values the install changed")
    f.add_argument("--macro-vars", help="AFC_Macro_Vars.cfg, to spot placeholder positions")
    f.add_argument("--purge-macro", default="", help="HatChanger's purge_macro, used as AFC poop_cmd")
    c = sub.add_parser("check")
    c.add_argument("--moonraker", default="http://localhost:7125")
    c.add_argument("--expect-afc", action="store_true")
    c.add_argument("--wait", type=float, default=0, help="seconds to wait for Klipper to start")
    pm = sub.add_parser("purge-macro", help="print the effective _HAT_CFG purge_macro")
    pm.add_argument("files", nargs="+", help="hatchanger.cfg, then hatchanger_user.cfg (later wins)")
    v = sub.add_parser("save-vars")
    v.add_argument("--cfg-dir", required=True)
    v.add_argument("--user-cfg", required=True)
    a = ap.parse_args()
    return {"check": cmd_check, "purge-macro": cmd_purge_macro, "save-vars": cmd_save_vars, "user-cfg": cmd_user_cfg, "printer-block": cmd_printer_block,
            "moonraker": cmd_moonraker, "afc-cfg": cmd_afc_cfg}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
