from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv, find_dotenv
import tkinter as tk
from tkinter import ttk
import os
import random

# References: https://www.geeksforgeeks.org/python-gui-tkinter/
#             https://www.w3schools.com/python/python_classes.asp


# Check if a .env file is present
useEnvVariables = False
if find_dotenv():
    useEnvVariables = True
    load_dotenv()


# Make MqttClientGui a child of Tk
class MqttClientGui(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Initialise window
        self.geometry("585x450")              # 16:9 aspect ratio
        self.title("MQTT Python GUI Client")
        self.resizable(False, False)          # Keep window size fixed, so I don't have to do reactive windows

        # Connection info. These will act essentially as global variables within the class
        self.publishTopics = []
        self.subscribeTopics = []
        self.client = mqtt_client.Client(
            client_id=f'gui-mqtt-{random.randint(0, 1000)}',
            callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2
        )
        self.connected = False

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

        self.initConnectionTab(connectionTab)
        self.initMessageTab(messageTab)


    def initConnectionTab(self, connectionTab):
        tabTitle = ttk.Label(connectionTab, text="MQTT Broker Connection Settings", font="Calibri, 18 bold")
        tabTitle.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        
        # Add in host field
        hostFrame = ttk.LabelFrame(connectionTab, text="Host", padding=(10, 10))
        hostFrame.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        
        hostLabel = ttk.Label(hostFrame, text="mqtt://")
        hostLabel.grid(row=0, column=0, padx=(2, 3), pady=(0, 7))
        
        self.hostEntry = ttk.Entry(hostFrame, width=22)                               # Entries will require self, since we need to call them in another function later
        self.hostEntry.grid(row=0, column=1, pady=(0, 7), sticky=tk.W)


        # Add in port field
        portFrame = ttk.LabelFrame(connectionTab, text="Port", padding=(10, 10))
        portFrame.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        
        self.portEntry = ttk.Entry(portFrame, width=30)
        self.portEntry.grid(row=0, column=0, pady=(0, 7), sticky=tk.W)
        self.portEntry.insert(0, 1883)                                      # Default MQTT port


        # Add in username field
        usernameFrame = ttk.LabelFrame(connectionTab, text="Username", padding=(10, 10))
        usernameFrame.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
                
        self.usernameEntry = ttk.Entry(usernameFrame, width=30)
        self.usernameEntry.grid(row=0, column=0, pady=(0, 7), sticky=tk.W)


        # Add in password field
        passwordFrame = ttk.LabelFrame(connectionTab, text="Password", padding=(10, 10))
        passwordFrame.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
                
        self.passwordEntry = ttk.Entry(passwordFrame, width=30, show="*")
        self.passwordEntry.grid(row=0, column=0, pady=(0, 7), sticky=tk.W)


        # Add in preset entries according to the .env file
        if useEnvVariables:
            self.hostEntry.insert(0, os.getenv('BROKER'))
            self.usernameEntry.insert(0, os.getenv('MQTT_USERNAME'))
            self.passwordEntry.insert(0, os.getenv('MQTT_PASSWORD'))


    def initMessageTab(self, messageTab):
        tabTitle = ttk.Label(messageTab, text="Messages", font="Calibri, 18 bold")
        tabTitle.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)


        # Create subscribe section
        subFrame = ttk.LabelFrame(messageTab, text="Subscribe", padding=(10,10))
        subFrame.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

        subTopicsLabel = ttk.Label(subFrame, text="Topics:")
        subTopicsLabel.grid(row=0, column=0, sticky=tk.W)

        subTopicsEntry = ttk.Entry(subFrame)
        subTopicsEntry.grid(row=0, column=1, padx=(22, 0), pady=10, sticky=tk.W)

        subButton = ttk.Button(subFrame, text="Subscribe")
        subButton.grid(row=1, column=0, columnspan=2, pady=10)
        

        # Create publish section
        pubFrame = ttk.LabelFrame(messageTab, text="Publish", padding=(10,10))
        pubFrame.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W + tk.N)

        pubTopicsLabel = ttk.Label(pubFrame, text="Topics:")
        pubTopicsLabel.grid(row=0, column=0, sticky=tk.W + tk.N)

        pubTopicsEntry = ttk.Entry(pubFrame)
        pubTopicsEntry.grid(row=0, column=1, padx=(10, 0), pady=(0, 10), sticky=tk.W)

        pubMessageLabel = ttk.Label(pubFrame, text="Message:")
        pubMessageLabel.grid(row=1, column=0, sticky=tk.W)

        pubMessageEntry = ttk.Entry(pubFrame)
        pubMessageEntry.grid(row=1, column=1, padx=(10, 0), pady=10, sticky=tk.W)

        pubButton = ttk.Button(pubFrame, text="Publish")
        pubButton.grid(row=2, column=0, columnspan=2, pady=10)

        # Create messages section
        messagesFrame = ttk.LabelFrame(messageTab, text="Received Messages", padding=(10,10))
        messagesFrame.grid(row=1, column=1, rowspan=2, padx=10, pady=10, sticky=tk.W)

        self.messagesDisplay = tk.Listbox(messagesFrame, height=17, width=50)
        self.messagesDisplay.grid(row=0, column=0)




if __name__ == "__main__":
    window = MqttClientGui()
    window.mainloop()