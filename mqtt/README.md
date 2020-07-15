## Raspberry Pi 1-Wire Temperature Sensor MQTT Publishing to Home Assistant

This setup will publish readings from a 1-wire temperature sensor (like [these](https://www.littlebird.com.au/products/1-wire-digital-temperature-sensor-for-raspberry-pi-assembled-1m "1-wire temperature sensor") from Little Bird) from a Raspberry Pi to remote MQTT broker. In my case, it was to Home Assistant on another Raspberry Pi on my network.  

![Temperature Sensor](lb_temp_sensor.jpg)


### Test Setup

* Raspberry Pi W running Raspberry Pi OS (32-bit) Lite
* 1-Wire Temperature Sensor from [Little Bird](https://www.littlebird.com.au/products/1-wire-digital-temperature-sensor-for-raspberry-pi-assembled-1m "1-wire temperature sensor"). Similar to the DS18B2, only with pullup resistor already fitted.
* Remote Home Assistant (on a remote Raspberry Pi using HASS.IO)


### Acknowledgement

This python and service script was mostly pulled from here: https://www.earth.li/~noodles/blog/2018/05/rpi-mqtt-temp.html


### Limitations

This code should work fine verbatim while using most standard 1-Wire devices connected to a Raspberry Pi. However, it doesn't descriminate between device IDs, so adjustments would be required if more than one sensor was hooked up to the host PI.



## Setup Guide


### Configure Mosquitto Broker on Home Assistant

1. **Open HA and navigate to "Supervisor", then click on the "Add-on store" tab up top.**  
2. **Seach for "Mosquitto broker", click on the add-on badge and click "INSTALL". Follow the installation information if needed.**  
3. **After it's installed, go to the "Configuration" tab and setup your user login. It should look something like this:**  
```
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



### Pi Prep

1. **Mount the 1-wire sensor to the Pi's GPIOs as pictured above**
2. **Boot up the Pi and enable 1-Wire on the OS using the following command:**  
`sudo dtoverlay w1-gpio`  
(alternatively, you can use the Raspberry Pi [configuration menu](https://www.raspberrypi-spy.co.uk/2018/02/enable-1-wire-interface-raspberry-pi/))  

2. **Install Python and pip:**  
`$ sudo apt udpate`  
`$ sudo apt upgrade`  
`$ sudo apt install python3`  
`$ sudo apt install python3-pip`  

3. **Check the version to assure installation:**  
`pip3 --version`  

4. **Install the MQTT publishing library for Python:**  
`pip3 install paho-mqtt`  

5. **Check the library is installed - paho-mqtt should appear in the list:**  
`pip3 list`  

6. **Reboot the pi:**  
`sudo reboot`  

7. **List the 1-Wire devices currently detected by the Pi:**  
`cd /sys/bus/w1/devices`  
`ls`  
_The sensor will show up as a directory with a unique device code starting with "28-". For example "28-00000482b243"._  

8. **Enter the unique device directory:** _Since we've only connected a single 1-wire sensor, we can use the wildcard "?"_  
`cd 28-?`  
`ls`  

9. **Run "cat" on the w1_save file to display it's reading:**  
`cat w1_slave`  
_This will print a bunch of hex values, with something like "t=19024" at the end. This is your temperature reading! 19°C in this case._  
  
  
### Setup The Scripts  
#### MQTT publisher  
_We'll now setup the script to pull the readings from the sensor and publish it via MQTT._  
  
1. **Navigate to the directory we'll store the python script in:**  
`cd /usr/local/bin/mqtt-temp.py`  

2. **Pull the mqtt-temp.py script:**  
`sudo wget https://github.com/MaxVRAM/server-dev/raw/master/mqtt/mqtt-temp.py`  

3. **Open the script with nano or vim:**  
`sudo nano mqtt-temp.py`  

4. **Change the details in the script to match your needs. Notably the following:**  
* Broker (Set to the address IP of your broker)  
* Port (If you've changed it from the default MQTT port)  
* Auth (Change them to the username and password you entered in your Mosquitto Broker configuration)  
* pub_topic (This is the "name" that will be given to the sensor reading. These need to be unique if you're deploying multiple MQTT publishers)  

5. **Save and exit nano with ctrl-x then press "y"**  

#### Script Service  
_Let's setup a service so the script runs when the Pi restarts or if the script exits for some reason._  

6. **Navitgate to the service directory:**  
`cd /lib/systemd/system`  

7. **Pull the mqtt-temp.service script:**  
`sudo wget https://github.com/MaxVRAM/server-dev/raw/master/mqtt/mqtt-temp.service`  
_You shouldn't need to make any changes here_  

8. **Enable the service and start it up just to be sure:**  
`sudo systemctl enable mqtt-temp`  
`sudo systemctl start mqtt-temp`  

9. **Restart the Pi and check if the service is running:**  
`sudo reboot`  
`sudo systemctl status mqtt-temp`  

_If all went well, you should get something like the following:_  
```
● mqtt-temp.service - MQTT Temperature sensor
   Loaded: loaded (/etc/systemd/system/mqtt-temp.service; enabled; vendor preset: enabled)
   Active: active (running) since Wed 2020-07-15 11:40:19 AEST; 3s ago
 Main PID: 19617 (mqtt-temp)
   Memory: 5.3M
   CGroup: /system.slice/mqtt-temp.service
           └─19617 /usr/bin/python3 /usr/local/bin/mqtt-temp

Jul 15 11:40:19 raspberrypi systemd[1]: Started MQTT Temperature sensor.
```
  

Congratulations! You're now publishing the sensor data to your broker.  
Let's check Home Assistant to finish the setup.  



### Setting Up The Sensor Entity Using Node-RED in Home Assistant  

1. **First check that HA is receiving the value by going back to "Supervisor" > "Mosquitto Broker" > "Log".**  
_You should see a log entry saying something like "New connection found from (IP) on port 1883."_  

2. **If you haven't got it already, install and configure HACS using the [guide](https://hacs.xyz/docs/installation/prerequisites)**  
3. **In HA, click on the HACS tab in the left menu and search for "Node-RED"**  
4. **Click on the Node-RED badge and install**  
5. **Restart Home Assistant. You should now have a Node-Red tab on the left menu**  
6. **Open Node-Red and **
