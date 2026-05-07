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
import signal
import json
import subprocess
from threading import Thread
from processes.smserver import StateMachineServer
from configure.constants import CONSTANT_FILE, PROJECT_PATH, PLATFORM, SLOTS


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
        self.launcher()

    def _load_config(self):
        self.config = None
        if not os.path.exists(self.config_file):
            return
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
        if self.config:
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
            process = subprocess.Popen(cmd, cwd=cwd, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
            # process = subprocess.Popen(cmd, cwd=cwd, env=env)
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
            if not process_cmd:
                continue
            self.start_process(process_name, process_cmd)

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