# 1-Wire Sensor from Remote Pi to Home Assistant via MQTT  
This setup will get readings from a 1-wire temperature sensor (like [these](https://www.littlebird.com.au/products/1-wire-digital-temperature-sensor-for-raspberry-pi-assembled-1m "1-wire temperature sensor") from Little Bird) hooked up to a Raspberry Pi and publish them to a remote Home Assistant server via MQTT.  

<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_pi.jpg)

<br>

### Prerequisites
For this guide I'm assuming you have a Home Assistant Server running on one system, and a separate Raspberry Pi with some form of Debian distro installed and a 1-Wire sensor. You'll need sudo/admin access on these systems. Apart from that, we're going to build this from scratch.  

<br>

### MQTT?
An extremely short background on MQTT to get started:  

MQTT is a protocol for networked message transmission that has two major components:  
* Publisher, which sends the MQTT messages to the Broker
* Broker, which can recieve messages from multiple Publishers. It's like a message hub.  

<br>

### What are we going to do?
We will set up a Raspberry Pi to read a value from a 1-wire temperature sensor. The Pi will act as an MQTT Publisher, and will send the temperature reading to a Broker set up on our Home Assistant server. This server exists on a remote machine from the Pi we're using to read the sensor. Finally, we grab the value using Node-RED (in Home Assistant) and create a temperature entity that we can put to use anywhere we want in Home Assistant.  

I personally use these values to automate "dumb" heaters (without thermostats), allowing me to control my room's temperature by turning the heaters on and off depending on my desired temperature using smart switches.  

In this particular guide, we create a LoveLace card to simply display the temperature.  

<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_card.jpg)

<br>


