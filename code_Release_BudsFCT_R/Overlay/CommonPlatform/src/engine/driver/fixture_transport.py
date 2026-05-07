#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq
import time
from rtSque.tinyrpc import FCT_HEARTBEAT
from rtSque.tinyrpc.transports import  ServerTransport,ClientTransport

HEARTBEAT_INTERVAL = 5


class ZmqFixtureServerTransport(ServerTransport):
    """Server transport based on a :py:const:`zmq.ROUTER` socket.

    :param socket: A :py:const:`zmq.ROUTER` socket instance, bound to an
                   endpoint.
    """

    def __init__(self, socket, polling_milliseconds=0):
        self.publisher = None
        self.socket = socket
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.polling_milliseconds = polling_milliseconds
        self.heartbeat_at = time.time()

    def broadcast(self, msg):
        if self.publisher:
            msg = msg.encode() if not isinstance(msg, bytes) else msg
            self.publisher.publish(msg)
        # TODO: HB shall be out per 5sec or only needed as NOP when PUB idle?

    def check_heartbeat(self):
        t_now = time.time()
        if t_now >= self.heartbeat_at:
            self.broadcast(FCT_HEARTBEAT.encode())
            self.heartbeat_at = time.time() + HEARTBEAT_INTERVAL

    def receive_message(self):
        """Asynchronous poll socket"""
        socks = dict(self.poller.poll(1000))
        if socks.get(self.socket) == zmq.POLLIN:
            msg = self.socket.recv_multipart(zmq.NOBLOCK)
            context, message = msg[:-1], msg[-1]
            message = message.decode() if isinstance(message, bytes) else message
            self.broadcast('received: ' + message)
        else:
            context, message = None, None
        return context, message

    def send_reply(self, context, reply):
        self.socket.send_multipart(context + [reply])
        reply = reply.decode() if isinstance(reply, bytes) else reply
        self.broadcast('response: ' + reply)

    @classmethod
    def create(cls, zmq_context, endpoint, polling_milliseconds=0):
        """Create new server transport.

        Instead of creating the socket yourself, you can call this function and
        merely pass the :py:class:`zmq.core.context.Context` instance.

        By passing a context imported from :py:mod:`zmq.green`, you can use
        green (gevent) 0mq sockets as well.

        :param zmq_context: A 0mq context.
        :param endpoint: The endpoint clients will connect to.
        """
        socket = zmq_context.socket(zmq.ROUTER)
        socket.bind(endpoint)
        return cls(socket, polling_milliseconds)

    def shutdown(self):
        if not self.socket.closed:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()


class ZmqFixtureClientTransport(ClientTransport):
    """Server transport based on a :py:const:`zmq.ROUTER` socket.

    :param socket: A :py:const:`zmq.ROUTER` socket instance, bound to an
                   endpoint.
    """

    def __init__(self, socket, polling_milliseconds=0):
        self.publisher = None
        self.socket = socket
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.polling_milliseconds = polling_milliseconds

    def broadcast(self, msg):
        if self.publisher:
            msg = msg.encode() if not isinstance(msg, bytes) else msg
            self.publisher.publish(msg)
        # TODO: HB shall be out per 5sec or only needed as NOP when PUB idle?

    def send_message(self, message, expect_reply=True):
        message = message.encode() if not isinstance(message, bytes) else message
        self.socket.send(message)
        reply = ""
        if expect_reply:
            socks = dict(self.poller.poll(self.polling_milliseconds))
            if socks.get(self.socket) == zmq.POLLIN:
                reply = self.socket.recv()
        else:
            return
        reply = reply.decode() if isinstance(reply, bytes) else reply
        self.broadcast('received: ' + reply)
        return reply

    send_reply = send_message

    @classmethod
    def create(cls, zmq_context, endpoint, polling_milliseconds=500):
        """Create new client transport.

        Instead of creating the socket yourself, you can call this function and
        merely pass the :py:class:`zmq.core.context.Context` instance.

        By passing a context imported from :py:mod:`zmq.green`, you can use
        green (gevent) 0mq sockets as well.

        :param zmq_context: A 0mq context.
        :param endpoint: The server endpoint.
        """
        socket = zmq_context.socket(zmq.DEALER)
        socket.connect(endpoint)
        return cls(socket, polling_milliseconds)

    def shutdown(self):
        if not self.socket.closed:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()

