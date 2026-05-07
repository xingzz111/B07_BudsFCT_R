import os
import datetime
import time
import json


from urllib import request
from xml.etree import ElementTree

user_home = os.path.expanduser('~')
mes_config_path = f"{user_home}/testerconfig/mes_config_for_logger.json"

with open(mes_config_path, "r") as f:
    CONST_OBJ = json.load(f)


STATION_CFG = CONST_OBJ.get("station_info")
MES_CFG = CONST_OBJ.get("mes_config")


HEARTBEAT_INTERVAL = MES_CFG.get("heartbeat_interval", 5)
FCT_HEARTBEAT = "FCT_HEARTBEAT"

MES_HOST = MES_CFG.get("host", "http://10.32.23.123/MESWebService/webservice.asmx/")
MES_HEADER = MES_CFG.get("header", {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate"
    })
MES_VERSION = MES_CFG.get("version", "V1.0")
MES_JIG_NO = MES_CFG.get("jig_no", "JIG_NO123456")

UPLOAD_SWITH = MES_CFG.get("upload_swith", False)
UPLOAD_ONLY_PASS = MES_CFG.get("upload_only_pass", False)

LOG_FILE_PATH = MES_CFG.get("log_file_path", "D:\\vault\\StationLog")
MES_LOG_PATH = MES_CFG.get("mes_log_path", "D:\\vault\\StationLog\\mes")
DUT_LOG_PATH = MES_CFG.get("dut_log", "D:\\vault\\StationLog\\dut_log")
MES_DUT_LOG_PATH = MES_CFG.get("mes_dut_log", "D:\\vault\\StationLog\\mes_dut_log")

SCAN_SN_ITEM = MES_CFG.get("scan_sn_item", [])
SCAN_SN_LIMIT = MES_CFG.get("scan_sn_limit", "")
PRODUCT_NAME = MES_CFG.get("product_name", "")
PRODUCT_NAME_LIMIT = MES_CFG.get("product_name_limit", "")
SPECIAL_LIMIT_ITEMS = MES_CFG.get("special_limit_items", [])
# print("SPECIAL_LIMIT_ITEM =", SPECIAL_LIMIT_ITEM)
PASS_LIMIT_ITEMS = MES_CFG.get("pass_limit_items", [])


TERMINAL_NAME = STATION_CFG.get("terminal_name", "")
PROJECT_CODE = STATION_CFG.get("project_code", "")
STATION_CODE = STATION_CFG.get("station_code", "")
CURRENT_PROJECT_NAME = STATION_CFG.get("project_name", "")
FIXTRUE_ID = STATION_CFG.get("fixtrue_id", "")

DEFAULT_TRANSPORT_PROTOCOL_SERVER = "tcp://127.0.0.1:"
DEFAULT_TRANSPORT_PROTOCOL_CLIENT = "tcp://127.0.0.1:"



def time_to_str(t, format_str="%Y-%m-%d %H-%M-%S"):
    return "{}.{:06d}".format(time.strftime(format_str, time.localtime(t)), int((t - int(t)) * 1000000))


class ConsoleLogLevelInfo:
    hide = -1
    info = 0
    warning = 1
    error = 2
    highlight = 3


def __console_log(level=ConsoleLogLevelInfo.info, *args):
    if level < ConsoleLogLevelInfo.info:
        return
    _prefix = ""
    _suffix = "\033[0m"
    if level == ConsoleLogLevelInfo.info:
        _prefix = ""
    elif level == ConsoleLogLevelInfo.warning:
        _prefix = "\033[1;33m"
    elif level == ConsoleLogLevelInfo.error:
        _prefix = "\033[5;31m"
    elif level == ConsoleLogLevelInfo.highlight:
        _prefix = "\033[5;32m"
    _msg = ""
    for _item in args:
        _msg += str(_item)
    print(_prefix + str(_msg) + _suffix)


def console_log_info(*args):
    __console_log(ConsoleLogLevelInfo.info, *args)


def console_log_warning(*args):
    __console_log(ConsoleLogLevelInfo.warning, *args)


def console_log_error(*args):
    __console_log(ConsoleLogLevelInfo.error, *args)


def console_log_highlight(*args):
    __console_log(ConsoleLogLevelInfo.highlight, *args)


class FileLog:
    def __init__(self, file_path, file_name, publisher=None):
        self._publisher = publisher
        try:
            if not os.path.exists(file_path):
                os.mkdir(file_path)
        except Exception as e:
            self.publish("check FileLog Path fail, path:{}, e:{}".format(file_path, str(e)))
            raise e

        self.__log_file_name = os.path.join(file_path, file_name)
        self.__log_file = open(self.__log_file_name, "a+")

    def write(self, msg):
        self.__log_file.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f:{}".format(str(msg) + "\n")))
        self.__log_file.flush()

    def publish(self, msg):
        if self._publisher:
            self._publisher.publish(msg)

    def log(self, msg):
        self.write(msg)


class HttpClient(object):

    def __init__(self, host, headers=None, params_prefix="strjson"):
        self.host = host
        self.headers = headers
        self.params_prefix = params_prefix

    # method: GET/POST
    # params: type dict/string/bytes
    # return: tuple(result, response, error_msg, total_time)
    def hrequest(self, url, method, params, timeout=30):
        _host = self.host + url
        # _data = params
        _data_json_str = json.dumps(params)
        _data = "{}={}".format(self.params_prefix, _data_json_str)
        # print("_data =", _data)

        _start_time = time.time()
        _result = False
        _response = None
        _error_msg = ""

        if isinstance(_data, dict):
            _data = json.dumps(_data).encode("UTF-8")
        elif isinstance(_data, str):
            _data = _data.encode("UTF-8")

        if not isinstance(_data, bytes):
            _result = False
            _response = None
            _error_msg = "http request type error: {}, {}".format(_host, _data)
        else:
            try:
                req = request.Request(url=_host, data=_data, headers=self.headers, method=method)

                _response = request.urlopen(req, timeout=timeout)
                _response = _response.read()
                # print("_response type =", type(_response))
                # print("_response =", _response)

                if isinstance(_response, bytes):
                    _response = _response.decode("UTF-8")
                # print("_host =", _host)
                # print("_data =", _data)
                # print("_response =", _response)

                _result = True
                _error_msg = ""

            except Exception as e:
                print("http request exception: {}, {}, {}".format(_host, request, e))
                _result = False
                _response = None
                _error_msg = "http request exception: {}, {}, {}".format(_host, request, e)

        _end_time = time.time()
        _total_time = _end_time - _start_time
        # print("_total_time =", _total_time)

        _dom = ElementTree.fromstring(_response)
        # print("_dom.text type =", type(_dom.text))
        # print("_dom.text =", _dom.text)

        # return _result, _response, _error_msg, _total_time
        return _result, _dom.text, _error_msg, _total_time
