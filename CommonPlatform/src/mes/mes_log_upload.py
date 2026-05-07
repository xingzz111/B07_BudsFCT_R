import json
import os
import threading
import time
import traceback
import zmq
import csv

from mes import mes_config
from mes.mes_config import FileLog, console_log_error, console_log_highlight, HttpClient

# from prmLib.common import Report, TesterReporter
# from prmLib import zmqports, events, levels

from rtrpcLib.common import Report, TesterReporter
from rtrpcLib import events, levels
from rtrpcLib import zmqports


class MESLogUpload:
    def __init__(self, site, publisher):
        self._publisher = publisher
        self.site = site
        self._log_buffer = dict()
        self._log_buffer_lock = threading.Lock()
        self._repoter = TesterReporter(publisher)
        self._poller = zmq.Poller()
        _socket = zmq.Context().socket(zmq.SUB)
        _address = mes_config.DEFAULT_TRANSPORT_PROTOCOL_CLIENT + str(zmqports.PRM_GUI_PUB)
        _socket.connect(_address)
        _socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL.encode("utf-8"))
        self._poller.register(_socket, zmq.POLLIN)
        
        self._error_code_dict = {}
        current_path = os.getcwd()
        file_path = current_path + '\mes\MB_FWDL.csv'
        key_column = 'FAIL Description'       
        value_column = 'EC'
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self._error_code_dict[row[key_column]] = row[value_column]

    def __get_sockets(self):
        tup_list = self._poller.sockets
        sockets = [i[0] for i in tup_list]
        return sockets

    def upload(self, key, data):
        if self._log_buffer.get(key):
            return

        self._log_buffer_lock.acquire(True)
        self._log_buffer.setdefault(key, data)
        self._log_buffer_lock.release()

        _log_file_path = os.path.join(mes_config.MES_LOG_PATH, "log")
        try:
            if not os.path.exists(_log_file_path):
                os.mkdir(_log_file_path)

            _log_file_name = "OSENSE" + "_" + mes_config.TERMINAL_NAME + "_Slot{}_".format(
                self.site) + key + "_MES_upload.log"

            _file_log = FileLog(_log_file_path, _log_file_name)

            self.send_data_to_mes(key, _file_log)
        except Exception as e:
            _msg = "check MES Upload Log Path fail, path:{}, e:{}".format(_log_file_path, str(e))
            console_log_error(_msg)

    def send_data_to_mes(self, key, file_log):
        file_log.log("=======>site:{}".format(self.site))
        console_log_highlight("[MESLogUpload]:site:{}, key:{} send_data_to_mes".format(self.site, key))

        _data = self._log_buffer.get(key)
        if not _data:
            _msg = "[send_data_to_mes], not _data, key:{}\n".format(key)
            file_log.log(_msg)
            return False

        console_log_highlight("send_data_to_mes-_data:{}".format(_data))

        sn = _data.get("sn")
        result = _data.get("result")
        error_code = "00000"
        if result and result != -1:
            error_code = _data.get("error_code")
        else:
            for value in _data.get("data"):
                if not value.get("result"):
                    fail_item = value.get("subsubtestname")
                    error_code = self._error_code_dict.get(fail_item)
                    break

        error_msg = _data.get("error_msg")
        log_file = _data.get("log_file", "")
        logs = _data.get("logs", "")
        _data_buffer = _data.get("data")
        mes_log_file = _data.get("mes_log_file", "")

        file_log.log("=======>sn:{}".format(sn))
        file_log.log("=======>result:{}".format(result))
        file_log.log("=======>error_code:{}".format(error_code))
        file_log.log("=======>error_msg:{}".format(error_msg))
        file_log.log("=======>log_file:{}".format(log_file))
        file_log.log("=======>logs:{}\n".format(logs))

        _params = dict({"COMMAND": "SendData", "SERIAL_NUMBER": sn})
        __result_str = "FAIL"
        # 如果FAIL, 则为错误代码; 如果PASS, 则为空
        _params.setdefault("ERROR_CODE", "")
        if result and result != -1:
            __result_str = "PASS"
        else:
            _params["ERROR_CODE"] = str(error_code)
        _params.setdefault("TEST_RESULT", __result_str)
        _params.setdefault("ERROR_MSG", "")
        _params.setdefault("LOG_FILE", mes_log_file)

        if mes_log_file and len(mes_log_file) > 0:
            _params["LOG_FILE"] = mes_log_file

        # TEST_DATA
        _test_data = []
        # if _data_buffer:
        #     for _item in _data_buffer:
        #         _k = "{}-{}-{}".format(_item.get("group", ""),
        #                                _item.get("tid", ""),
        #                                _item.get("subsubtestname", ""))
        #         _v = _item.get("value", "FAIL")
        #         _test_data.append({
        #             "NAME": _k,
        #             "VALUE": _v
        #         })
        _params.setdefault("TEST_DATA", _test_data)

        try:
            # self.app_show_loading()

            http_client = HttpClient(mes_config.MES_HOST, mes_config.MES_HEADER)
            _result, _response, _error_msg, _total_time = http_client.hrequest("SendData", "POST", _params)
            if _result:
                _result = _response.get("RESULT", "FAIL")
                _result_info = _response.get("RESULT_INFO")
                _result = True if (_result == "OK" or _result == "PASS" or "重测PASS次数少于2次" in _result_info) else False
                _error_msg = _response.get("RESULT_INFO", "")
            else:
                _error_msg = "Network anomaly"

            if _result:
                self._log_buffer_lock.acquire(True)
                self._log_buffer.pop(key)
                self._log_buffer_lock.release()
            else:
                # upload fail, retry
                self._log_upload_fail_process(key, sn, _error_msg, file_log)
        except Exception as e:
            _format_exc = traceback.format_exc()
            print(_format_exc)
            file_log.log("MES Service not available. site:{} sn:{} e:{}".format(self.site, sn, str(e)))
            console_log_error("MES Service not available. site:{} sn:{} e:{}".format(self.site, sn, str(e)))

            self._log_upload_fail_process(key, sn, "MES Service not available", file_log)
        finally:
            # self.app_hide_loading()
            pass

    def _log_upload_fail_process(self, key, sn, msg, file_log):

        report = Report()
        report.event = events.LOG_UPLOAD_FAIL_EVENT
        report.data = {
            "key": key,
            "sn": sn,
            "msg": "Upload MES log fail\nsn:{}\n\n{}\n".format(sn, msg)
        }
        self._publisher.publish(report.serialize(), level=levels.CRITICAL)

        try:
            _receiving = True
            _begin_time = time.time()
            while _receiving:
                try:
                    socks = dict(self._poller.poll(1000))
                    for socket in self.__get_sockets():
                        if socket in socks and socks[socket] == zmq.POLLIN:
                            recv_list = socket.recv_multipart(zmq.NOBLOCK)
                            topic, ts, level, origin, data = [key.decode() for key in recv_list]
                            message = self._repoter.parse_report(data)
                            if events.LOG_UPLOAD_RETRY_EVENT == message.event \
                                    and len(message.data) > 2 \
                                    and message.data[1] == sn:
                                self._send_data_to_mes_retry(message.data, file_log)
                                return
                except zmq.ZMQError as e:
                    _format_exc = traceback.format_exc()
                    print(_format_exc)
                    console_log_error("zmq.ZMQError-e:{}".format(str(e)))
                    file_log.log("zmq.ZMQError-e:{}".format(str(e)))
                    break
                time.sleep(0.5)
        except Exception as e:
            _format_exc = traceback.format_exc()
            print(_format_exc)
            file_log.log("MESLogupload-_log_upload_fail_process-Exception:{}\n".format(str(e)))
            console_log_error("MESLogupload-_log_upload_fail_process-Exception:\n", e)

        console_log_highlight("_log_upload_fail_process end")

    def _send_data_to_mes_retry(self, msg, file_log):
        _data = msg
        file_log.log("_send_data_to_mes_retry-msg:{}".format(msg))
        if len(_data) < 3:
            file_log.log("_send_data_to_mes_retry param error. data:{}".format(str(_data)))
            console_log_error("[MESLogUpload]:_send_data_to_mes_retry param error. data:{}".format(str(_data)))

        key = _data[0]
        sn = _data[1]
        retry = _data[2]
        file_log.log("sn:{}, site:{}, key:{} _send_data_to_mes_retry retry({})".format(sn, self.site, key, retry))
        console_log_highlight(
            "[MESLogUpload]:sn:{}, site:{} _send_data_to_mes_retry retry({})".format(sn, self.site, retry))

        if not key:
            return

        if not retry:
            file_log.log("_send_data_to_mes_retry:{}".format(retry))
            return

        self.send_data_to_mes(key, file_log)

    def app_show_loading(self):
        report = Report()
        report.event = events.APP_SHOW_LOADING_EVENT
        report.data = {}
        self._publisher.publish(report.serialize(), level=levels.CRITICAL)

    def app_hide_loading(self):
        report = Report()
        report.event = events.APP_HIDE_LOADING_EVENT
        report.data = {}
        self._publisher.publish(report.serialize(), level=levels.CRITICAL)

