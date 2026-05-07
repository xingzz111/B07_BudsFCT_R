#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/6/18 09:57
=====================
"""

import os
import sys
import time
from datetime import datetime
import signal
import logging
import json
import subprocess
from threading import Thread
import re
from processes.smserver import StateMachineServer
from configure import constants as constant
from configure.constants import CONSTANT_FILE, PROJECT_PATH, PLATFORM, SLOTS
from rtlib.ictmes import get_mes_status, save_mes_status
from rtfixture.fixture_server import FixtureServer

from mes.mes_log_server import MESLogServer


def setup_logger(log_dir):
    """
    设置 logger，日志文件名包含当前的日期和时间。
    :param log_dir: 日志保存的目录路径
    :return: 配置好的 logger 对象
    """
    # 获取当前时间并生成日志文件名
    log_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "process_log.txt"
    log_filepath = os.path.join(log_dir, log_filename)

    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)

    # 配置 logger
    logging.basicConfig(
        filename=log_filepath,
        level=logging.DEBUG,  # 可以根据需要修改为 INFO 或 ERROR
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='a'  # 'a' 表示追加模式，如果文件不存在则创建
    )

    # 记录启动信息
    logging.info("Logger initialized.")
    return logging


class ProcessManage(Thread):
    def __init__(self, config_file=CONSTANT_FILE):
        super().__init__()
        self.setDaemon(True)
        self.processes = {}
        self.config_file = config_file
        self.config = None
        self.closeEvent = None
        self.smserver = StateMachineServer(SLOTS)
        self.smserver.start()
        self.daemon = False
        self.logger = setup_logger("D:/vault/StationLog")
        self.launcher()
        self.start_mes_log_server()
        if not constant.SIMULATE:
            self.fixture_server_start()

    def _load_config(self):
        self.config = None
        if not os.path.exists(self.config_file):
            return
        self.logger.info("open file : {}".format(self.config_file))
        print(self.config_file)
        with open(self.config_file, "r") as f:
            self.config = json.load(f)
        return self.config

    def _get_config(self, key):
        if self.config:
            return self.config.get(key, None)
        return None

    def _set_config(self, key, value):
        if self.config:
            self.config[key] = value
            return True
        return False

    def _save_config_file(self):
        if not os.path.exists(self.config_file):
            return False
        self.logger.info("save file : {}".format(self.config_file))
        if self.config:
            self.logger.info("{}".format(self.config))
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(self.config, file, ensure_ascii=False, indent=4, sort_keys=False)
                return True
        return False

    def check_pdca_status(self):
        config = self._load_config()
        process = config.get("processes", {})
        process_name = "logger"
        process_cmd = list(process.get(process_name)["command"])
        key = "--disable_pudding"
        if key in process_cmd:
            return False
        return True

    def check_stoponfail_status(self):
        config = self._load_config()
        process = config.get("processes", {})
        for k,v in process.items():
            process_name = "sequence"
            if process_name in k:
                process_cmd = list(process.get(k)["command"])
                key = "-c"
                if key in process_cmd:
                    return False
        return True

    def open_mes(self, enable=True):
        save_mes_status(isenable=enable)
        return get_mes_status()

    def check_mes_status(self):
        return get_mes_status()

    def open_pdca(self, enable=True):
        config = self._load_config()
        process = config.get("processes", {})
        process_name = "logger"
        process_cmd = process.get(process_name)["command"]
        process_cmd = list(process_cmd)
        key = "--disable_pudding"
        if key in list(process_cmd) and enable:
            process_cmd.remove(key)
        else:
            if not enable:
                process_cmd.append(key)
        process[process_name]["command"] = process_cmd
        self._set_config("processes", process)
        self._save_config_file()
        self.restart_process(process_name,  process[process_name])

    def stop_on_fail(self, enable=True):
        config = self._load_config()
        process = config.get("processes", {})
        for k, v in process.items():
            if "sequencer" in k:
                process_name = k
                process_cmd = process.get(process_name)["command"]
                process_cmd = list(process_cmd)
                key = "-c"
                if key in list(process_cmd) and enable:
                    process_cmd.remove(key)
                else:
                    if not enable:
                        process_cmd.append(key)
                process[process_name]["command"] = process_cmd
        self._set_config("processes", process)
        self._save_config_file()
        for k, v in process.items():
            if "sequencer" in k:
                self.restart_process(k,  process[k])


    def restart_process(self, process_name, process_cmd):
        self.stop_process(process_name)
        self.start_process(process_name, process_cmd)

    def start_process(self, process_name, process_cmd):
        try:
            cmd = process_cmd.get("command")
            _cwd = f'{os.path.sep}'.join(os.path.realpath(sys.argv[0]).split(os.path.sep)[0:-1])

            cwd = process_cmd.get("cwd", _cwd)
            env = os.environ.copy()
            env["PYTHONPATH"] = PROJECT_PATH
            self.logger.info("start_process: {}".format(cmd))
            if PLATFORM == "Windows":
                # process = subprocess.Popen(cmd, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
                process = subprocess.Popen(cmd, cwd=cwd, env=env)
            else:
                process = subprocess.Popen(cmd, cwd=cwd, env=env)
            self.processes[process_name] = process
        except subprocess.SubprocessError as e:
            print(f"Error occurred while executing command: {e}")
        except OSError as e:
            print(f"OS error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def stop_process(self, process_name):
        try:
            process = self.processes[process_name]
            # processes.terminate()
            if PLATFORM == "Windows":
                cmd = f"taskkill /F /pid {process.pid}"
                self.logger.info("stop_process: {}".format(cmd))
                p = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW, shell=True)
                p.wait()
            else:
                os.kill(process.pid, signal.SIGKILL)
            self.processes.pop(process_name)
            print(self.processes)
        except OSError:
            pass

    def launcher(self):
        config = self._load_config()
        for process_name, process_cmd in config.get("processes", {}).items():
            if process_name == "engine":
                father_path = re.search("(\w:\\\[\w]+)", self.config_file).group(0)
                father_path = father_path.replace("\\", "\\")
                new_cmd = father_path + process_cmd.get("command")[0]
                process_cmd["command"] = [new_cmd]

            if not process_cmd:
                continue
            self.start_process(process_name, process_cmd)

    def start_mes_log_server(self):
        # mes log
        for slot in range(constant.SLOTS):
            self.mes_log_server = MESLogServer(slot)
            self.mes_log_server.daemon = True
            self.mes_log_server.start()

    def fixture_server_start(self):
        fs = FixtureServer()
        if fs.connect():
            fs.start()
            # fs.join()

    def run(self):
        while True:
            if not self.closeEvent or not self.closeEvent.wait(1):
                continue
            self.smserver.receiving = False
            for ps in list(self.processes.keys()):
                self.stop_process(ps)
            self.smserver.join()
            break

# a = ProcessManage()
# a.stop_on_fail(True)