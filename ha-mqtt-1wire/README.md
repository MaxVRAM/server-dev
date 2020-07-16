# 1-Wire Sensor from Remote Pi to Home Assistant via MQTT  
This setup will get readings from a 1-wire temperature sensor hooked up to a Raspberry Pi, then publish the value to a remote Home Assistant server via MQTT.  

<br>

![Temperature Sensor](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_pi.jpg)
> _My test hardware_  
<br>

### Prerequisites
* Home Assistant (HA) Server running on a system within your local network (I'm running HA on a Pi 4 using [hass.io](https://www.home-assistant.io/hassio/))
* A separate Raspberry Pi running some form of Debian distro (I'm using a Pi Zero W running [Raspberry Pi OS Lite](https://www.raspberrypi.org/downloads/raspberry-pi-os/))
* A 1-Wire sensor (like [this](https://www.littlebird.com.au/products/1-wire-digital-temperature-sensor-for-raspberry-pi-assembled-1m "1-wire temperature sensor") super convenient one from [Little Bird Electronics](https://www.littlebird.com.au/) (Australia), pictured above)

> Apart from the above we're going to build this from scratch. You'll just need sudo/admin access on these systems.  

<br>

### MQTT?  
MQTT is a protocol for networked message transmission that has two major components:  
* Publisher, which sends the MQTT messages to the Broker
* Broker, which can recieve messages from multiple Publishers. It's like a message hub.  

<br>

### What are we going to do?
* Set up a Raspberry Pi to read a value from a 1-wire temperature sensor.
* Configure the Pi as an MQTT Publisher that will send the temperature reading to a Broker.
* Set up a broker on our remote HA server to listen to the sensor data.
* Grab the value in Node-RED (on HA)
* Make a temperature entity using that value, which we can put to use anywhere in HA.  
* Create a LoveLace card to display our temperature data.

> I personally use these values to automate "dumb" heaters (without thermostats), allowing me to control my room's temperature by turning the heaters on and off depending on my desired temperature using smart switches.  

<br>

![Home Assistant Card](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_card.jpg)
> _An example Home Assisstant card of multiple temperature readings_
<br>

### Limitations

This code should work fine verbatim while using most standard 1-Wire devices connected to a Raspberry Pi. However, the python script doesn't descriminate between device IDs at all. You'd need to do some extra coding in the Python script if you had more than one sensor connected to the Pi.  

<br>

### Acknowledgement

This python and service script was mostly pulled from here: https://www.earth.li/~noodles/blog/2018/05/rpi-mqtt-temp.html  

<br>
<br>

# Setup Guide
Let's get this show on the road!  

<br>

## Setting up Mosquitto Broker on HA
First we'll setup the receiving end of our MQTT system in HA.

<br>

1. Open HA and navigate to **Supervisor**, then click on the **Add-on store** tab up top.  
2. Seach for "Mosquitto broker", click on the add-on badge and click **INSTALL**. Follow the installation information if needed.  
3. After it's installed, go to the **Configuration** tab and setup your user login. It should look something like this:  
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
> _NOTE: Since we're only publishing the MQTT internally over the local network, we don't need to worry about certificates. However, if you're sending this data over the internet, aka externally, you **reaaaaaalllly** want to be using certificates over the secure port 8883._  

<br>
<br>

## Configuring the Raspberry Pi to read and send the sensor data
Now, let's get the remote Raspberry Pi set up with some dependencies, then check to see if it's reading the 1-Wire sensor we've plugged in.  

<br>

1. Physically install the 1-wire sensor to the Pi's GPIOs as pictured at the top of this page.  
> If you're using a bare sensor without the handy plug-in board like me, you'll most likely need to do some basic electronic circuit setup to get rolling. We're not covering that here, so I'm assuming you've got that side of things sorted.  
2. Use the [configuration menu](https://www.raspberrypi-spy.co.uk/2018/02/enable-1-wire-interface-raspberry-pi/) to enable the 1-Wire bus.  
```bash
sudo raspi-config
```  
3. Install Python and pip (so we can run our MQTT/sensor script):  
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
5. Install the MQTT library for Python:  
```bash
pip3 install paho-mqtt
```  
6. Check the library is installed. **paho-mqtt** should appear in the list:  
```bash
pip3 list
```  
7. Reboot the pi:  
```bash
sudo reboot
```  
8. Check to see if our Pi is reading the sensor by printing 1-Wire devices currently detected:  
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
9. Assuming the sensor is appearing here, navigate into the unique device directory and use **"ls"** to print out what's in the directory. Since we've only connected a single 1-wire sensor, we can use the wildcard **"?"** so we don't have to type in or copy/paste the entire set of random numbers:  
```bash
cd 28-?
ls
```  
> _You should get a list similar to this. We're after the **w1_slave** file:_  
```bash
pi@raspberrypi:/sys/bus/w1/devices/28-03109794634b $ ls
driver  hwmon  id  name  power  subsystem  uevent  w1_slave
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
  
1. Navigate to the directory that we'll store the python script in:  
```bash
cd /usr/local/bin
```  
2. Pull the **[mqtt-temp.py](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/mqtt-temp.py)** script:  
```bash
sudo wget https://github.com/MaxVRAM/server-dev/raw/master/ha-mqtt-1wire/mqtt-temp.py
```  
3. Open the script with **nano** or **vim**:  
```bash
sudo nano mqtt-temp.py
```  
4. Change the details in the script to match your needs. Notably the following:  
* **Broker** (Set to the address IP of your broker)  
* **Port** (If you've changed it from the default MQTT port)  
* **Auth** (Change them to the username and password you entered in your Mosquitto Broker configuration)  
* **pub_topic** (This is the "name" that will be given to the sensor reading. These need to be unique if you're deploying multiple MQTT publishers)  
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
7. Pull the **[mqtt-temp.service](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/mqtt-temp.service)** script:  
```bash
sudo wget https://github.com/MaxVRAM/server-dev/raw/master/ha-mqtt-1wire/mqtt-temp.service
```  
> _You shouldn't need to make any changes here_  
8. **Enable** the service and start it up just to be sure it's running:  
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

Congratulations! You're now publishing the sensor data to your broker. Let's configure an entity in HA to read the value.  

<br>
<br>

## Setup Home Asistant Entity Using Node-RED  
Now that the remote Raspberry Pi and sensor are setup, we can finally focus on the HA side of things.

1. First, let's check that HA is receiving the temperature value by going to **Supervisor** > **Mosquitto Broker** > **Log**.  
> _You should see a log entry saying something like "New connection found from (IP) on port 1883."_  

<br>

### Installing Node-RED integrations  
**Node-RED** is an awesome node-based programming environment we can use inside HA to create complex interactive systems.  

2. Install the base Node-RED add-on for HA by clicking "Supervisor" > "Add-on Store" then search for "Node-RED" and follow the installation guide.  

**HACS** allows us to further extend the possibilities of HA. **HACS** lets us install an additional version of **Node-RED** so we can generate new entities that we can use anywhere within HA.  

3. Install and configure **HACS** using this [guide](https://hacs.xyz/docs/installation/prerequisites).  
4. Click on the **HACS** tab in the left menu and search for "Node-RED". We're now installing an extra integration of **Node-RED** so we can create entities.  
5. Click on the **Node-RED** badge and install.  
6. Restart HA.

<br>

### Building the Node-RED flow and HA entity  
Once **Node-RED** is properly installed, we can create what's called a Node-RED "flow". This is effectively a script that we can deploy on our HA server. We're now going to set up the code to read the sensor data we're sending from our Pi.

7. Open up **Node-RED** (it should be an item in the left menu), then click the hamburger menu in the icon top right corner and select **import**.  
8. Copy the following [Node-RED flow code](mqtt-node-red-receiver.json) and paste it into the Node-RED **import** window:  

<br>

<details>
  <summary><strong><u>Click to display the Node-RED flow code...</u></strong></summary>
  
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

![Node-RED Flow](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_nodepaste.jpg)  
> _After pasting this code, you should have a flow like this (**how many dudes you know flow like this??**)_  

<br>
 
9. The node on the **left** is the **MQTT node**, double click it and configure a new server:  
  - (connection tab) Server: localhost (since Mosquitto is running locally on HA)  
  - (connection tab) Port: 1833  
  - (connection tab) Client ID: node-red-input  
  - (security tab) Username: (the broker user you created when we first installed Mosquitto on HA)
  - (security tab) Password: (the broker password you when we first installed Mosquitto on HA)  
10. Hit **update** to save your server settings, then make sure the server you just configured is selected for the MQTT node. Also make sure the topic field is set to "temperature/1" or whatever you entered in the python script configuration on your Pi. Hit **done**.
11. The node on the **right** is the **Entity node**, this will setup an entity for you to use on your LoveLace dashboard or anywhere else in HA. Double click it and check the following:  
  - Server: Home Assistant  
  - Type: Sensor 
  - State: <msg.> payload 
  - name: room_temperature (This needs to be unqiue. Here, the entity will be named "sensor.room_temperature" in HA)
  - device_class: temperature (More on this in a moment) 
  - unit_of_measurement: °C (You'll need to do some math in your python script if you want to convert this value to F  

> _In HA, device_class is a handy way to assign common frontend characteristics to entities. For more information check this [page](https://www.home-assistant.io/integrations/sensor#device-class)._  
12. Hit "okay" to save.  

<br>

13. Now the time of reckoning. Click the big red **Deploy** button in the top right-hand corner of Node-RED.  
> _If the MQTT node and Mosquitto broker are configured correctly, you'll see a green square and "connected" under the node. Likewise, the temperature reading and time of the last message should be displayed under the entity node. Depicted below_  

<br>

![3 Sensors in Node-RED](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_node.jpg)  
> _An example of what having 3 sensors connected would look like in Node-RED._  

* _If you're not getting the "connected" message under the MQTT node, then Mosquitto or your MQTT node aren't configured correctly._  
* _If updated values and update times aren't appearing under the entity node, then either the messages aren't being sent from the Pi correctly to Mosquitto, or the MQTT node isn't listening to the correct topic_  

<br>

### Check in HA that the entity we've created exists and is receiving data  

14. Check if the entity is listed in your HA entity list. Click the **Configuration** buttom in the bottom right of HA, go to the **Entity** tab, then search for "room_temperature", or whatever you named your entity in Node-RED.  
15. When the entity appears, click on it then hit the icon that looks like 3 sliders in the top right of the panel. This will display a graph with the sensor's readings.  

<br>

![Entity graph in HA](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_graph.jpg)  
> _It should look something like this._ 

<br><br>

## Create a LoveLace card to display the readings  
Now you can add the entity to your LoveLace dashboard like any other input.  

<br>

A very basic setup to display these readings is through a card like this:

```yml
type: sensor
entity: sensor.room_temperature
graph: line
name: Room Temperature
icon: 'mdi:thermometer'
unit: C
```  
> _With this you should get a simple graph to display your temperature readings as a card in HA._

<br>

For something a little more advanced, here's an HA card of my own as a reference to extend your own dashboard. Note that I'm using custom theme colours, so they would need to be either removed or replaced with your own (or hard-coded colour codes). Also, I'm using the custom card [mini-graph-card](https://github.com/kalkih/mini-graph-card), which is available on HACS.  

<br>

<details>
  <summary><strong><u>Click to display my personal card config...</u></strong></summary>

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
</details>

<br>

![Home Assistant Card](https://raw.githubusercontent.com/MaxVRAM/server-dev/master/ha-mqtt-1wire/images/1wire_card.jpg)

<br>
<br>


### Happy home automating!!
