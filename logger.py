from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv
from datetime import datetime
import os
import random
import logging


# The broker, username and password are stored in a .env file which needs to be made if not already included
load_dotenv()

# This code uses the Paho MQTT Python Client library
# References: https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
#             https://github.com/eclipse/paho.mqtt.python/blob/master/docs/migrations.rst


# Connection info
broker = os.getenv('BROKER')
port = 1883
baseTopic = "<104547242>"
topics = [
    (f"{baseTopic}/servers/avg_cpu_util", 0),
    (f"{baseTopic}/servers/active", 0),
    (f"{baseTopic}/servers/warnings", 0),
    (f"{baseTopic}/commands", 0),
    ("public/#", 0)
]
clientId = f'logger-{random.randint(0, 1000)}'                  # Assign a random ID to the client device
username = os.getenv('MQTT_USERNAME')
password = os.getenv('MQTT_PASSWORD')

# Define the path to the logs directory
scriptDir = os.path.dirname(os.path.abspath(__file__))
logsDir = os.path.join(scriptDir, "logs")

# Initialise logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
loggingActive = False


def startLogging() -> None:
    """Create and setup logging handler"""
    global loggingActive
    if loggingActive: return            # This is so we don't start a new log if one is already started

    loggingActive = True
    os.makedirs(logsDir, exist_ok=True) # Ensures log directory exists

    # Make unique name for the log file using current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logFile = os.path.join(logsDir, f"server_log_{timestamp}.log")

    # Ensure there are no existing handlers
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    try:
        # Setup handler to insert server metrics into log file
        handler = logging.FileHandler(logFile)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(handler)
    
        logger.info("Start log:")
    except Exception as e:
        loggingActive = False
        print(f"Failed to start logging: {e}")


def stopLogging() -> None:
    """Stops logging and cleans up handlers."""
    global loggingActive

    if not loggingActive: return    # no need to stop logging if already stopped
    
    loggingActive = False
    logger.info("End log.")

    # Remove all handlers. There should only be one at a time, but this is just in case
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def connect_mqtt() -> mqtt_client:
    """Connects to the MQTT broker and returns the client object."""
    def on_connect(client, userdata, flags, rc, properties):
        """Callback when connected to the broker."""
        if rc == 0: 
            print("Connected to MQTT Broker!")
            subscribe(client)
        else: 
            print(f"Failed to connect, return code {rc}")
    
    client = mqtt_client.Client(client_id=clientId, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.on_connect = on_connect

    try:
        client.connect(broker, port)
        print(f"Attempting to connect to {broker} on port {port}")
    except Exception as e:
        print(f"Error occurred while connecting to the MQTT broker: {e}")
        return None

    return client


def disconnect_mqtt(client: mqtt_client) -> None:
    """Disconnects client from the MQTT broker."""
    def on_disconnect(client, userdata, flags, rc, properties):
        """Callback when disconnected from the broker."""
        if rc == 0:
            print("Successfully disconnected from MQTT Broker")
        else:
            print(f"Disconnected with an error. Reason code: {rc}")

    client.on_disconnect = on_disconnect
    client.disconnect()


def subscribe(client: mqtt_client):
    """Subscribe client to topics."""
    def on_message(client, userdata, msg):
        """Print received messages to terminal and process commands"""
        global loggingActive

        print("\n====================[SUB]====================")
        print(msg.topic)
        print(f"QoS: {msg.qos}")
        print(f"Retained?: {msg.retain}")
        print(f"\nMessage:")
        print(msg.payload.decode())
        print("=============================================")

        if msg.topic == f"{baseTopic}/commands":
            # Remove all whitespace from command
            command = msg.payload.decode().strip().lower()
            
            # Execute valid commands
            commands = {
                "!startlog": startLogging,
                "!stoplog": stopLogging
            }
            if command in commands: commands[command]()
        
        # Log message if from valid topic
        logTopics = {
            f"{baseTopic}/servers/avg_cpu_util",
            f"{baseTopic}/servers/active",
            f"{baseTopic}/warnings",
            f"{baseTopic}/commands"
        }
        if loggingActive and msg.topic in logTopics:
            logger.info("====================[SUB]====================")
            logger.info(msg.topic)
            logger.info(f"Retained?: {msg.retain}")
            logger.info(f"QoS: {msg.qos}")
            logger.info("")
            logger.info(f"Message:")
            logger.info(msg.payload.decode())
            logger.info("=============================================")


    client.subscribe(topics)
    print(f"Subscribed to topics: {topics}\n")
    client.on_message = on_message


def main() -> None:
    """Main program logic."""
    print("Starting the logger...")
    
    client = connect_mqtt()
    if client is None:
        print("Failed to connect to the MQTT broker. Exiting...")
        stopLogging()
        return
    
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected, disconnecting from MQTT broker...")
    except Exception as e:
        print(f"Error during main operation: {e}")
    finally:
        stopLogging()
        disconnect_mqtt(client)
        print("Client disconnected, exiting program.")


if __name__ == "__main__":
    main()