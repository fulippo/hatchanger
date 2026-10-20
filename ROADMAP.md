# Roadmap

Known limitations and planned work. Contributions on any of these are welcome.

## Open

- **Error recovery.** Errors stop the sequence and wait for you; there's no retry logic.
- **Hat tilt under bowden pull.** The hold-down (the pogo connector's magnets) is at the back, so
  a bowden pulling backwards tips the hat about its back edge, where it has little lever.
  Options, not yet built:
  - **3 magnets + 1 pin:** a third 6×3 magnet in place of the +X dowel (fits with ~0.6–0.75 mm
    walls); the −X dowel stays, in a slot pointing at the cone.
  - **Longer hat:** extend the hat's back edge to the end of the pad (+2.6 mm) for ~65 % more
    lever.
  - **Forward extension:** grow the pad and hat 4–5 mm forward for a full front magnet pair
    (needs the rack moved).
  - **Front magnets:** move the magnets back to the front of the pad.
- **Runout and endless spool under AFC.** The lanes have no sensors.

## Constraints

- Lanes need about 40 mm between them, so the head can pass the neighbouring stingers.
- With a hat on the head, the clearance below the racks limits the maximum print height (about
  175 mm on the prototype).
