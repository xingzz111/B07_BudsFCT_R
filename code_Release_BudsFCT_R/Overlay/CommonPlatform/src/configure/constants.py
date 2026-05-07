#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/25 13:35
=====================
"""

import os
import sys
import json
import platform


IS_APP = hasattr(sys, "_MEIPASS")
PLATFORM = platform.system()

def projectPath():
    if IS_APP:
        if PLATFORM in ("Windows", "Linux"):
            path_list = os.path.realpath(sys.argv[0]).split(os.path.sep)[:-1]
            base_path = f"{os.path.sep}".join(path_list)
        elif PLATFORM == "Darwin":
            path_list = os.path.realpath(sys.argv[0]).split(os.path.sep)[:-3] + ["project"]
            base_path = f"{os.path.sep}".join(path_list)
    else:
        path_list = os.path.abspath(__file__).split(os.path.sep)[:-2]
        base_path = f"{os.path.sep}".join(path_list)
    return base_path

PROJECT_PATH = projectPath()
# if os.name == "nt":
#     CONFIGURE = os.path.expanduser('~\\testerconfig')
# else:
#     CONFIGURE = os.path.expanduser('~/testerconfig')
# CONSTANT_FILE = os.path.join(CONFIGURE, "config.json")

CONFIGURE = os.path.join(PROJECT_PATH, "configure")
CONSTANT_FILE = os.path.join(CONFIGURE, "constant.json")
PROFILE = os.path.join(PROJECT_PATH, "profile")
SIG_PATH = os.path.join(PROJECT_PATH, "encrypted.sig")

if IS_APP:
    IMAGE_PATH = os.path.join(sys._MEIPASS, "img")
else:
    IMAGE_PATH = os.path.join(PROJECT_PATH, "gui", "img")
GLockPng = os.path.join(IMAGE_PATH, "green_lock.png")
RLockPng = os.path.join(IMAGE_PATH, "red_lock.png")
LogoPng = os.path.join(IMAGE_PATH, "Bose_Logo.png")
UserPng = os.path.join(IMAGE_PATH, "user.png")
ResetPng = os.path.join(IMAGE_PATH, "reset.png")
ICONPATH = os.path.join(IMAGE_PATH, "ossns_icon.ico")


ResetButtonQSS = '''QPushButton
{
    border-image:url(reset.png);
    font-family:PingFang HK;
    border-radius:5px;

}

QPushButton:hover
{
    background-color:rgb(220 , 220 , 220);
}

QPushButton:pressed
{
    background-color:rgb(200 , 200 , 200);
    padding-left:3px;
    padding-top:3px;
}'''.replace("reset.png", ResetPng)

with open(CONSTANT_FILE, "r") as f:
    const = json.load(f)
GROUP = const.get("group", 1)
SLOTS = const.get("slots", 1)
FIXTURE = const.get("fixture", 1)
SIMULATE = const.get("simulate", True)
SCANNER_FLAG = const.get("autoscan", True)
HSM = const.get("HSM", False)
yubi_path = const.get("yubi_path", "C:\\SMA\\madi-v0.13.0-0-g00592a1.exe")
PROJECT = const.get("project", "CommonPlatform")
FIXTURE_CFG = const.get("fixture_config")
SCANNER_CFG = const.get("scanner_config")
USB_PORT_CONFIG = const.get("usb_port_config")
GUI_CFG = const.get("gui")

CHECK_SN_LENGTH = GUI_CFG.get("check_sn_length", False)
SN_LENGTH = GUI_CFG.get("sn_length", 14)
CHECK_SN_PATTERN = GUI_CFG.get("check_sn_pattern",False)
SN_PATTERN = GUI_CFG.get("sn_pattern",None)

HEADERS = [
    "TestName",
    "SubTestName",
    "SubSubTestName",
    "LL",
    "UL",
    "Unit",
    "Slot1"
]

FAKEDATA = [
    ["Fake", "A", "1", 95, 100, "%", ""],
    ["Fake", "A", "2", 95, 100, "%", ""],
    ["Fake", "A", "3", 95, 100, "%", ""],
    ["Fake", "A", "4", 95, 100, "%", ""],
    ["Fake", "A", "5", 95, 100, "%", ""],
    ["Fake", "A", "6", 95, 100, "%", ""],
]


class State:
    IDLE = "IDLE"
    READY = "READY"
    RUNNING = "RUNNING"
    PASS = "PASS"
    FAIL = "FAIL"
    DISABLE = "DISABLE"


ZMQ_PATH = "ipc:///tmp/.localhost:"
# DEFAULT_TRANSPORT_PROTOCOL_SERVER = "ipc:///tmp/.localhost:"  # 'tcp://*:'
# DEFAULT_TRANSPORT_PROTOCOL_CLIENT = "ipc:///tmp/.localhost:"  # 'tcp://localhost:'

DEFAULT_TRANSPORT_PROTOCOL_SERVER = "tcp://127.0.0.1:"
DEFAULT_TRANSPORT_PROTOCOL_CLIENT = "tcp://127.0.0.1:"
