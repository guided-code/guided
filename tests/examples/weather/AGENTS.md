# AGENTS.md

Weather is a CLI tool that fetches and displays current weather conditions and forecasts using the [OpenWeatherMap API](https://openweathermap.org/api).

## Running the Tool

Requires Python 3.11+ and `uv`.

```bash
uv run weather current "New York"     # Current conditions for a city
uv run weather forecast "London"      # 5-day forecast
uv run weather current --lat 37.77 --lon -122.41  # Lookup by coordinates
```

Set your API key before running:

```bash
export OPENWEATHER_API_KEY=your_key_here
```

## Architecture

The tool is a Python CLI built with **Typer** and **Rich**. The entry point is `weather.cli:run`.

### Module layout (`src/weather/`)

- `cli.py` — Root Typer app; registers `current` and `forecast` subcommands
- `client.py` — HTTP client wrapping the OpenWeatherMap REST API; handles auth, retries, and response parsing
- `models.py` — Pydantic models for API responses (`CurrentWeather`, `Forecast`, `WeatherCondition`)
- `format.py` — Rich-based display formatters; renders weather data as tables and panels in the terminal
- `config.py` — Loads configuration from environment variables and `~/.weather/config.yaml`

### API Integration

The tool uses the OpenWeatherMap **Current Weather** and **5 Day / 3 Hour Forecast** endpoints.

- Base URL: `https://api.openweathermap.org/data/2.5/`
- Authentication: `appid` query parameter
- Units: configurable (`metric`, `imperial`, `standard`); defaults to `metric`

City lookups resolve via the `/weather?q={city}` endpoint. Coordinate lookups use `lat` and `lon` query parameters.

### Config file

Config is stored at `~/.weather/config.yaml`:

```yaml
api_key: your_key_here   # overridden by OPENWEATHER_API_KEY env var
units: metric            # metric | imperial | standard
default_city: ""         # optional fallback city
```

## Commands

| Command | Description |
|---|---|
| `weather current <city>` | Current temperature, conditions, humidity, and wind |
| `weather forecast <city>` | 5-day forecast in 3-hour intervals |
| `weather configure` | Set API key and default preferences |

Both commands accept `--lat` / `--lon` flags to look up by coordinates instead of city name.

## Tests

```bash
uv run pytest tests/
```

Tests mock the OpenWeatherMap HTTP responses — no live API key is required to run the test suite.

## Workspace

This project was initialized with `guide workspace init`. Configuration is stored in `.workspace/config.yaml`.
