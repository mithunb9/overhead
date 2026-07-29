# AGENTS.md

## Project

flights-api is a selfhostable FastAPI service that aggregates commercial flight
data (ADS-B position/callsign, enriched with registration, airline, and
route) for use across other projects, primarily FlightMatrix. See README.md
for the milestone roadmap and data source table — keep that file, and this one, in sync when
scope changes.

Status: pre-implementation. No Python package exists yet; the sections below
are the conventions to follow once code lands.

## Stack

- Python, FastAPI
- Package/env management: `uv` (`uv add`, `uv run`, `uv sync`) — never pip or poetry
- Pydantic models for all request/response schemas and enrichment data
- Deployment: Docker Compose and Render config (see README)

## Conventions

- Type hints everywhere, modern syntax (`list[str]`, `str | None`, not `List`/`Optional`)
- async/await for I/O (ADS-B aggregator calls, route lookups), not blocking requests calls
- External data sources (adsb.lol, adsbdb.com) are community-sourced —
  handle missing/partial data (e.g. "route unknown") explicitly rather than assuming fields exist
- Caching is config-driven with defaults per README section 4 (24h TTL for
  origin/destination enrichment, 60s for positions) — don't hardcode TTLs inline
- Keep enrichment lookups (hex→reg, ICAO-prefix→airline) as static bundled data, not live calls

## Testing

No test suite yet. Once one exists, run it with `uv run pytest` and document
any project-specific test commands here.
