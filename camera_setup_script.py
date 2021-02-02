#!/usr/bin/env python
import subprocess
import os
from bs4 import BeautifulSoup
import urllib2
from zipfile import ZipFile
from io import BytesIO


def read_required_firmware_version():
    """
    Reads required firmware version number and corresponding binary file name.

    Returns:
        Tuple: firmware version number and binary file name pair (fw_version_number, fw_file_name)
    """

    file = open('firmware-version.txt', 'r')
    line = file.readlines()[0].rstrip()

    return (line.split(":")[0], line.split(":")[1])


def update_firmware(camera_serial, fw_file_name):
    """
    Updates realsense device based on a serial number and given firwmare file.

    Args:
        camera_serial (str): Serial number of target device.
        fw_file_name (str): Filename of firmware to be uploaded.
    Returns:
        Bool: The return value. True for success, False otherwise.
    """

    download_path = os.environ['HOME']+"/Downloads"

    # check if firmware is already downloaded.
    firmware_found = False
    for file1 in os.listdir(download_path):
        if fw_file_name in file1:
            firmware_found = True

    # if unable to find firmware binary download it.
    if firmware_found:
        print("Using firmware found in '%s'"%(os.path.join(download_path, fw_file_name)))
    else:
        success = download_firmware(fw_file_name, download_path)
        if not success:
            return False

    # upload firmware to device
    try:
        cmd = "rs-fw-update -s %s -f %s" % (camera_serial,
                                            os.path.join(download_path, fw_file_name))
        subprocess.check_call(cmd, shell=True)
        return True
    except:
        print("Failed to update camera firmware using 'rs-fw-update' ")
        return False


def download_firmware(fw_file_name, download_path):
    """
    Fetches frimware from URL and downloads/unzips file to a destination path.

    Args:
        fw_file_name (str): Excepted firmware file name to be foud in URL page.
        download_path (str): Directory destination of file.
    Returns:
        Bool: The return value. True for success, False otherwise.
    """

    print("Attempting to downloading firmware from realsense.")
    parser = 'html.parser'  # or 'lxml' (preferred) or 'html5lib', if installed
    try:
        req = urllib2.Request(
            "https://dev.intelrealsense.com/docs/firmware-releases", headers={"User-Agent": "Chrome"})
        resp = urllib2.urlopen(req)
    except:
        print("Failed to get request page from 'https://dev.intelrealsense.com/docs/firmware-releases'")
        return False

    soup = BeautifulSoup(
        resp, parser, from_encoding=resp.info().getparam('charset'))

    for link in soup.find_all('a', href=True):
        if fw_file_name in link.text:
            try:
                request = urllib2.Request(link['href'], headers={
                                          "User-Agent": "Chrome"})
                responds = urllib2.urlopen(request)
                with ZipFile(BytesIO(responds.read())) as zfile:
                    zfile.extract(fw_file_name, download_path)
                    return True
            except:
                print("Failed to download and unzip firmware.")
                return False

    return False


def get_camera_serial_and_firmware(console_text):
    """
    Scraps console text for serial and firmware information of all connected realsense devices.

    Args:
        console_text (str): input console text contaning all connected device information

    Returns:
        Array[dic]: Array item for each connect devices.  
    """

    camera_data = []
    for line in console_text.split("\n"):
        if "serial" in line and "firmware" in line:
            serial_num = None
            firmware_num = None
            for item in line.split(","):
                if "serial" in item and "update" not in item:  # there are two items which have the word serial in them
                    serial_num = item.split(" ")[-1]
                elif "firmware" in item:
                    firmware_num = item.split(" ")[-1]
            camera_data.append(
                {"serial": serial_num, "firmware": firmware_num})

    return camera_data


def run_script():
    """
    Top level script for updating librealsense libary and firmware for all connected devices.
    """
    # insure realsense utilities package is installed
    try:
        subprocess.check_call(
            'sudo apt install librealsense2-utils', shell=True)
    except:
        print("Failed to install librealsense2-utils. Exiting.")
        return

    # Get the firmware versions for each connected camera
    camera_data = []
    try:
        result_string = subprocess.check_output('rs-fw-update -l', shell=True)
        camera_data = get_camera_serial_and_firmware(result_string)
    except subprocess.CalledProcessError as e:
        print(e)
        print("Failed to call command 'rs-fw-update -l' . Exiting.")
        return

    if len(camera_data) < 1:
        print("Failed to detect camera serial and firmware. Exiting.")
        return
    else:
        print("Successfully found %d cameras." % (len(camera_data)))
        print(camera_data)

    # get name of required frimware version
    fw_version, fw_file_name = read_required_firmware_version()

    for camera in camera_data:
        if fw_version not in camera["firmware"]:
            success  = update_firmware(camera["serial"], fw_file_name)
            if not success:
                return
        else:
            print("Firmware correct on camera " + camera["serial"])


if __name__ == "__main__":
    run_script()
