; HatChanger + AFC: Eject (Mainsail shows the button on every lane). Run on its own: the refusal
; is an error, and any error ends a Klipper batch run.
G28
PREP
SET_MATERIAL LANE=hat1 MATERIAL=PETG
LANE_UNLOAD LANE=hat1
EXPECT_LANE LANE=hat1 MATERIAL=PETG
HAT_SIM_NOTE MSG="HATCHANGER AFC TEST DONE"
