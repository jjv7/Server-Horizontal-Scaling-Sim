from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv
import os
import random
import time
import threading

# The broker, username and password are stored in a .env file which needs to be made if not already included
load_dotenv()

# This code uses the Paho MQTT Python Client library
# References: https://www.emqx.com/en/blog/how-to-use-mqtt-in-python
#             https://github.com/eclipse/paho.mqtt.python/blob/master/docs/migrations.rst

# Connection info
broker = os.getenv('BROKER')
port = 1883
subscribeTopics = [("<104547242>/vcpus/commands", 0), ("public/#", 0)]            # Pub and sub topics need to be separate, or public will be spammed as well
client_id = f'server-{random.randint(0, 1000)}'                                   # Assign a random ID to the client device
username = os.getenv('MQTT_USERNAME')
password = os.getenv('MQTT_PASSWORD')


# Global variables, so multiple functions can access this
avgVcpuUtil = 10
vcpuActive = 1


def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        # Response code is 0 for a successful connection
        print("Connected to MQTT Broker!") if rc == 0 else print(f"Failed to connect. Reason code: {rc}\n")
            
    
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


def pubAvgVcpuUse(client):
    global avgVcpuUtil
    topic = "<104547242>/vcpus/avg_usage"

    while True:
        # Pub msg to topic
        msg = f"Avg CPU utilisation: {avgVcpuUtil}%"
        result = client.publish(topic, msg)

        # Print message send status to terminal
        status = result[0]
        print("\n--------------------[PUB]--------------------")
        print(topic)
        print(f"\nSent:\n{msg}") if status == 0 else print(f"Failed to send message to topic")
        print("---------------------------------------------")
        
        # Create variation in data
        avgVcpuUtil += random.randint(-4, 4)

        # Make sure utilisation stays within bounds of 0-100%
        if avgVcpuUtil < 0: avgVcpuUtil = 0
        if avgVcpuUtil > 100: avgVcpuUtil = 100

        time.sleep(2)


def pubVcpuActive(client):
    global vcpuActive
    topic = "<104547242>/vcpus/active"

    while True:
        # Pub msg to topic
        msg = f"Active VCPUs: {vcpuActive}"
        result = client.publish(topic, msg)

        # Print message send status to terminal
        status = result[0]
        print("\n--------------------[PUB]--------------------")
        print(topic)
        print(f"\nSent:\n{msg}") if status == 0 else print(f"Failed to send message to topic")
        print("---------------------------------------------")

        # Active vCPUs should stay relatively consistent, so don't need to create variation here
        # Instead provide a recommendation to scale in/out

        time.sleep(5)


def handleScaleIn():
    global avgVcpuUtil
    global vcpuActive
    if vcpuActive > 1:
        oldVcpuActive = vcpuActive
        vcpuActive -= 1

        # Increase the average utilisation proportionally as fewer vCPUs handle the same workload
        avgVcpuUtil = int(avgVcpuUtil * (oldVcpuActive / vcpuActive))
        
        # Make sure utilisation stays within bounds of 0-100%
        avgVcpuUtil = max(0, min(avgVcpuUtil, 100))


def handleScaleOut():
    global avgVcpuUtil
    global vcpuActive
    
    oldVcpuActive = vcpuActive
    vcpuActive += 1

    # Decrease the average utilisation proportionally as more vCPUs handle the same workload
    avgVcpuUtil = int(avgVcpuUtil * (oldVcpuActive / vcpuActive))
    
    # Make sure utilisation stays within bounds of 0-100%
    avgVcpuUtil = max(0, min(avgVcpuUtil, 100))


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

        # Process command if from logger topic
        if msg.topic == "<104547242>/vcpus/commands":
            command = msg.payload.decode().strip()      # Remove all whitespace from command
            
            # Valid commands
            match command:
                case "!scalein":
                    handleScaleIn()
                case "!scaleout":
                    handleScaleOut()
    
    client.subscribe(subscribeTopics)
    client.on_message = on_message



def main():
    client = connect_mqtt()
    subscribe(client)

    # Create threads for each publish function
    avgVcpuUtilThread = threading.Thread(target = pubAvgVcpuUse, args = (client,))
    vcpuActiveThread = threading.Thread(target = pubVcpuActive, args = (client,))

    # Start threads
    avgVcpuUtilThread.start()
    vcpuActiveThread.start()

    try:
        client.loop_forever()               # Blocking network loop function for MQTT client
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected, disconnecting from MQTT broker...")
        disconnect_mqtt(client)
        print("Client disconnected, exiting program.")


if __name__ == "__main__":
    main()