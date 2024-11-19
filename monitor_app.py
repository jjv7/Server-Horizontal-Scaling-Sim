from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv, find_dotenv
import tkinter as tk
from tkinter import ttk, messagebox
from socket import gaierror
import os
import random
import time
import threading

# References: https://www.geeksforgeeks.org/python-gui-tkinter/
#             https://www.w3schools.com/python/python_classes.asp
#             https://www.geeksforgeeks.org/python-tkinter-messagebox-widget/

# YOU DON'T HAVE TO DO THE FOLLOWING IF YOU HAVE THE .env PROVIDED BY ME
# If monitoring the example application copy the following topics into the fields:
# sub -> public/#,<104547242>/servers/avg_cpu_util,<104547242>/servers/active,<104547242>/warnings
# pub -> <104547242>/commands

# You will then need to press the subscribe button to be subscribed to the sub topics

# Check if a .env file is present
useEnvVariables = False
if find_dotenv():
    useEnvVariables = True
    load_dotenv()


# Make MqttClientGui a child of Tk
class MqttClientGui(tk.Tk):
    def __init__(self):
        super().__init__()                    # Allows the class to make use of Tkinter methods
        
        # Initialise window
        self.geometry("585x450")
        self.title("MQTT Python GUI Client")
        self.resizable(False, False)          # Keep window size fixed, so I don't have to do reactive windows

        # Connection info. These will act essentially as global variables within the class
        self.publishTopics = []
        self.subscribeTopics = []
        self.connected = False
        self.handlingWarning = False

        # Create tabs for different sections of the client
        self.createTabs()


    def createTabs(self):
        # Create notebook container to hold tabs
        tabBar = ttk.Notebook(self)
        tabBar.pack(expand = True, fill = "both")
        
        # Create tabs
        connectionTab = ttk.Frame(tabBar)
        messageTab = ttk.Frame(tabBar)

        # Add tabs to the notebook container
        tabBar.add(connectionTab, text = "Connection")
        tabBar.add(messageTab, text = "Messages")

        # Initialise the UI in each of the tabs
        self.initConnectionTab(connectionTab)
        self.initMessageTab(messageTab)


    def initConnectionTab(self, connectionTab):
        # Title of connection tab
        tabTitle = ttk.Label(connectionTab, text = "MQTT Broker Connection Settings", font = "Calibri, 18 bold")
        tabTitle.grid(row = 0, column = 0, columnspan = 2, padx = 10, pady = 10, sticky = tk.W)
        
        # Add in host field
        hostFrame = ttk.LabelFrame(connectionTab, text = "Host", padding = (10, 10))
        hostFrame.grid(row = 1, column = 0, padx = 10, pady = 10, sticky = tk.W)
        
        hostLabel = ttk.Label(hostFrame, text = "mqtt://")
        hostLabel.grid(row = 0, column = 0, padx = (2, 3), pady = (0, 7))
        
        self.hostEntry = ttk.Entry(hostFrame, width = 22)
        self.hostEntry.grid(row = 0, column = 1, pady = (0, 7), sticky = tk.W)


        # Add in port field
        portFrame = ttk.LabelFrame(connectionTab, text = "Port", padding = (10, 10))
        portFrame.grid(row = 2, column = 0, padx = 10, pady = 10, sticky = tk.W)
        
        self.portEntry = ttk.Entry(portFrame, width = 30)
        self.portEntry.grid(row = 0, column = 0, pady = (0, 7), sticky = tk.W)
        self.portEntry.insert(0, 1883)                                      # Default MQTT port will be automatically input into the field


        # Add in username field
        usernameFrame = ttk.LabelFrame(connectionTab, text = "Username", padding = (10, 10))
        usernameFrame.grid(row = 3, column = 0, padx = 10, pady = 10, sticky = tk.W)
                
        self.usernameEntry = ttk.Entry(usernameFrame, width = 30)
        self.usernameEntry.grid(row = 0, column = 0, pady = (0, 7), sticky = tk.W)


        # Add in password field
        passwordFrame = ttk.LabelFrame(connectionTab, text = "Password", padding = (10, 10))
        passwordFrame.grid(row = 4, column = 0, padx = 10, pady = 10, sticky = tk.W)
                
        self.passwordEntry = ttk.Entry(passwordFrame, width = 30, show = "*")               # show = "*" hides the password
        self.passwordEntry.grid(row = 0, column = 0, pady = (0, 7), sticky = tk.W)


        # Add in connection status section
        connStatFrame = ttk.LabelFrame(connectionTab, text = "Connection Status", padding = (10, 10))
        connStatFrame.grid(row = 2, column = 1, columnspan = 2, padx = 30, pady = 10)

        self.connStatLabel = ttk.Label(connStatFrame, text = "Not Connected", font = "Calibri, 11 bold", background = "gray64", foreground = "red", width = 30, anchor = tk.CENTER)
        self.connStatLabel.grid(row = 0, column = 0, padx = 5, pady = 5)

        # Add connect button to trigger .connect_mqtt()
        connButton = ttk.Button(connectionTab, text = "Connect", command = self.connect_mqtt)
        connButton.grid(row = 3, column = 1, padx = (0, 30), pady = 10, sticky = tk.N + tk.E)

        # Add disconnect button to trigger .disconnect_mqtt()
        disconnButton = ttk.Button(connectionTab, text = "Disconnect", command = self.disconnect_mqtt)
        disconnButton.grid(row = 3, column = 2, pady = 10, sticky = tk.N + tk.W)


        # Add in preset entries into fields according to the .env file
        if useEnvVariables:
            self.hostEntry.insert(0, os.getenv('BROKER'))
            self.usernameEntry.insert(0, os.getenv('MQTT_USERNAME'))
            self.passwordEntry.insert(0, os.getenv('MQTT_PASSWORD'))


    def initMessageTab(self, messageTab):
        # Title of message tab
        tabTitle = ttk.Label(messageTab, text = "Messages", font = "Calibri, 18 bold")
        tabTitle.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = tk.W)


        # Create subscribe section
        subFrame = ttk.LabelFrame(messageTab, text = "Subscribe", padding = (10, 10))
        subFrame.grid(row = 1, column = 0, padx = 10, pady = 10, sticky = tk.W)

        # Create sub topics field
        subTopicsLabel = ttk.Label(subFrame, text = "Topics:")
        subTopicsLabel.grid(row = 0, column = 0, sticky = tk.W)

        self.subTopicsEntry = ttk.Entry(subFrame)
        self.subTopicsEntry.grid(row = 0, column = 1, padx = (22, 0), pady = 10, sticky = tk.W)

        # Button to trigger .subscribe()
        subButton = ttk.Button(subFrame, text = "Subscribe", command = self.subscribe)
        subButton.grid(row = 1, column = 0, columnspan = 2, pady = 10)
        

        # Create publish section
        pubFrame = ttk.LabelFrame(messageTab, text = "Publish", padding = (10, 10))
        pubFrame.grid(row = 2, column = 0, padx = 10, pady = 10, sticky = tk.W + tk.N)

        # Create pub topics field
        pubTopicsLabel = ttk.Label(pubFrame, text = "Topics:")
        pubTopicsLabel.grid(row = 0, column = 0, sticky = tk.W + tk.N)

        self.pubTopicsEntry = ttk.Entry(pubFrame)
        self.pubTopicsEntry.grid(row = 0, column = 1, padx = (10, 0), pady = (0, 10), sticky = tk.W)

        # Message field
        pubMessageLabel = ttk.Label(pubFrame, text = "Message:")
        pubMessageLabel.grid(row = 1, column = 0, sticky = tk.W)

        self.pubMessageEntry = ttk.Entry(pubFrame)
        self.pubMessageEntry.grid(row = 1, column = 1, padx = (10, 0), pady = 10, sticky = tk.W)

        # Button to trigger .publish()
        pubButton = ttk.Button(pubFrame, text = "Publish", command = self.publish)
        pubButton.grid(row = 2, column = 0, columnspan = 2, pady = 10)


        # Create messages box to display received messages
        messagesFrame = ttk.LabelFrame(messageTab, text = "Received Messages", padding = (0, 10))
        messagesFrame.grid(row = 1, column = 1, rowspan = 2, padx = (10, 0), pady = 10, sticky = tk.W)

        # Scrollbar for easy scrolling in the messages box
        scrollbar = tk.Scrollbar(messagesFrame)
        scrollbar.grid(row = 0, column = 1, sticky = tk.NSEW)

        self.messagesDisplay = tk.Text(
            messagesFrame, 
            height = 20, 
            width = 42, 
            font = "Consolas, 9", 
            background = "black", 
            foreground = "white", 
            insertbackground = "white",
            yscrollcommand = scrollbar.set
        )

        self.messagesDisplay.grid(row = 0, column = 0, padx = (10, 0))
        self.messagesDisplay.insert(tk.END, "=====================================\n")  # This is to create the top of the first message
        scrollbar.config(command=self.messagesDisplay.yview)                            # Sets the scrollbar to control the y-position in the messages box
        self.messagesDisplay.config(state=tk.DISABLED)                                  # Disable any input into the messages box

        
        # Add in preset topics into fields according to the .env file
        # You will still need to press the subscribe button to subscribe to the topics
        if useEnvVariables:
            self.subTopicsEntry.insert(0, os.getenv('SUB_TOPICS'))
            self.pubTopicsEntry.insert(0, os.getenv('PUB_TOPICS'))


    def disconnect_mqtt(self):
        def on_disconnect(client, userdata, flags, rc, properties):
            self.connected = False

            # Create notification windows showing the disconnection status
            if rc == 0:
                messagebox.showinfo("Disconnection successful", "Successfully disconnected from MQTT Broker")
            else:
                messagebox.showerror("Disconnection with error", f"Disconnected with an error. Reason code: {rc}\n")
            
            # Change connection status to display not connected
            self.connStatLabel.config(text="Not Connected", foreground="red")

        self.client.on_disconnect = on_disconnect

        # Only attempt disconnecting if client is already connected, or errors happen
        if self.connected:
            self.client.disconnect()


    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc, properties):
            # No actual connection logic here
            # This is mainly for providing info about the status of a new connection

            #  Create notification windows showing the connection status
            if rc == 0:
                self.connected = True
                messagebox.showinfo("Connection successful", "Connected to MQTT Broker!")
                self.connStatLabel.config(text="Connected", foreground="green")     # Change connection status to display connected
            else:
                self.connected = False                                              # Ensure connected is False in case the first connection was successful
                messagebox.showerror("Connection unsuccessful", f"Failed to connect. Reason: {rc}\n")
                self.connStatLabel.config(text="Not Connected", foreground="red")   # Change connection status to display not connected just in case
                self.client.loop_stop()                                             # If this is not here, with the wrong authentication details it will keep trying the connection
        
        # Don't try connecting again if already connected
        if self.connected:
            messagebox.showwarning("Connection active", "Please close the current connection before connecting again")
            return

        # Get inputs from broker and port fields
        broker = self.hostEntry.get()
        port = self.portEntry.get()

        # Check broker and port fields aren't empty
        if not broker and not port:
            messagebox.showerror("Input Error", "Please input a host and port")
            return
        if not broker:
            messagebox.showerror("Input Error", "Please input a host")
            return
        elif not port:
            messagebox.showerror("Input Error", "Please input a port")
            return

        # Cast port value obtained to an int
        try:
            port = int(port)
        except ValueError:
            messagebox.showerror("Input Error", "Port must be a valid integer")
            return

        # Validate port is inside range (1 to 65535)
        if not (0 < port < 65536):
            messagebox.showerror("Input Error", "Port must be between 1 and 65535")
            return
        
        # Get inputs from username and password fields
        username = self.usernameEntry.get()
        password = self.passwordEntry.get()

        # Connect client object to MQTT broker
        self.client = mqtt_client.Client(client_id=f'gui-mqtt-{random.randint(0, 1000)}', callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(username, password)
        self.client.on_connect = on_connect
        
        try:
            self.client.connect(broker, port)
            self.client.loop_start()            # Start networking threads for the mqtt library
        except (TimeoutError, ConnectionRefusedError, gaierror) as err:
            # Display caught connection errors
            messagebox.showerror("Connection Error", f"Connection error: {err}")

    def showWarningHandle(self, command, message):
        messagebox.showinfo("Handling warning", f"Sending `{command}` in response to `{message}`")

    def processWarning(self, msg):
        topic = "<104547242>/commands"
        warning = msg.payload.decode()
        command = ""
        message = ""

        # Handle one warning at a time
        if self.handlingWarning: return
        self.handlingWarning = True

        # Set command depending on warning
        match warning:
            case "Warning: CPU utilisation low":
                command = "!scalein"
                message = "CPU utilisation low"
            case "Warning: CPU utilisation high":
                command = "!scaleout"
                message = "CPU utilisation high"
            case _:
                self.handlingWarning = False
                return  # A valid warning was not received

        # Start a separate thread to show that the warning is being handled
        # If this isn't here, the warning handling will be blocked until the pop-up is closed
        warningHandleNotification = threading.Thread(target = self.showWarningHandle, args = (command, message)) 
        warningHandleNotification.start()

        # Start logging server cluster metrics to keep a history of the alert
        self.client.publish(topic, "!startlog")

        # Resolve the problem the server cluster is experiencing
        self.client.publish(topic, command)

        # Keep logging information for 15 seconds
        # This may not be perfect, another warning may be sent in the time the log is still running
        time.sleep(10)
        self.client.publish(topic, "!stoplog")
        self.handlingWarning = False


    def publish(self):
        # Make sure client is connected before trying publishing
        if not self.connected:
            messagebox.showerror("Error", "Please connect to an MQTT broker first")
            return

        # Obtain publish topics
        # Accepts CSVs
        # Strip gets rid of the whitespaces, so ", " is acceptable
        self.publishTopics = [topic.strip() for topic in self.pubTopicsEntry.get().split(",")]
        
        # Check that publish topics aren't empty
        if len(self.publishTopics) == 1 and self.publishTopics[0] == '':
            messagebox.showerror("Error", "Please input a topic to publish to")
            return
        
        msg = self.pubMessageEntry.get()            # Get message from field

        # Make sure message field wasn't empty
        if not msg:
            messagebox.showerror("Error", "Please input a message to publish")
            return
        
        # Publish message to all the topics specified
        for topic in self.publishTopics:
            result = self.client.publish(topic, msg)
            
            # Show status of message sent in notification
            status = result[0]
            if status == 0:
                messagebox.showinfo("Message Published", f"Sent `{msg}` to topic `{topic}`")
            else:
                messagebox.showinfo("Error", f"Failed to send message to topic `{topic}`")


    def subscribe(self):
        def on_message(client, userdata, msg):
            self.messagesDisplay.config(state=tk.NORMAL)      # Enable text input

            # Display message received in message box
            self.messagesDisplay.insert(tk.END, f"{msg.topic}")
            self.messagesDisplay.insert(tk.END, f"\nQoS: {msg.qos}")
            self.messagesDisplay.insert(tk.END, f"\nRetained?: {msg.retain}")
            self.messagesDisplay.insert(tk.END, f"\n\nMessage:\n")
            self.messagesDisplay.insert(tk.END, msg.payload.decode())
            self.messagesDisplay.insert(tk.END, "\n=====================================\n")
            
            # This is for automatic scrolling of the textbox if the user is at the bottom
            # Range is because the values for yview are inconsistent
            # This isn't a perfect solution, since you will just snap back if you don't scroll up far enough
            if self.messagesDisplay.yview()[1] < 1.0 and self.messagesDisplay.yview()[1] >= 0.8:
                self.messagesDisplay.yview(tk.END)

            self.messagesDisplay.config(state=tk.DISABLED)    # Disable text input

            # Automatically respond to warnings
            if msg.topic == "<104547242>/warnings" and not self.handlingWarning:
                warningProcess = threading.Thread(target = self.processWarning, args = (msg,))
                warningProcess.start()

        # Make sure connection is established before subscribing
        if not self.connected:
            messagebox.showerror("Error", "Please connect to an MQTT broker first")
            return
        
        # Make sure topics field isn't empty
        if not self.subTopicsEntry.get():
            messagebox.showerror("Error", "Please input a topic to subscribe to")
            return
        
        # Unsubscribe from previously subscribed topics if any
        if self.subscribeTopics:
            self.client.unsubscribe([topic[0] for topic in self.subscribeTopics])

        # Clear old subscriptions array and add in new subscriptions
        self.subscribeTopics = []
        for topic in [subTopic.strip() for subTopic in self.subTopicsEntry.get().split(",")]:   # This also accepts CSVs
            self.subscribeTopics.append((topic, 0))                                             # To subscribe to multiple topics, we need to also set the QoS (0)
        
        self.client.subscribe(self.subscribeTopics)
        self.client.on_message = on_message

        # Show all topics subscribed
        messagebox.showinfo("Subscribed to topic", f"Subscribed to {[topic[0] for topic in self.subscribeTopics]}")



if __name__ == "__main__":
    window = MqttClientGui()
    window.mainloop()
    window.client.loop_stop()