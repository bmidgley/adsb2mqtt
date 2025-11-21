# ADSB2MQTT

A Python bridge that fetches aircraft data from ADSB Exchange (tar1090) and publishes it to an MQTT broker over TLS.

## Features

- Fetches aircraft data from configurable ADSB Exchange endpoint
- Publishes to MQTT broker with TLS encryption
- Configurable via environment variables
- Graceful shutdown handling
- Comprehensive logging

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Configuration is done via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ADSB_URL` | `http://adsbexchange.local/tar1090/data/aircraft.json` | URL to fetch ADSB data from |
| `MQTT_BROKER` | `localhost` | MQTT broker hostname |
| `MQTT_PORT` | `8883` | MQTT broker port (TLS) |
| `MQTT_USERNAME` | (empty) | MQTT username |
| `MQTT_PASSWORD` | (empty) | MQTT password |
| `MQTT_TOPIC` | `adsb/aircraft` | MQTT topic to publish to |
| `MQTT_CLIENT_ID` | `adsb2mqtt` | MQTT client ID |
| `POLL_INTERVAL` | `5` | Polling interval in seconds |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Usage

### Basic Usage

```bash
python adsb2mqtt.py
```

### With Custom Configuration

```bash
export MQTT_USERNAME="your_username"
export MQTT_PASSWORD="your_password"
export ADSB_URL="http://your-adsb-server/tar1090/data/aircraft.json"
export POLL_INTERVAL=10

python adsb2mqtt.py
```

### Using a .env File

Create a `.env` file in the project directory:

```bash
ADSB_URL=http://adsbexchange.local/tar1090/data/aircraft.json
MQTT_BROKER=localhost
MQTT_PORT=8883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
MQTT_TOPIC=adsb/aircraft
POLL_INTERVAL=5
LOG_LEVEL=INFO
```

The application will automatically load environment variables from the `.env` file if present.

## MQTT Message Format

The application publishes individual aircraft data as separate JSON messages. Each aircraft is published to its own topic based on its identifier.

### Topic Format

Messages are published to topics in the format: `{MQTT_TOPIC}/{aircraft_id}`

- `{MQTT_TOPIC}` is the base topic configured via the `MQTT_TOPIC` environment variable (default: `adsb/aircraft`)
- `{aircraft_id}` is the aircraft's hex code (ICAO identifier) or flight number

**Examples:**
- `adsb/aircraft/abc123` - Aircraft with hex code "abc123"
- `adsb/aircraft/ABC123` - Aircraft with flight number "ABC123"

To subscribe to all aircraft messages, use a wildcard: `adsb/aircraft/+`

### Message Format

Each message contains a single aircraft object as JSON:

```json
{
  "hex": "abc123",
  "flight": "ABC123",
  "lat": 37.7749,
  "lon": -122.4194,
  "altitude": 35000,
  "track": 180,
  "speed": 450,
  "vert_rate": 0,
  "squawk": "1234",
  "rssi": -45.2,
  "messages": 1234,
  "seen": 5.2,
  "seen_pos": 2.1
}
```

**Note:** Messages are only published when the aircraft data has changed (using checksum comparison), reducing unnecessary MQTT traffic.

## Requirements

- Python 3.7+
- Network access to ADSB Exchange endpoint
- Network access to MQTT broker
- Valid MQTT credentials (if required by broker)

## License

MIT

