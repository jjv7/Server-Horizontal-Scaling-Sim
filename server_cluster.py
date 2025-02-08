from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv
from enum import Enum
from textwrap import dedent
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
baseTopic = "simulation"
subscribeTopics = [(f"{baseTopic}/commands", 0), ("public/#", 0)]    # Pub and sub topics need to be separate, or public will be spammed as well
client_id = f'server-{random.randint(0, 1000)}'                     # Assign a random ID to the client device
username = os.getenv('MQTT_USERNAME')
password = os.getenv('MQTT_PASSWORD')

# Environment variable checks
if not broker:
    print("Missing MQTT BROKER environment variable in .env file")
    exit(1)

if not username or not password:
    username = None
    password = None
    print("Missing MQTT_USERNAME and/or MQTT_PASSWORD environment variables in .env file")
    print("MQTT client will attempt to connect without username and password")

# Global variables, so multiple functions can access this
avgVcpuUtil = 10
serversActive = 1

isConn = threading.Event()

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
            isConn.set()
            subscribe(client)
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


def pubMsg(client: mqtt_client, topic: str, msg: str) -> None:
    """Publishes a message to a specified topic"""
    result = client.publish(topic, msg)
    status = result[0]

    # Without the whitespace, dedent will not work properly due to the \n
    if status == 0:
        sendMsg = f"Sent:\n{" " * 17}{msg}"
    else:
        sendMsg = f'Error code: {status}\n{" " * 17}Failed to publish: "{msg}"'
    
    print(dedent(f"""\
                 --------------------[PUB]--------------------
                 {topic}

                 {sendMsg}
                 ---------------------------------------------
                 """))


def pubAvgVcpuUse(client) -> None:
    """Publishes the average CPU utilisation"""

    global isRunning, avgVcpuUtil, serversActive, simMode

    isConn.wait()

    avgTopic = f"{baseTopic}/servers/avg_cpu_util"
    warningTopic = f"{baseTopic}/warnings"
    lowCount = 0
    highCount = 0

    while isRunning:
        msg = f"Avg CPU utilisation: {avgVcpuUtil}%"
        pubMsg(client, avgTopic, msg)
        
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
            lowCount += 1
        else:
            lowCount = 0

        if avgVcpuUtil > 80:
            highCount += 1
        else:
            highCount = 0

        # Provide a recommendation to scale in/out
        # Scaling in too early can cause resources to become overloaded fast, hence it needs to trigger low more times
        # Scaling out too early can cause too many resources to be created too fast, wasting computational power
        if lowCount > 10 and serversActive > 1:
            pubMsg(client, warningTopic, "Warning: CPU utilisation low")
            lowCount = 0

        if highCount > 5:
            # Beyond 8 servers, we start getting diminishing returns
            if serversActive < 8:
                pubMsg(client, warningTopic, "Warning: CPU utilisation high")
            else:
                pubMsg(client, warningTopic, "Warning: Servers are at capacity")      # There is no need to handle this warning in the monitor
            highCount = 0

        time.sleep(2)


def pubServersActive(client) -> None:
    """Publishes the active servers"""
    
    global isRunning, serversActive

    isConn.wait()

    topic = f"{baseTopic}/servers/active"

    while isRunning:
        msg = f"Active servers: {serversActive}"
        pubMsg(client, topic, msg)

        # Active servers should stay relatively consistent, so don't need to create variation here

        time.sleep(5)


def handleScaleIn() -> None:
    """Handles scaling in by decreasing the number of active servers."""
    global avgVcpuUtil, serversActive

    # Ensure at least 1 server is running
    if serversActive > 1:
        oldServersActive = serversActive
        serversActive -= 1

        # Increase the average utilisation proportionally
        # This assumes that the workload stays constant
        avgVcpuUtil = int(avgVcpuUtil * (oldServersActive / serversActive))
        
        # Make sure utilisation stays within bounds of 0-100%
        avgVcpuUtil = max(0, min(avgVcpuUtil, 100))


def handleScaleOut() -> None:
    """Handles scaling out by increasing the number of active servers."""
    global avgVcpuUtil, serversActive
    
    oldServersActive = serversActive
    serversActive += 2                          # Add on two servers, since 1 isn't enough for a big difference

    if serversActive > 8: serversActive = 8     # Cap number of servers at 8

    # Decrease the average utilisation proportionally
    # This assumes that the workload stays constant
    avgVcpuUtil = int(avgVcpuUtil * (oldServersActive / serversActive))
    
    # Make sure utilisation stays within bounds of 0-100%
    avgVcpuUtil = max(0, min(avgVcpuUtil, 100))


def subscribe(client: mqtt_client) -> None:
    """Subscribe client to topics."""
    def on_message(client, userdata, msg):
        """Print received messages to terminal and process commands"""
        global simMode

        print(dedent(f"""\
                     ====================[SUB]====================
                     {msg.topic}
                     QoS: {msg.qos}
                     Retained?: {msg.retain}
                     
                     Message:
                     {msg.payload.decode()}
                     =============================================
                     """))

        if msg.topic == f"{baseTopic}/commands":
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


if __name__ == "__main__":
    print("Starting the server cluster simulation...")
    
    client = connect_mqtt()
    if client is None:
        print("Failed to connect to the MQTT broker. Exiting...")
        exit(1)

    # Create threads for each publish function
    avgVcpuUtilThread = threading.Thread(target=pubAvgVcpuUse, args=(client,))
    serversActiveThread = threading.Thread(target=pubServersActive, args=(client,))

    print("Starting publishing threads")
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
        print("Successfully stopped publishing threads")

        disconnect_mqtt(client)
        print("Client disconnected, exiting program.")