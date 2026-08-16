# Local ephh chart adapter

`scripts/ephh_local_adapter.py` is the project-facing wrapper for the desktop
ephh Swiss-Ephemeris backend. It imports `backend.py` directly and does not
start a web server.

## Project default and supported modes

The project default is tropical zodiac plus Placidus (`--house-system placidus`).
This is the only mode used for ordinary readings and knowledge extraction.
Whole-sign output is retained as an explicit research comparison and must be
requested with `--house-system whole_sign` or `--house-system both`.

- `placidus`: uses the source backend's Swiss Ephemeris Placidus cusps.
- `whole_sign`: uses the same source longitudes and axes, then assigns house 1
  to the Ascendant sign and advances one sign per house. This is a transparent
  house-system transformation; the source backend itself currently exposes
  only Placidus, Equal, and Koch.
- `both`: emits both results in one JSON object for comparison.

## Provenance and safety

The adapter records the backend path and SHA-256 hash in every chart package.
It intentionally does not copy the desktop app's unrelated client storage or
its embedded address-service credentials. A future vendored core should be
introduced only after the hash and numeric outputs are regression-tested.

The location in the current test run is the Nominatim administrative centroid
for Zhouning County (27.0872517 N, 119.2950426 E), not an exact birth address.
House cusps and angles should therefore be treated as sensitive to a possible
small location/time correction.

The output keeps the MC point separate from the house-cusp model. In Placidus,
MC/IC are the 10th/4th cusps. In whole-sign houses, the MC remains the
calculated angle and can fall in the 9th, 10th, or 11th sign-house; forcing it
to be the 10th cusp would be a mixed house system and must be labelled as such.

## Example

```powershell
python scripts/ephh_local_adapter.py --year 1997 --month 8 --day 3 --hour 5 --minute 5 --second 0 --lat 27.0872517 --lon 119.2950426 --tz 8 --place Zhouning-County-Fujian --house-system placidus --output clients/19970803-0505-ZhouningFujian/analysis/ROUND129-19970803-CHART-FACTS.json
```
