# Roadmap

Known limitations and planned work. Contributions on any of these are welcome.

## Open

- **Hat ID in the standalone macros.** The reader and `HAT_ID` / `HAT_ID_CHECK` work, but the
  change macros don't use them yet: no automatic check after a pickup or drop-off, no startup
  sync from the hat on the head, no print watch. (The AFC unit already checks after each change.)
- **Error recovery.** Errors stop the sequence and wait for you; there's no retry logic.
- **Hat tilt under bowden pull.** With the magnets at the back (for the hat-ID wiring), a bowden
  pulling backwards tips the hat about its back edge, where the magnets have little lever.
  Options, not yet built:
  - **3 magnets + 1 pin:** a third 6×3 magnet in place of the +X dowel (fits with ~0.6–0.75 mm
    walls); the −X dowel stays, in a slot pointing at the cone.
  - **Longer hat:** extend the hat's back edge to the end of the pad (+2.6 mm) for ~65 % more
    lever.
  - **Forward extension:** grow the pad and hat 4–5 mm forward for a full front magnet pair
    (needs the rack moved).
  - **Pogo-pin ID contacts:** move the magnets back to the front.
- **Runout and endless spool under AFC.** The lanes have no sensors.

## Constraints

- Lanes need about 40 mm between them, so the head can pass the neighbouring stingers.
- With a hat on the head, the clearance below the racks limits the maximum print height (about
  175 mm on the prototype).
