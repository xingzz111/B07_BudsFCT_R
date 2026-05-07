import datetime
import threading

import zmq
from rtSque.tinyrpc import levels
# from rtSque import zmqports
PUB_CHANNEL = '101'





class ZmqPublisher(object):

    rpc_public_api = ["publish"]

    def __init__(self, port, identity):
        ctx = zmq.Context().instance()
        self.publisher = ctx.socket(zmq.PUB)
        self.identity = identity.encode()
        self.publisher.setsockopt(zmq.IDENTITY, self.identity)
        self.publisher.bind("tcp://127.0.0.1:{}".format(port))
        self.lock = threading.Lock()

    def _send(self, ts, id_str, msg, level):
        # zmq socket is not thread safe
        self.lock.acquire()
        self.publisher.send_multipart([str(PUB_CHANNEL).encode(), str(ts).encode(),
                                       str(level).encode(), str(id_str).encode(), str(msg).encode()])
        self.lock.release()

    def stop(self):
        if not self.publisher.closed:
            if zmq is None:
                # the zmq module may have been released by this time
                return
            self.publisher.setsockopt(zmq.LINGER, 0)
            self.publisher.close()

    def publish(self, msg, id_postfix=None, level=levels.DEBUG):
        t = datetime.datetime.now()
        ts = datetime.datetime.strftime(t, '%m-%d_%H:%M:%S.%f')
        id_str = self.identity
        if id_postfix:
            id_str = id_str + '--' + id_postfix
        if hasattr(self, '_send'):
            self._send(ts, id_str, msg, level)


    def __del__(self):
        self.stop()