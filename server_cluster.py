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
isRunning = True

class SimMode(Enum):
    NORMAL = 1
    INCREASING = 2
    DECREASING = 3

# Start in normal simulation mode
simMode = SimMode.NORMAL.value


def connect_mqtt() -> mqtt_client:
    """Connects to the MQTT broker and returns the client object."""
    def on_connect(client, userdata, flags, rc, properties):
        """Callback when connected to the broker."""
        if rc == 0: 
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect. Reason code: {rc}")            
    
    client = mqtt_client.Client(client_id = client_id, callback_api_version = mqtt_client.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username, password)
    client.on_connect = on_connect

    try:
        print(f"Attempting to connect to {broker} on port {port}")
        client.connect(broker, port)
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
    global isRunning, avgVcpuUtil, serversActive, simMode
    topic = "<104547242>/servers/avg_cpu_util"
    vcpuUtilLowCount = 0
    vcpuUtilHighCount = 0

    # Loop thread forever while no keyboard interrupt
    while isRunning:
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
            case SimMode.INCREASING.value:
                avgVcpuUtil += random.randint(-5, 15)
            case SimMode.DECREASING.value:
                avgVcpuUtil += random.randint(-15, 5)
            
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
        # Scaling out too early can cause too many resources to be created too fast, wasting computational power
        if vcpuUtilLowCount > 10 and serversActive > 1:
            pubWarning(client, "Warning: CPU utilisation low")
            vcpuUtilLowCount = 0

        if vcpuUtilHighCount > 5:
            # Beyond 8 servers, we start getting diminishing returns
            if serversActive < 8:
                pubWarning(client, "Warning: CPU utilisation high")
            else:
                pubWarning(client, "Warning: Servers are at capacity")      # There is no need to handle this warning in the monitor
            vcpuUtilHighCount = 0

        time.sleep(2)


def pubServersActive(client):
    global isRunning, serversActive
    topic = "<104547242>/servers/active"

    # Loop thread forever while no keyboard interrupt
    while isRunning:
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
    global avgVcpuUtil, serversActive

    # We want to have at least 1 server running, having 0 or less isn't realistic
    if serversActive > 1:
        oldServersActive = serversActive
        serversActive -= 1

        # Increase the average utilisation proportionally as fewer vCPUs handle the same workload
        avgVcpuUtil = int(avgVcpuUtil * (oldServersActive / serversActive))
        
        # Make sure utilisation stays within bounds of 0-100%
        avgVcpuUtil = max(0, min(avgVcpuUtil, 100))


def handleScaleOut():
    global avgVcpuUtil, serversActive
    
    oldServersActive = serversActive
    serversActive += 2                          # Add on two servers, since 1 isn't enough for a big difference

    if serversActive > 8: serversActive = 8     # Keep the servers capped at 8

    # Decrease the average utilisation proportionally as more servers handle the same workload
    avgVcpuUtil = int(avgVcpuUtil * (oldServersActive / serversActive))
    
    # Make sure utilisation stays within bounds of 0-100%
    avgVcpuUtil = max(0, min(avgVcpuUtil, 100))


def subscribe(client: mqtt_client) -> None:
    """Subscribe client to topics."""
    def on_message(client, userdata, msg):
        """Print received messages to terminal and process commands"""
        global simMode

        print("\n====================[SUB]====================")
        print(msg.topic)
        print(f"QoS: {msg.qos}")
        print(f"Retained?: {msg.retain}")
        print(f"\nMessage:")
        print(msg.payload.decode())
        print("=============================================")

        if msg.topic == "<104547242>/commands":
            cmdActions = {
                "!scalein": handleScaleIn,
                "!scaleout": handleScaleOut,
                "!simnormal": SimMode.NORMAL.value,
                "!simincrease": SimMode.INCREASING.value,
                "!simdecrease": SimMode.DECREASING.value
            }

            # Remove all whitespace from command and make everything lowercase
            command = msg.payload.decode().strip().lower()
            
            # Execute valid commands
            if command in cmdActions:
                action = cmdActions[command]
                result = action() if callable(action) else action   # Call function if function

                if not callable(action): simMode = result           # Update simMode if value

    client.on_message = on_message
    client.subscribe(subscribeTopics)
    print(f"Subscribed to topics: {subscribeTopics}\n")



def main() -> None:
    """Main program logic."""
    global isRunning
    print("Starting the server cluster simulation...")
    
    client = connect_mqtt()
    if client is None:
        print("Failed to connect to the MQTT broker. Exiting...")
        return

    subscribe(client)

    # Create threads for each publish function
    avgVcpuUtilThread = threading.Thread(target = pubAvgVcpuUse, args = (client,))
    serversActiveThread = threading.Thread(target = pubServersActive, args = (client,))

    avgVcpuUtilThread.start()
    serversActiveThread.start()

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected, disconnecting from MQTT broker...")
    except Exception as e:
        print(f"Error during main operation: {e}")
    finally:
        # Signal the threads to stop and wait for them to finish operations
        isRunning = False
        avgVcpuUtilThread.join()
        serversActiveThread.join()

        disconnect_mqtt(client)
        print("Client disconnected, exiting program.")


if __name__ == "__main__":
    main()