#!/usr/bin/env bash
# HatChanger installer: links the Klipper files into your config, adds the includes to
# printer.cfg and registers HatChanger with Moonraker's update manager.
#
#   cd ~ && wget -q https://github.com/fulippo/hatchanger/releases/latest/download/hatchanger.zip \
#     && unzip -oq hatchanger.zip -d hatchanger && rm hatchanger.zip && bash hatchanger/install.sh
#
# Updates always come from GitHub releases (Moonraker update type zip: no CAD files on the
# printer). Run from a git clone, the installer downloads the latest release into
# ~/hatchanger-release and installs from there (Moonraker can't manage a folder inside git).
#
# Options:
#   --afc | --standalone   run as an AFC unit, or on its own with T0/T1/... macros
#                          (default: --afc if AFC is installed, else --standalone; asked if unsure)
#   --hat-id | --no-hat-id include the hat-ID reader config (default: asked)
#   -c DIR                 Klipper config dir         (default ~/printer_data/config)
#   -k DIR                 Klipper checkout           (default ~/klipper)
#   -m FILE                moonraker.conf             (default <config dir>/moonraker.conf)
#   -y                     take the default answer to every question (no prompts)
#   --beta                 also take pre-releases (Moonraker channel beta)
#   --no-restart           don't restart Klipper / Moonraker at the end
#   --afc-help             print the answers to give AFC's own installer, and exit
#   --check                after restarting Klipper: ask Moonraker whether Klipper, AFC and
#                          HatChanger started cleanly, and print what's wrong
#   --moonraker URL        Moonraker for --check   (default http://localhost:7125)
#   --uninstall            undo the install: include block, links, update-manager entry, AFC.cfg
#                          values and disabled AFC files are put back (asks first for the files);
#                          can also restore a previous hand-made install. Keeps your files unless
#   --purge                (with --uninstall) also deletes ~/printer_data/config/hatchanger
#                          (hatchanger_user.cfg, the lane file) and the saved hat state
#
# What it does (every edited file is backed up as <file>.hatchanger-<date>):
#   <config>/hatchanger/hatchanger.cfg, hatchanger_id.cfg  -> links into this repo (updated by git)
#   <config>/hatchanger/hatchanger_tools.cfg or _afc.cfg   -> copied once (your lanes)
#   <config>/hatchanger/hatchanger_user.cfg                -> your values, never overwritten
#   printer.cfg                                            -> one marked include block
#   moonraker.conf                                         -> [update_manager hatchanger], type zip
#   AFC mode: klippy/extras/AFC_HatChanger.py link, AFC.cfg tool_cut/park/form_tip off
# An older hand-made install (hatchanger*.cfg copies in the config dir) is migrated: options
# whose values differ from the repo go into hatchanger_user.cfg, the old files move aside.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARGS=("$@")
RELEASE_DIR="${HOME}/hatchanger-release"   # where a clone puts the release it installs
CFG_DIR="${HOME}/printer_data/config"
KLIPPER_DIR="${HOME}/klipper"
MOONRAKER_CONF=""
MODE=""
HAT_ID=""
YES=0
RESTART=1
RESTARTED=""
UNINSTALL=0
PURGE=0
AFC_HELP=0
CHECK=0
MOONRAKER_URL=""
CHANNEL=stable

while [ $# -gt 0 ]; do
  case "$1" in
    --afc) MODE=afc ;;
    --standalone) MODE=standalone ;;
    --hat-id) HAT_ID=1 ;;
    --no-hat-id) HAT_ID=0 ;;
    -c) CFG_DIR="$2"; shift ;;
    -k) KLIPPER_DIR="$2"; shift ;;
    -m) MOONRAKER_CONF="$2"; shift ;;
    -y) YES=1 ;;
    --beta) CHANNEL=beta ;;
    --no-restart) RESTART=0 ;;
    --uninstall) UNINSTALL=1 ;;
    --purge) PURGE=1 ;;
    --afc-help) AFC_HELP=1 ;;
    --check) CHECK=1 ;;
    --moonraker) MOONRAKER_URL="$2"; shift ;;
    -h|--help) sed -n '2,/^# What it does/p' "$0" | sed '$d'; exit 0 ;;
    *) echo "unknown option: $1 (see --help)"; exit 1 ;;
  esac
  shift
