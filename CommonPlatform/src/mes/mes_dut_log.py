import csv
import os
import threading
import datetime
import time
import traceback
from mes import mes_config
from configure import constants as constant
from rtlib.ictmes import get_mes_status

LOG_FILE_PATH = mes_config.LOG_FILE_PATH
MES_LOG_PATH = mes_config.MES_LOG_PATH
DUT_LOG_PATH = mes_config.DUT_LOG_PATH
MES_DUT_LOG_PATH = mes_config.MES_DUT_LOG_PATH

if not os.path.exists(LOG_FILE_PATH):
    os.makedirs(LOG_FILE_PATH, exist_ok=True)

if not os.path.exists(MES_LOG_PATH):
    os.makedirs(MES_LOG_PATH, exist_ok=True)

DUT_LOG_PATH_CSV = os.path.join(os.path.dirname(DUT_LOG_PATH), "dut_log_csv")
MES_DUT_LOG_PATH_CSV = os.path.join(os.path.dirname(MES_DUT_LOG_PATH), "mes_dut_log_csv")

DUTLOG_SEQUENCE_RESULT = 0
DUTLOG_TEST_ITEM_RESULT = 1
DUTLOG_TEST_ITEM_IN = 2
DUTLOG_TEST_ITEM_OUT = 3

_tab_1 = "\t"
_tab_2 = "\t\t"
_tab_3 = "\t\t\t"


