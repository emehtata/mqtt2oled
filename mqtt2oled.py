#!/usr/bin/python3

# TODO:
# Uusi formaatti näyttöjen datalle
'''
displays = [
  {
    "port": 0,
    "address": 0x3C,
    "topics": [ { "home/ruuvi1", "home/ruuvi2" ],
    "display_rows": []
  },
  {
    "port": 4,
    "address": 0x3C,
    "topics": [ "home/greenhouse", "home/biergarten" ],
    "display_rows": []
  }
]
'''
#

import os
import sys
import time
import json
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%Y-%m-%d %H:%M:%S')

from demo_opts import get_device
from luma.core.interface.serial import i2c, spi, pcf8574
from luma.oled.device import ssd1306
from luma.core.render import canvas
from luma.core.legacy import show_message
from luma.core.legacy.font import proportional, SINCLAIR_FONT
from PIL import ImageFont
import paho.mqtt.client as mqtt
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.WARNING,
    datefmt='%Y-%m-%d %H:%M:%S')

def get_time():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S %d.%m.")
    return current_time

broker_address="192.168.7.8"
broker_port=1883

topics=[ "home/ruuvi1", "home/car-interior", "home/pool", "home/greenhouse" ]
mqtt_topics=[]

display_rows = [{ "Ruuvitags": "Lämpötilat1" }, { "Ruuvitags": "Lämpötilat2" }]

for t in topics:
    mqtt_topics.append((t,0))

device_defs = [
  { "port": 0, "address": 0x3C },
  { "port": 4, "address": 0x3C },
]

def get_dev_port(i):
  return device_defs[i]['port']

def get_dev_address(i):
  return device_defs[i]['address']

devices = []

for d in range(len(device_defs)):
  serial = i2c(port=get_dev_port(d), address=get_dev_address(d))
  devices.append(ssd1306(serial))
# serial = i2c(port=4, address=

font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
font_size = ImageFont.truetype(font_path, 11)
step_size = 13

def remove_vowels(string):
    vowels = "aeiouAEIOU"
    return ''.join(char for char in string if char not in vowels)


def on_message(client, userdata, message):
    global display_rows
    logging.info("on_message")
    payload=str(message.payload.decode("utf-8"))

    jsondata=json.loads(payload)

    logging.info(f"message received: {payload}")
    logging.info(f"message json: {jsondata}")
    logging.info(f"message topic: {message.topic}")
    logging.info(f"message retain flag: {message.retain}")
    display_rows[0][message.topic]=f"{remove_vowels(jsondata['room'])}: {jsondata['temperature']}"
    display_rows[1][message.topic]=f"{remove_vowels(jsondata['room'])}: {jsondata['temperature']}"
    logging.info(f"Room: {jsondata['room']}")
    logging.info(f"Temp: {jsondata['temperature']}")
    logging.info(f"Displaying: {display_rows}:{len(display_rows)}")

    di=0
    for device in devices:
        with canvas(device) as draw:
            logging.info(f"Now drawing to {device}")
            i=0
            rows = display_rows[di]
            logging.info(f"Display {di}: {rows}")
            for r in rows:
                logging.info(f"Row: {r}")
                draw.text((0, step_size*i), rows[r], font=font_size, fill="white")
                i+=1
            draw.text((0, step_size*i), get_time(), font=font_size, fill="white")
        di+=1

def on_connect(client, userdata, flags, rc):
    if rc==0:
        logging.info(f"connected OK Returned code {rc}")
    else:
        logging.error(f"bad connection Returned code {rc}")

    logging.info(f"Subscribe {mqtt_topics}")
    client.subscribe(mqtt_topics)


def on_disconnect(client, userdata, rc):
    if rc != 0:
        logging.error("Unexpected MQTT disconnection. Will reconnect.")
        client.disconnect()
        time.sleep(30)
        logging.info("Connecting.")
        client.connect(broker_address, port=broker_port)
        logging.info("Connected.")


if __name__ == '__main__':
    i=0
    for device in devices:
        with canvas(device) as draw:
            logging.info("Initializing")
            # show_message(device, "Nordpool init", fill="white", font=proportional(SINCLAIR_FONT))
            draw.text((0, 0), f"Ruuvitags {i}", font=font_size, fill="white")
            logging.info("Initialized")
            row=step_size
            for m in mqtt_topics:
                draw.text((0,row), str(m), font=font_size, fill="white")
                row+=step_size
            i+=1
    client = mqtt.Client("OLED") #create new instance
    client.on_message=on_message #attach function to callback
    client.on_connect=on_connect
    client.on_disconnect=on_disconnect
    client.connect(broker_address, port=broker_port) #connect to broker
    client.loop_forever()
