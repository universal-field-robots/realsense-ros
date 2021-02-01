#!/usr/bin/env python
import subprocess
import re
from bs4 import BeautifulSoup
import urllib2, cookielib


def installFirmware():
    parser = 'html.parser'  # or 'lxml' (preferred) or 'html5lib', if installed
    try:
        req = urllib2.Request("https://dev.intelrealsense.com/docs/firmware-releases", headers={"User-Agent": "Chrome"})
        resp = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print e.fp.read()
    soup = BeautifulSoup(resp, parser, from_encoding=resp.info().getparam('charset'))
    for link in soup.find_all('a', href=True):
        print link['name']

def run_script():
    #insure realsense utilities package is installed
    try:
        subprocess.check_call('sudo apt install librealsense2-utils', shell=True)
    except:
        print("Failed to install librealsense2-utils. Exiting.")
        return

    # Get the firmware versions for each connected camera
    camera_data = []
    try:
        result_string = subprocess.check_output('rs-fw-update -l', shell=True)
        camera_data = getCameraSerialAndFirmware(result_string)
    except:
        print("Failed to call command 'rs-fw-update -l' . Exiting.")
        return
    
    if len(camera_data) < 1:
        print("Failed to detect camera serial and firmware. Exiting.")
        return
    else:
        print("Successfully found %d cameras."%(len(camera_data)))
        print(camera_data)
       

def getCameraSerialAndFirmware(console_text):
    camera_data = []
    for line in console_text.split("\n"):
        if "serial" in line and "firmware" in line:
            serial_num = None
            firmware_num = None
            for item in line.split(","):
                if "serial" in item and "update" not in item: # there are two items which have the word serial in them
                    serial_num = item.split(" ")[-1]
                elif "firmware" in item:
                    firmware_num = item.split(" ")[-1]
            camera_data.append({"serial": serial_num, "firmware": firmware_num})

    return camera_data


if __name__ == "__main__":
    installFirmware()
    #run_script()