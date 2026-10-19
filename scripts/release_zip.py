#!/usr/bin/env python3
"""Build the release assets (run by the release workflow, or by hand to test):

  hatchanger.zip              what a printer needs: install.sh, scripts/, klipper/config, klipper/extras,
                              docs/*.md, README, LICENSE, CHANGELOG + release_info.json. Moonraker's
                              update manager ([update_manager hatchanger], type: zip) downloads this
                              asset ({section name}.zip) and unpacks it into ~/hatchanger.
  hatchanger-stl-<tag>.zip    the print files of this version (cad/<component>/stl/**.stl), one
                              folder per component (hatchanger/, ptfe_rail_clamp/, tophat/<size>/)

  python3 scripts/release_zip.py --version v0.2.0 --out dist

Files are taken from `git ls-files` (tracked files only) when the repo is a git checkout,
otherwise from the folder itself.
"""
import argparse
import json
import pathlib
import subprocess
import zipfile

REPO = pathlib.Path(__file__).resolve().parent.parent
OWNER, NAME = "fulippo", "hatchanger"
# what goes on the printer: no CAD, no tests
PRINTER = ["install.sh", "scripts/", "klipper/config/", "klipper/extras/", "docs/", "README.md",
           "LICENSE", "CHANGELOG.md"]
SKIP = ["docs/images/", "scripts/release_zip.py"]
EXEC = {"install.sh", "scripts/cfgtool.py"}


def tracked() -> list:
    try:
        out = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True,
                             check=True).stdout.decode()
        return sorted(f for f in out.split("\0") if f)
    except (OSError, subprocess.CalledProcessError):
        return sorted(p.relative_to(REPO).as_posix() for p in REPO.rglob("*")
                      if p.is_file() and ".git/" not in p.as_posix())


def pick(files, include, skip=()) -> list:
    def ok(f):
        return (any(f == i or (i.endswith("/") and f.startswith(i)) for i in include)
                and not any(f.startswith(s) for s in skip) and "__pycache__" not in f)
    return [f for f in files if ok(f) and (REPO / f).is_file()]


def add(z: zipfile.ZipFile, arc: str, data: bytes, executable: bool = False) -> None:
    info = zipfile.ZipInfo(arc, date_time=(2020, 1, 1, 0, 0, 0))   # reproducible
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = ((0o755 if executable else 0o644) | 0o100000) << 16
    z.writestr(info, data)


def build(version: str, out: pathlib.Path) -> tuple:
    out.mkdir(parents=True, exist_ok=True)
    files = tracked()
    app = out / f"{NAME}.zip"
    with zipfile.ZipFile(app, "w") as z:
        for f in pick(files, PRINTER, SKIP):
            add(z, f, (REPO / f).read_bytes(), f in EXEC)
        info = {"project_name": NAME, "project_owner": OWNER, "version": version,
                "asset_name": f"{NAME}.zip"}
        add(z, "release_info.json", (json.dumps(info, indent=2) + "\n").encode())
    stl = out / f"{NAME}-stl-{version}.zip"
    with zipfile.ZipFile(stl, "w") as z:
        for f in pick(files, ["cad/"]):
            parts = pathlib.PurePosixPath(f).parts      # cad/<component>/stl/...
            if f.endswith(".stl") and len(parts) > 3 and parts[2] == "stl":
                rel = pathlib.PurePosixPath(parts[1], *parts[3:])
                add(z, f"{NAME}-stl-{version}/{rel}", (REPO / f).read_bytes())
    return app, stl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", required=True, help="release tag, e.g. v0.2.0")
    ap.add_argument("--out", default="dist", type=pathlib.Path)
    a = ap.parse_args()
    for p in build(a.version, a.out):
        print(f"{p} ({p.stat().st_size // 1024} kB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
