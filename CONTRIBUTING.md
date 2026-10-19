# Contributing

Thanks for your interest in HatChanger! Bug reports, test results from other printers, and pull
requests are all welcome.

## Reporting issues

Open an [issue](https://github.com/fulippo/hatchanger/issues) and include:

- your printer, toolhead board and whether you run standalone or under AFC;
- the output of `HAT_STATUS` and `./hatchanger/install.sh --check`;
- the relevant part of `klippy.log`.

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Keep each pull request focused on one change.
3. Run the tests (see below) and describe what you tested on a printer.
4. Update the documentation in `docs/` when behaviour or configuration changes.
5. Title the pull request as a [Conventional Commit](https://www.conventionalcommits.org/)
   (`feat:`, `fix:`, `docs:`, …).

### CAD changes

Each component has its own folder under `cad/` (`hatchanger/`, `ptfe_rail_clamp/`, `tophat/`)
with the CadQuery script in `source/` and the exports in `stl/` and `step/` (see
[docs/CAD.md](docs/CAD.md)). When you change a part, commit the updated script together with
the regenerated STL and STEP files.

### Klipper macros and installer

Machine-specific values belong in `hatchanger_user.cfg`, not in the repository's config files.
Keep defaults in `klipper/config/` generic and mark values users must measure with `MEASURE` or
`CALIBRATE`.

## Tests

```sh
# installer and cfgtool (fake printer homes, fake Moonraker)
python tests/test_install.py

# macros + AFC unit in Klipper batch mode (needs Klipper and AFC checkouts)
python klipper/tests/run_afc_test.py --klipper ~/klipper
```

The setup for the Klipper test is at the top of
[`run_afc_test.py`](klipper/tests/run_afc_test.py). Both run in CI on every push and pull
request.

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you are
expected to uphold it.

## License

By contributing, you agree that your contributions will be licensed under the
[GPL-3.0](LICENSE).
