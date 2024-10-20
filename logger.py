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
topics = [("<104547242>/servers/avg_cpu_util", 0), ("<104547242>/servers/active", 0), ("<104547242>/commands", 0), ("public/#", 0)]              # <104547242>/temperature can be replaced with any private topic. The 0 indicates the QoS
client_id = f'logger-{random.randint(0, 1000)}'                  # Assign a random ID to the client device
username = os.getenv('MQTT_USERNAME')
password = os.getenv('MQTT_PASSWORD')

# Create a logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

# Create unique log file using timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
logFile = f"logs/logger_client_{timestamp}.log"

# Initialise logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Flag for controlling logging
loggingActive = False


def startLogging():
    global loggingActive
    
    # This is so we don't start a new log if one is already started
    if loggingActive: return
    loggingActive = True

    # Make unique name for log file using a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logFile = f"logs/mqtt_client_{timestamp}.log"

    # Setup handler for to insert server metrics into log file
    handler = logging.FileHandler(logFile)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(handler)
    logger.info("Start log:")


def stopLogging():
    global loggingActive
    
    # So we don't run into errors if there is no actual logging active
    if not loggingActive: return
    loggingActive = False
    logger.info("End log.")

    # Remove all handlers. There should only be one at a time, but this is just in case
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        # Response code is 0 for a successful connection
        # This is printed on every connection
        print("Connected to MQTT Broker!") if rc == 0 else print("Failed to connect, return code {rc}\n")
    
    # Connect client object to MQTT broker
    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def disconnect_mqtt(client: mqtt_client):
    def on_disconnect(client, userdata, flags, rc, properties):
        # Print disconnection status
        # This is printed on every disconnection
        print("Successfully disconnected from MQTT Broker") if rc == 0 else print(f"Disconnected with an error. Reason code: {rc}\n")

    client.on_disconnect = on_disconnect
    client.disconnect()


def subscribe(client: mqtt_client):
    # Print message and its details in specified format
    # I tried to create something similar to the MQTTX GUI client messages
    def on_message(client, userdata, msg):
        global loggingActive

        # Print received messages to terminal
        print("\n====================[SUB]====================")
        print(msg.topic)
        print(f"QoS: {msg.qos}")
        print(f"Retained?: {msg.retain}")
        print(f"\nMessage:")
        print(msg.payload.decode())
        print("=============================================")

        # Process command if from commands topic
        # This is so someone in public can't just post the command and mess things up
        if msg.topic == "<104547242>/commands":
            command = msg.payload.decode().strip()      # Remove all whitespace from command
            
            # Valid logging commands accepted
            match command:
                case "!startlog":
                    startLogging()
                case "!stoplog":
                    stopLogging()
        
        # Log server cluster metrics if logging is active
        if loggingActive and (msg.topic == "<104547242>/servers/avg_cpu_util" or msg.topic == "<104547242>/servers/active"):
            logger.info("====================[SUB]====================")
            logger.info(msg.topic)
            logger.info(f"Retained?: {msg.retain}")
            logger.info(f"QoS: {msg.qos}")
            logger.info("")
            logger.info(f"Message:")
            logger.info(msg.payload.decode())
            logger.info("=============================================")


    client.subscribe(topics)
    client.on_message = on_message


def main():
    # Setup MQTT client
    client = connect_mqtt()
    subscribe(client)
    
    try:
        client.loop_forever()       # Blocking network loop function for MQTT client
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected, disconnecting from MQTT broker...")

        # Clean up program before ending
        stopLogging()
        disconnect_mqtt(client)


if __name__ == "__main__":
    main()