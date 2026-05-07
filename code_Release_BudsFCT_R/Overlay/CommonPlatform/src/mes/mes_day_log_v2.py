import os
import datetime
import csv
import threading
import hashlib
import traceback
import ast
from datetime import datetime

from mes import mes_config


class MESDayLog(object):
    def __init__(self):
        self.writer = None
        self.file_csv = None
        self.log_file_path = ""
        self.log_file_name_check_md5 = ""
        self.__test_plan = dict()
        self.__reload_log_file_lock = threading.Lock()
        self.__write_log_lock = threading.Lock()
        self.__open_lock = threading.Lock()
        self.__header = []

        if not os.path.exists(mes_config.MES_LOG_PATH):
            os.mkdir(mes_config.MES_LOG_PATH)

    def reload_log_file(self, test_plan=None):
        try:
            self.__reload_log_file_lock.acquire(True)

            if test_plan:
                self.__test_plan = test_plan

            self.__open()
        except Exception as e:
            _format_exc = traceback.format_exc()
            print(_format_exc)
            print("MESDayLog-reload_log_file-Exception:{}".format(str(e)))
        finally:
            self.__reload_log_file_lock.release()

    def __open(self):
        try:
            self.__open_lock.acquire(True)

            if not self.__test_plan:
                # self.__open_lock.release()
                return

            _file_md5 = self.__test_plan.get("file_md5")
            _file_name = "{}_{}_{}_{}_mes_log_v2.csv".format(mes_config.TERMINAL_NAME,
                                                             self.__test_plan.get("name"),
                                                             _file_md5[:8],
                                                             datetime.now().strftime("%Y-%m-%d"))
            self.log_file_path = os.path.join(mes_config.MES_LOG_PATH, _file_name)
            # print("self.log_file_path =", self.log_file_path)

            log_file_name_check_md5_old = self.log_file_name_check_md5
            self.log_file_name_check_md5 = hashlib.md5((self.log_file_path + _file_md5).encode())
            self.__header = [
                "Product",
                "SN",
                "Station_ID",
                "Slot_ID",
                "PASS/FAIL",
                "Failed_List",
                "Total_Time(s)",
                "Start_time",
                "Stop_time",
                "Timestamp",
                "MES"
            ]
            _header1 = ["" for _ in range(len(self.__header))]
            _header2 = ["" for _ in range(len(self.__header))]
            _header3 = ["" for _ in range(len(self.__header))]
            _header1[0] = "Upper Limit----------->"
            _header2[0] = "Lower Limit----------->"
            _header3[0] = "Measurement unit------>"

            _case_list = self.__test_plan.get("case_list")[1:]
            for _item in _case_list:
                _case_item_str = _item[1]
                _case_item = ast.literal_eval(_case_item_str)

                _subsubtestname = _case_item.get("SubSubTestName")
                if not _subsubtestname or not _subsubtestname.startswith("@"):
                    continue

                _subsubtestname = _subsubtestname.removeprefix("@")
                _v = "{}".format(_subsubtestname)
                self.__header.append(_v)
                _header1.append(_case_item.get("UpperLimit", ""))
                _header2.append(_case_item.get("LowerLimit", ""))
                _header3.append(_case_item.get("Units", ""))

            _write_header_tag = False
            if not os.path.exists(self.log_file_path):
                _write_header_tag = True

            self.file_csv = open(self.log_file_path, "a+", encoding="utf-8-sig", newline='')
            self.writer = csv.DictWriter(self.file_csv, fieldnames=self.__header)

            if self.log_file_name_check_md5 != log_file_name_check_md5_old and _write_header_tag:
                self.writer.writeheader()
                self.writer.writerows([dict(zip(self.__header, _header1)),
                                       dict(zip(self.__header, _header2)),
                                       dict(zip(self.__header, _header3))
                                       ])
                self.file_csv.flush()
        except Exception as e:
            _format_exc = traceback.format_exc()
            print(_format_exc)
            print("MESDayLog-__open-Exception:{}".format(str(e)))
        finally:
            self.__open_lock.release()

    def get_log_file_path(self):
        return self.log_file_path

    def write_blank_line(self):
        self.writer.writerow({})
        self.file_csv.flush()

    def write_datas(self, site, param, datas, sn):

        try:
            self.__write_log_lock.acquire(True)

            sn = sn
            result = param.get("result", False)
            timestamp = param.get("timestamp", "")
            stop_time = param.get("stop_time", "")
            total_time = param.get("total_time", "")
            start_time = param.get("start_time", "")
            log_upload_swith = "Enable" if param.get("log_upload_swith", False) else "Disable"
            print("log_upload_swith =", log_upload_swith)

            __data = [
                mes_config.PROJECT_CODE,
                sn,
                mes_config.TERMINAL_NAME,
                site + 1,
                "PASS" if result else "FAIL",
                param.get("failed_list", ""),
                total_time,
                start_time,
                stop_time,
                timestamp,
                log_upload_swith
            ]

            for _item in datas:
                _value = _item.get("value", "")
                if isinstance(_value, bool):
                    _value = "PASS" if _value else "FAIL"
                __data.append(_value)
            self.writer.writerow(dict(zip(self.__header, __data)))
            self.file_csv.flush()
        except Exception as e:
            print("MESDayLog-write_datas-Exception:{}".format(str(e)))
        finally:
            self.__write_log_lock.release()


if __name__ == "__main__":
    # print("=" * 20)
    pass
