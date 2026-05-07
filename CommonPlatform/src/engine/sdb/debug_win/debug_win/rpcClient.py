# -*- coding: utf-8 -*-
# !/usr/bin/python

import re
import time
import traceback
from datetime import datetime
import threading
from prmcommon import constant
from prmcommon.prmlib.prmrpc.tcpClient import TcpClient
from prmcommon.prmlib.prmrpc.rpc_client import RPCClientWrapper
from prmcommon.prmlib.prmrpc.protocols.jsonrpc import JSONRPCServerError, JSONRPCErrorResponse
# from mix.lynx.rpc.rpc_client import RPCClientWrapper as mixRPCClientWrapper

class MixRpc(object):
    """
    this is the base driver for rpc_client
    user JSONRPCProtocol
    :param1     :port 6100  :int            it's a port for remote
    :param2     :ip_addr    :str            this param is the remote server ip address  default is '127.0.0.1'
    :param3     :publisher  :ZmqPublisher   publish info to which subcriber
    :example:
            client = kRpc(6100,'127.0.0.1',publisher=NoOpPublisher)
            reply = client.call('delay',1000,timeout=1500)
            print reply
            reply = client.call('vendor_id')
            print reply
            reply = client.call('add',10,100)
            print reply
    """
    rpc_public_api = ["rpc_call"]

    def __init__(self, endpoint, publisher=None):
        transport = endpoint
        rpctype = endpoint['type']
        assert isinstance(transport, dict)
        assert 'requester' in transport
        _ip = re.findall("tcp://([0-9\.]+)", endpoint['requester'])[0]
        _port = re.findall(":([0-9]+)", endpoint['requester'])[0]
        # print('===================================debug================>')
        # print('ip:', _ip)
        # print('port', _port)
        # print('===================================debug================>')
        _tcp = TcpClient(_ip, int(_port), publisher)
        if rpctype == "rpc":
            self.client = RPCClientWrapper(_tcp, publisher) 
        # else:
        #     self.client = mixRPCClientWrapper(_ip, _port)

        self._rpc_proxy = self.client.get_proxy()
        self.publisher = publisher
        self.lock = threading.Lock()

    def rpc_log(self, message):
        self.lock.acquire()
        try:
            if constant.DEBUG_MODE:
                print(str(datetime.now()) + ' ' * 3 + message)
            if self.publisher:
                self.publisher.publish(message)
        finally:
            self.lock.release()

    def rpc_call(self, method, *args, **kwargs):
        """
        this function is the wrapper of rpc call
        :param method: string                   this is the function name of remote server
        :param args:   (string,int,float....)   it's the params of remote function
        :param kwargs: (string,int)             timeout or unit in this dict
        :return: result
        """

        try:
            # print('===================================debug================>')
            # print('method', method)
            # print('===================================debug================>')
            if kwargs and 'description' in kwargs.keys():
                kwargs.pop('description')
            if kwargs and 'timeout_ms' in kwargs.keys():
                kwargs.pop('timeout_ms')
            _strArg = ','.join([str(arg) for arg in args] + ['{}={}'.format(k, v) for k, v in kwargs.items()])
            # self.rpc_log('[rpc send]  {}({})'.format(method, _strArg))
            # print("rpc-call-args:" + str(args))
            # print("rpc-call-kwargs:" + str(kwargs))
            response = getattr(self._rpc_proxy, method)(*args, **kwargs)
            # print('response====', response)

            if response is None:
                raise JSONRPCServerError('Timed out waiting for response from test engine in test: ' + str(method))
            if isinstance(response, JSONRPCErrorResponse):
                raise response.to_exception_obj()

            # self.rpc_log('[rpc recv]  {}({}) <-<<  {} \n'.format(method, _strArg, str(response.result)))

        except JSONRPCServerError as e:
            print(traceback.format_exc())
            self.rpc_log('[rpc recv]  {}({}) <-<<  {} (Code:{}) \n'.format(method, _strArg, e.message, e.jsonrpc_error_code))
            raise e
        except Exception as e:
            print(traceback.format_exc())
            self.rpc_log(
                '[rpc recv]  {}({}) <-<<  {} \n'.format(method, _strArg, e))
            raise e
            # response.error

        result = response.result

        return result

    def get_transport_timeout(self):
        return self._rpc_proxy.transport.timeout_ms

    def set_transport_timeout(self, timeout):
        self._rpc_proxy.transport.timeout_ms = timeout


# if __name__ == '__main__':
#     endpoint = {'type': 'rpc', 'requester': 'tcp://169.254.1.100:7801'}
#     client = MixRpc(endpoint)
#     print(client.rpc_call("baseboard.module_init"))