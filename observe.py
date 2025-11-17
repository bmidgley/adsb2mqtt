#!/usr/bin/env python3
"""
MQTT Message Subscriber
Subscribes to configured MQTT topic and displays messages.
"""

import os
import sys
import json
import signal
import logging
from typing import Optional

from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Load environment variables from .env file
load_dotenv()


class MQTTSubscriber:
    """MQTT subscriber that displays messages from configured topic."""
    
    def __init__(self):
        """Initialize the MQTT subscriber with configuration."""
        self.running = False
        self.setup_logging()
        
        # Configuration from environment variables or defaults
        self.mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
        self.mqtt_port = int(os.getenv('MQTT_PORT', '8883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME', '')
        self.mqtt_password = os.getenv('MQTT_PASSWORD', '')
        self.mqtt_topic = os.getenv('MQTT_TOPIC', 'adsb/aircraft')
        self.mqtt_client_id = os.getenv('MQTT_CLIENT_ID', 'mqtt_subscriber')
        
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
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            self.logger.info("Connected to MQTT broker successfully")
            # Subscribe to base topic with wildcard to receive all aircraft messages
            subscribe_topic = f"{self.mqtt_topic}/+"
            self.logger.info(f"Subscribing to topic: {subscribe_topic}")
            client.subscribe(subscribe_topic, qos=1)
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
            self.running = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection, return code: {rc}")
        else:
            self.logger.info("Disconnected from MQTT broker")
    
    def on_message(self, client, userdata, msg):
        """Callback for received MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Try to parse as JSON for pretty printing
            try:
                data = json.loads(payload)
                print(f"\n{'='*80}")
                print(f"Topic: {topic}")
                print(f"Timestamp: {self.get_timestamp()}")
                print(f"{'='*80}")
                print(json.dumps(data, indent=2))
                print(f"{'='*80}\n")
            except json.JSONDecodeError:
                # If not JSON, print as plain text
                print(f"\n{'='*80}")
                print(f"Topic: {topic}")
                print(f"Timestamp: {self.get_timestamp()}")
                print(f"{'='*80}")
                print(payload)
                print(f"{'='*80}\n")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            print(f"Error processing message: {e}")
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for subscription confirmation."""
        subscribe_topic = f"{self.mqtt_topic}/+"
        self.logger.info(f"Subscribed to topic: {subscribe_topic} (QoS: {granted_qos[0]})")
        print(f"\nListening for messages on topic: {subscribe_topic}")
        print("Press Ctrl+C to exit\n")
    
    def get_timestamp(self):
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def setup_mqtt(self):
        """Setup and connect to MQTT broker with TLS."""
        try:
            self.mqtt_client = mqtt.Client(
                client_id=self.mqtt_client_id,
                protocol=mqtt.MQTTv311
            )
            
            # Set callbacks
            self.mqtt_client.on_connect = self.on_connect
            self.mqtt_client.on_disconnect = self.on_disconnect
            self.mqtt_client.on_message = self.on_message
            self.mqtt_client.on_subscribe = self.on_subscribe
            
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
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup MQTT connection: {e}")
            return False
    
    def run(self):
        """Main loop to listen for messages."""
        self.logger.info("Starting MQTT subscriber...")
        self.logger.info(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        self.logger.info(f"MQTT Topic: {self.mqtt_topic}/+")
        
        # Setup MQTT connection
        if not self.setup_mqtt():
            self.logger.error("Failed to setup MQTT connection, exiting")
            return 1
        
        self.running = True
        
        try:
            # Keep running until interrupted
            while self.running:
                import time
                time.sleep(0.1)
                
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
    subscriber = MQTTSubscriber()
    sys.exit(subscriber.run())


if __name__ == '__main__':
    main()

