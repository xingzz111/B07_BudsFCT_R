import os
import time
import zmq
import traceback
import threading
import hashlib
import re

from threading import Thread
from datetime import datetime

from rtlib.ictmes import get_mes_status

from mes import mes_day_log_v2
from mes import mes_dut_log
from mes import mes_config
from mes import mes_log_upload
from mes.mes_config import FileLog, time_to_str, console_log_error, console_log_highlight

# from prmLib import zmqports, events
# from prmLib.common import TesterReporter

from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

# from rtSque.constant import zmqports
# from rtSque.prmlib import prmevents
# from rtSque.Alib.reporter import ReporterProtocol

from rtrpcLib import zmqports, events
from rtrpcLib.common import TesterReporter
from rtrpcLib.rpc.publisher import ZmqPublisher
from configure import constants as constant



class MESLogServer(Thread):
    # __day_log_obj = mes_day_log_v2.MESDayLog()

    log_upload_swith = mes_config.UPLOAD_SWITH
    print("MESLogServer log_upload_swith =", log_upload_swith)

    def __init__(self, site):
        super(MESLogServer, self).__init__()
        self.test_case_obj = None
        self.heartbeat_at = 0
        self.poller = zmq.Poller()
        self.receiving = True
        ctx = zmq.Context().instance()
        self._publisher = ZmqPublisher(
            ctx, constant.DEFAULT_TRANSPORT_PROTOCOL_SERVER + str(zmqports.TEST_ENGINE_PUB + site),
            "MES_{:02}".format(0)
        )
        self._reporter = TesterReporter(self._publisher)
        self.site = site
        self.__sn_logs = []
        self.test_plan = dict()
        self.on_sequence_start_time = 0
        self.on_item_start_time = 0
        self.test_item_dict = dict()
        self.dut_log_list = list()
        self.log_in_list = list()
        self._on_sequence_end_data = None
        self._fixture_in_flag = False
        self._fixture_end_flag = False
        self.upload_only_pass = mes_config.UPLOAD_ONLY_PASS

        self.log_uploader = None
        # self.log_uploader = mes_log_upload.MESLogUpload(site, publisher)

        self.__file_log_path = os.path.join(mes_config.MES_LOG_PATH, "log")

        # _log_file_name = "OSENS" + "_" + mes_config.TERMINAL_NAME + "_Slot{}_".format(self.site) + \
        #                  datetime.now().strftime("%Y-%m-%d") + "_MES_server.log"
        try:
            # self.__file_log = FileLog(self.__file_log_path, _log_file_name)
            self.__day_log_obj = mes_day_log_v2.MESDayLog()

            self.dut_log = mes_dut_log.MESDutLog()
        except Exception as e:
            print("MESLogServer init error: ", str(e))

    def subscribe(self, url, port=zmqports.SEQUENCER_PUB):
        ctx = zmq.Context.instance()
        socket = ctx.socket(zmq.SUB)
        seq_address = url + str(port)
        socket.connect(seq_address)
        # socket.setsockopt(zmq.IDENTITY, str(port).encode())
        socket.setsockopt(zmq.SUBSCRIBE, zmqports.PUB_CHANNEL)
        # socket.connect("{}:{}".format(url, port))
        self.poller.register(socket, zmq.POLLIN)

    def unsubscribe(self, socket):
        self.poller.unregister(socket)
        socket.setsockopt(zmq.LINGER, 0)
        socket.close()

    def event_dispatch(self, msg):
        sequencer_event_map = {
            events.SEQUENCE_START: 'on_sequence_start',
            events.SEQUENCE_END: 'on_sequence_end',
            events.ITEM_START: 'on_item_start',
            events.ITEM_FINISH: 'on_item_finish',
            events.ATTRIBUTE_FOUND: 'on_attribute_found',
            events.SEQUENCE_LOADED: 'on_sequence_loaded',
            events.ZIP_LOGS_END: 'on_zip_logs_end',
            events.PRM_SM_REQ: 'on_sm_event'
        }
        if len(msg) != 5:
            return
        topic, ts, level, origin, data = msg[:]

        if self.test_item_dict.get("SUBSUBTESTNAME"):
            if "CB_PUB_" in origin and self.test_item_dict["SUBSUBTESTNAME"].startswith("@"):
                self.on_dut_log_found_armpub(data)
                return

        # if "MixRpc" in origin and self.test_item_dict["SUBSUBTESTNAME"].startswith("@"):
        if "BMT_PUB_" in origin and self.test_item_dict["SUBSUBTESTNAME"].startswith("@"):
            self.on_dut_log_found(data)
            return

        # report = ReporterProtocol.parse_report(data)
        report = self._reporter.parse_report(data)
        # print(f">>>>>>>>>>>>>>>>>>>>report event is :{report.event}")
        if report.event == events.ILLEGAL_EVENT:
            return

        func_name = sequencer_event_map.get(report.event)
        if not func_name:
            print("Unrecognized event; {}".format(report.event), msg)
            return

        try:
            # print(f">>>>>>>>>>>>>>>>>>func_name:{func_name}")
            func = getattr(self, func_name, None)
            if callable(func):
                # print(f">>>>>>>>>>>>>>>>>>>>report data is :{report._to_dict()}")
                func(self.site, report._to_dict())
        except Exception as e:
            _format_exc = traceback.format_exc()
            print(_format_exc)
            print("event_dispatch error: ", str(e))

    def on_sm_event(self, site, data):
        sm_data = data.get('data')[0]
        if sm_data in ('fixture_in', 'fixture_start'):
            self._fixture_in_flag = True
            self._test_start()
            start_data = {'event': 2, 'data': {'group': 'Fixture', 'subtestname': 'Action', 'subsubtestname': '@Fixture_IN', 'lowerlimit': 'PASS', 'upperlimit': 'PASS', 'units': '', 'to_pdca': True, 'timestamp': str(datetime.now())}}
            self.on_item_start(site, start_data)
        elif sm_data == 'start_test':
            if not self._fixture_in_flag:
                self._test_start()
            else:
                finish_data = {'event': 3, 'data': {'result': True, 'tid': 'Action', 'group': 'Fixture', 'subsubtestname': '@Fixture_IN', 'value': 'PASS', 'to_pdca': True, 'timestamp': str(datetime.now())}}
                self.on_item_finish(site, finish_data, False)
            time.sleep(0.1)
            self._fixture_in_flag = False
        elif sm_data == 'fixture_end':
            self._fixture_end_flag = True
            start_data = {'event': 2, 'data': {'group': 'Fixture', 'subtestname': 'Action', 'subsubtestname': '@Fixture_OUT', 'lowerlimit': 'PASS', 'upperlimit': 'PASS', 'units': '', 'to_pdca': True, 'timestamp': str(datetime.now())}}
            self.on_item_start(site, start_data)
        elif sm_data == 'test_finish':
            if self._fixture_end_flag:
                finish_data = {'event': 3, 'data': {'result': True, 'tid': 'Action', 'group': 'Fixture', 'subsubtestname': '@Fixture_OUT', 'value': 'PASS', 'to_pdca': True, 'timestamp': str(datetime.now())}}
                self.on_item_finish(site, finish_data, False)
            self._test_finish(site)
            self._fixture_end_flag = False
        else:
            pass

    def on_dut_log_found(self, data):
        # print("=" * 50, " on_dut_log_found")
        # print("SUBSUBTESTNAME =", self.test_item_dict["SUBSUBTESTNAME"])
        # print("data =", data)

        data_list = data.split("@")
        if "log_in" in data_list[0]:
            self.log_in_list.append(str(data_list[1]))
        elif "log_out" in data_list[0]:
            self.dut_log_list.append({"log_in": "\n".join(self.log_in_list)})
            self.log_in_list = list()
            self.dut_log_list.append({"log_out": str(data_list[1])})
        else:
            print("log args error !")
        pass

    def on_dut_log_found_armpub(self, data):
        # print("=" * 50, " on_dut_log_found_armpub")
        # print("SUBSUBTESTNAME =", self.test_item_dict["SUBSUBTESTNAME"])
        # print("data =", data)

        parse_data = re.search("\w+\.\w+\(", data)

        if parse_data:
            if "calibration_mode" in parse_data.group(0) or "audio_record" in parse_data.group(0) or "read_calibration_cell" in parse_data.group(0) or "VOLT_MEAS_MUX_SEL_BUD_TP34_QCC_BAT_STB" in data:
                return
            self.log_in_list.append(str(data))
        else:
            if self.log_in_list == []:
                return
            self.dut_log_list.append({"log_in": "\n".join(self.log_in_list)})
            self.log_in_list = list()
            self.dut_log_list.append({"log_out": str(data)})
        pass

    def on_attribute_found(self, site, data):
        pass

    def on_sequence_loaded(self, site, data):
        self.dut_log.on_sequence_loaded(site, data)

        self.test_case_obj = data.get("data", {})

        testplan_path = self.test_case_obj.get("path")
        testplan_md5 = ""
        with open(testplan_path, 'rb') as f:
            testplan_md5 = hashlib.md5(f.read()).hexdigest()

        self.test_case_obj["file_md5"] = testplan_md5
        # self.write_file_log(
        #     "on_sequence_loaded-test_plan_file_path:{}, file_md5:{}".format(self.test_case_obj.get("file_path"),
                                                                            # self.test_case_obj.get("file_md5")))
        self.__day_log_obj.reload_log_file(self.test_case_obj)

    def _test_start(self):
        self.log_upload_swith = get_mes_status()
        self.on_sequence_start_time = time.time()
        self.__sn_logs = []

    def on_sequence_start(self, site, data):
        self.dut_log.on_sequence_start(site, data)

    def on_sequence_end(self, site, data):
        self._on_sequence_end_data = data
    
    def _test_finish(self, site):
        data = self._on_sequence_end_data
        self._on_sequence_end_data = None
        if not data:
            return None
        _on_sequence_end_time = time.time()
        _total_time = round(_on_sequence_end_time - self.on_sequence_start_time, 3)
        _p = {
            "start_time": time_to_str(self.on_sequence_start_time),
            "stop_time": time_to_str(_on_sequence_end_time),
            "total_time": _total_time
        }
        _p.update(data)
        pdca_status = self.log_upload_swith
        self.dut_log.on_sequence_end(site, _p, pdca_status)

        param = data.get("data", {})
        # sn = param.get("sn")
        sn = self.dut_log.sn
        result = param.get("result", False)
        param["log_upload_swith"] = self.log_upload_swith

        if result == -1:
            # sequence aborted
            self.write_file_log('sequence aborted, sh:{}'.format(sn))
            console_log_error(
                "{} Error: MESLogServer(site:{})-on_sequence_end sequence aborted".format(time.time(), site))
            return None

        if not sn or len(sn) < 1:
            self.write_file_log("Error: MESLogServer(site:{})-on_sequence_end get sn nil".format(site))
            console_log_error("Error: MESLogServer(site:{})-on_sequence_end get sn nil".format(site))
            return None
        param.setdefault("total_time", _total_time)
        param.setdefault("start_time", time_to_str(self.on_sequence_start_time))
        param.setdefault("stop_time", time_to_str(_on_sequence_end_time))
        param.setdefault("mes_log_file", self.__day_log_obj.get_log_file_path())

        _failed_list = ""

        for __sn_log in self.__sn_logs:
            if __sn_log.get("subsubtestname", None) in ("Fixture_IN", "Fixture_OUT"):
                self.__sn_logs.remove(__sn_log)
            if not __sn_log.get("result", False):
                if len(_failed_list) > 0:
                    _failed_list += ";"
                _failed_list += __sn_log.get("subsubtestname")
        param["failed_list"] = _failed_list

        self.__day_log_obj.write_datas(site, param, self.__sn_logs, self.dut_log.sn)
        # self.__day_log_obj.write_blank_line()

        upload_flag = True
        if result != 1 and self.upload_only_pass or not self.log_upload_swith:
            upload_flag = False

        if upload_flag and not self.log_upload_swith:
            app = QApplication([])
            QMessageBox.warning(QMessageBox(), "MES Error", "mes enable error", buttons=QMessageBox.Ok)

        # if self.log_upload_swith and upload_flag:
        #     th = threading.Thread(target=self.upload_sn_log_to_mes_server, args=(site, param))
        #     th.daemon = True
        #     th.start()
        

    def on_zip_logs_end(self, site, data):
        pass
    
    def on_item_start(self, site, data):
        self.on_item_start_time = time.time()

        self.dut_log.on_item_start(site, data)

        self.test_item_dict = dict()
        data = data.get("data")
        self.test_item_dict["GROUP"] = data["group"]
        self.test_item_dict["SUBTESTNAME"] = data["subtestname"]
        self.test_item_dict["SUBSUBTESTNAME"] = data["subsubtestname"]
        self.test_item_dict["high"] = data["upperlimit"]
        self.test_item_dict["low"] = data["lowerlimit"]
        self.test_item_dict["unit"] = data["units"]

        self.dut_log_list = list()

    def on_item_finish(self, site, data, dut_log_flag=True):
        param = data.get("data", {})
        subsubtestname = param.get("subsubtestname")

        # SCAN_PCBA_SN
        value = param.get("value")
        if subsubtestname in ("@Scan_PCBA_SN", "@Get_USB_Serial_Number") and "--SKIP--" not in value:
            sn = value.strip("'")

            self.dut_log.sn = sn

            # _log_file_name = "OSENS" + "_" + mes_config.TERMINAL_NAME + "_Slot{}_{}_".format(self.site, sn) + \
            #                  datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_MES_server.log"
            # self.__file_log = FileLog(self.__file_log_path, _log_file_name)

        _on_item_finish_time = time.time()
        _step_time = round(_on_item_finish_time - self.on_item_start_time, 6)
        _p = {
            "start_time_t": time_to_str(self.on_item_start_time),
            "stop_time": time_to_str(_on_item_finish_time),
            "step_time": _step_time
        }
        data['data'].update({"high" : self.test_item_dict["high"],
                             "low" : self.test_item_dict["low"],
                             "unit" : self.test_item_dict["unit"]})
        _p.update(data)
        self.dut_log.on_item_finish(site, _p)

        if not subsubtestname or not subsubtestname.startswith("@"):
        # if not subsubtestname:
            return None

        if dut_log_flag:
            self.dut_log.set_dut_log(self.dut_log_list, self.test_item_dict)

        param["subsubtestname"] = subsubtestname.removeprefix("@")
        param["result"] = param.get("result", False)
        param["value"] = str(param.get("value")).replace("--PASS--", "").replace("--FAIL--", "")

        if len(param["value"]) < 1:
            param["value"] = param["result"]
        self.__sn_logs.append(param)

    def log(self, msg):
        if self._publisher:
            self._publisher.publish("[MESLogServer-{}]: {}".format(self.site, str(msg)),
                                    id_postfix="MESLogServer thread")

    def write_file_log(self, msg):
        if self.__file_log:
            self.__file_log.publish("[MESLogServer-{}]: {}".format(self.site, str(msg)))

    def upload_sn_log_to_mes_server(self, site, data):
        sn = data.get("sn")
        _param = dict({
            "sn": data.get("sn"),
            "result": data.get("result", False),
            "value": str(data.get("value", '')).replace("--PASS--", "").replace("--FAIL--", ""),
            "error_code": data.get("error_code"),
            "error_msg": data.get("error_msg"),
            "log_file": self.__day_log_obj.log_file_path,
            "logs": data.get("logs", ""),
            "mes_log_file": data.get("mes_log_file", "")
        })

        if not sn or len(sn) < 1:
            self.write_file_log("Error: upload_sn_log_to_mes_server get sn nil")
            return None

        _key = sn + "_" + datetime.now().strftime("%Y-%m-%d_%H%M%S")
        _param["data"] = self.__sn_logs

        try:
            self.log_uploader.upload(_key, _param)
        except Exception as e:
            _format_exc = traceback.format_exc()
            print(_format_exc)
            self.write_file_log("upload_sn_log_to_mes_server fail, e:{}".format(self.site, str(e)))
            console_log_error("MESLogServer({}) upload_sn_log_to_mes_server fail, e:{}".format(self.site, str(e)))

    def run(self):
        self.log("MESLogServer({}) started".format(self.site))

        self.heartbeat_at = time.time() + mes_config.HEARTBEAT_INTERVAL

        self.subscribe(url=constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT, port=zmqports.SEQUENCER_PUB + self.site)
        self.subscribe(url=constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT, port=zmqports.ARM_PUB + self.site)
        self.subscribe(url=constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT, port=zmqports.UART2_PUB + self.site)
        self.subscribe(url=constant.DEFAULT_TRANSPORT_PROTOCOL_CLIENT, port=zmqports.PRM_GUI_PUB)


        while self.receiving:
            # print(">>>>>>>>>>>>>>>>>>>>>>>>receiving")
            try:
                socks = dict(self.poller.poll(1000))
                for socket in self.__get_sockets():
                    if socket in socks and socks[socket] == zmq.POLLIN:
                        msg = socket.recv_multipart(zmq.NOBLOCK)
                        msg = [key.decode("utf-8") for key in msg]
                        # print(f">>>>>>>>>>>>>>>>>>>>>mes_log_message: {msg}")
                        # console_log_highlight("mes_log_server-run-msg:{}-{}".format(type(msg), msg))
                        self.event_dispatch(msg)
            except zmq.ZMQError as e:
                _format_exc = traceback.format_exc()
                print(_format_exc)

                self.log(str(e) + "\n" + str(traceback.format_exc()))
            finally:
                pass

            self.__signal_heartbeat()
        self.__shutdown()

    def __get_sockets(self):
        tup_list = self.poller.sockets
        sockets = [i[0] for i in tup_list]
        return sockets

    def __shutdown(self):
        for socket in self.__get_sockets():
            self.unsubscribe(socket)

    def __signal_heartbeat(self):
        t_now = time.time()
        if t_now >= self.heartbeat_at:
            self.log(mes_config.FCT_HEARTBEAT)
            self.heartbeat_at = t_now + mes_config.HEARTBEAT_INTERVAL


