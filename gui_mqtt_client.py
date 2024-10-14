from paho.mqtt import client as mqtt_client
import tkinter as tk
from tkinter import ttk
import random

# References: https://www.geeksforgeeks.org/python-gui-tkinter/

# Make MqttClientGui a child of Tk
class MqttClientGui(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Initialise window
        self.geometry("800x450")              # 16:9 aspect ratio
        self.title("MQTT Python GUI Client")
        self.resizable(False, False)          # Keep window size fixed, so I don't have to do reactive windows

        # Connection info. These will act essentially as global variables within the class
        self.publishTopics = []
        self.subscribeTopics = []
        self.client = mqtt_client.Client(client_id=f'gui-mqtt-{random.randint(0, 1000)}', callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
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

        self.initConnectionTab()

    def initConnectionTab(self):
        pass


if __name__ == "__main__":
    window = MqttClientGui()
    window.mainloop()