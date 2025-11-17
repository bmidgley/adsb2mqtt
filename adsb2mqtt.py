#!/usr/bin/env python3
"""
ADSB to MQTT Bridge
Fetches aircraft data from ADSB Exchange and publishes to MQTT broker.
"""

import os
import sys
import json
import time
import logging
import signal
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from dotenv import load_dotenv
import requests
import paho.mqtt.client as mqtt

# Load environment variables from .env file
load_dotenv()


class ADSB2MQTT:
    """Bridge between ADSB Exchange API and MQTT broker."""
    
    def __init__(self):
        """Initialize the ADSB2MQTT bridge with configuration."""
        self.running = False
        self.setup_logging()
        
        # Configuration from environment variables or defaults
        self.adsb_url = os.getenv(
            'ADSB_URL',
            'http://adsbexchange.local/tar1090/data/aircraft.json'
        )
        self.mqtt_broker = os.getenv('MQTT_BROKER', 'evalink.archresearch.net')
        self.mqtt_port = int(os.getenv('MQTT_PORT', '8883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME', '')
        self.mqtt_password = os.getenv('MQTT_PASSWORD', '')
        self.mqtt_topic = os.getenv('MQTT_TOPIC', 'adsb/aircraft')
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '5'))
        self.mqtt_client_id = os.getenv('MQTT_CLIENT_ID', 'adsb2mqtt')
        
        # MQTT client
        self.mqtt_client = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def setup_logging(self):
        """Configure logging."""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def setup_mqtt(self):
        """Setup and connect to MQTT broker with TLS."""
        try:
            self.mqtt_client = mqtt.Client(
                client_id=self.mqtt_client_id,
                protocol=mqtt.MQTTv311
            )
            
            # Set callbacks
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_publish = self.on_mqtt_publish
            
            # Set credentials if provided
            if self.mqtt_username and self.mqtt_password:
                self.mqtt_client.username_pw_set(
                    self.mqtt_username,
                    self.mqtt_password
                )
            
            # Configure TLS
            self.mqtt_client.tls_set()
            
            # Connect to broker
            self.logger.info(
                f"Connecting to MQTT broker {self.mqtt_broker}:{self.mqtt_port}..."
            )
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            timeout = 10
            elapsed = 0
            while not self.mqtt_client.is_connected() and elapsed < timeout:
                time.sleep(0.1)
                elapsed += 0.1
            
            if not self.mqtt_client.is_connected():
                raise Exception("Failed to connect to MQTT broker within timeout")
            
            self.logger.info("Successfully connected to MQTT broker")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup MQTT connection: {e}")
            return False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.logger.info("MQTT broker connected successfully")
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection, return code: {rc}")
        else:
            self.logger.info("MQTT broker disconnected")
    
    def on_mqtt_publish(self, client, userdata, mid):
        """Callback for MQTT publish."""
        self.logger.debug(f"Message published with mid: {mid}")
    
    def fetch_adsb_data(self) -> Optional[Dict[str, Any]]:
        """Fetch aircraft data from ADSB Exchange API."""
        try:
            self.logger.debug(f"Fetching ADSB data from {self.adsb_url}")
            response = requests.get(self.adsb_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Validate data structure
            if 'aircraft' not in data:
                self.logger.warning("Response does not contain 'aircraft' key")
                return None
            
            self.logger.debug(f"Fetched {len(data.get('aircraft', []))} aircraft")
            return data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching ADSB data: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching ADSB data: {e}")
            return None
    
    def publish_to_mqtt(self, data: Dict[str, Any]) -> bool:
        """Publish aircraft data to MQTT broker."""
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            self.logger.error("MQTT client not connected")
            return False
        
        try:
            payload = json.dumps(data, separators=(',', ':'))
            result = self.mqtt_client.publish(
                self.mqtt_topic,
                payload,
                qos=1,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published to {self.mqtt_topic}")
                return True
            else:
                self.logger.error(f"Failed to publish to MQTT, return code: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error publishing to MQTT: {e}")
            return False
    
    def run(self):
        """Main loop to fetch and publish ADSB data."""
        self.logger.info("Starting ADSB2MQTT bridge...")
        self.logger.info(f"ADSB URL: {self.adsb_url}")
        self.logger.info(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        self.logger.info(f"MQTT Topic: {self.mqtt_topic}")
        self.logger.info(f"Poll Interval: {self.poll_interval} seconds")
        
        # Setup MQTT connection
        if not self.setup_mqtt():
            self.logger.error("Failed to setup MQTT connection, exiting")
            return 1
        
        self.running = True
        
        try:
            while self.running:
                # Fetch ADSB data
                data = self.fetch_adsb_data()
                
                if data:
                    # Publish to MQTT
                    self.publish_to_mqtt(data)
                else:
                    self.logger.warning("No data to publish")
                
                # Wait before next poll
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup()
        
        return 0
    
    def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up...")
        self.running = False
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            if self.mqtt_client.is_connected():
                self.mqtt_client.disconnect()
        
        self.logger.info("Cleanup complete")


def main():
    """Main entry point."""
    bridge = ADSB2MQTT()
    sys.exit(bridge.run())


if __name__ == '__main__':
    main()

