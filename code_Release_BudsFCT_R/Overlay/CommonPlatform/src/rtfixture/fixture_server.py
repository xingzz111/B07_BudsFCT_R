#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import json
import time
import serial
import select
import argparse
import traceback
import re
from threading import Thread, Event
import socket

from setuptools.windows_support import windows_only

from rtrpcLib import zmqports, events
from rtrpcLib.common import TesterReporter
from configure import constants as constant
from configure.constants import FIXTURE_CFG
from configure.constants import SCANNER_CFG
from rtrpcLib.rpc.publisher import ZmqPublisher
from rtfixture.fixture_transport import ZmqFixtureServerTransport


class FixtureHandler:
    RESET = FIXTURE_CFG.get("cmd",{}).get("reset", "fixture_reset")
    START = FIXTURE_CFG.get("cmd",{}).get("start", "fixture_start")
    IN = FIXTURE_CFG.get("cmd",{}).get("mid", "fixture_in")
    IN1 = FIXTURE_CFG.get("cmd", {}).get("mid", "fixture_in1")
    DOWN = FIXTURE_CFG.get("cmd",{}).get("down", "fixture_up")
    UP = FIXTURE_CFG.get("cmd",{}).get("up", "fixture_up")
    OUT = FIXTURE_CFG.get("cmd",{}).get("out", "fixture_out")
    RELEASE = FIXTURE_CFG.get("cmd",{}).get("release", "S:FUN_RELEASE_DUT()")
    VERSION = FIXTURE_CFG.get("cmd",{}).get("version", "S:VERSION()")
    OUT_IO = FIXTURE_CFG.get("cmd", {}).get("out_io", "set_pin_status solenoid_out {}")
    IN_IO = FIXTURE_CFG.get("cmd", {}).get("in_io", "set_pin_status solenoid_in {}")
    
    RESET_OK = "fixture_reset [OK]"
    START_OK = "fixture_in [OK]"
    IN_OK = "fixture_in [OK]"
    DOWN_OK = "fixture_down [OK]"
    UP_OK = "fixture_up [OK]"
    FIX_OK = "fix ok!"
    OUT_OK = "fixture_out [OK]"
    RELEASE_OK = "relaese ok!"
    VERSION_OK = "BuildTime:"

    START_AUTO_SCAN = {
        "msg": "method",
        "method": "BarcodeReadCycleStart",
        "params": {"ReturnDdp": 1},
        "id": "3"
    }

    STOP_AUTO_SCAN = {
        "msg": "method",
        "method": "BarcodeReadCycleStop",
        "params": '',
        "id": "3"
    }



