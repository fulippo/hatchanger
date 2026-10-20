; HatChanger: HAT_DOCK resuming a dock that stopped with the hat set down in its rack (e.g. the
; pre-park seek failed there). Errors end a batch run, so the stop is staged by hand: the cut is
; done, the head is set down in rack 0, _HAT_STATE.docking = 0.
G28
M104 S220
PREP
SET_GCODE_VARIABLE MACRO=_HAT_STATE VARIABLE=lane VALUE=0
SET_GCODE_VARIABLE MACRO=_HAT_STATE VARIABLE=loaded VALUE=0
AFC_HATCHANGER_SYNC UNIT=HatChanger_1 QUIET=1
_HAT_GO_DOCK_FRONT LANE=0
_HAT_DOCK_IN LANE=0
EXPECT HAT=0 LOADED=0 AFC=None POOPS=0
; run again: no cut, no travel: pre-park in the rack, then drop away
HAT_DOCK
EXPECT HAT=-1 LOADED=0 AFC=None POOPS=0
HAT_SIM_STATUS
HAT_SIM_NOTE MSG="HATCHANGER AFC TEST DONE"
