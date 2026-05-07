#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/4/16 12:31
=====================
"""
import os
import time
import pickle
from hashlib import sha1
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from configure.constants import PROJECT_PATH, SIG_PATH


class SignerServer(FileSystemEventHandler):
    def __init__(self, report=None):
        super().__init__()
        self.on_modified = self.on_moved = self.on_deleted = self.handleEvent
        self.__sigTab = {}
        self.__whiteList = []
        self.__reporter = report
        self.signatureStatus = True
        self.loadSignerTab()
        self.loadWhiteList()

    def loadSignerTab(self):
        if os.path.exists(SIG_PATH):
            with open(SIG_PATH, "rb") as f:
                sigTab = pickle.loads(f.read())
            for _path, code in sigTab.items():
                sigPath = os.path.join(PROJECT_PATH, _path.replace(f"<<root>>{os.path.sep}", ""))
                self.__sigTab[sigPath] = code
        if not self.__sigTab:
            self.report("signatureEvent", "Project has not signature!!", False)
            self.signatureStatus = False

    def loadWhiteList(self):
        """add white list to skip check signature"""
        pass

    def report(self, callback, *args):
        if self.__reporter:
            self.__reporter(callback, args)

    def handleEvent(self, event):
        targetFile = event.src_path
        if self.__sigTab.get(targetFile, None):
            self.checkSignature(targetFile)
        elif os.path.isdir(targetFile):
            for f in os.listdir(targetFile):
                subFile = os.path.join(targetFile, f)
                if not os.path.isfile(subFile) or not self.__sigTab.get(subFile, False):
                    continue
                self.checkSignature(subFile)

    def checkSignature(self, targetFile):
        fileType = os.path.splitext(targetFile)[-1]
        sigCode = self.__sigTab.get(targetFile, None)
        if sigCode and fileType.lower() in (".py", ".json", ".csv", ".lua", ".sh", ".png", ".jpg"):
            if not os.path.exists(targetFile):
                self.report("signatureEvent", targetFile, False)
                self.signatureStatus = False
                return
            with open(targetFile, "rb") as f:
                currCode = sha1(f.read()).hexdigest()
            if currCode != sigCode:
                self.report("signatureEvent", targetFile, False)
                self.signatureStatus = False

    def checkAllSignature(self):
        result = True
        sigFile = ""
        if self.signatureStatus is False:
            return
        for targetFile, sigCode in self.__sigTab.items():
            if not os.path.exists(targetFile):
                result = False
                sigFile = targetFile
                break
            with open(targetFile, "rb") as f:
                currCode = sha1(f.read()).hexdigest()
            if currCode != sigCode:
                result = False
                sigFile = targetFile
                break
        self.report("signatureEvent", sigFile, result)
        self.signatureStatus = result


if __name__ == "__main__":
    path = PROJECT_PATH
    event_handler = SignerServer()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
