from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv
from enum import Enum
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
subscribeTopics = [("<104547242>/commands", 0), ("public/#", 0)]                  # Pub and sub topics need to be separate, or public will be spammed as well
client_id = f'server-{random.randint(0, 1000)}'                                   # Assign a random ID to the client device
username = os.getenv('MQTT_USERNAME')
password = os.getenv('MQTT_PASSWORD')


# Global variables, so multiple functions can access this
avgVcpuUtil = 10
serversActive = 1

# This is to kill the threads when a keyboard interrupt is used
running = True

class SimMode(Enum):
    NORMAL = 1
    INCREASING = 2
    DECREASING = 3

simMode = SimMode.NORMAL.value


def connect_mqtt():
    def on_connect(client, userdata, flags, rc, properties):
        # Response code is 0 for a successful connection
        # this is printed on every connection
        print("Connected to MQTT Broker!") if rc == 0 else print(f"Failed to connect. Reason code: {rc}\n")
            
    
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


def pubWarning(client, msg):
    # Pub warning msg to topic
    topic = "<104547242>/warnings"
    result = client.publish(topic, msg)

    # Print message send status to terminal
    status = result[0]
    print("\n--------------------[PUB]--------------------")
    print(topic)
    print(f"\nSent:\n{msg}") if status == 0 else print(f"Failed to send message to topic")
    print("---------------------------------------------")


def pubAvgVcpuUse(client):
    global running
    global avgVcpuUtil
    global serversActive
    global simMode
    topic = "<104547242>/servers/avg_cpu_util"
    vcpuUtilLowCount = 0
    vcpuUtilHighCount = 0

    # Loop thread forever while no keyboard interrupt
    while running:
        # Pub avg CPU utilisation of servers to topic
        msg = f"Avg CPU utilisation: {avgVcpuUtil}%"
        result = client.publish(topic, msg)

        # Print message send status to terminal
        status = result[0]
        print("\n--------------------[PUB]--------------------")
        print(topic)
        print(f"\nSent:\n{msg}") if status == 0 else print(f"Failed to send message to topic")
        print("---------------------------------------------")
        
        # Create variation in data based on simulation mode
        match simMode:
            case SimMode.NORMAL.value:
                avgVcpuUtil += random.randint(-5, 5)
                print("normal")
            case SimMode.INCREASING.value:
                avgVcpuUtil += random.randint(-5, 15)
                print("+")
            case SimMode.DECREASING.value:
                avgVcpuUtil += random.randint(-15, 5)
                print("-")
            
        # Make sure utilisation stays within bounds of 0-100%
        avgVcpuUtil = max(0, min(avgVcpuUtil, 100))

        # Check if vCPU usage is too low/high and add to count
        if avgVcpuUtil < 20 and serversActive > 1:
            vcpuUtilLowCount += 1
        else:
            vcpuUtilLowCount = 0

        if avgVcpuUtil > 80:
            vcpuUtilHighCount += 1
        else:
            vcpuUtilHighCount = 0

        # Provide a recommendation to scale in/out
        # Scaling in too early can cause resources to become overloaded fast, hence it needs to trigger low more times
        if vcpuUtilLowCount > 10 and serversActive > 1:
            pubWarning(client, "Warning: CPU utilisation low")
            vcpuUtilLowCount = 0

        if vcpuUtilHighCount > 5:
            # Beyond 8 servers, we start getting diminishing returns
            
            if serversActive < 8:
                pubWarning(client, "Warning: CPU utilisation high")
            else:
                pubWarning(client, "Warning: Servers are at capacity")      # This warning isn't handled because of the diminishing returns 
            
            vcpuUtilHighCount = 0

        
        if vcpuUtilHighCount > 5 and serversActive == 8:
            
            vcpuUtilHighCount = 0

        time.sleep(2)


def pubServersActive(client):
    global running
    global serversActive
    topic = "<104547242>/servers/active"

    # Loop thread forever while no keyboard interrupt
    while running:
        # Pub active servers to topic
        msg = f"Active servers: {serversActive}"
        result = client.publish(topic, msg)

        # Print message send status to terminal
        status = result[0]
        print("\n--------------------[PUB]--------------------")
        print(topic)
        print(f"\nSent:\n{msg}") if status == 0 else print(f"Failed to send message to topic")
        print("---------------------------------------------")

        # Active servers should stay relatively consistent, so don't need to create variation here

        time.sleep(5)


def handleScaleIn():
    global avgVcpuUtil
    global serversActive

    # We want to have at least 1 server running, having 0 or less isn't realistic
    if serversActive > 1:
        oldServersActive = serversActive
        serversActive -= 1

        # Increase the average utilisation proportionally as fewer vCPUs handle the same workload
        avgVcpuUtil = int(avgVcpuUtil * (oldServersActive / serversActive))
        
        # Make sure utilisation stays within bounds of 0-100%
        avgVcpuUtil = max(0, min(avgVcpuUtil, 100))


def handleScaleOut():
    global avgVcpuUtil
    global serversActive
    
    oldServersActive = serversActive
    serversActive += 2                          # Add on two servers, since 1 isn't enough for a big difference

    if serversActive > 8: serversActive = 8     # Keep the servers capped at 8

    # Decrease the average utilisation proportionally as more servers handle the same workload
    avgVcpuUtil = int(avgVcpuUtil * (oldServersActive / serversActive))
    
    # Make sure utilisation stays within bounds of 0-100%
    avgVcpuUtil = max(0, min(avgVcpuUtil, 100))


def subscribe(client: mqtt_client):
    # Print message and its details in specified format
    # I tried to create something similar to the MQTTX GUI client messages
    def on_message(client, userdata, msg):
        global simMode

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
            command = msg.payload.decode().strip().lower()      # Remove all whitespace from command and make everything lowercase
            
            # Valid commands accepted
            match command:
                case "!scalein":
                    handleScaleIn()
                case "!scaleout":
                    handleScaleOut()
                case "!simnormal":
                    simMode = SimMode.NORMAL.value
                case "!simincrease":
                    simMode = SimMode.INCREASING.value
                case "!simdecrease":
                    simMode = SimMode.DECREASING.value


    
    client.subscribe(subscribeTopics)
    client.on_message = on_message



def main():
    global running
    client = connect_mqtt()
    subscribe(client)

    # Create threads for each publish function
    avgVcpuUtilThread = threading.Thread(target = pubAvgVcpuUse, args = (client,))
    serversActiveThread = threading.Thread(target = pubServersActive, args = (client,))

    # Start threads
    avgVcpuUtilThread.start()
    serversActiveThread.start()

    try:
        client.loop_forever()               # Blocking network loop function for MQTT client
    except KeyboardInterrupt:
        # Clean up environment
        running = False                     # Kill the threads by setting the while condition to false
        print("\nKeyboardInterrupt detected, disconnecting from MQTT broker...")
        disconnect_mqtt(client)
        print("Client disconnected, exiting program.")


if __name__ == "__main__":
    main()