### Test Setup  
I was using the following setup to create this guide:  
* Raspberry Pi W running [Raspberry Pi OS (32-bit) Lite](https://www.raspberrypi.org/downloads/raspberry-pi-os/)
* 1-Wire Temperature Sensor from [Little Bird](https://www.littlebird.com.au/products/1-wire-digital-temperature-sensor-for-raspberry-pi-assembled-1m "1-wire temperature sensor"). Similar to the DS18B2, only with pullup resistor already fitted.
* Home Assistant setup on a remote Raspberry Pi using [HASS.IO](https://www.home-assistant.io/hassio/)

<br>

### Limitations

This code should work fine verbatim while using most standard 1-Wire devices connected to a Raspberry Pi. However, the python script doesn't descriminate between device IDs at all. The script would need to be adjusted if more than one sensor was hooked up to the Pi.  

<br>

### Acknowledgement

This python and service script was mostly pulled from here: https://www.earth.li/~noodles/blog/2018/05/rpi-mqtt-temp.html  

<br>
<br>

# Setup Guide
Let's get this show on the road!  

<br>

## Setting up Mosquitto Broker on Home Assistant
First we'll setup the receiving end of our MQTT system in HA.

<br>

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
> _NOTE: Since we're publishing over the local network, we don't need to worry about the certificates. If you're sending this data over the internet externally, you'll be using the secure ports 8883 and will require certs._  

<br>
<br>

## Configuring up the environment for the Pi hosting the sensor
Now, let's get the remote Raspberry Pi setup with the required dependencies and check that it's reading the 1-Wire sensor.  

<br>

1. Install the 1-wire sensor to the Pi's GPIOs as pictured at the top of this page.
2. Boot up the Pi and enable 1-Wire using the following command:  
```bash
sudo dtoverlay w1-gpio
```  
> (alternatively, if you're using Raspberry Pi OS like me, you can use the [configuration menu](https://www.raspberrypi-spy.co.uk/2018/02/enable-1-wire-interface-raspberry-pi/), but using the command is just easier)  
3. Install Python and pip (for our MQTT/sensor script):  
```bash
sudo apt udpate
sudo apt upgrade
sudo apt install python3
sudo apt install python3-pip
```  
4. Check the version to assure installation:  
```bash
pip3 --version
```  
5. Install the MQTT publishing library for Python:  
```bash
pip3 install paho-mqtt
```  
6. Check the library is installed. Paho-mqtt should appear in the list:  
```bash
pip3 list
```  
7. Reboot the pi:  
```bash
sudo reboot
```  
8. List the 1-Wire devices currently detected by the Pi:  
```bash
cd /sys/bus/w1/devices
ls
```  
> _The sensor will show up as a directory with a unique device code starting with "28-". My sensor was at "28-03109794634b"._  
```bash
pi@raspberrypi:/sys/bus/w1/devices $ ls
28-03109794634b  w1_bus_master1
```
> _If no directories like this appear, your Pi most likely isn't reading the sensor. There could be a number of things wrong, but that's outside the scope of this guide._  
9. Assuming the sensor is appearing here, navigate into the unique device directory. Since we've only connected a single 1-wire sensor, we can use the wildcard "?" so we don't have to type in or copy/paste the entire set of random numbers:  
```bash
cd 28-?
ls
```  
10. Run "cat" on the w1_slave file to display its reading:  
```bash
cat w1_slave
```  
> _This will print a bunch of hex values, with something like "t=14500" at the end. This is your temperature reading! 14.5°C for me._  

```bash
pi@raspberrypi:/sys/bus/w1/devices/28-03109794634b $ cat w1_slave
e8 00 55 05 7f a5 a5 66 16 : crc=16 YES
e8 00 55 05 7f a5 a5 66 16 t=14500
``` 
<br>
<br>
  
## Setting up the MQTT Publisher  
It's time to get that MQTT/sensor script running so we can pull the readings from the sensor and publish it to our Broker.  

<br>
  
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

<br>
<br>

## Create a Script Service  
For ultimate convenience, we want that Python script we just wrote to run when the Pi restarts or in case the script exits for some reason.  

<br>

6. Navitgate to the service directory:  
```bash
cd /lib/systemd/system
```  
7. Pull the mqtt-temp.service script:  
```bash
sudo wget https://github.com/MaxVRAM/server-dev/raw/master/ha-mqtt-1wire/mqtt-temp.service
```  
> _You shouldn't need to make any changes here_  
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
> _If all went well, you should get something like the following:_  
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

<br>

Congratulations! You're now publishing the sensor data to your broker. Let's configure an entity in Home Assistant to read the value.  

<br>
<br>

## Setup Home Asistant Entity Using Node-RED  
Now that the remote Raspberry Pi and sensor are setup, we can finally focus on the Home Assistant side of things.

1. First, let's check that HA is receiving the temperature value by going to "Supervisor" > "Mosquitto Broker" > "Log".  
> _You should see a log entry saying something like "New connection found from (IP) on port 1883."_  

<br>

### Installing Node-RED integrations  
2. Install the base Node-RED add-on for HA by clicking "Supervisor" > "Add-on Store" then search for "Node-RED" and follow the installation guide.  
3. If you haven't got it already, install and configure HACS using the [guide](https://hacs.xyz/docs/installation/prerequisites).  
4. Click on the HACS tab in the left menu and search for "Node-RED". We're now installing an extra integration of Node-RED so we can create entities.  
5. Click on the Node-RED badge and install.  
6. Restart Home Assistant. You should now have a Node-RED tab on the left menu.  

<br>

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

> After pasting this code, you should have a flow like this (how many dudes you know flow like this??):  

![Node-RED Paste](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_nodepaste.jpg)  

<br>
 
9. The node on the left is the MQTT node, double click it and configure a new server:  
  - Server: localhost (since Mosquitto is running locally on HA)  
  - (connection tab) Port: 1833  
  - (connection tab) Client ID: node-red-input  
  - (security tab) Username: (the broker user you created when we first installed Mosquitto on HA)
  - (security tab) Password: (the broker password you when we first installed Mosquitto on HA)  
10. Hit "update" to save your server settings, then make sure the server you just configured is selected for the MQTT node. Also make sure the topic field is set to "temperature/1" or whatever you entered in the python script configuration on your Pi. Hit "done".
11. The node on the right is the Entity node, this will setup an entity for you to use on your LoveLace dashboard or anywhere else in HA. Double click it and check the following:  
  - Server: Home Assistant  
  - Type: Sensor 
  - State: <msg.> payload 
  - name: room_temperature (This needs to be unqiue. Here, the entity will be named "sensor.room_temperature" in HA)
  - device_class: temperature (More on this in a moment) 
  - unit_of_measurement: °C (You'll need to do some math in your python script if you want to convert this value to F  

> _In Home Assistant, device_class is a handy way to assign common frontend characteristics to entities. For more information check this [page](https://www.home-assistant.io/integrations/sensor#device-class)._  
12. Hit "okay" to save.  

<br>

13. Now the time of reckoning. Click the big red "Deploy" button in the top right-hand corner of Node-RED.  
> _If the MQTT node and Mosquitto broker are configured correctly, you'll see a green square and "connected" under the node. Likewise, the temperature reading and time of the last message should be displayed under the entity node_  

<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_node.jpg)  

_An example of what having 3 sensors connected would look like in Node-RED._ 

<br>

14. Check if the entity is listed in your Home Assistant entity list. Click the "Configuration" buttom in the bottom right of HA, click on the "Entity" tab, then search for "room_temperature", or whatever you named your entity in Node-RED.  
15. Click on the entity, then click the 3 sliders icon in the top right of the entity details popup. This will display a graph with the sensor's readings.  

<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_graph.jpg)  

_It should look something like this._ 

<br><br>


## Create a LoveLace card to display the readings  
Now you can add the entity to your LoveLace dashboard like any other input.  

<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_card.jpg)

<br>

Here's my Home Assistant card as a reference for your own dashboard. Note that I'm using custom theme colours, so they would need to be either removed or replaced with your own (or hard-coded colour codes). Also, I'm using the custom card [mini-graph-card](https://github.com/kalkih/mini-graph-card), which is available on HACS.  

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

Happy home automating!!
