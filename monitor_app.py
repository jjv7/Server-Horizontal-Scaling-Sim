from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv, find_dotenv
import tkinter as tk
from tkinter import ttk, messagebox
from socket import gaierror
from textwrap import dedent
import os
import random
import time
import threading

# References: https://www.geeksforgeeks.org/python-gui-tkinter/
#             https://www.w3schools.com/python/python_classes.asp
#             https://www.geeksforgeeks.org/python-tkinter-messagebox-widget/


# If monitoring the example application copy the following into the .env file:
# sub -> public/#,simulation/servers/avg_cpu_util,simulation/servers/active,simulation/warnings
# pub -> simulation/commands

# You will then need to press the subscribe button to be subscribed to the sub topics


# Check if a .env file is present
useEnvVariables = False
if find_dotenv():
    useEnvVariables = True
    load_dotenv()


class MqttClientGui(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        
        # Initialise window
        self.geometry("585x450")
        self.title("MQTT Python GUI Client")
        self.resizable(False, False)    # Keep window size fixed

        # State variables for connections and warnings
        self.publishTopics = []
        self.subscribeTopics = []
        self.isConnected = False
        self.handlingWarning = False
        self.client = None
        self.warningLock = threading.Lock()

        self.setupUi()


    def setupUi(self) -> None:
        # Create notebook container to hold tabs
        tabBar = ttk.Notebook(self)
        tabBar.pack(expand=True, fill="both")
        
        # Create tabs
        connectionTab = ttk.Frame(tabBar)
        messageTab = ttk.Frame(tabBar)

        # Add tabs to the notebook container
        tabBar.add(connectionTab, text="Connection")
        tabBar.add(messageTab, text="Messages")

        # Initialise the UI in each of the tabs
        self.initConnectionTab(connectionTab)
        self.initMessageTab(messageTab)


    def initConnectionTab(self, connectionTab: ttk.Frame) -> None:
        # Title
        tabTitle = ttk.Label(connectionTab, text="MQTT Broker Connection Settings", font="Calibri, 18 bold")
        tabTitle.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)
        
        # Host field
        hostFrame = ttk.LabelFrame(connectionTab, text="Host", padding=(10, 10))
        hostFrame.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        hostLabel = ttk.Label(hostFrame, text="mqtt://")
        hostLabel.grid(row=0, column=0, padx=(2, 3), pady=(0, 7))
        
        self.hostEntry = ttk.Entry(hostFrame, width=22)
        self.hostEntry.grid(row=0, column=1, pady=(0, 7), sticky=tk.W)


        # Port field
        portFrame = ttk.LabelFrame(connectionTab, text="Port", padding=(10, 10))
        portFrame.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.portEntry = ttk.Entry(portFrame, width=30)
        self.portEntry.grid(row=0, column=0, pady=(0, 7), sticky=tk.W)
        self.portEntry.insert(0, 1883)                                      # Default MQTT port will be automatically input into the field


        # Username field
        usernameFrame = ttk.LabelFrame(connectionTab, text="Username", padding=(10, 10))
        usernameFrame.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
                
        self.usernameEntry = ttk.Entry(usernameFrame, width=30)
        self.usernameEntry.grid(row=0, column=0, pady=(0, 7), sticky=tk.W)


        # Password field
        passwordFrame = ttk.LabelFrame(connectionTab, text="Password", padding=(10, 10))
        passwordFrame.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
                
        self.passwordEntry = ttk.Entry(passwordFrame, width=30, show="*")
        self.passwordEntry.grid(row=0, column=0, pady=(0, 7), sticky=tk.W)


        # Connection status section
        connStatFrame = ttk.LabelFrame(connectionTab, text="Connection Status", padding=(10, 10))
        connStatFrame.grid(row=2, column=1, columnspan=2, padx=30, pady=10)

        self.connStatLabel = ttk.Label(connStatFrame, text="Not Connected", font="Calibri, 11 bold", background="gray64", foreground="red", width=30, anchor=tk.CENTER)
        self.connStatLabel.grid(row=0, column=0, padx=5, pady=5)

        # Connect button
        connButton = ttk.Button(connectionTab, text="Connect", command=self.connect_mqtt)
        connButton.grid(row=3, column=1, padx=(0, 30), pady=10, sticky=tk.N + tk.E)

        # Disconnect button
        disconnButton = ttk.Button(connectionTab, text="Disconnect", command=self.disconnect_mqtt)
        disconnButton.grid(row=3, column=2, pady=10, sticky=tk.N + tk.W)


        # Add in preset entries into fields according to the .env file
        if useEnvVariables:
            self.hostEntry.insert(0, os.getenv('BROKER'))
            self.usernameEntry.insert(0, os.getenv('MQTT_USERNAME'))
            self.passwordEntry.insert(0, os.getenv('MQTT_PASSWORD'))


    def initMessageTab(self, messageTab: ttk.Frame) -> None:
        # Title
        tabTitle = ttk.Label(messageTab, text="Messages", font="Calibri, 18 bold")
        tabTitle.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)


        # Subscribe section
        subFrame = ttk.LabelFrame(messageTab, text="Subscribe", padding=(10, 10))
        subFrame.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

        # Sub topics field
        subTopicsLabel = ttk.Label(subFrame, text="Topics:")
        subTopicsLabel.grid(row=0, column=0, sticky=tk.W)

        self.subTopicsEntry = ttk.Entry(subFrame)
        self.subTopicsEntry.grid(row=0, column=1, padx=(22, 0), pady=10, sticky=tk.W)

        # You will still need to press the subscribe button to subscribe to these topics
        self.subTopicsEntry.insert(0, "public/#,simulation/servers/avg_cpu_util,simulation/servers/active,simulation/warnings,simulation/commands")

        # Sub button
        subButton = ttk.Button(subFrame, text="Subscribe", command=self.subscribe)
        subButton.grid(row=1, column=0, columnspan=2, pady=10)
        

        # Publish section
        pubFrame = ttk.LabelFrame(messageTab, text="Publish", padding=(10, 10))
        pubFrame.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W + tk.N)

        # Pub topics field
        pubTopicsLabel = ttk.Label(pubFrame, text="Topics:")
        pubTopicsLabel.grid(row=0, column=0, sticky=tk.W + tk.N)

        self.pubTopicsEntry = ttk.Entry(pubFrame)
        self.pubTopicsEntry.grid(row=0, column=1, padx=(10, 0), pady=(0, 10), sticky=tk.W)

        self.pubTopicsEntry.insert(0, "simulation/commands")

        # Message field
        pubMessageLabel = ttk.Label(pubFrame, text="Message:")
        pubMessageLabel.grid(row=1, column=0, sticky=tk.W)

        self.pubMessageEntry = ttk.Entry(pubFrame)
        self.pubMessageEntry.grid(row=1, column=1, padx=(10, 0), pady=10, sticky=tk.W)

        # Pub button
        pubButton = ttk.Button(pubFrame, text="Publish", command=self.publish)
        pubButton.grid(row=2, column=0, columnspan=2, pady=10)


        # Message box
        messagesFrame = ttk.LabelFrame(messageTab, text="Received Messages", padding=(0, 10))
        messagesFrame.grid(row=1, column=1, rowspan=2, padx=(10, 0), pady=10, sticky=tk.W)
        scrollbar = tk.Scrollbar(messagesFrame)
        scrollbar.grid(row=0, column=1, sticky=tk.NSEW)

        self.messagesDisplay = tk.Text(
            messagesFrame,
            height=20,
            width=42,
            font="Consolas, 9",
            background="black", 
            foreground="white",
            insertbackground="white",
            yscrollcommand=scrollbar.set
        )

        self.messagesDisplay.grid(row=0, column=0, padx=(10, 0))
        self.messagesDisplay.insert(tk.END, "=====================================\n")  # This is to create the top of the first message
        scrollbar.config(command=self.messagesDisplay.yview)                            # Sets the scrollbar to control the y-position in the messages box
        self.messagesDisplay.config(state=tk.DISABLED)                                  # Disable any input into the messages box


    def getConnData(self) -> dict[str, str]:
        """Returns a dictionary of the connection parameters entered by the user"""
        return {
            "broker": self.hostEntry.get(),
            "port": self.portEntry.get(),
            "username": self.usernameEntry.get(),
            "password": self.passwordEntry.get()
        }


    def connect_mqtt(self) -> None:
        """Connects client to the MQTT broker."""
        def on_connect(client, userdata, flags, rc, properties) -> None:
            """Callback when connected to the broker."""
            if rc == 0:
                self.isConnected = True
                self.connStatLabel.config(text="Connected", foreground="green")
                self.after(0, lambda: messagebox.showinfo("Connection successful", "Connected to MQTT Broker!"))
            else:
                self.isConnected = False  # Ensure connected is False in case the first connection was successful
                self.connStatLabel.config(text="Not Connected", foreground="red")
                self.client.loop_stop() # If this is not here, with the wrong authentication details it will keep retrying the connection
                self.after(0, lambda: messagebox.showerror("Connection unsuccessful", f"Failed to connect. Reason code: {rc}\n"))

        # Exit if already connected
        if self.isConnected:
            messagebox.showwarning("Connection active", "Please close the current connection before connecting again")
            return
        
        # Retrieve connection info
        connData = self.getConnData()
        broker = connData["broker"]
        port = connData["port"]
        username = connData["username"]
        password = connData["password"]

        # Validate connection info
        if not broker:
            messagebox.showerror("Input Error", "Please input a host")
            return
        if not port:
            messagebox.showerror("Input Error", "Please input a port")
            return
        
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Input Error", "Port must be a valid integer")
            return

        if not (0 < port < 65536):
            messagebox.showerror("Input Error", "Port must be between 1 and 65535")
            return

        # Connect client object to MQTT broker
        self.client = mqtt_client.Client(
            client_id=f'gui-mqtt-{random.randint(0, 1000)}',
            callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
        )
        self.client.username_pw_set(username, password)
        self.client.on_connect = on_connect
        
        try:
            self.client.connect(broker, port)
            self.client.loop_start()
        except (TimeoutError, ConnectionRefusedError, gaierror) as e:
            messagebox.showerror("Connection Error", f"Connection error: {e}")
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")


    def disconnect_mqtt(self) -> None:
        """Disconnects client from the MQTT broker."""
        def on_disconnect(client, userdata, flags, rc, properties):
            """Callback when disconnected from the broker."""
            self.isConnected = False

            if rc == 0:
                self.after(0, lambda: messagebox.showinfo("Disconnection successful", "Successfully disconnected from MQTT Broker"))
            else:
                self.after(0, lambda: messagebox.showerror("Disconnection with error", f"Disconnected with an error. Reason code: {rc}\n"))
            
            self.connStatLabel.config(text="Not Connected", foreground="red")

        self.client.on_disconnect = on_disconnect

        # Only attempt disconnecting if client is already connected, or errors happen
        if self.isConnected:
            self.client.disconnect()


    def processWarning(self, msg) -> None:
        """Processes the input message as a warning"""
        with self.warningLock:
            if self.handlingWarning: return
            self.handlingWarning = True        

        topic = "simulation/commands"
        warning = msg.payload.decode()
        command = ""
        match warning:
            case "Warning: CPU utilisation low":
                command = "!scalein"
            case "Warning: CPU utilisation high":
                command = "!scaleout"
            case _:
                with self.warningLock:
                    self.handlingWarning = False
                return

        self.after(0, lambda: messagebox.showinfo("Handling warning", f"Sending `{command}` in response to `{warning}`"))
        self.client.publish(topic, "!startlog") # Start logging server cluster metrics to keep a history of the alert
        self.client.publish(topic, command)     # Resolve the problem the server cluster is experiencing
        time.sleep(10)                          # Keep logging information for 10 seconds
        self.client.publish(topic, "!stoplog")
        with self.warningLock:
            self.handlingWarning = False


    def publish(self) -> None:
        if not self.isConnected:
            messagebox.showerror("Error", "Please connect to an MQTT broker first")
            return

        topics = [topic.strip() for topic in self.pubTopicsEntry.get().split(",")]
        if len(topics) == 1 and topics[0] == '':
            messagebox.showerror("Error", "Please input a topic to publish to")
            return
        
        msg = self.pubMessageEntry.get()
        if not msg:
            messagebox.showerror("Error", "Please input a message to publish")
            return
        
        for topic in topics:
            result = self.client.publish(topic, msg)
            status = result[0]
            if status == 0:
                self.after(0, lambda: messagebox.showinfo("Message Published", f"Sent `{msg}` to topic `{topic}`"))
            else:
                self.after(0, lambda: messagebox.showinfo("Error", f"Failed to send message to topic `{topic}`"))


    def subscribe(self) -> None:
        def on_message(client, userdata, msg) -> None:
            def updateMsgBox() -> None:
                # Enable text input and display message
                self.messagesDisplay.config(state=tk.NORMAL)
                self.messagesDisplay.insert(tk.END, dedent(f"""\
                    {msg.topic}
                    QoS: {msg.qos}
                    Retained?: {msg.retain}
                    
                    Message:
                    {msg.payload.decode()}
                    =====================================
                    """))
                # This is for auto-scrolling of the message box if the user is at the bottom
                # Range is because the values for yview are inconsistent
                # Not a perfect solution, it just snaps back if you don't scroll up enough
                if self.messagesDisplay.yview()[1] < 1.0 and self.messagesDisplay.yview()[1] >= 0.8:
                    self.messagesDisplay.yview(tk.END)
                self.messagesDisplay.config(state=tk.DISABLED)    # Disable text input

            self.after(0, updateMsgBox)

            # Automatically process warnings
            if msg.topic == "simulation/warnings" and not self.handlingWarning:
                threading.Thread(target=self.processWarning, args=(msg,)).start()

        # Make sure connection is established before subscribing
        if not self.isConnected:
            messagebox.showerror("Error", "Please connect to an MQTT broker first")
            return
        
        # Make sure topics field isn't empty
        topics = [topic.strip() for topic in self.subTopicsEntry.get().split(",")]
        if not topics or (len(topics) == 1 and topics[0] == ''):
            messagebox.showerror("Error", "Please input a topic to subscribe to")
            return
        
        # Unsubscribe from previously subscribed topics if any
        if self.subscribeTopics:
            self.client.unsubscribe([topic[0] for topic in self.subscribeTopics])

        # Clear old subscriptions array and add in new subscriptions
        self.subscribeTopics = [(topic, 0) for topic in topics]     # If adding in multiple topics, the QoS must also be specified
        self.client.subscribe(self.subscribeTopics)
        self.client.on_message = on_message
        messagebox.showinfo("Subscribed to topic", f"Subscribed to {[topic[0] for topic in self.subscribeTopics]}")



if __name__ == "__main__":
    window = MqttClientGui()
    window.mainloop()
    window.client.loop_stop()