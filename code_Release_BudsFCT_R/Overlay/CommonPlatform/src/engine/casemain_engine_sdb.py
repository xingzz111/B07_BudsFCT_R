from ctypes import c_int
from turtledemo.penrose import start

from rtSque.tinyrpc import RPCClientWrapper
from rtSque.tinyrpc.publisher import NoOpPublisher
from rtSque.tinyrpc.protocols.jsonrpc import JSONRPCSuccessResponse, JSONRPCErrorResponse
from rtrpc.transports.transport import PRMClientTransport

# from sdb.debug import run_shell_with_timeout

TEST_ENGINE_PORT = 6100
bind_url = 'tcp://*'
transport = bind_url + ":" + str(TEST_ENGINE_PORT)
pub = NoOpPublisher()

client = RPCClientWrapper("tcp://127.0.0.1:6100", pub)


def call_rpc(client, cmd, *args, timeout=5000):
    res = client.rpc(cmd, *args, timeout=timeout)
    if isinstance(res, JSONRPCSuccessResponse):
        print(res.result)
        return True
    else:
        print("ERROR: {}".format(res.error))
    return False


