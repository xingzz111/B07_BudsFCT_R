#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/5/7 14:41
=====================
"""

import zmq
import time
import argparse
import traceback
from threading import Thread
from watchdog.observers import Observer
from rtrpcLib import zmqports, events
from rtrpcLib.common import TesterReporter
from configure import constants as constant
from rtrpcLib.rpc.tinyrpc import HEARTBEAT_INTERVAL, FCT_HEARTBEAT
from rtrpcLib.rpc.rpc_client import RPCClientWrapper
from rtrpcLib.rpc.tinyrpc.protocols.jsonrpc import JSONRPCErrorResponse
from rtrpcLib.rpc.publisher import ZmqPublisher, NoOpPublisher
from rtfixture.fixture_client import ControlBoard
from processes.sigserver import SignerServer


class StateMachineServer(Thread):
    def __init__(self, nSlots=1, nFixtureId=0):
        super(StateMachineServer, self).__init__()
        self._nFixtureId = nFixtureId
        self._nSlots = nSlots
        self.receiving = True
        self.heartbeat_at = 0
        self._poller = zmq.Poller()
        self._testEngineList = self.connect_engines()
        self._sequencerList = self.connect_sequencers()
        ctx = zmq.Context().instance()
        self._fixtureProxy = ControlBoard(nFixtureId)
        self.dispatcher = StateMachineDispatcher(self._sequencerList, self._testEngineList, self._fixtureProxy)
        self.publisher = ZmqPublisher(
            ctx, constant.DEFAULT_TRANSPORT_PROTOCOL_SERVER + str(zmqports.SM_RPC_PUB + nFixtureId),
            "StateMachine_{:02}".format(nFixtureId)
        )
        """ Subscribe PRM_GUI_PUB message """
        _socket = ctx.socket(zmq.SUB)
        _address = constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.PRM_GUI_PUB)
        _socket.connect(_address)
        _socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        self._poller.register(_socket, zmq.POLLIN)
        """ Subscribe Fixture message """
        # _socket = ctx.socket(zmq.SUB)
        # _address = constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.FIXTURE_CTRL_PUB)
        # _socket.connect(_address)
        # _socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        # self._poller.register(_socket, zmq.POLLIN)
        self._reporter = TesterReporter(self.publisher)
        self.observer = Observer()
        self.sigServer = SignerServer(self.createSMEvent)
        self.observer.schedule(self.sigServer, constant.PROJECT_PATH, recursive=True)
        ## sleep 200mS, get zmq some time
        time.sleep(0.2)

    def connect_sequencers(self):
        ctx = zmq.Context().instance()
        proxyList = []
        for slot in range(self._nSlots):
            url = constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.SEQUENCER_PORT + slot)
            pub = NoOpPublisher() ## maybe not useful
            proxy = RPCClientWrapper(url, pub, ctx).remote_server()
            proxyList.append(proxy)
        return proxyList

    def stop_sequencers(self):
        for sequencer in self._sequencerList:
            sequencer.client.transport.shutdown()
            sequencer.client.publisher.stop()

    def connect_engines(self):
        ctx = zmq.Context().instance()
        proxyList = []
        for slot in range(self._nSlots):
            url = constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.TEST_ENGINE_PORT + slot)
            pub = NoOpPublisher()  ## maybe not useful
            proxy = RPCClientWrapper(url, pub, ctx).remote_server()
            proxyList.append(proxy)
        return proxyList

    def shutdown(self):
        for socket in self.__get_sockets():
            self._poller.unregister(socket)
            socket.setsockopt(zmq.LINGER, 0)
            socket.close()
        self.observer.stop()
        self.observer.join()

    def __get_sockets(self):
        tup_list = self._poller.sockets
        sockets = [i[0] for i in tup_list]
        return sockets

    def __signal_heartbeat(self):
        t_now = time.time()
        if t_now >= self.heartbeat_at:
            self.publisher.publish(FCT_HEARTBEAT)
            self.heartbeat_at = t_now + HEARTBEAT_INTERVAL

    def createSMEvent(self, *req):
        event = events.PRM_SM_REP
        self._reporter.create_report(event, req)

    def deal_message(self, message):
        if message.event == events.PRM_SM_REQ:
            func, params = message.data[0], message.data[1:]
            try:
                res = getattr(self.dispatcher, func)(*tuple(params))
            except Exception as e:
                print(traceback.format_exc())
                res = "Error", (e,)
            if res:
                callback, parm = res
                parm = parm if isinstance(parm, tuple) else (parm,)
                self.createSMEvent(callback, parm)

    def run(self):
        self.publisher.publish('Starting...')
        self.heartbeat_at = time.time() + HEARTBEAT_INTERVAL
        self.sigServer.checkAllSignature()
        self.observer.start()
        while self.receiving:
            try:
                socks = dict(self._poller.poll(1000))
                for socket in self.__get_sockets():
                    if socket in socks and socks[socket] == zmq.POLLIN:
                        recv_list = socket.recv_multipart(zmq.NOBLOCK)
                        topic, ts, level, origin, data = [key.decode() for key in recv_list]
                        print(f"topic:{topic}, ts:{ts}, level:{level}, origin:{origin}, data:{data}")
                        message = self._reporter.parse_report(data)
                        self.deal_message(message)
                if not self.sigServer.signatureStatus:
                    self.sigServer.report("signatureEvent", "", False)
            except zmq.ZMQError:
                continue
            self.__signal_heartbeat()
        self.shutdown()


class StateMachineDispatcher:
    def __init__(self, sequencers, engines, fixture=None):
        self._sequencers = sequencers
        self._engines = engines
        self._fixture = fixture

    def are_all_finished(self):
        test_states = [s.status().result != "RUNNING" for s in self._sequencers]
        return all(test_states)

    def test_finish(self):
        pass

    def load(self, path, sub_site='all'):
        info = list()
        for seq in self._sequencers:
            ret = seq.load(path, sub_site)
            if isinstance(ret, JSONRPCErrorResponse):
                info.append(ret.error)
            else:
                info.append(ret.result)
        load_states = [item.rfind('loaded') > 0 for item in info]
        return "loadDone", (all(load_states), info)

    def list_test_plan(self, lines='all'):
        return self._sequencers[0].list(lines).result

    def fixture_start(self):
        self._fixture.fixture_in()

    def fixture_in(self):
        # self._fixture.fixture_in1()
        # time.sleep(5)
        self._fixture.fixture_in()

    def fixture_out(self):
        self._fixture.fixture_out()

    def fixture_down(self):
        self._fixture.fixture_down()
        # time.sleep(1)
        # self._fixture.fixture_fix()

    def fixture_end(self):
        # pass
        # self._fixture.fixture_release()
        # time.sleep(1)
        self._fixture.fixture_reset()

    def abort_test(self):
        self.fixture_end()
        for site in range(len(self._sequencers)):
            self._sequencers[int(site)].abort()
            self._engines[int(site)].reset_all()

    def start_test(self, e_travelers):
        # """fixture action"""
        # self._fixture.fixture_down()
        # """fixture action"""
        if e_travelers is not None:
            for s_site in e_travelers.keys():
                site = int(s_site)
                if not e_travelers[s_site].get("attributes", None):
                    _t = Thread(target=self._sequencers[site].run, args=(None,))
                    _t.start()
                else:
                    _t = Thread(target=self._sequencers[site].run, args=(e_travelers[s_site],))
                    _t.start()
        else:
            self._sequencers[0].run()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--nSlots', help='the number of the sequencer to connect to', type=int, default=1)
    parser.add_argument('-f', '--nFixtureId', help='the fixture id', type=int, default=0)
    args = parser.parse_args()

    server = StateMachineServer(args.nSlots, args.nFixtureId)
    server.start()