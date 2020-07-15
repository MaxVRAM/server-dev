# Raspberry Pi 1-Wire Temperature Sensor MQTT Publishing to Home Assistant

<br>

This setup will publish readings from a 1-wire temperature sensor (like [these](https://www.littlebird.com.au/products/1-wire-digital-temperature-sensor-for-raspberry-pi-assembled-1m "1-wire temperature sensor") from Little Bird) on a Raspberry Pi to Home Assistant via MQTT.  
MQTT is a protocol for networked message transmission that has two major components:  
* Publisher
* Broker  

The publisher is responsible for sending the MQTT messages to the Broker. The Broker can receive messages from multiple Publishers - it's like a hub.  

<br>

In this guide, we'll be setting up a Raspberry Pi to read values from 1-wire temperature sensor and act as an MQTT publisher. A Broker is setup in Home Assistant on a remote machine that receives the messages and lets up use the temperature readings in our LoveLace dashboard.  

<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_pi.jpg)

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_card.jpg)

<br>


### Test Setup  
_I was using the following setup to create this guide_  
* Raspberry Pi W running [Raspberry Pi OS (32-bit) Lite](https://www.raspberrypi.org/downloads/raspberry-pi-os/)
* 1-Wire Temperature Sensor from [Little Bird](https://www.littlebird.com.au/products/1-wire-digital-temperature-sensor-for-raspberry-pi-assembled-1m "1-wire temperature sensor"). Similar to the DS18B2, only with pullup resistor already fitted.
* Remote Home Assistant on a remote Raspberry Pi using [HASS.IO](https://www.home-assistant.io/hassio/)


### Acknowledgement

This python and service script was mostly pulled from here: https://www.earth.li/~noodles/blog/2018/05/rpi-mqtt-temp.html


### Limitations

This code should work fine verbatim while using most standard 1-Wire devices connected to a Raspberry Pi. However, the python script doesn't descriminate between device IDs at all. The script would need to be adjusted if more than one sensor was hooked up to the Pi.

<br><br>

# Setup Guide

<br>

## Setting up Mosquitto Broker on Home Assistant

1. Open HA and navigate to "Supervisor", then click on the "Add-on store" tab up top.  
2. Seach for "Mosquitto broker", click on the add-on badge and click "INSTALL". Follow the installation information if needed.  
3. After it's installed, go to the "Configuration" tab and setup your user login. It should look something like this:  
```yml
logins:
  - username: <someusername>
    password: <somepassword>
anonymous: false
customize:
  active: false
  folder: mosquitto
certfile: fullchain.pem
keyfile: privkey.pem
require_certificate: false
```
_NOTE: Since we're publishing over the local network, we don't need to worry about the certificates. If you're sending this data over the internet externally, you'll be using the secure ports 8883 and will require certs._  

<br><br>

## Configuring up the environment for the Pi hosting the sensor

1. Mount the 1-wire sensor to the Pi's GPIOs as pictured above
2. Boot up the Pi and enable 1-Wire on the OS using the following command:  
```bash
sudo dtoverlay w1-gpio
```  
(alternatively, you can use the Raspberry Pi [configuration menu](https://www.raspberrypi-spy.co.uk/2018/02/enable-1-wire-interface-raspberry-pi/))  

2. Install Python and pip:  
```bash
sudo apt udpate
sudo apt upgrade
sudo apt install python3
sudo apt install python3-pip
```  

3. Check the version to assure installation:  
```bash
pip3 --version
```  

4. Install the MQTT publishing library for Python:  
```bash
pip3 install paho-mqtt
```  

5. Check the library is installed - paho-mqtt should appear in the list:  
```bash
pip3 list
```  

6. Reboot the pi:  
```bash
sudo reboot
```  

7. List the 1-Wire devices currently detected by the Pi:  
```bash
cd /sys/bus/w1/devices
ls
```  

_The sensor will show up as a directory with a unique device code starting with "28-". My sensor was at "28-03109794634b"._  

```bash
pi@raspberrypi:/sys/bus/w1/devices $ ls
28-03109794634b  w1_bus_master1
```
  
8. Enter the unique device directory: _Since we've only connected a single 1-wire sensor, we can use the wildcard "?"_  
```bash
cd 28-?
ls
```  

9. Run "cat" on the w1_save file to display its reading:  
```bash
cat w1_slave
```  

_This will print a bunch of hex values, with something like "t=14500" at the end. This is your temperature reading! 14.5°C for me._  

```bash
pi@raspberrypi:/sys/bus/w1/devices/28-03109794634b $ cat w1_slave
e8 00 55 05 7f a5 a5 66 16 : crc=16 YES
e8 00 55 05 7f a5 a5 66 16 t=14500
``` 
  
<br><br>
  
## Setting up the MQTT Publisher  
_We'll now setup the script to pull the readings from the sensor and publish it via MQTT._  
  
1. Navigate to the directory we'll store the python script in:  
```bash
cd /usr/local/bin
```  

2. Pull the mqtt-temp.py script:  
```bash
sudo wget https://github.com/MaxVRAM/server-dev/raw/master/ha-mqtt-1wire/mqtt-temp.py
```  

3. Open the script with nano or vim:  
```bash
sudo nano mqtt-temp.py
```  

4. Change the details in the script to match your needs. Notably the following:  
* Broker (Set to the address IP of your broker)  
* Port (If you've changed it from the default MQTT port)  
* Auth (Change them to the username and password you entered in your Mosquitto Broker configuration)  
* pub_topic (This is the "name" that will be given to the sensor reading. These need to be unique if you're deploying multiple MQTT publishers)  

5. Save and exit nano with ctrl-x then press "y"  

<br><br>

## Create a Script Service  
_Let's setup a service so the script runs when the Pi restarts or if the script exits for some reason._  

6. Navitgate to the service directory:  
```bash
cd /lib/systemd/system
```  

7. Pull the mqtt-temp.service script:  
```bash
sudo wget https://github.com/MaxVRAM/server-dev/raw/master/ha-mqtt-1wire/mqtt-temp.service
```  
_You shouldn't need to make any changes here_  

8. Enable the service and start it up just to be sure:  
```bash
sudo systemctl enable mqtt-temp
sudo systemctl start mqtt-temp
```  

9. Restart the Pi and check if the service is running:  
```bash
sudo reboot
```  
```bash
sudo systemctl status mqtt-temp
```  

_If all went well, you should get something like the following:_  
```bash
● mqtt-temp.service - MQTT Temperature sensor
   Loaded: loaded (/etc/systemd/system/mqtt-temp.service; enabled; vendor preset: enabled)
   Active: active (running) since Wed 2020-07-15 11:40:19 AEST; 3s ago
 Main PID: 19617 (mqtt-temp)
   Memory: 5.3M
   CGroup: /system.slice/mqtt-temp.service
           └─19617 /usr/bin/python3 /usr/local/bin/mqtt-temp

Jul 15 11:40:19 raspberrypi systemd[1]: Started MQTT Temperature sensor.
```

<br><br>

Congratulations! You're now publishing the sensor data to your broker. Let's configure an entity in Home Assistant to read the value.  

<br><br>

## Setup Home Asistant Entity Using Node-RED  

1. First check that HA is receiving the value by going back to "Supervisor" > "Mosquitto Broker" > "Log".  
_You should see a log entry saying something like "New connection found from (IP) on port 1883."_  

### Installing Node-RED integrations  
2. Install the base Node-RED add-on for HA by clicking "Supervisor" > "Add-on Store" then search for "Node-RED" and follow the installation guide.  
3. If you haven't got it already, install and configure HACS using the [guide](https://hacs.xyz/docs/installation/prerequisites).  
4. Click on the HACS tab in the left menu and search for "Node-RED". We're now installing an extra integration of Node-RED so we can create entities.  
5. Click on the Node-RED badge and install.  
6. Restart Home Assistant. You should now have a Node-RED tab on the left menu.  

### Building the Node-RED flow and HA entity  
7. Open up Node-RED, and in the top right corner click the hamburger menu and select "import".  
8. Copy the following block and paste it into the Node-RED import window:  

<details>
  <summary>Click to display the Node-RED flow code...</summary>
  
```json
[
    {
        "id": "11915a35.ad0356",
        "type": "tab",
        "label": "MQTT Temperatures",
        "disabled": false,
        "info": ""
    },
    {
        "id": "7fe46076.99bf88",
        "type": "mqtt in",
        "z": "11915a35.ad0356",
        "name": "",
        "topic": "temperature/1",
        "qos": "2",
        "datatype": "auto",
        "broker": "35f8e40a.df5f7c",
        "x": 250,
        "y": 160,
        "wires": [
            [
                "539dec4a.586e34"
            ]
        ]
    },
    {
        "id": "539dec4a.586e34",
        "type": "ha-entity",
        "z": "11915a35.ad0356",
        "name": "Room Temperature",
        "server": "dc09bc1e.a5f7f",
        "version": 1,
        "debugenabled": false,
        "outputs": 1,
        "entityType": "sensor",
        "config": [
            {
                "property": "name",
                "value": "room_temperature"
            },
            {
                "property": "device_class",
                "value": "temperature"
            },
            {
                "property": "icon",
                "value": "mdi:thermometer"
            },
            {
                "property": "unit_of_measurement",
                "value": "°C"
            }
        ],
        "state": "payload",
        "stateType": "msg",
        "attributes": [],
        "resend": true,
        "outputLocation": "",
        "outputLocationType": "none",
        "inputOverride": "allow",
        "x": 650,
        "y": 160,
        "wires": [
            []
        ]
    },
    {
        "id": "35f8e40a.df5f7c",
        "type": "mqtt-broker",
        "z": "",
        "name": "Mosquitto",
        "broker": "localhost",
        "port": "1883",
        "clientid": "node-red-input",
        "usetls": false,
        "compatmode": false,
        "keepalive": "60",
        "cleansession": true,
        "birthTopic": "",
        "birthQos": "0",
        "birthPayload": "",
        "closeTopic": "",
        "closeQos": "0",
        "closePayload": "",
        "willTopic": "",
        "willQos": "0",
        "willPayload": ""
    },
    {
        "id": "dc09bc1e.a5f7f",
        "type": "server",
        "z": "",
        "name": "Home Assistant",
        "addon": true
    }
]
```
  
</details>

<br>
 
9. The node on the left is the MQTT node, double click it and add a server with the details you entered when you first installed Mosquito. For instance:  
```
Connections Tab
---------------
Server: localhost (since Mosquitto is running locally on HA)
Port: 1833
Client ID: node-red-input

Security Tab
------------
Username: <the broker user you created at the start>
Password: <the broker password you created at the start>
```  
10. Hit "update" to save your server settings, then make sure the server you just configured is selected, and the topic is the same string you entered in the python script on your Pi. Hit "done"  
11. The node on the right is the Entity node, this will setup an entity for you to use on your LoveLace dashboard or anywhere else in HA. Double click it and check the following, then hit "okay" to save:  
```
Name: (feel free to change the node's name for your convenience)
Server: Home Assistant
Type: Sensor
State: <msg.> payload

name: room_temperature (This needs to be unqiue. Here, the entity will be named "sensor.room_temperature" in HA)
device_class: temperature (More on this in a moment)
icon: mdi:termometer
unit_of_measurement: °C (You'll need to do some math in your python script if you want to convert this value to F
```  
_In Home Assistant, device_class is a handy way to assign common frontend characteristics to entities. For more information check this [page](https://www.home-assistant.io/integrations/sensor#device-class)._  

<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_node.jpg)

_An example of what having 3 sensors would look like in Node-RED._ 

<br><br>


12. Now the time of reckoning. Click the big red "Deploy" button in the top right-hand corner of Node-RED.  
_If the MQTT node and Mosquitto broker are configured correctly, you'll see a green square and "connected" under the node. Likewise, the temperature reading and time of the last message should be displayed under the entity node_  

<br>

13. Check if the entity is listed in your Home Assistant entity list. Click the "Configuration" buttom in the bottom right of HA, click on the "Entity" tab, then search for "room_temperature", or whatever you named your entity in Node-RED.  
15. Click on the entity, then click the 3 sliders icon in the top right of the entity details popup. This will display a graph with the sensor's readings.  

<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_graph.jpg)

_It should look something like this._ 

<br><br>


## Create a LoveLace card to display the readings   

Now you can add the entity to your LoveLace dashboard like any other input.  

Here's my Home Assistant card as a reference for your own dashboar. Note that I'm using custom theme colours, so they would need to be either removed or replaced with your own (or hard-coded colour codes). Also, I'm using the custom card [mini-graph-card](https://github.com/kalkih/mini-graph-card), which is available on HACS.  

```yml
decimals: 1
entities:
  - color: var(--accent-color)
    entity: sensor.chris_room_temp
    name: Chris' Room
  - color: var(--colour-silver)
    entity: sensor.zen_room_temp
    name: Zen
  - color: var(--colour-asbestos)
    entity: sensor.melbourne_temp
    name: Melbourne
    show_state: true
  - color: var(--colour-midnightblue)
    entity: sensor.night
    name: Night
    y_axis: secondary
font_size: 80
height: 170
hours_to_show: 72
line_width: 2
name: Climate ( 72 hours )
points_per_hour: 1
show:
  extrema: true
  fill: true
  icon: false
  labels: true
  labels_secondary: false
  name: true
  points: false
smoothing: true
type: 'custom:mini-graph-card'
```  
<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_card.jpg)

<br>

Happy home automating!!
