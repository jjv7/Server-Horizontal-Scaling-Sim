from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv
import os
import random

load_dotenv()

# This code uses the Paho MQTT Python Client library
# References: https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
#             https://github.com/eclipse/paho.mqtt.python/blob/master/docs/migrations.rst


# Connection info
broker = os.getenv('BROKER')
port = 1883
topics = [("<104547242>/temperature", 0), ("public/#", 0)]
client_id = f'client-device-{random.randint(0, 1000)}'
username = os.getenv('MQTT_USERNAME')
password = os.getenv('MQTT_PASSWORD')


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc, properties):
        # Response code is 0 for a successful connection
        print("Connected to MQTT Broker!") if rc == 0 else print("Failed to connect, return code %d\n", rc)
            
    
    # Connect client object to MQTT broker
    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client) -> None:
    def on_message(client, userdata, msg):
        print("\n########################################")
        print(f"Topic: {msg.topic}")
        print(f"QoS: {msg.qos}")
        print(f"Retain: {msg.retain}")
        print(f"\nMessage:\n{msg.payload.decode()}")
        print("########################################")

    client.subscribe(topics)
    client.on_message = on_message


def main():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == "__main__":
    main()