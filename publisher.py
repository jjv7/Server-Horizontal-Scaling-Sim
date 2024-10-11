from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv
import os
import random
import time

load_dotenv()

# This code uses the Paho MQTT Python Client library
# References: https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
#             https://github.com/eclipse/paho.mqtt.python/blob/master/docs/migrations.rst

# Connection info
broker = os.getenv('BROKER')
port = 1883
topic = "<104547242>/temperature"
client_id = f'temperature-sensor-{random.randint(0, 1000)}'
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


def publish(client):
    temperature = 25                                          # Generate fake temperature data with a starting value of 25°C
    
    while True:
        msg = f"Temperature: {temperature}°C"      # Generate fake temperature data
        result = client.publish(topic, msg)
        
        # Check if message was successfully sent
        status = result[0]
        print(f"Send `{msg}` to topic `{topic}`") if status == 0 else print(f"Failed to send message to topic {topic}")

        temperature += random.randint(-2, 2)                  # Create variation in temperature reading
        time.sleep(1)                                         # Wait 1 second, so we don't spam the broker



def main():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()


if __name__ == "__main__":
    main()