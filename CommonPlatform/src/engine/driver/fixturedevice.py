#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import traceback
from driver.fixture_transport import ZmqFixtureClientTransport


class FixtureClient(object):
    rpc_public_api = ["send_reply"]
    def __init__(self, nFixtureId):
        ctx = zmq.Context().instance()
        transport = "tcp://127.0.0.1:" + str(6600 + nFixtureId)
        self.transport = ZmqFixtureClientTransport.create(ctx, transport, 1000)

    def send_reply(self, cmd, expect_reply=True):
        result = ''
        try:
            result = self.transport.send_reply(cmd, expect_reply)
        except Exception as e:
            print(traceback.format_exc())
        return result




if __name__ == '__main__':
    fc = FixtureClient(0)
    fc.send_reply("fixture_down")
