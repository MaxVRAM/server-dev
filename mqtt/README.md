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

### Prep

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
We'll now setup the script to pull the readings from the sensor and publish it via MQTT.  
  
10. **Navigate to the directory we'll store the python script in:**  
`cd /usr/local/bin/mqtt-temp.py`  

11. **Pull the mqtt-temp.py script:**  
`sudo wget https://github.com/MaxVRAM/server-dev/raw/master/mqtt/mqtt-temp.py`  

12. **Open the script with nano or vim:**  
`sudo nano mqtt-temp.py`  

13. **Change the details in the script to match your needs. Notably the following:**  
* Broker (set to the address IP of your broker)  
* Port (if you've changed it from the default MQTT port)  
* Auth (set the username and password to the details registered in your broker)  
* pub_topic (these need to be unique if you're deploying multiple MQTT publishers)  

14. **Save and exit nano with ctrl-x then press "y"**  

Let's setup a service so the script runs when the Pi restarts or if the script exits for some reason.  

15. **Navitgate to the service directory:**  
`cd /lib/systemd/system`  

11. **Pull the mqtt-temp.service script:**  
`sudo wget https://github.com/MaxVRAM/server-dev/raw/master/mqtt/mqtt-temp.service`  
_You shouldn't need to make any changes here_  

12. **Enable the service and start it up just to be sure:**  
`sudo systemctl enable mqtt-temp`  
`sudo systemctl start mqtt-temp`  

13. **Restart the Pi and check if the service is running:**  
`sudo reboot` 
`sudo systemctl status mqtt-temp`  

If all went well, you should get something like the following:  
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