done
MOONRAKER_CONF="${MOONRAKER_CONF:-${CFG_DIR}/moonraker.conf}"
MOONRAKER_URL="${MOONRAKER_URL:-http://localhost:7125}"
DEST="${CFG_DIR}/hatchanger"
EXTRAS="${KLIPPER_DIR}/klippy/extras"
TOOL="python3 ${REPO}/scripts/cfgtool.py"
STAMP="$(date +%Y%m%d-%H%M%S)"
STATE="${DEST}/.install-state"   # what the install changed outside its own files, for --uninstall

say()  { printf '\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m%s\033[0m\n' "$*"; }
ask() {  # ask "question" default(y/n) -> 0 for yes
  local q="$1" def="${2:-y}" r
  if [ "$YES" = 1 ]; then [ "$def" = y ]; return; fi
  read -r -p "$q [$( [ "$def" = y ] && echo Y/n || echo y/N )] " r || true
  r="${r:-$def}"
  [[ "$r" =~ ^[Yy] ]]
}
record() { mkdir -p "$DEST"; echo "$*" >> "$STATE"; }
recorded() { [ -f "$STATE" ] && grep -qxF "$*" "$STATE"; }
link() {  # link src dst
  if [ -e "$2" ] && [ ! -L "$2" ]; then mv "$2" "$2.hatchanger-${STAMP}"; fi
  ln -sfn "$1" "$2"
}
GIT_EXCLUDE="${KLIPPER_DIR}/.git/info/exclude"
exclude_from_git() {  # keep Moonraker from reporting klipper as dirty
  local entry="klippy/extras/$1"
  if [ -d "${KLIPPER_DIR}/.git" ] && ! grep -qxF "$entry" "$GIT_EXCLUDE" 2>/dev/null; then
    mkdir -p "$(dirname "$GIT_EXCLUDE")"; echo "$entry" >> "$GIT_EXCLUDE"
    record "git_exclude $entry"
  fi
}
restart() {
  if [ "$RESTART" = 0 ]; then return; fi
  if command -v systemctl >/dev/null && systemctl list-unit-files 2>/dev/null | grep -q "^$1\.service"; then
    if ask "Restart $1 now?" y; then
      sudo systemctl restart "$1" && say "  $1 restarted" && RESTARTED="$RESTARTED $1"
    fi
  else
    warn "  restart $1 yourself"
  fi
}

afc_howto() {
  cat <<'TXT'
  To run HatChanger under AFC, install AFC first, then rerun ./install.sh --afc:
      cd ~ && git clone https://github.com/ArmoredTurtle/AFC-Klipper-Add-On.git
      cd AFC-Klipper-Add-On && ./install-afc.sh
  In AFC's menu (it needs a unit type, HatChanger isn't one of them):
      T  BoxTurtle (4-Lane)   keep: its files are disabled by this installer
      3  toolhead cutter      False  (HAT_DOCK cuts)
      5  kick macro           False
      6  park macro           False
      8  wipe macro           False  (unless you set up AFC_BRUSH)
      9  toolhead sensor      Sensor (leave the pin Unknown)
      B  buffer type          None   (press B until it says None)
      C  unit name            any    (the HatChanger unit has its own name)
  Klipper shows an error until ./install.sh --afc has run: that's expected.
TXT
}
if [ "$AFC_HELP" = 1 ]; then afc_howto; exit 0; fi
if [ "$CHECK" = 1 ]; then
  say "Checking Klipper / AFC / HatChanger through ${MOONRAKER_URL}"
  EXP=""; [ -e "${EXTRAS}/AFC_HatChanger.py" ] && EXP="--expect-afc"
  exec $TOOL check --moonraker "$MOONRAKER_URL" $EXP
