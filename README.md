# overhead

A selfhostable API built in FastAPI and Python to display overhead commercial flight data for use across my projects. Primarily built for [FlightMatrix](https://www.github.com/mithunb9/FlightMatrix).

Use Docker Compose or the built in Render config for easy deployment.

## 2. Development Milestones

v0.1 - `POST /overhead` with lat, long coords returns the nearest commercial flight flying overhead. ✅

v0.1.5 - repository CI/CD and github container repository regristation. ✅

v0.2 - `POST /overhead` with amount returns a list of the nearest commercial flights up to the amount, clamped by configurable values. ✅

v0.3 - configurable route enrichment source, free community data or a paid provider (e.g. AeroAPI), user's choice via config.

v0.4 - airline logos and operating/marketing carrier reconciliation (e.g. ENY flights operate as American Eagle for American) config flag.

v0.5 - Additional location discriminators like city, zip code and airport.

## 3. Data Sources

ADS-B broadcasts give position, altitude, callsign, and ICAO hex. The base data provided by them will be enriched.

| Field                             | Source                                                                                                              |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Position, altitude, callsign, hex | ADS-B aggregator (primary (planned): **adsb.lol** `/v2` point query)                                                |
| Registration + aircraft type      | adsb.lol response `r` / `t` fields (hex→reg DB)                                                                     |
| Airline name                      | Static ICAO-prefix lookup table (AAL→American), bundled JSON                                                        |
| Flight number                     | Derived from callsign (AAL2847 → AA 2847)                                                                           |
| Origin/destination                | **adsbdb.com** free API (callsign → route) - less accurate or **AeroAPI** paid API (callsign → route), configurable |

## 4. Caching

Plan to have configurable caching values with defaults set to:

- 24hr TTL on origin/destination enrichment.
- 60s for Aircraft Positions.