class FixtureServer(Thread):
    def __init__(self, nFixtureId=0):
        super(FixtureServer, self).__init__()
        self.fixture_id = nFixtureId
        self.serving = True
        self._cfg = constant.FIXTURE_CFG
        ctx = zmq.Context()
        self.frontend = ctx.socket(zmq.ROUTER)
        endpoint = constant.DEFAULT_TRANSPORT_PROTOCOL_SERVER + str(zmqports.FIXTURE_CTRL_PORT + nFixtureId)
        self.frontend.bind(endpoint)
        self.transport = ZmqFixtureServerTransport(self.frontend)
        self.publisher = ZmqPublisher(ctx, constant.DEFAULT_TRANSPORT_PROTOCOL_SERVER + str(
            zmqports.FIXTURE_CTRL_PUB + nFixtureId), "Fixture_{:02}".format(nFixtureId))
        self.transport.publisher = self.publisher
        self._reporter = TesterReporter(self.publisher)
        self._fixtureURL = self._cfg.get("url")
        self._baudRate =  self._cfg.get("baudrate", 115200)
        self._timeout =  self._cfg.get("timeout", 5)
        self._strEnd =  self._cfg.get("delimiter", "")
        self.fixtureUart = None
        self.isTesting = False

        self.if_auto_scan = constant.SCANNER_FLAG
        self._is_scan_start = False
        # self._scan_complete = Event()
        if self.if_auto_scan:
            self._scanner_list = []
            self._scanner_cfg = constant.SCANNER_CFG
            for key in self._scanner_cfg.keys():
                self._scanner_list.append(self.connect_scanner(self._scanner_cfg[key].get("ip"),
                                                           self._scanner_cfg[key].get("port"),
                                                           self._scanner_cfg[key].get("timeout")))   

    def post_init(self):
        cmd = FixtureHandler.RESET + self._strEnd
        cmd = cmd.encode() if not isinstance(cmd, bytes) else cmd
        self.fixtureUart.write(cmd)
        time.sleep(3)
        self.fixtureUart.read_all()

    def _control_auto_scan(self, signal):
        if signal == "start":
            self._is_scan_start = True
            self.log(f"[Scan] start auto scan {json.dumps(FixtureHandler.START_AUTO_SCAN)}")
            for scanner in self._scanner_list:
                scanner.send((json.dumps(FixtureHandler.START_AUTO_SCAN) + '\r\n').encode())
        elif signal == "stop":
            self._is_scan_start = False
            self.log(f"[Scan] stop auto scan {json.dumps(FixtureHandler.STOP_AUTO_SCAN)}")
            for scanner in self._scanner_list:
                scanner.send((json.dumps(FixtureHandler.STOP_AUTO_SCAN) + '\r\n').encode())
        else:
            return False
        return True

    def _read_scan_sn(self):
        sn_list = []
        time.sleep(3)
        for k, scanner in enumerate(self._scanner_list):
            sn_str = ["None"]
            try:
                sn_raw_str = scanner.recv(1024).decode()
            except Exception as e:
                sn_raw_str = None
            self.log(f"[Scan] sn_raw_str in slot{k} = {sn_raw_str}")
            if isinstance(sn_raw_str, str) and sn_raw_str:
                sn_raw_list = re.findall("\"BarcodeResult\":\"(\w+)", sn_raw_str)
                if len(sn_raw_list) > 0:
                    for item in sn_raw_list:
                        if item != 'Fail' and item != 'Timeout':
                            sn_str.append(item)
                            break
            sn_list.append(sn_str[-1])
        return sn_list

    def _clear_scanner_buffer(self):
        for k, scanner in enumerate(self._scanner_list):
            try:
                while True:
                    sn_raw_str = scanner.recv(1024)
            except Exception as e:
                print(f"clear_scanner_buffer: {e}")
        return

    def connect(self):
        try:
            self.fixtureUart = serial.Serial(self._fixtureURL, self._baudRate)
            self.log("[Fixture Sever] Open {} Serial Port Success\n".format(self._fixtureURL))
        except Exception as e:
            self.log('[Fixture Sever]' + str(e))
            self.log("[Fixture Sever] Open {} Serial Port Fail \n".format(self._fixtureURL))
            return False
        return True
    
    def connect_scanner(self, ip, port, timeout):
        """建立与扫码枪的TCP连接"""
        try:
            socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_obj.settimeout(timeout)  # 设置超时
            socket_obj.connect((ip, port))
            print(f"Connect to scanner succeed： {ip}:{port}")
            return socket_obj
        except Exception as e:
            print(f"Connect failed: {str(e)}")
            return False

    def run(self):
        """
        run the server for accepting action; a thread for monitor fixture status
        when accept a request from client, the monitor thread should be hang up,
        so use the thread lock
        :return:
        # """
        self.post_init()
        self.transport.heartbeat_at = time.time() + 5
        while self.serving:
            context, message = self.transport.receive_message()
            self.transport.check_heartbeat()
            if message:
                # print(">>>>>>>>>>>>>>>>>>>>>>>>>>message11111")
                # print(message)
                # print(">>>>>>>>>>>>>>>>>>>>>>>>>>message22222")
                cmd = message.encode() if not isinstance(message, bytes) else message
                cmd += self._strEnd.encode()
                if self.if_auto_scan:
                    if "fixture_in1" in message:
                        self._clear_scanner_buffer()
                        self._control_auto_scan("start")
                try:
                    self.fixtureUart.write(cmd)
                    res = b"Success"
                except Exception:
                    print(traceback.format_exc())
                    res = b"Failure"
                self.transport.send_reply(context, cmd + b"-->" + res)
            else:
                reply = self.fixtureUart.read_all()
                event = ''
                if reply:
                    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>reply11111")
                    # print(reply)
                    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>reply22222")
                    reply = reply.decode() if isinstance(reply, bytes) else reply
                    if self.isTesting and FixtureHandler.DOWN_OK in reply:
                        continue
                    if FixtureHandler.DOWN_OK in reply:
                        self.isTesting = True
                        event = 'group_start'
                    # elif FixtureHandler.FIX_OK in reply:
                    #     print("fix reply = ", reply)
                    # elif FixtureHandler.RELEASE_OK in reply:
                    #     print("release reply = ", reply)
                    elif self.isTesting and FixtureHandler.RESET_OK in reply:
                        self.isTesting = False
                        event = 'group_end'
                    elif self.if_auto_scan and self._is_scan_start and FixtureHandler.IN_OK in reply:
                        sn_list = self._read_scan_sn()
                        self._control_auto_scan("stop")
                        self._clear_scanner_buffer()
                        event = '[AutoScan]:' + "@".join(sn_list)
                    elif FixtureHandler.IN_OK in reply:
                        sn_list = ["SLOT1", "SLOT2", "SLOT3", "SLOT4"]
                        event = '[NoScan]:' + "@".join(sn_list)
                if event:
                    self._reporter.create_report(events.PRM_FIXTURE_EVENT, (self.fixture_id, event))
        self.transport.shutdown()

    def stop_serving(self):
        self.publisher.stop()
        self.serving = False

    def log(self, msg):
        if self.publisher:
            print(msg)
            self.publisher.publish(msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--nFixtureId', help='Index of the fixture', type=int, default=0)
    args = parser.parse_args()
    fs = FixtureServer(args.nFixtureId)
    if fs.connect():
        fs.start()
        fs.join()