fi
[ -f "${CFG_DIR}/printer.cfg" ] || { echo "no printer.cfg in ${CFG_DIR} (use -c DIR)"; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }

# ------------------------------------------------------------------------- release ----------
# Installs always run from an unpacked release, which Moonraker then keeps updated. From a git
# clone: fetch the latest release and hand over to its installer.
if [ "$UNINSTALL" = 0 ] && [ ! -f "${REPO}/release_info.json" ]; then
  say "Getting the latest HatChanger release$( [ "$CHANNEL" = beta ] && echo ' (pre-releases too)' ) -> ${RELEASE_DIR}"
  $TOOL fetch-release --out "$RELEASE_DIR" $( [ "$CHANNEL" = beta ] && echo --beta ) \
    || { warn "  could not get the release: check the network, or install from the release zip (README)"; exit 1; }
  exec bash "${RELEASE_DIR}/install.sh" ${ARGS[@]+"${ARGS[@]}"}
fi

# ------------------------------------------------------------------------- uninstall --------
if [ "$UNINSTALL" = 1 ]; then
  say "Uninstalling HatChanger"
  # 1. includes and update manager
  RESTORE_OLD=0
  if [ -f "$STATE" ] && grep -q "^migrated " "$STATE"; then
    if ask "Put back your previous hand-made install (old hatchanger*.cfg copies and includes)?" n; then
      RESTORE_OLD=1; fi
  fi
  if [ "$RESTORE_OLD" = 1 ]; then
    $TOOL printer-block --printer "${CFG_DIR}/printer.cfg" --remove --uncomment-legacy
    while read -r kind orig bak; do
      [ "$kind" = migrated ] || continue
      if [ -f "$bak" ] && [ ! -e "$orig" ]; then mv "$bak" "$orig"; echo "  $(basename "$orig") restored"; fi
    done < "$STATE"
  else
    $TOOL printer-block --printer "${CFG_DIR}/printer.cfg" --remove
    if [ -f "$STATE" ] && grep -q "^migrated " "$STATE"; then
      echo "  your previous hand-made files stay aside as *.hatchanger-<date>"
    fi
  fi
  $TOOL moonraker --conf "$MOONRAKER_CONF" --remove

  # 2. links into the repo and into Klipper
  for f in hatchanger.cfg hatchanger_id.cfg; do
    if [ -L "${DEST}/$f" ]; then rm "${DEST}/$f"; echo "  $f link removed"; fi
  done
  if [ -L "${EXTRAS}/AFC_HatChanger.py" ]; then
    rm "${EXTRAS}/AFC_HatChanger.py"; echo "  AFC_HatChanger.py unlinked from Klipper"
  fi
  if [ -f "$GIT_EXCLUDE" ] && grep -qxF "klippy/extras/AFC_HatChanger.py" "$GIT_EXCLUDE"; then
    grep -vxF "klippy/extras/AFC_HatChanger.py" "$GIT_EXCLUDE" > "${GIT_EXCLUDE}.tmp" || true
    mv "${GIT_EXCLUDE}.tmp" "$GIT_EXCLUDE"; echo "  Klipper git exclude entry removed"
  fi

  # 3. AFC: the values and files the install changed
  if [ -f "${CFG_DIR}/AFC/AFC.cfg" ] && [ -f "$STATE" ] && grep -q "^afc_cfg " "$STATE"; then
    $TOOL afc-cfg --afc-cfg "${CFG_DIR}/AFC/AFC.cfg" --state "$STATE" --restore
  elif [ -f "${CFG_DIR}/AFC/AFC.cfg" ] && [ ! -f "$STATE" ]; then
    warn "  no record of the install's AFC.cfg changes: check tool_cut / park / form_tip in AFC/AFC.cfg"
  fi
  DISABLED=()
  if [ -f "$STATE" ]; then
    while read -r kind path _; do
      [ "$kind" = disabled ] && [ -f "${path}.disabled" ] && DISABLED+=("$path")
    done < "$STATE"
  else   # installed before the state file existed: offer the AFC files that look like ours
    for f in "${CFG_DIR}"/AFC/*.cfg.disabled; do [ -f "$f" ] && DISABLED+=("${f%.disabled}"); done
  fi
  for f in "${DISABLED[@]+"${DISABLED[@]}"}"; do
    if [ -e "$f" ]; then warn "  $(basename "$f") exists, $(basename "$f").disabled left as is"; continue; fi
    if ask "Re-enable AFC's $(basename "$f")?" y; then
      mv "${f}.disabled" "$f"; echo "  $(basename "$f") re-enabled"; fi
  done
  if [ -f "${CFG_DIR}/AFC/AFC.cfg" ] && grep -qE '^\[include AFC/' "${CFG_DIR}/printer.cfg" \
     && [ "${#DISABLED[@]}" = 0 ]; then
    warn "  AFC stays installed without HatChanger lanes: give it a unit (AFC_Hardware.cfg) or remove its include"
  fi

  # files the install created for AFC: removed only if AFC never wrote to them
  if [ -f "$STATE" ]; then
    while read -r kind path _; do
      if [ "$kind" = created ] && [ -f "$path" ] && [ "$(cat "$path")" = "{}" ]; then
        rm "$path"; echo "  $(basename "$path") removed (still empty)"
      fi
    done < "$STATE"
  fi

  # 4. your files
  rm -f "$STATE"
  if [ -d "$DEST" ]; then
    if [ "$PURGE" = 1 ] && ask "Delete ${DEST} (hatchanger_user.cfg, lane file) and the saved hat state?" y; then
      rm -rf "$DEST"; rm -f "${CFG_DIR}/hatchanger_vars.cfg"; echo "  ${DEST} deleted"
    else
      echo "  kept: ${DEST} (your values; --uninstall --purge deletes it)"
    fi
  fi
  ls "${CFG_DIR}"/*.hatchanger-* >/dev/null 2>&1 && \
    echo "  backups of edited files: ${CFG_DIR}/*.hatchanger-<date> (delete when happy)"
  echo "  the repo itself: rm -rf ${REPO}"
  restart moonraker; restart klipper
  exit 0
fi

# ------------------------------------------------------------------------- choices ----------
AFC_FOUND=0
[ -e "${EXTRAS}/AFC.py" ] && AFC_FOUND=1
if [ -z "$MODE" ]; then
  if [ "$AFC_FOUND" = 1 ]; then
    if ask "AFC is installed. Run HatChanger as an AFC unit?" y; then MODE=afc; else MODE=standalone; fi
  else
    warn "AFC (Armored Turtle) is not installed in ${KLIPPER_DIR}: installing HatChanger STANDALONE"
    echo "  (T0, T1, ... macros, no AFC panel in Mainsail)."
    afc_howto
    if ! ask "Continue with the standalone install?" y; then exit 0; fi
    MODE=standalone
  fi
fi
if [ "$MODE" = afc ] && [ "$AFC_FOUND" = 0 ]; then
  warn "--afc: AFC (Armored Turtle) is not installed in ${KLIPPER_DIR} (no klippy/extras/AFC.py)."
  afc_howto
  exit 1
fi
if [ -z "$HAT_ID" ]; then
  if [ -e "${CFG_DIR}/hatchanger_id.cfg" ] || ask "Include the hat-ID reader (ADS1115 board)?" n; then
    HAT_ID=1; else HAT_ID=0; fi
fi
say "Installing HatChanger: ${MODE}$( [ "$HAT_ID" = 1 ] && echo ', hat-ID reader' ) -> ${DEST}"

# ------------------------------------------------------------------------- files ------------
mkdir -p "$DEST"
OLD=()
for f in hatchanger.cfg hatchanger_id.cfg; do
  [ -f "${CFG_DIR}/$f" ] && [ ! -L "${CFG_DIR}/$f" ] && OLD+=("${CFG_DIR}/$f")
done
REPO_CFG=("${REPO}/klipper/config/hatchanger.cfg" "${REPO}/klipper/config/hatchanger_id.cfg")
$TOOL user-cfg --out "${DEST}/hatchanger_user.cfg" --repo-cfg "${REPO_CFG[@]}" \
  --hat-id "$HAT_ID" ${OLD[@]+--old "${OLD[@]}"}
$TOOL save-vars --cfg-dir "$CFG_DIR" --user-cfg "${DEST}/hatchanger_user.cfg"
for f in "${OLD[@]+"${OLD[@]}"}"; do
  mv "$f" "$f.hatchanger-${STAMP}"; echo "  old $(basename "$f") moved to $(basename "$f").hatchanger-${STAMP}"
  record "migrated $f $f.hatchanger-${STAMP}"
done
for f in hatchanger_tools.cfg hatchanger_afc.cfg; do   # an old hand copy of the lane file wins
  [ -f "${CFG_DIR}/$f" ] && [ ! -f "${DEST}/$f" ] && mv "${CFG_DIR}/$f" "${DEST}/$f" \
    && echo "  your $f moved into ${DEST}"
done

link "${REPO}/klipper/config/hatchanger.cfg" "${DEST}/hatchanger.cfg"
if [ "$HAT_ID" = 1 ]; then
  link "${REPO}/klipper/config/hatchanger_id.cfg" "${DEST}/hatchanger_id.cfg"
elif [ -L "${DEST}/hatchanger_id.cfg" ]; then rm "${DEST}/hatchanger_id.cfg"; fi
LANES="hatchanger_tools.cfg"; [ "$MODE" = afc ] && LANES="hatchanger_afc.cfg"
if [ ! -f "${DEST}/${LANES}" ]; then
  cp "${REPO}/klipper/config/${LANES}" "${DEST}/${LANES}"
  echo "  ${LANES} copied: one lane per hat (edit it when you add racks)"
else
  echo "  ${LANES} exists, kept"
fi
echo "  hatchanger.cfg$( [ "$HAT_ID" = 1 ] && echo ', hatchanger_id.cfg' ) linked to the repo"

# ------------------------------------------------------------------------- AFC --------------
if [ "$MODE" = afc ]; then
  link "${REPO}/klipper/extras/AFC_HatChanger.py" "${EXTRAS}/AFC_HatChanger.py"
  exclude_from_git AFC_HatChanger.py
  echo "  AFC_HatChanger.py linked into ${EXTRAS}"
  PURGE_MACRO="$($TOOL purge-macro "${REPO}/klipper/config/hatchanger.cfg" "${DEST}/hatchanger_user.cfg")"
  if [ -n "$PURGE_MACRO" ] && ! grep -rqiE "^\[gcode_macro ${PURGE_MACRO}\]" "$CFG_DIR" --include='*.cfg' 2>/dev/null; then
    warn "  purge_macro '${PURGE_MACRO}' isn't defined in your config: not used as AFC's poop_cmd"
    PURGE_MACRO=""
  fi
  $TOOL afc-cfg --afc-cfg "${CFG_DIR}/AFC/AFC.cfg" --state "$STATE" \
    --macro-vars "${CFG_DIR}/AFC/AFC_Macro_Vars.cfg" --purge-macro "$PURGE_MACRO"
  # AFC keeps lane state in <VarFile>.unit and complains at the first PREP if it doesn't exist yet
  VARFILE="$(sed -n 's/^VarFile:[[:space:]]*\([^#[:space:]]*\).*/\1/p' "${CFG_DIR}/AFC/AFC.cfg" 2>/dev/null | head -1)"
  case "$VARFILE" in   # a relative path is relative to klippy's working dir (the Klipper checkout)
    ../*) VARFILE="${KLIPPER_DIR}/${VARFILE}" ;;
    "~"/*) VARFILE="${HOME}/${VARFILE#\~/}" ;;
  esac
  if [ -n "$VARFILE" ] && [ -d "$(dirname "$VARFILE")" ] && [ ! -s "${VARFILE}.unit" ]; then
    echo "{}" > "${VARFILE}.unit"; echo "  created $(basename "$VARFILE").unit (AFC's lane state file)"
    record "created ${VARFILE}.unit"
  fi
  # AFC's installer names the unit file after the unit (AFC_Turtle_1.cfg, or AFC_<your name>.cfg),
  # so find unit files by their content: a section for a unit type HatChanger replaces.
  UNIT_RX='^\[AFC_(BoxTurtle|NightOwl|HTLF|Claymore|QuattroBox|OpenAMS|ViViD|Vivid|EMU) '
  for f in "${CFG_DIR}"/AFC/*.cfg; do
    [ -f "$f" ] || continue
    if [ "$(basename "$f")" != AFC_Hardware.cfg ] && ! grep -qE "$UNIT_RX" "$f"; then continue; fi
    if ask "Disable AFC's $(basename "$f") (hardware you don't have)?" y; then
      mv "$f" "$f.disabled"; echo "  $(basename "$f") -> $(basename "$f").disabled"
      recorded "disabled $f" || record "disabled $f"
    fi
  done
  if ! grep -qE '^\[include AFC/' "${CFG_DIR}/printer.cfg"; then
    warn "  printer.cfg has no [include AFC/*.cfg]: AFC's installer normally adds it"
  fi
else
  [ -L "${EXTRAS}/AFC_HatChanger.py" ] && rm "${EXTRAS}/AFC_HatChanger.py" && echo "  AFC unit unlinked"
fi

# ------------------------------------------------------------------------- includes ---------
$TOOL printer-block --printer "${CFG_DIR}/printer.cfg" --mode "$MODE" --hat-id "$HAT_ID"
if [ "$MODE" = standalone ] && [ -f "${CFG_DIR}/AFC/AFC.cfg" ] && grep -qE '^\[include AFC/' "${CFG_DIR}/printer.cfg"; then
  warn "  AFC is included too: AFC and hatchanger_tools.cfg both define T0/T1. Use --afc, or remove AFC's include"
fi
GH_REPO="$(python3 -c 'import json,sys; i=json.load(open(sys.argv[1])); print(i["project_owner"] + "/" + i["project_name"])' "${REPO}/release_info.json")"
if git -C "$REPO" rev-parse --show-toplevel >/dev/null 2>&1; then
  warn "  ${REPO} is inside a git repository: Moonraker's zip updates refuse that path. Move it out."
fi
$TOOL moonraker --conf "$MOONRAKER_CONF" --repo "$REPO" --github-repo "$GH_REPO" --channel "$CHANNEL"

say "Done."
if ! grep -rqE '^\[respond\]' "${CFG_DIR}"/*.cfg 2>/dev/null; then
  warn "  no [respond] section found: HatChanger's messages need it (add [respond] to printer.cfg)"
fi
echo "  Set your values (sensor pin, dock, cutter) in ${DEST}/hatchanger_user.cfg."
[ "$MODE" = afc ] && echo "  Lanes: ${DEST}/hatchanger_afc.cfg. Setup notes: ${REPO}/docs/AFC.md"
echo "  Updates: Mainsail/Fluidd update manager ('hatchanger', $( [ "$CHANNEL" = beta ] && echo 'releases and pre-releases' || echo releases ))."
restart moonraker
restart klipper
if [[ "$RESTARTED" == *klipper* ]]; then
  say "Checking the result (./install.sh --check runs this again any time)"
  EXP=""; [ "$MODE" = afc ] && EXP="--expect-afc"
  $TOOL check --moonraker "$MOONRAKER_URL" --wait 60 $EXP || true
else
  echo "  After restarting Klipper, run ./install.sh --check to see if everything started cleanly."
fi
