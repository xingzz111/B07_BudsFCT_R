# import re
# import threading
import time
import traceback
# from datetime import datetime
from rtrpc.rpc_client import RPCClientWrapper
from rtrpc.tcpClient import TcpClient
from rtrpc.protocols.jsonrpc import JSONRPCServerError, JSONRPCErrorResponse
# from sdb.sdb import client


class MixRpc(object):

    def __init__(self, ip, port, publisher=None):
        # transport = endpoint
        # rpctype = endpoint['type']
        # assert isinstance(transport, dict)
        # assert 'requester' in transport
        # _ip = re.findall("tcp://([0-9\.]+)", endpoint['requester'])[0]
        # _port = re.findall(":([0-9]+)", endpoint['requester'])[0]
        self.client = RPCClientWrapper(TcpClient(ip, int(port), publisher), publisher)
        self._rpc_proxy = self.client.get_proxy()
        self.publisher = publisher
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
            # if kwargs and 'description' in kwargs.keys():
            #     kwargs.pop('description')
            # if kwargs and 'timeout_ms' in kwargs.keys():
            #     kwargs.pop('timeout_ms')
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


def cb_call(client, cmd, *args, time_out_ms=5000):
    r = client.rpc_call(cmd, *args, timeout=time_out_ms)
    print("cmd: -->{}".format(r))
    return r



def send_read(client, cmd, terminator, retry=3, time_out_ms=2000, timeout_ms=50000):
    for i in range(retry):
        cb_call(client, "com.write", cmd)
        isTimeout, recv = cb_call(client, "com.read_until", terminator, time_out_ms, time_out_ms=timeout_ms)
        print(isTimeout)
        print(recv)
        if not isTimeout and recv:
            return recv
        continue
    return None

def send_read_key_words(client, cmd, expect_keyword , terminator, retry=3, time_out_ms1=5000, time_out_ms2=5000, time_out_ms=50000):
    for i in range(retry):
        cb_call(client, "com.write", cmd)
        isTimeout1, recv1 = cb_call(client, "com.read_until", expect_keyword, time_out_ms1, time_out_ms=time_out_ms)
        if not isTimeout1 and recv1:
            isTimeout2, recv2 = cb_call(client, "com.read_until", terminator, time_out_ms2, time_out_ms=time_out_ms)
            if not isTimeout2 and recv2:
                return recv1 + recv2
        continue
    return None

def read_until(client, terminator, time_out_ms=5000, timeout_ms=50000):
    isTimeout, recv = cb_call(client, "com.read_until", terminator, time_out_ms, time_out_ms=timeout_ms)
    if isTimeout and recv:
        return recv
    return None

def uart_open(client, issigled=True):

    r = cb_call(client, "com.init", issigled)
    print(r)
    return r


if __name__ == "__main__":
    client = MixRpc("169.254.1.32", 7801)

    # print(client.rpc_call("baseboard.reset", timeout_ms=1000))
    uart_open(client)

    print(client.rpc_call("com.read", timeout=1000))

    print(client.rpc_call("mixdevice.sendrecv", "[get_8300_version,]", "\n",timeout=1000))
    print(client.rpc_call("mixdevice.sendrecv", "[stop_trim,]", "CLK trim stop\n", timeout=1000))
    print(client.rpc_call("mixdevice.sendrecv_by_key", "[start_trim,]","CLK trim start", "8300 CLK trim SUCCESS!\n",timeout1_ms=5000, timeout2_ms=20000, timeout=50000))
    # send_read(client, "[get_8300_version,]", "\n")
    # send_read(client, "[get_8300_version,]", "\r\n")

    client.rpc_call("com.deinit", timeout=1000)
    #
    # # send_read(client, "[stop_trim,]", "CLK trim stop")
    #
    # send_read_key_words(client, "[start_trim,]", "CLK trim start","8300 CLK trim SUCCESS!", 3, "2000","40000", timeout_ms=50000)
    # send_read(client, "[stop_trim,]", "CLK trim stop")
    # # send_read_key_words(client, "[switch_app,]","switch panama SUCCESS!","Rst8300", 3, "20000","2000", timeout_ms=50000)
    #
    # # send_read(client, "[get_8300_version,]", "Fw1Version:03.02.02")
    #
    # # cal8300_power()
    # # test1()
    #
    # # mix_rpc_client = MixRpc("169.254.1.32", 7801)
    # # print(mix_rpc_client.rpc_call("mixdevice.reset"))