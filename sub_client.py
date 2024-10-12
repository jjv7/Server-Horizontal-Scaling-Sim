from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv
import os
import random


# The broker, username and password are stored in a .env file which needs to be made if not already included
load_dotenv()

# This code uses the Paho MQTT Python Client library
# References: https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
#             https://github.com/eclipse/paho.mqtt.python/blob/master/docs/migrations.rst


# Connection info
broker = os.getenv('BROKER')
port = 1883
topics = [("<104547242>/temperature", 0), ("public/#", 0)]              # <104547242>/temperature can be replaced with any private topic. The 0 indicates the QoS
client_id = f'client-device-{random.randint(0, 1000)}'                  # Assign a random ID to the client device
username = os.getenv('MQTT_USERNAME')
password = os.getenv('MQTT_PASSWORD')


def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        # Response code is 0 for a successful connection
        print("Connected to MQTT Broker!") if rc == 0 else print("Failed to connect, return code {rc}\n")
            
    
    # Connect client object to MQTT broker
    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def disconnect_mqtt(client: mqtt_client):
    def on_disconnect(client, userdata, flags, rc, properties):
        print("Successfully disconnected from MQTT Broker") if rc == 0 else print(f"Disconnected with an error. Reason code: {rc}\n")

    client.on_disconnect = on_disconnect
    client.disconnect()


def subscribe(client: mqtt_client):
    # Print message and its details in specified format
    # I tried to create something similar to the MQTTX GUI client messages
    def on_message(client, userdata, msg):
        print("\n====================[SUB]====================")
        print(msg.topic)
        print(f"QoS: {msg.qos}")
        print(f"Retained?: {msg.retain}")
        print(f"\nMessage:")
        print(msg.payload.decode())
        print("=============================================")
    
    client.subscribe(topics)
    client.on_message = on_message


def main():
    client = connect_mqtt()
    subscribe(client)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected, disconnecting from MQTT broker...")
        disconnect_mqtt(client)


if __name__ == "__main__":
    main()