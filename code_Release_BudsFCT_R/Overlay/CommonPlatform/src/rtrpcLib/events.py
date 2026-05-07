#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/25 23:04
=====================
"""

SEQUENCE_START = 0
SEQUENCE_END = 1
ITEM_START = 2
ITEM_FINISH = 3
ATTRIBUTE_FOUND = 4
REPORT_ERROR = 5
UOP_DETECT = 6
SEQUENCE_LOADED = 7
IP_START_FAIL_DETECT = 8
ZIP_LOGS_END = 9

PRM_SM_REQ = 100
PRM_SM_REP = 101
PRM_FIXTURE_EVENT = 102
ILLEGAL_EVENT = 200


def getEvents(event_type):
    if event_type == 0:
        return 'SEQUENCE_START'
    elif event_type == 1:
        return 'SEQUENCE_END'
    elif event_type == 2:
        return 'ITEM_START'
    elif event_type == 3:
        return 'ITEM_FINISH'
    elif event_type == 4:
        return 'ATTRIBUTE_FOUND'
    elif event_type == 5:
        return 'REPORT_ERROR_OCCURRED'
    elif event_type == 6:
        return 'UOP_DETECTED'
    elif event_type == 7:
        return 'SEQUENCE LOADED'
    elif event_type == 8:
        return "IP_START_FAIL_DETECT"
    elif event_type == 9:
        return "ZIP_LOGS_END"
    elif event_type == 100:
        return "PRM_SM_REQ"
    elif event_type == 101:
        return "PRM_SM_REP"
    else:
        return 'UNKNOWN event type: ' + str(event_type)