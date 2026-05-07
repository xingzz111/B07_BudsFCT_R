import re
import threading
import traceback
from datetime import datetime
from rtrpc.rpc_client import RPCClientWrapper
from rtrpc.tcpClient import TcpClient
from rtrpc.protocols.jsonrpc import JSONRPCServerError, JSONRPCErrorResponse
import zmq
from rtSque.tinyrpc.publisher import  ZmqPublisher


class MixRpc(object):

    rpc_public_api = ["rpc_call"]

    def __init__(self, ip, port, publisher=None):
        # transport = endpoint
        # rpctype = endpoint['type']
        # assert isinstance(transport, dict)
        # assert 'requester' in transport
        # _ip = re.findall("tcp://([0-9\.]+)", endpoint['requester'])[0]
        # _port = re.findall(":([0-9]+)", endpoint['requester'])[0]
        # ctx = zmq.Context().instance()
        self.client = RPCClientWrapper(TcpClient(ip, int(port), publisher), publisher)
        self._rpc_proxy = self.client.get_proxy()
        self.publisher = publisher
        # self.publisher = ZmqPublisher(ctx, "tcp://127.0.0.1:7650".encode(), "MIX_PUB".encode())
        # self.lock = threading.Lock()

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
            if self.publisher:
                self.publisher.publish('[rpc send]  {}({})'.format(method, _strArg))
            # print("rpc-call-args:" + str(args))
            # print("rpc-call-kwargs:" + str(kwargs))
            response = getattr(self._rpc_proxy, method)(*args, **kwargs)
            # print('response====', response)


            if response is None:
                raise JSONRPCServerError('Timed out waiting for response from test engine in test: ' + str(method))
            if isinstance(response, JSONRPCErrorResponse):
                raise response.to_exception_obj()
            if self.publisher:
                self.publisher.publish('[rpc recv]  {}({}) <-<<  {} \n'.format(method, _strArg, str(response.result)))
            # self.rpc_log('[rpc recv]  {}({}) <-<<  {} \n'.format(method, _strArg, str(response.result)))

        except JSONRPCServerError as e:
            print(traceback.format_exc())
            print('[rpc recv]  {}({}) <-<<  {} (Code:{}) \n'.format(method, _strArg, e.message, e.jsonrpc_error_code))
            raise e
        except Exception as e:
            print(traceback.format_exc())
            print(
                '[rpc recv]  {}({}) <-<<  {} \n'.format(method, _strArg, e))
            raise e
            # response.error

        result = response.result

        return result

    def get_transport_timeout(self):
        return self._rpc_proxy.transport.timeout_ms

    def set_transport_timeout(self, timeout):
        self._rpc_proxy.transport.timeout_ms = timeout