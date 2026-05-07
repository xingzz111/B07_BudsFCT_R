#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from configure.constants import PROJECT_PATH
if os.name == "nt":
    CONFIGURE = os.path.expanduser('~\\testerconfig')
else:
    CONFIGURE = os.path.expanduser('~/testerconfig')
config_file = os.path.join(CONFIGURE, "zmqports.json")

# config_file = os.path.join(PROJECT_PATH, 'configure', 'zmqports.json')

with open(config_file, 'r') as f:
    config = json.load(f)
    f.close()

PUB_PORT = config["PUB_PORT"] # this is our magic number between a server port and a publisher port
PUB_CHANNEL = str(config["PUB_CHANNEL"]).encode()
DIMENSION_PORTS_SPAN = config["DIMENSION_PORTS_SPAN"]
TEST_ENGINE_PORT = config["TEST_ENGINE_PORT"]
TEST_ENGINE_SUPP_PORT = config["TEST_ENGINE_SUPP_PORT"]
TEST_ENGINE_PUB = config["TEST_ENGINE_PUB"]
TEST_ENGINE_SUPP_PUB = config["TEST_ENGINE_SUPP_PUB"]
SEQUENCER_PORT = config["SEQUENCER_PORT"]
SEQUENCER_PUB = config["SEQUENCER_PUB"]
SEQUENCER_SUPP_PUB = config["SEQUENCER_SUPP_PUB"]
SEQ_MANAGER_PUB = config["SEQ_MANAGER_PUB"]

SEQUENCER_PROXY_PUB = config["SEQUENCER_PROXY_PUB"]
SM_PORT = config["SM_PORT"]
SM_PUB = config["SM_PUB"]
SM_RPC_PUB = config["SM_RPC_PUB"]
SM_PROXY_PUB = config["SM_PROXY_PUB"]
FIXTURE_CTRL_PORT = config["FIXTURE_CTRL_PORT"]
FIXTURE_CTRL_PUB = config["FIXTURE_CTRL_PUB"]
LOGGER_PORT = config["LOGGER_PORT"]
LOGGER_PUB = config["LOGGER_PUB"]
UART_PORT = config["UART_PORT"]
UART_PUB = config["UART_PUB"]
UART2_PORT = config["UART2_PORT"]
UART2_PUB = config["UART2_PUB"]
UART3_PORT = config["UART3_PORT"]
UART3_PUB = config["UART3_PUB"]


DATALOGGER_PORT = config["DATALOGGER_PORT"]
DATALOGGER_PUB = config["DATALOGGER_PUB"]


ARM_PORT = config["ARM_PORT"]
ARM_PUB = config["ARM_PUB"]

DCSD_PORT = config["DCSD_PORT"]
DCSD_PUB = config["DCSD_PUB"]
LOG_PATH_PORT = config["LOG_PATH_PORT"]

AUDIO_PUB = config["AUDIO_PUB"]
SPDIF_PUB = config["SPDIF_PUB"]
HDMI_PUB = config["HDMI_PUB"]
PWR_SEQUENCER_PUB = config["PWR_SEQUENCER_PUB"]
BKLT_PUB = config["BKLT_PUB"]
B2PCLI_PORT = config["B2PCLI_PORT"]
B2PCLI_PUB = config["B2PCLI_PUB"]

PARSE_PORT = 15000
PARSE_PUB = 16000
SLT_PUB = 17000

PRM_PROCESS_CENTER_PUB = 20000
PRM_PROCESS_CENTER_PORT = 20001
PRM_TESTER_CONTROLLER_PUB = 20002
PRM_TESTER_CONTROLLER_PORT = 20003
PRM_GUI_PUB = 20004
PRM_GUI_PORT = 20005
PRM_TESTER_LOGGER_PUB = 20006
PRM_TESTER_LOGGER_PORT = 20007
PRM_SLT_COMMUNICATION_PUB = 20008
PRM_APP_INITIAL_PUB = 20009
PRM_APP_INITIAL_PORT = 20010
