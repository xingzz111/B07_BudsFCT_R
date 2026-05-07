#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import traceback
from rtrpcLib import zmqports
from configure import constants as constant
from rtfixture.fixture_server import FixtureHandler
from rtfixture.fixture_transport import ZmqFixtureClientTransport


class FixtureClient(object):
    def __init__(self, nFixtureId):
        ctx = zmq.Context().instance()
        transport = constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.FIXTURE_CTRL_PORT + nFixtureId)
        self.transport = ZmqFixtureClientTransport.create(ctx, transport, 1000)

    def send_reply(self, cmd, expect_reply=True):
        result = ''
        try:
            result = self.transport.send_reply(cmd, expect_reply)
        except Exception as e:
            print(traceback.format_exc())
        return result


class ControlBoard(FixtureClient):
    def __init__(self, nFixtureId):
        super(ControlBoard, self).__init__(nFixtureId)

    def query(self, cmd, expect_reply=True):
        return self.send_reply(cmd, expect_reply)

    def fixture_reset(self):
        self.query(FixtureHandler.RESET)

    def fixture_out_io(self, status):
        self.query(FixtureHandler.OUT_IO.format(str(status)))

    def fixture_in_io(self, status):
        self.query(FixtureHandler.IN_IO.format(str(status)))

    def fixture_start(self):
        self.query(FixtureHandler.START)

    def fixture_out(self):
        self.query(FixtureHandler.OUT)

    def fixture_down(self):
        self.query(FixtureHandler.DOWN)

    def fixture_up(self):
        self.query(FixtureHandler.UP)

    def fixture_fix(self):
        self.query(FixtureHandler.FIX)

    def fixture_release(self):
        self.query(FixtureHandler.RELEASE)

    def fixture_version(self):
        self.query(FixtureHandler.VERSION)

    def fixture_in(self):
        self.query(FixtureHandler.IN)

    def fixture_in1(self):
        self.query(FixtureHandler.IN1)


if __name__ == '__main__':
    fc = ControlBoard(0)
