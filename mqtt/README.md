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

