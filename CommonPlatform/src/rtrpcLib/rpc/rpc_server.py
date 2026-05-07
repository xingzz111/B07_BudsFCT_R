#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
from rtrpcLib.rpc.tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from rtrpcLib.rpc.tinyrpc.transports.zmq import ZmqServerTransport
from rtrpcLib.rpc.tinyrpc.server import RPCServer
from rtrpcLib.rpc.tinyrpc.dispatch import RPCDispatcher
from configure import constants as constant


class RPCServerWrapper:
    def __init__(self, transport, publisher, ctx=None, protocol=None, dispatcher=None):
        self.ctx = ctx if ctx else zmq.Context().instance()
        self.protocol = protocol if protocol else JSONRPCProtocol()
        self.dispatcher = dispatcher if dispatcher else RPCDispatcher()

        if isinstance(transport, ZmqServerTransport):
            self.transport = transport
        else:
            if 'tcp' not in str(transport) or 'ipc' not in str(transport):
                transport = constant.DEFAULT_TRANSPORT_PROTOCOL_SERVER + str(transport)
            self.transport = ZmqServerTransport.create(self.ctx, transport)

        self.publisher = publisher
        self.transport.publisher = publisher

        self.rpc_server = RPCServer(self.transport, self.protocol, self.dispatcher)

        if hasattr(self.dispatcher, 'public'):
            @self.dispatcher.public('::stop::')
            def stop():
                self.rpc_server.serving = False

    # def start_server(self):
    #     self.rpc_server.serving = True

    def stop_server(self):
        self.rpc_server.serving = False
