#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/27 13:14
=====================
"""
import re
import os
import sys
import platform
from multiprocessing import freeze_support
from gui.startGUI import MainController
from PySide6.QtWidgets import QApplication
from gui.controller.msg_box import MessageBox
from rtrpcLib.common import Utility
from processes.processmanager import ProcessManage

import subprocess


def ping_connect(ip):
    cmd = "ping -c 2 -W 2 {}".format(ip)
    _, out, err = Utility.run_shell_with_timeout(cmd, timeout=3)
    out = str(out)
    result = "".join(out.split('\n')).strip()
    t = re.search('.*(ttl=64)', result)
    if not t:
        MessageBox.show(f'ping ip {ip} failed')

def cleanProcess():
    if platform.system() == "Windows":
        # windows will kill self process
        # os.system("taskkill /F /IM pythonw.exe")
        bat_script_path = ".\\killport.bat"

        result = subprocess.run([bat_script_path])

        # 检查执行结果
        if result.returncode == 0:
            print("killport success")
        else:
            print("killport failed: ", result.returncode)
        return
    else:
        os.system("pkill -9 Python")
        os.system("pkill -9 python")
        os.system("lsof -ti :6100-6300 | xargs kill")


if __name__ == "__main__":
    freeze_support()
    cleanProcess()
    rootPath = f'{os.path.sep}'.join(os.path.realpath(sys.argv[0]).split(os.path.sep)[0:-1])
    sys.path.append(rootPath)
    pm = ProcessManage()
    pm.start()
    app = QApplication(sys.argv)
    # ping_connect("169.254.1.32")
    gui = MainController()
    gui.processes = pm
    gui.load_pdca()
    gui.load_stop_on_fail()
    pm.closeEvent = gui.closeE
    gui.show()
    sys.exit(app.exec())
