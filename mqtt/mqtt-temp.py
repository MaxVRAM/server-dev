#!/usr/bin/python3

import glob
import time
import datetime
import paho.mqtt.publish as publish         # requires python3-paho-mqtt package

Broker = '192.168.1.50'                     # ip address of your broker
Port = 1883                                 # mqtt broker port, change you've changed this in your broker
Auth = {
    'username': "<mqtt_broker_username>",   # broker's username
    'password': "<mqtt_broker_password>",   # password for the broker's user
}

pub_topic = 'temperature/1'                 # topic to publish sensor reading on, needs to be unqiue per sensor

base_dir = '/sys/bus/w1/devices/'           # navigate here in bash to see what devices are available
device_folder = glob.glob(base_dir + '28-*')[0]  # this script will simply grab any device with 28- at the start
device_file = device_folder + '/w1_slave'

def read_temp():
    valid = False
    temp = 0
    with open(device_file, 'r') as f:
        for line in f:
            if line.strip()[-3:] == 'YES':
                valid = True
            temp_pos = line.find(' t=')     # iterates through the lines to find "t=", which represents the temp value
            if temp_pos != -1:
                temp = float(line[temp_pos + 3:]) / 1000.0

    if valid:
        return temp
    else:
        return None


while True:
    time.sleep(20)                          # wait 20 seconds between reading and publishing
    try:
        temp = read_temp()
        if temp is not None:
            publish.single(pub_topic, str(temp),
                    hostname=Broker, port=Port,
                    auth=Auth)
    except:
        print("Borked")                     # just a placeholder for the except if it doesn't work
