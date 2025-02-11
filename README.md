# Horizontal Server Scaling Simulator

This is an example IoT solution for how  web servers can be auto-scaled using the MQTT protocol.

## Contents  

- [Introduction](#horizontal-server-scaling-simulator)  
- [Features](#features)  
- [Components](#components)
- [Prerequisites](#prerequisites) 
- [Installation and Getting Started](#installation-and-getting-started)  
  - [Clone the Repository](#1-clone-the-repository)  
  - [Install Dependencies](#2-install-dependencies)  
  - [Configure Environment Variables](#3-configure-environment-variables)  
  - [Run the Application Components](#4-run-the-application-components)  
- [Command Reference](#command-reference)  
- [Usage](#usage) 
- [Troubleshooting](#troubleshooting)  
- [Acknowledgements](#acknowledgements)  
- [License](#license)  


## Features

- **Graphical User Interface**: Includes a GUI client for monitoring and controlling the simulation.
- **Auto-Scaling Mechanism**: Automatically adjusts the number of active servers based on simulated load conditions.
- **MQTT Communication**: Utilizes MQTT protocol for efficient message exchange between components.
- **Logging**: Includes a logging application to log scaling events.

## Components

- `monitor_app.py`: Monitors system for warnings and triggers scaling actions.
- `logger.py`: Handles logging of messages sent to various MQTT topics.
- `server_cluster.py`: Manages the simulated server cluster, handling the addition and removal of server instances.
- `gui_mqtt_client.py`: Stripped down version of the monitor app for general purpose interactions as an MQTT client.

## Prerequisites

- Python 3.10 or higher
- Access to an MQTT broker
- A working internet connection for MQTT communications

## Installation and Getting Started

### 1. Clone the Repository

Clone the repository and change to the project directory:

```bash
git clone https://github.com/jjv7/Server-Horizontal-Scaling-Sim
cd Server-Horizontal-Scaling-Sim
```

### 2. Install Dependencies

Install the required dependencies using pip. (If you haven’t already, consider creating a virtual environment.):

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a .env file in the root directory of the project. Add the following configuration, adjusting the values as required. Username and password may be omitted if not required:

```env
BROKER=broker.address
MQTT_USERNAME=username
MQTT_PASSWORD=password
```

### 4. Run the Application Components

Open separate terminal windows for each of the following components and run them individually:

- **Monitor Application:**
```bash
python monitor_app.py
```
- **Logger:**
```bash
python logger.py
```
- **Server Cluster:**
```bash
python server_cluster.py
```

## Command Reference

Below is a list of commands and their corresponding actions for controlling the server cluster simulation:

| Command        | Action                                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| `!scalein`     | Scales-in the server cluster, removing one running instance of a server                                |
| `!scaleout`    | Scales-out the server cluster, adding one running instance of a server                                 |
| `!simdecrease` | Biases the server cluster’s average vCPU utilisation to decrease                                       |
| `!simincrease` | Biases the server cluster’s average vCPU utilisation to increase                                       |
| `!simnormal`   | Makes the server cluster’s average vCPU utilisation stable, neither favouring an increase nor decrease |
| `!startlog`    | Starts a log in the datalogger                                                                         |
| `!stoplog`     | Stops a started log in the datalogger                                                                  |

## Usage

After launching all components, interact with the simulation by sending commands (as shown in the command reference). For instance, use the monitor app or another MQTT client to publish `!scaleout` to the simulation/commands topic to add a new server instance to the cluster. The  server cluster component will reflect the changes in real-time.

## Troubleshooting

**Issue**: Unable to connect to the MQTT broker.
Solution: Verify that the `BROKER` address in your `.env` file is correct and that you have network access to the broker. If a username or password is required, make sure these have been included in the .env file and your details are correct.

## Acknowledgements

This project utilises the following external libraries which may be installed via pip:
- [python-dotenv (1.0.1)](https://github.com/theskumar/python-dotenv)
- [paho-mqtt (2.1.0)](https://github.com/eclipse-paho/paho.mqtt.python)

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.