if __name__ == "__main__":
    pass

    # MESLogServer(site=0).start()
    # MESLogServer(site=1).start()
    # MESLogServer(site=2).start()
    # MESLogServer(site=3).start()
    #
    # _ip = "tcp://127.0.0.1"
    # _port = str(zmqports.SEQUENCER_PUB + 1)
    # _channel = "PUB_CHANNEL"
    # _poller = zmq.Poller()
    # ctx = zmq.Context.instance()
    # _socket = ctx.socket(zmq.SUB)
    # _socket.connect("{}:{}".format(_ip, _port))
    # # _socket.setsockopt(zmq.IDENTITY, _port.encode("utf-8"))
    # _socket.setsockopt(zmq.SUBSCRIBE, str(zmqports.PUB_CHANNEL).encode("utf-8"))
    # _poller.register(_socket, zmq.POLLIN)
    #
    # while True:
    #     try:
    #         _socks = dict(_poller.poll(1000))
    #         if _socket in _socks and _socks[_socket] == zmq.POLLIN:
    #             msg = _socket.recv_multipart(zmq.NOBLOCK)
    #             msg = [key.decode("utf-8") for key in msg]
    #             MESLogServer.event_dispatch(msg)
    #             print("msg =", msg)
    #     except zmq.ZMQError as e:
    #         print(e, traceback.format_exc())
    #     finally:
    #         pass
    #