class MESDutLog(object):
    def __init__(self):
        self.sn = ""
        self.site = None
        self.dut_log = {}
        self.test_plan_name = ""
        self._dut_log_lock = threading.Lock()
        self.log_in_str = ""
        self.__write_log_csv_flag = False
        self.test_tool_dict = {}

    def set_dut_log(self, _logs, _test_item):
        try:
            self._dut_log_lock.acquire(True)

            _site = self.site
            _test_name = _test_item.get("GROUP")
            _sub_test_name = _test_item.get("SUBTESTNAME")
            _sub_sub_test_name = _test_item.get("SUBSUBTESTNAME")

            if _sub_sub_test_name and _sub_sub_test_name.startswith("@"):
            # if _sub_sub_test_name:
                _sub_sub_test_name = _sub_sub_test_name.removeprefix("@")
                # _sub_sub_test_name = _test_name + '@' + _sub_sub_test_name
                _dut_log_item = self.dut_log.get(_site, {})
                _dut_log_test_items = _dut_log_item.get("test_items", [])

                _dut_log_test_item = {}
                _have = False
                for _item in _dut_log_test_items:
                    if _sub_sub_test_name in _item:
                        _dut_log_test_item = _item[_sub_sub_test_name]
                        _have = True
                        break

                if not _have:
                    _dut_log_test_items.append({
                        _sub_sub_test_name: _dut_log_test_item
                    })

                _dut_log_test_item.setdefault("logs", _logs)
                _dut_log_item.setdefault("test_items", _dut_log_test_items)
                self.dut_log.setdefault(_site, _dut_log_item)
        except Exception as e:
            _format_exc = traceback.format_exc()
            print(_format_exc)
            print("set_dut_log error: ", str(e))
        finally:
            self._dut_log_lock.release()

    def __set_result(self, site, data, flag):
        try:
            self._dut_log_lock.acquire(True)

            _data = data.get("data")
            # _sn = _data.get("sn")
            _site = site
            _result = _data.get("result")
            _dut_log_item = self.dut_log.get(_site, {})

            if flag == DUTLOG_SEQUENCE_RESULT:
                _start_time = data.get("start_time")
                _stop_time = data.get("stop_time")
                _total_time = data.get("total_time")

                _dut_log_item["result"] = _result
                _dut_log_item["start_time"] = _start_time
                _dut_log_item["stop_time"] = _stop_time
                _dut_log_item["total_time"] = _total_time
            elif flag == DUTLOG_TEST_ITEM_RESULT:
                # print('_data-------->',_data)
                _test_name = _data.get("group")
                _sub_sub_test_name = _data.get("subsubtestname")
                _low = _data.get("low")
                _high = _data.get("high")
                _unit = _data.get("unit")
                _value = _data.get("value")

                _data["start_time_t"] = data.get("start_time_t")
                _data["end_time_t"] = data.get("stop_time")
                _data["cycle_time"] = data.get("step_time")

                if _sub_sub_test_name and _sub_sub_test_name.startswith("@"):
                # if _sub_sub_test_name:
                    _sub_sub_test_name = _sub_sub_test_name.removeprefix("@")
                    # _sub_sub_test_name = _test_name + '@' + _sub_sub_test_name
                    _dut_log_test_items = _dut_log_item.get("test_items", [])

                    _dut_log_test_item = {}
                    _have = False
                    for _item in _dut_log_test_items:
                        if _sub_sub_test_name in _item:
                            _dut_log_test_item = _item[_sub_sub_test_name]
                            _have = True
                            break

                    _dut_log_test_item["result"] = _data.copy()

                    if not _have:
                        _dut_log_test_items.append({
                            _sub_sub_test_name: _dut_log_test_item
                        })

                    _dut_log_item.setdefault("test_items", _dut_log_test_items)
            self.dut_log.setdefault(_site, _dut_log_item)
        except Exception as e:
            _format_exc = traceback.format_exc()
            print(_format_exc)
            print("__set_result error: ", str(e))
        finally:
            self._dut_log_lock.release()

    def __set_log(self, data, flag, _test_item):
        try:
            self._dut_log_lock.acquire(True)

            _site = self.site

            if not _test_item:
                self._dut_log_lock.release()
                return

            _test_name = _test_item.get("GROUP")
            _sub_test_name = _test_item.get("SUBTESTNAME")
            _sub_sub_test_name = _test_item.get("SUBSUBTESTNAME")

            if _sub_sub_test_name and _sub_sub_test_name.startswith("@"):
            # if _sub_sub_test_name:
                _sub_sub_test_name = _sub_sub_test_name.removeprefix("@")
                # _sub_sub_test_name = _test_name + '@' + _sub_sub_test_name
                _dut_log_item = self.dut_log.get(_site, {})
                _dut_log_test_items = _dut_log_item.get("test_items", [])

                _dut_log_test_item = {}
                _have = False
                for _item in _dut_log_test_items:
                    if _sub_sub_test_name in _item:
                        _dut_log_test_item = _item[_sub_sub_test_name]
                        _have = True
                        break

                if not _have:
                    _dut_log_test_items.append({
                        _sub_sub_test_name: _dut_log_test_item
                    })

                _logs = _dut_log_test_item.get("logs", [])

                if flag == DUTLOG_TEST_ITEM_OUT:
                    _log = {}
                    if len(_logs) > 0:
                        _log = _logs[len(_logs) - 1]
                    else:
                        _logs.append(_log)
                    _log["log_out"] = str(data)
                else:
                    _logs.append({
                        "log_in": str(data)
                    })

                _dut_log_test_item.setdefault("logs", _logs)
                _dut_log_item.setdefault("test_items", _dut_log_test_items)
                self.dut_log.setdefault(_site, _dut_log_item)
        except Exception as e:
            _format_exc = traceback.format_exc()
            print(_format_exc)
            print("__set_log error: ", str(e))
        finally:
            self._dut_log_lock.release()

    def log_in(self, data, test_item):
        self.__set_log(data, flag=DUTLOG_TEST_ITEM_IN, _test_item=test_item)

    def log_out(self, data, test_item):
        self.__set_log(data, flag=DUTLOG_TEST_ITEM_OUT, _test_item=test_item)

    def on_sequence_loaded(self, site, data):
        self.test_plan_name = data.get("data", {}).get("name", "")
        test_plan_path = data.get("data", {}).get("path", None)
        if test_plan_path:
            self.test_tool_dict = {}
            with open(test_plan_path, "r") as f:
                reader = csv.reader(f)
                next(reader)
                for raw in reader:
                    if len(raw) == 15:
                        self.test_tool_dict[raw[3]] = raw[14]

    def on_sequence_start(self, site, data):
        self.site = site
        pass

    def on_sequence_end(self, site, data, pdca_status):
        self.__set_result(site, data, DUTLOG_SEQUENCE_RESULT)

        param = data.get("data", {})
        # sn = param.get("sn")
        sn = self.sn

        th = threading.Thread(target=self.__write_log, args=(sn, site, pdca_status))
        th.daemon = True
        th.start()

        th_csv = threading.Thread(target=self.__write_log_csv, args=(sn, site, pdca_status))
        th_csv.daemon = True
        th_csv.start()

    def on_item_start(self, site, data):
        pass

    def on_item_finish(self, site, data):
        # print(f">>>>>>>>>>>>>>>>>>>>>on_item_finish_data: {data}")
        self.__set_result(site, data, DUTLOG_TEST_ITEM_RESULT)

    def check_mic_reboot(self, site):
        file_object = open(mes_config.LOG_FILE_PATH + "\\" + "sn_{}.txt".format(0), "r")
        all_test = file_object.read()
        if "{}_mic_reboot".format(site) in all_test:
            return "MIC_REBOOT"
        else:
            return ""

    def __write_log(self, sn, site, pdca_status):

        sfc_status = "Enable" if get_mes_status() else "Disable"
        time.sleep(0.5)
        _dut_log = self.dut_log.get(site)
        # print(f">>>>>>>>>>>>>>>>dut_log：{_dut_log}")

        if not _dut_log:
            return False

        _sequenc_result = _dut_log.get("result")
        if _sequenc_result < 0:
            self._dut_log_lock.acquire(True)
            self.dut_log.pop(site)
            self._dut_log_lock.release()
            return False

        _sequenc_result = "PASS" if _sequenc_result == 1 else "FAIL"

        _start_time = _dut_log.get("start_time")
        _stop_time = _dut_log.get("stop_time")
        _total_time = _dut_log.get("total_time")
        # _dut_log_item = self.dut_log.get(site, {})

        _file_name = "{}_{}_{}_{}_{}_{}.txt".format(_sequenc_result,
                                                    mes_config.PROJECT_CODE,
                                                    mes_config.STATION_CODE,
                                                    mes_config.CURRENT_PROJECT_NAME,
                                                    sn,
                                                    datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
                                                    )

        if not os.path.exists(mes_config.MES_DUT_LOG_PATH):
            os.makedirs(mes_config.MES_DUT_LOG_PATH, exist_ok=True)

        if not os.path.exists(mes_config.DUT_LOG_PATH):
            os.makedirs(mes_config.DUT_LOG_PATH, exist_ok=True)

        if pdca_status:
            _log_file_path = os.path.join(mes_config.MES_DUT_LOG_PATH, _file_name)
        else:
            _log_file_path = os.path.join(mes_config.DUT_LOG_PATH, _file_name)
        print("_log_file_path =", _log_file_path)

        _log_file = open(_log_file_path, "w", encoding="utf-8-sig", newline="")

        _log_file.write("Serial No:{}\n".format(sn))
        _log_file.write("Customer:Bose\n")
        _log_file.write("Product:{}\n".format(mes_config.PROJECT_CODE))
        _log_file.write("Station:{}\n".format(mes_config.CURRENT_PROJECT_NAME))
        _log_file.write("Line:1\n")
        _log_file.write("StationID:{}\n".format(mes_config.TERMINAL_NAME))
        _log_file.write("Fixture:{}\n".format(mes_config.FIXTRUE_ID))
        _log_file.write("Slot:{}\n".format(site + 1))
        _log_file.write(f"SFC:{sfc_status}\n")
        _log_file.write("TestPlan:{}\n".format(self.test_plan_name))
        _log_file.write("OperaterID:{}\n".format("A001"))
        _log_file.write("Result:{}\n".format(_sequenc_result))
        _log_file.write("Start Time:{}\n".format(_start_time))
        _log_file.write("Stop Time:{}\n".format(_stop_time))
        _log_file.write("Station Time:{}\n".format(_total_time))

        _dut_log_test_items = _dut_log.get("test_items", [])

        _idx = 0
        for _item in _dut_log_test_items:
            _idx += 1
            _log_file.write("\n***************LOG START**********************\n")
            _log_file.write("ItemIndex\t\t: {}\n".format(_idx))

            for _k in _item.keys():
                _data = _item[_k]
                _data_result = _data["result"]
                _log_file.write("TestItem{}: {}\n".format(_tab_2, _k))

                _subsubtestname = str(_data_result.get("subsubtestname", ""))
                test_tool = self.test_tool_dict.get(_subsubtestname)
                if not test_tool:
                    test_tool = "Test Sequence"
                _log_file.write("TestTool{}: {}\n".format(_tab_2, test_tool))

                _result = _data_result.get("result", "")
                _result = "PASS" if _result else "FAIL"
                _log_file.write("TestResult{}: {}\n".format(_tab_2, _result))

                _value = str(_data_result.get("value", "")).replace("--PASS--", "PASS").replace("--FAIL--", "FAIL").replace('--SKIP--', "SKIP")
                _error = "False"
                _err_message = ""
                if "FAIL" != _value and "FAIL" in _value:
                    _error = "True"
                    _err_message = _value.replace("FAIL", "")
                    _value = "FAIL"

                _high = str(_data_result.get("high", "")).replace("--PASS--", "PASS").replace("--FAIL--", "FAIL")
                _low = str(_data_result.get("low", "")).replace("--PASS--", "PASS").replace("--FAIL--", "FAIL")

                if _subsubtestname in mes_config.SCAN_SN_ITEM:
                    _high = mes_config.SCAN_SN_LIMIT
                    _low = mes_config.SCAN_SN_LIMIT

                if _subsubtestname in mes_config.PRODUCT_NAME:
                    _high = mes_config.PRODUCT_NAME_LIMIT
                    _low = mes_config.PRODUCT_NAME_LIMIT

                for special_limit_item in mes_config.SPECIAL_LIMIT_ITEMS.keys():
                    if _subsubtestname == special_limit_item:
                        _limit = mes_config.SPECIAL_LIMIT_ITEMS.get(special_limit_item)
                        _high = _limit
                        _low = _limit

                if _subsubtestname in mes_config.PASS_LIMIT_ITEMS:
                    _high = "PASS"
                    _low = "PASS"
                    if _value != "FAIL" and _value != "SKIP":
                        _value = "PASS"

                if _high == "":
                    _high = _low

                _log_file.write("Value{}: {}\n".format(_tab_2, _value))
                _log_file.write("USL{}: {}\n".format(_tab_2, _high))
                _log_file.write("LSL{}: {}\n".format(_tab_2, _low))
                _log_file.write("Unit{}: {}\n".format(_tab_2, _data_result.get("unit", "")))
                _log_file.write("ErrorCode{}: \n".format(_tab_2))
                _log_file.write("Step Time{}: {}\n".format(_tab_2, _data_result.get("cycle_time", "")))
                _log_file.write("Number of try{}: 0\n".format(_tab_1))
                _log_file.write("Number of goto{}: 0\n".format(_tab_1))
                _log_file.write("Start Time{}: {}\n".format(_tab_2, _data_result.get("start_time_t", "")))
                _log_file.write("Stop Time{}: {}\n".format(_tab_2, _data_result.get("end_time_t", "")))
                _log_file.write("Error{}: {}\n".format(_tab_2, _error))
                _log_file.write("ErrorMessage{}: {}\n".format(_tab_1, _err_message))
                _log_file.write("\n")

                _data_logs = _data.get("logs", [])
                # print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>_data_logs: {_data_logs}")
                _log_in_list = []
                _log_out_list = []
                for _log_item in _data_logs:
                    _log_in = _log_item.get("log_in")
                    if _log_in:
                        _log_in_list.append(_log_in)
                    _log_out = _log_item.get("log_out")
                    if _log_out:
                        _log_out_list.append(_log_out)

                if len(_log_in_list) > 0:
                    _log_file.write("***************Parameters Input*****************\n\n")
                    for item in _log_in_list:
                        _log_file.write("{}\n".format(item))
                    _log_file.write("\n")
                if len(_log_out_list) > 0:
                    _log_file.write("***************Results Output*****************\n\n")
                    for item in _log_out_list:
                        _log_file.write("{}\n".format(item))
                    _log_file.write("\n")

                break
            _log_file.write("***************LOG END************************\n\n\n")

        start_time = time.time()
        while True:
            print(f">>>>>>>>>>>>>>>>>>>>>>>>>__write_log_csv_flag {self.__write_log_csv_flag}")
            if self.__write_log_csv_flag:
                self._dut_log_lock.acquire(True)
                self.dut_log.pop(site)
                self._dut_log_lock.release()
                break
            time.sleep(1)
            time_now = time.time()
            if start_time - time_now > 5:
                self._dut_log_lock.acquire(True)
                self.dut_log.pop(site)
                self._dut_log_lock.release()
                break

    def __write_log_csv(self, sn, site, pdca_status):

        self.__write_log_csv_flag = False
        time.sleep(0.5)

        _dut_log = self.dut_log.get(site)

        if not _dut_log:
            self.__write_log_csv_flag = True
            return False

        _sequenc_result = _dut_log.get('result')

        if _sequenc_result < 0:
            self.__write_log_csv_flag = True
            self._dut_log_lock.acquire(True)
            self.dut_log.pop(site)
            self._dut_log_lock.release()
            return False

        _sequenc_result = 'PASS' if _sequenc_result == 1 else 'FAIL'

        _start_time = _dut_log.get('start_time')
        _stop_time = _dut_log.get('stop_time')
        _total_time = _dut_log.get('total_time')
        # _dut_log_item = self.dut_log.get(site, {})
        self.__write_log_csv_flag = True

        if "898048" in self.sn:
            _file_name = '{}_{}_CN_{}_{}_{}_{}.csv'.format(_sequenc_result,
                                                          mes_config.PROJECT_CODE,
                                                          mes_config.STATION_CODE,
                                                          mes_config.CURRENT_PROJECT_NAME,
                                                          sn,
                                                          datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
                                                          )
        else:
            _file_name = '{}_{}_{}_{}_{}_{}.csv'.format(_sequenc_result,
                                                          mes_config.PROJECT_CODE,
                                                          mes_config.STATION_CODE,
                                                          mes_config.CURRENT_PROJECT_NAME,
                                                          sn,
                                                          datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
                                                          )

        # print('_file_name =', _file_name)
        # print('MES_DUT_LOG_PATH =', MES_DUT_LOG_PATH)
        # print('DUT_LOG_PATH =', DUT_LOG_PATH)
        if not os.path.exists(MES_DUT_LOG_PATH_CSV):
            os.makedirs(MES_DUT_LOG_PATH_CSV, exist_ok=True)

        if not os.path.exists(DUT_LOG_PATH_CSV):
            os.makedirs(DUT_LOG_PATH_CSV, exist_ok=True)

        if pdca_status:
            _log_file_path = os.path.join(MES_DUT_LOG_PATH_CSV, _file_name)
        else:
            _log_file_path = os.path.join(DUT_LOG_PATH_CSV, _file_name)
        print('_log_file_path csv =', _log_file_path)

        _log_file = open(_log_file_path, 'w', encoding='utf-8-sig', newline='')

        header = [
            'ItemIndex',
            'TestItem',
            'TestTool',
            'TestResult',
            'Value',
            'USL',
            'LSL',
            'Unit',
            'ErrorCode',
            'Step Time',
            'Number of try',
            'Number of goto',
            'Start Time',
            'Stop Time',
            'Error',
            'ErrorMessage',
            'ParametersInput',
            'ResultsOutput'
        ]
        # print('len(header) =', len(header))
        sfc_status = "Enable" if get_mes_status() else "Disable"
        writer = csv.DictWriter(_log_file, fieldnames=header)

        writer.writerow(dict(zip(header, ['Serial No', sn])))
        writer.writerow(dict(zip(header, ['Customer', 'Bose'])))
        writer.writerow(dict(zip(header, ['Product', mes_config.PROJECT_CODE])))
        writer.writerow(dict(zip(header, ['Station', mes_config.CURRENT_PROJECT_NAME])))
        writer.writerow(dict(zip(header, ['Line', '1'])))
        writer.writerow(dict(zip(header, ['StationID', mes_config.TERMINAL_NAME])))
        writer.writerow(dict(zip(header, ['Fixture', mes_config.FIXTRUE_ID])))

        writer.writerow(dict(zip(header, ['Slot', site+1])))
        writer.writerow(dict(zip(header, ['SFC', sfc_status])))
        writer.writerow(dict(zip(header, ['TestPlan', self.test_plan_name])))
        writer.writerow(dict(zip(header, ['OperatorID', 'A001'])))
        writer.writerow(dict(zip(header, ['Result', _sequenc_result])))
        writer.writerow(dict(zip(header, ['Start Time', _start_time])))
        writer.writerow(dict(zip(header, ['Stop Time', _stop_time])))
        writer.writerow(dict(zip(header, ['Station Time', _total_time])))

        writer.writeheader()

        _dut_log_test_items = _dut_log.get('test_items', [])

        _idx = 0
        for _item in _dut_log_test_items:
            _csv_data = []

            _idx += 1
            _csv_data.append(_idx)

            for _k in _item.keys():
                _data = _item[_k]
                _data_result = _data['result']
                _csv_data.append(_k)

                _subsubtestname = str(_data_result.get("subsubtestname", ""))
                test_tool = self.test_tool_dict.get(_subsubtestname)
                if not test_tool:
                    test_tool = "Test Sequence"
                _csv_data.append(test_tool)

                _result = _data_result.get('result', '')
                _result = 'PASS' if _result else 'FAIL'
                _csv_data.append(_result)

                _value = str(_data_result.get('value', '')).replace('--PASS--', 'PASS').replace('--FAIL--', 'FAIL').replace('--SKIP--', "SKIP")
                _error = "False"
                _err_message = ""
                if "FAIL" != _value and "FAIL" in _value:
                    _error = "True"
                    _err_message = _value.replace("FAIL", "")
                    _value = "FAIL"

                _high = str(_data_result.get('high', '')).replace('--PASS--', 'PASS').replace('--FAIL--', 'FAIL')
                _low = str(_data_result.get('low', '')).replace('--PASS--', 'PASS').replace('--FAIL--', 'FAIL')

                if _subsubtestname in mes_config.SCAN_SN_ITEM:
                    _high = mes_config.SCAN_SN_LIMIT
                    _low = mes_config.SCAN_SN_LIMIT

                if _subsubtestname in mes_config.PRODUCT_NAME:
                    _high = mes_config.PRODUCT_NAME_LIMIT
                    _low = mes_config.PRODUCT_NAME_LIMIT

                if _subsubtestname in mes_config.PASS_LIMIT_ITEMS:
                    # if _subsubtestname == pass_limit_item:
                    _high = "PASS"
                    _low = "PASS"
                    if _value != "FAIL" and _value != "SKIP":
                        _value = "PASS"

                for special_limit_item in mes_config.SPECIAL_LIMIT_ITEMS.keys():
                    if _subsubtestname == special_limit_item:
                        _limit = mes_config.SPECIAL_LIMIT_ITEMS.get(special_limit_item)
                        _high = _limit
                        _low = _limit

                if _high == "":
                    _high = _low

                _csv_data.append(_value)
                _csv_data.append(_high)
                _csv_data.append(_low)
                _csv_data.append(_data_result.get('unit', ''))
                _csv_data.append('')
                _csv_data.append(_data_result.get('cycle_time', ''))
                _csv_data.append('')
                _csv_data.append('')
                _csv_data.append(_data_result.get('start_time_t', ''))
                _csv_data.append(_data_result.get('end_time_t', ''))
                _csv_data.append(_error)
                _csv_data.append(_err_message)

                while len(_csv_data) < 18:
                    _csv_data.append('')

                _data_logs = _data.get('logs', [])
                # print('_data_logs =', _data_logs)

                _all_logs_in = []
                _all_logs_out = []

                for _log_item in _data_logs:
                    _log_in = _log_item.get('log_in')
                    if _log_in:
                        _all_logs_in.append(_log_in)

                    _log_out = _log_item.get('log_out')
                    if _log_out:
                        _all_logs_out.append(_log_out)

                if len(_csv_data) > 16:  # ParametersInput字段位置
                    _csv_data[16] = '\n'.join(_all_logs_in) if _all_logs_in else _csv_data[16]
                if len(_csv_data) > 17:  # ResultsOutput字段位置
                    _csv_data[17] = '\n'.join(_all_logs_out) if _all_logs_out else _csv_data[17]

                break
            # print('len(_csv_data) =', len(_csv_data))
            # print('_csv_data =', _csv_data)
            writer.writerow(dict(zip(header, _csv_data)))
