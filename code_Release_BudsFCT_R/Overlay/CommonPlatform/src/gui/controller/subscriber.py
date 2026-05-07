#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/25 22:32
=====================
"""

import re
import zmq
import time
import traceback
from threading import Thread
from rtrpcLib import zmqports
from rtrpcLib import levels
import configure.constants as constant
from rtrpcLib.common import TesterReporter
from rtrpcLib.protocal.sequencerprotocal import SequencerProtocol


class SequencerSubscriberProcess(Thread):
    SITE_PATTERN = re.compile(r'Sequencer_(\d+)')

    def __init__(self, queue, event):
        super(SequencerSubscriberProcess, self).__init__()
        self._queue = queue
        self._close = event
        self._poller = zmq.Poller()

    def unregister_subscribers_of_sequencers(self):
        for socket in self.__get_sockets():
            self._poller.unregister(socket)
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()

    def __get_sockets(self):
        tup_list = self._poller.sockets
        sockets = [i[0] for i in tup_list]
        return sockets

    def run(self):
        ctx = zmq.Context().instance()
        """ state machine subscriber"""
        gui_socket = ctx.socket(zmq.SUB)
        gui_address = constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.SM_RPC_PUB)
        gui_socket.connect(gui_address)
        gui_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        self._poller.register(gui_socket, zmq.POLLIN)
        """ test fixture subscriber """
        fixture_socket = ctx.socket(zmq.SUB)
        fixture_address = constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.FIXTURE_CTRL_PUB)
        fixture_socket.connect(fixture_address)
        fixture_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        self._poller.register(fixture_socket, zmq.POLLIN)

        for site in range(constant.SLOTS):
            """ sequencer subscriber """
            seq_socket = ctx.socket(zmq.SUB)
            seq_address = constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.SEQUENCER_PUB + site)
            seq_socket.connect(seq_address)
            seq_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
            self._poller.register(seq_socket, zmq.POLLIN)
            """ test engine subscriber """
            te_socket = ctx.socket(zmq.SUB)
            te_address = constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.TEST_ENGINE_PUB + site)
            te_socket.connect(te_address)
            te_socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
            self._poller.register(te_socket, zmq.POLLIN)

        _poller_socks = self.__get_sockets()

        while not self._close.is_set():
            try:
                socks = dict(self._poller.poll(200))
                for fd, event in list(socks.items()):
                    if fd in _poller_socks and event == zmq.POLLIN:
                        recv_list = fd.recv_multipart(zmq.NOBLOCK)
                        topic, ts, level, origin, data = [key.decode() for key in recv_list]
                        # print(f"topic:{topic}, ts:{ts}, level:{level}, origin:{origin}, data:{data}")
                        if origin.startswith('StateMachine_'):
                            message = TesterReporter.parse_report(data)
                            self._queue.put((-1, message))
                        elif origin.startswith('TestEngine_') and int(level) == levels.CRITICAL:
                            site = int(origin[11:])
                            message = SequencerProtocol.parse_report(data)
                            self._queue.put((site, message))
                        elif origin.startswith('Sequencer_'):
                            if int(level) == levels.REPORTER or int(level) == levels.CRITICAL:
                                site = int(origin[10:])
                                message = SequencerProtocol.parse_report(data)
                                self._queue.put((site, message))
                            elif data.endswith('SKIP') and int(level) == levels.INFO:
                                site = int(origin[10:])
                                item_start = SequencerProtocol.create_skip_start_report(data)
                                self._queue.put((site, item_start))
                                time.sleep(0.005)  # get gui handle item start same time
                                item_finish = SequencerProtocol.create_skip_finish_report(data)
                                self._queue.put((site, item_finish))
                            # elif int(level) == levels.INFO:
                            #     print data
                        elif origin.startswith('Fixture_'):
                            message = TesterReporter.parse_report(data)
                            self._queue.put((-1, message))
            except zmq.ZMQError as e:
                print(traceback.format_exc())
        self.unregister_subscribers_of_sequencers()
