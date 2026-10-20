# Roadmap

Known limitations and planned work. Contributions on any of these are welcome.

## Open

- **Error recovery.** Errors stop the sequence and wait for you; there's no retry logic.
- **Hat lifting under bowden drag.** The front magnets (v0.34) hold against tipping with
  ~15 mm of lever, and `HAT_DOCK` retracts only with the hat in its rack. A hard pull (a jam,
  a very steep bowden while printing) can still beat any magnets. If hats still lift: a spring
  latch on the head that grips the hat and is opened by a ramp on the rack as the head slides in.
- **Runout and endless spool under AFC.** The lanes have no sensors.

## Constraints

- Lanes need about 40 mm between them, so the head can pass the neighbouring stingers.
- With a hat on the head, the clearance below the racks limits the maximum print height (about
  175 mm on the prototype).
