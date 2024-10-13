from paho.mqtt import client as mqtt_client
import tkinter as tk
from tkinter import ttk
import random

# References: https://www.geeksforgeeks.org/python-gui-tkinter/

def createTabs(window):
    # Create tabs for different sections of client
    tabBar = ttk.Notebook(window)
    tabBar.pack(expand = True, fill = "both")
    
    connectionTab = ttk.Frame(tabBar)
    subscriptionTab = ttk.Frame(tabBar)
    messageTab = ttk.Frame(tabBar)

    tabBar.add(connectionTab, text = "Connection")
    tabBar.add(subscriptionTab, text = "Subscriptions")
    tabBar.add(messageTab, text = "Messages")



def main():
    # Initialise window
    window = tk.Tk()
    window.geometry("600x450")              # 16:9 aspect ratio
    window.title("MQTT Python GUI Client")
    # window.config(background = "#0a0a0a")

    createTabs(window)



    # Connection status
    #connectionStatusFrame = ttk.LabelFrame(window, text = "Connection status", padding = (10, 5))

    # Connection info
    #connectionInfoFrame = 
    



    window.mainloop()

if __name__ == "__main__":
    main()