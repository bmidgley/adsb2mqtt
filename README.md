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
| `MQTT_BROKER` | `evalink.archresearch.net` | MQTT broker hostname |
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

The application publishes JSON messages to the configured MQTT topic. The message format matches the ADSB Exchange API response:

```json
{
  "now": 1234567890.123,
  "messages": 12345,
  "aircraft": [
    {
      "hex": "abc123",
      "flight": "ABC123",
      "lat": 37.7749,
      "lon": -122.4194,
      "altitude": 35000,
      ...
    }
  ]
}
```

## Requirements

- Python 3.7+
- Network access to ADSB Exchange endpoint
- Network access to MQTT broker
- Valid MQTT credentials (if required by broker)

## License

MIT

