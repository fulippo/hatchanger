; HatChanger + AFC integration test (Klipper batch mode, run_afc_test.py)
; Start: hat 0 on the head and loaded (save_variables preset by the runner).
G28
M104 S220
; PREP reads the HatChanger state from save_variables (hat 0 loaded): AFC must say hat0
PREP
; what _HAT_RESTORE_STATE does 1 s after start (batch mode runs the gcode before any timer)
SET_GCODE_VARIABLE MACRO=_HAT_STATE VARIABLE=lane VALUE=0
SET_GCODE_VARIABLE MACRO=_HAT_STATE VARIABLE=loaded VALUE=1
AFC_HATCHANGER_SYNC UNIT=HatChanger_1 QUIET=1
EXPECT HAT=0 LOADED=1 AFC=hat0 POOPS=0

; slicer tool change: AFC unloads hat0 (HAT_DOCK), loads hat1 (HAT_PICKUP STUB=0), poops
T1
EXPECT HAT=1 LOADED=1 AFC=hat1 POOPS=1
; same tool again: nothing moves, no purge
T1
EXPECT HAT=1 LOADED=1 AFC=hat1 POOPS=1
T0
EXPECT HAT=0 LOADED=1 AFC=hat0 POOPS=2

; HatChanger commands by hand: AFC follows through the state hook
HAT_DOCK
EXPECT HAT=-1 LOADED=0 AFC=None
HAT_START LANE=1
EXPECT HAT=1 LOADED=1 AFC=hat1 POOPS=2
; ...so the slicer's first T1 after START_PRINT does nothing
T1
EXPECT HAT=1 LOADED=1 AFC=hat1 POOPS=2
HAT_SET_STATE LANE=1 LOADED=0
EXPECT HAT=1 LOADED=0 AFC=None
; hat on the head but not loaded: AFC's load path loads it without a pickup
T1
EXPECT HAT=1 LOADED=1 AFC=hat1 POOPS=3

; lane commands registered even with hatchanger_afc.cfg included before AFC's files
SET_MATERIAL LANE=hat0 MATERIAL=PETG
EXPECT_LANE LANE=hat0 MATERIAL=PETG

; AFC_HATCHANGER_SYNC by hand
AFC_HATCHANGER_SYNC UNIT=HatChanger_1

; failed grab: hat0's filament out of reach. AFC must report it, not crash, and stay in step
HAT_SIM_SET_TIP LANE=0 TIP=-100
; (HAT_PICKUP left the head at the loaded travel height: back down to "printing" height, or
; AFC's z_hop would lift it above what the dock allows)
G1 Z10 F1200
T0
HAT_SIM_STATUS
EXPECT HAT=0 LOADED=0 AFC=None POOPS=3
HAT_SIM_NOTE MSG="HATCHANGER AFC TEST DONE"
