import time
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


def call_rpc(client, cmd, *args, timeout=15000):
    res = client.rpc(cmd, *args, timeout=timeout)
    if isinstance(res, JSONRPCSuccessResponse):
        print(res.result)
        return True
    else:
        print("ERROR: {}".format(res.error))
    return False


def reset(client):
    call_rpc(client, "common.start_test")

def fixture_action(client,mode):
    call_rpc(client,"common.fixture_action",mode)


def hall_test(client,mode):
    if not call_rpc(client, "specific.check_hall",mode):
        return False

def btn_test(client,mode):
    if not call_rpc(client, "specific.check_button",mode):
        return False

def led_test(client,net):
    if not call_rpc(client, "specific.check_led",net):
        return False

def esd_test(client,net):
    if not call_rpc(client, "specific.check_esd_specific",net):
        return False


# fixture_action(client,"DOWN")

# fixture_action(client,"UP")
#
#
reset(client)
time.sleep(3)
# hall_test(client,"OFF")
# hall_test(client,"ON")
# hall_test(client,"OFF")

# btn_test(client,"OFF")
#
# btn_test(client,"ON")
#
# btn_test(client,"OFF")

# led_test(client,"CURRENT_SOURCE_TO_DUT_TP5_LED_RHI_B")

# esd_test(client,"CURRENT_SOURCE_TO_DUT_TP12_HI_DATA_L")


# call_rpc(client, "fixture_ctrl.reset")
# call_rpc(client, "fixture_ctrl.cylinder_enable")
# call_rpc(client, "fixture_ctrl.cylinder_disable")