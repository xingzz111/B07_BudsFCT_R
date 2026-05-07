#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/22 15:31
=====================
"""

import os
import sys
import zmq
import time
import traceback
from functools import partial
from threading import Thread
from multiprocessing import freeze_support
from multiprocessing import Queue, Event
from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog

from rtrpcLib import zmqports
from rtrpcLib import events, levels
from rtrpcLib.common import Report, Utility
from rtrpcLib.common import TesterReporter
from rtrpcLib.rpc.publisher import ZmqPublisher
from configure.constants import State
from configure import constants as constant
from gui.controller.baseview import BaseView
from gui.controller.scan import ScanController
from gui.controller.heater import HeaderController
from gui.controller.content import ContentController
from gui.controller.subscriber import SequencerSubscriberProcess
from rtlib.ictmes import get_mes_status


class MainController(BaseView):
    _signalMessageBox = Signal(str, int)
    _signalEvent = Signal(int, Report)
    _signalHeater = Signal()
    _signalContent = Signal()
    _signalScan = Signal()

    def __init__(self):
        self.heaterC = HeaderController(self._signalMessageBox)
        self.contentC = ContentController(self._signalMessageBox)
        self.scanC = ScanController(self._signalMessageBox)
        super().__init__(self.heaterC.view, self.contentC.view, self.scanC.view)
        if constant.SCANNER_FLAG:
            self.scanC.view.lineEditSn.setEnabled(False)
        if constant.HSM:
            os.startfile(constant.yubi_path)
        self._queue = Queue()
        self.closeE = Event()
        self.subscriberC = None
        self.isTesting = False
        self.isLoading = False
        self._receive = True
        self._tpPath = ""
        self._handleThread = None
        self._publisher = None
        self._reporter = None
        self.processes = None
        self._testLogPath = os.path.expanduser("~") + "/vault/StationLog"
        self._slotsSeq = {}
        self.taskTimer = QTimer()
        self.connectAction()
        self.launcher()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Question',"Are you sure to quit?",
                                     QMessageBox.Yes, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.closeE.set()
            self._receive = False
            self._handleThread.join()
            self.subscriberC.join()
            event.accept()
        else:
            event.ignore()

    def launcher(self):
        self.subscriberC = SequencerSubscriberProcess(self._queue, self.closeE)
        self.subscriberC.start()
        self._handleThread = Thread(target=self._pollerEvent, name='application_poller_event')
        self._handleThread.daemon = True
        self._handleThread.start()
        ctx = zmq.Context().instance()
        self._publisher = ZmqPublisher(
            ctx, constant.DEFAULT_TRANSPORT_PROTOCOL_SERVER + str(zmqports.PRM_GUI_PUB), "PRM_GUI"
        )
        self._reporter = TesterReporter(self._publisher)
        self.scanC.reporter = self._reporter
        self.scanC.setFocusScan()
        tpFile = Utility.get_first_absPathFile(constant.PROFILE)
        self.addTaskWithTimer(500, self.loadTestPlan, tpFile)

    def connectAction(self):
        self._signalEvent.connect(self.handleEvent)
        self._signalMessageBox.connect(self.messageBox)
        self.scanC.view.buttonLogin.clicked.connect(self.login)
        self.scanC.view.buttonLoad.clicked.connect(self.loadTestPlan)
        self.scanC.view.buttonReLoad.clicked.connect(self.openPDCA)
        self.scanC.view.stopOnFail.clicked.connect(self.stop_on_fail)
        self.scanC.view.buttonLoop.clicked.connect(self.loopAction)
        self.scanC.view.buttonLogPath.clicked.connect(self.openTestLog)
        self.scanC.view.buttonStart.clicked.connect(self.startTest)
        self.scanC._signalLoop.connect(self.startTest)
        self.scanC.view.buttonStop.clicked.connect(self.abortTest)
        self.scanC.view.lineEditSn.returnPressed.connect(self.scanAction)


    def createTesterEvent(self, *req):
        self._reporter.create_report(events.PRM_SM_REQ, req)

    def addTaskWithTimer(self, timeout:int, func, *args):
        self.taskTimer.singleShot(timeout, partial(func, *args))

    @classmethod
    def messageBox(cls, msg, event=levels.INFO):
        if event == levels.INFO:
            QMessageBox.information(QMessageBox(), "Done", str(msg))
        elif event == levels.WARNING:
            QMessageBox.warning(QMessageBox(), "Warning", str(msg), buttons=QMessageBox.Ok)
        elif event == levels.CRITICAL:
            QMessageBox.critical(QMessageBox(), "Error", str(msg), buttons=QMessageBox.Ok)

    def _pollerEvent(self):
        while self._receive:
            try:
                if self._queue.empty():
                    time.sleep(0.01)
                    continue
                site, message = self._queue.get()
                if message is None:
                    continue
                self._signalEvent.emit(site, message)
            finally:
                time.sleep(0.001)
                QApplication.processEvents()

    def handleEvent(self, site, message):
        try:
            if message.event == events.SEQUENCE_START:
                self.sequence_start(site)
            elif message.event == events.SEQUENCE_END:
                result = message.data.get('result', 0)
                self.sequence_end(site, result)
            elif message.event == events.ITEM_START:
                self.item_start(site, message)
            elif message.event == events.ITEM_FINISH:
                self.item_finish(site, message)
            elif message.event == events.UOP_DETECT or message.event == events.IP_START_FAIL_DETECT:
                self._signalMessageBox.emit(str(message), levels.CRITICAL)
            elif message.event == events.PRM_SM_REP:
                self.handleSMEvent(message.data)
            elif message.event == events.PRM_FIXTURE_EVENT:
                self.handleFixtureEvent(message.data)
            elif message.event == events.ATTRIBUTE_FOUND:
                name = message.data['name']
                value = str(message.data['value'])
                if name == "scanned_sn" and "FAIL" not in value:
                    self.scanC.slotsC.setText(site, value)
            ## todo wait develop
            # elif message.event == events.ABORT:
            #     self.create_gui_report('abort', ())
            # elif message.event == events.TEST_ENGINE_EVENT:
            #     self._signalTestEngineEvent.emit(message.data)
            # elif message.event == events.TESTER_EVENT:
            #     # print message
            #     self._signalTesterEvent.emit(message.data)
        except TypeError:
            print(traceback.format_exc())

    def sequence_start(self, site):
        self._slotsSeq[site] = {
            "result": False,
            "isFinish": False
        }
        self.contentC.testPlanC.sequence_start(site)
        self.scanC.slotsC.setState(site, State.RUNNING)
        if self.scanC.looping and self.scanC.loopAction == "NoAction":
            self.heaterC.startTest()
        self.contentC.startTest()

    def sequence_end(self, site, result):
        result = True if result > 0 else False
        state = result and State.PASS or State.FAIL
        self._slotsSeq[site]["isFinish"] = True
        self._slotsSeq[site]["result"] = result
        self.scanC.slotsC.setState(int(site), state)
        self.scanC.updateYield(result)
        self.contentC.testPlanC.sequence_end(site)
        checkFinish = all([self._slotsSeq[i]["isFinish"] for i in self._slotsSeq.keys()])
        if checkFinish:
            overallResult = all([self._slotsSeq[i]["result"] for i in self._slotsSeq.keys()])
            self.sequence_finish(overallResult)

    def sequence_finish(self, result):
        self.contentC.endTest(result)
        self.scanC.endTest(result)
        self._slotsSeq = {}
        self.isTesting = False
        if constant.SIMULATE:
            self.createTesterEvent("test_finish")
            self.heaterC.endTest(result)
            return
        elif self.scanC.looping and self.scanC.loopAction == "NoAction":
            self.createTesterEvent("test_finish")
            self.heaterC.endTest(result)
            return
        self.createTesterEvent("fixture_end")

    def item_start(self, site, message):
        self.contentC.testPlanC.item_start(site, message)

    def item_finish(self, site, message):
        self.contentC.testPlanC.item_finish(site, message)

    def handleSMEvent(self, message):
        func, params = message
        if hasattr(self, func):
            getattr(self, func)(*tuple(params))
        else:
            print(f'Tester Event {func} not exist')

    def handleFixtureEvent(self, message):
        _nFixtureId, event = message
        if event == 'group_start':
            self.isTesting = True
            self.startTest()
        elif event == 'group_end':
            self.createTesterEvent("test_finish")
            self.heaterC.endTest(None)
            self.abortTest()
        elif event.startswith('[AutoScan]:'):
            isOKtoStart = True
            sn_list = event.replace('[AutoScan]:', '').strip().split("@")
            for k,v in enumerate(sn_list):
                if self.scanC.slotsC.currState(k) not in ("DISABLE", "READY", "RUNNING"):
                    if v == "None" or len(v) != 23:
                        self.messageBox(f"SLOT{k} SN: '{v}' is invalid!", levels.CRITICAL)
                        self.createTesterEvent("fixture_out")
                        isOKtoStart = False
                        self.heaterC.endTest(None)
                        break
                    else:
                        self.scanC.updateSn(v)
                # self.startTest()
            if isOKtoStart:
                self.createTesterEvent("fixture_down")
            else:
                for index in range(constant.SLOTS):
                    if self.scanC.slotsC.currState(index) not in ("DISABLE"):
                        self.scanC.slotsC.setState(index, State.IDLE)
        elif event.startswith('[NoScan]:'):
            sn_list = event.replace('[NoScan]:', '').strip().split("@")
            for k,v in enumerate(sn_list):
                if self.scanC.slotsC.currState(k) not in ("DISABLE", "READY", "RUNNING"):
                    self.scanC.updateSn(v)
            time.sleep(1)
            self.createTesterEvent("fixture_down")
        elif event == 'start_counting' and self.scanC.isReady():
            self.heaterC.start_header_timer()
        elif event.startswith('[Message]:'):
            info = event.replace('[Message]:', '')
            self._signalMessageBox.emit(info, levels.WARNING)

    def loadDone(self, load_states, info):
        if load_states:
            self.isLoading = True
            self.contentC.testPlanC.load_test_plan(self._tpPath)
            projectInfo, versionInfo = Utility.parseTestPlan(self._tpPath)
            self.heaterC.updateProjectInfo(projectInfo, versionInfo)
        else:
            self._signalMessageBox.emit(info, levels.WARNING)

    def startTest(self, flag=False):
        e_travelers = self.scanC.isReady()
        if not flag and not constant.SIMULATE and not self.isTesting:
            self.heaterC.startTest()
            for index in range(constant.SLOTS):
                self.contentC.testPlanC.tpAllModel.clean_column(index)
                self.contentC.testPlanC.tpStaticModel.clean_column(index)
            if constant.SCANNER_FLAG:
                self.createTesterEvent("fixture_in")
            else:
                self.createTesterEvent("fixture_start")
            return
        if e_travelers and self.isLoading:
            self.createTesterEvent("start_test", e_travelers)
            self.scanC.startTest(e_travelers)
            self.contentC.startTest()
            if constant.SIMULATE:
                self.heaterC.startTest()
        elif self.scanC.view.lineEditSn.text() != "":
            currSn = self.scanC.view.lineEditSn.text().strip().upper()
            self.scanC.updateSn(currSn)
            self.startTest()

    def abortTest(self):
        if self.isTesting:
            self.createTesterEvent("abort_test")
        self.isTesting = False

    def login(self):
        self.scanC.login()

    def openTestLog(self):
        if constant.PLATFORM == "Darwin":
            os.system("open /vault/StationLog")
        elif constant.PLATFORM == "Linux":
            os.system(f"xdg-open {self._testLogPath}")
        elif constant.PLATFORM == "Windows":
            os.system("explorer D:\\vault\\StationLog")

    def loadTestPlan(self, tpPath=None):
        try:
            if tpPath:
                _selectedFile = tpPath
            else:
                _pathProfile = constant.PROFILE
                _selectedFile, _ = QFileDialog.getOpenFileName(QFileDialog(), 'Select test plan', _pathProfile,
                                                               "*.csv", options=QFileDialog.DontUseNativeDialog)
            if not _selectedFile:
                return
            elif os.path.exists(_selectedFile):
                self._tpPath = _selectedFile
                self.createTesterEvent("load", _selectedFile)
            else:
                self._signalMessageBox.emit(f"{_selectedFile} not exists!", levels.WARNING)
        except Exception as e:
            self._signalMessageBox.emit(f"Open file dialog exception {e}", levels.CRITICAL)

    def reloadTestPlan(self):
        self.createTesterEvent("load", self._tpPath)

    def openPDCA(self):
        self.scanC.view.buttonReLoad.setEnabled(False)
        if get_mes_status():
            self.processes.open_mes(False)
            self.heaterC.view.enable_pdca(False)
        else:
            self.processes.open_mes(True)
            self.heaterC.view.enable_pdca(True)
        self.scanC.view.buttonReLoad.setEnabled(True)

    def stop_on_fail(self):
        self.scanC.view.stopOnFail.setEnabled(False)
        if self.processes.check_stoponfail_status():
            self.processes.stop_on_fail(False)
            self.scanC.view.stopOnFail.setText("ContinueOnFail")
            # self.heaterC.view.enable_pdca(False)
        else:
            self.processes.stop_on_fail(True)
            self.scanC.view.stopOnFail.setText("StopOnFail")
            # self.heaterC.view.enable_pdca(True)
        self.reloadTestPlan()
        self.scanC.view.stopOnFail.setEnabled(True)

    def load_pdca(self):
        if get_mes_status():
            self.heaterC.view.enable_pdca(True)
        else:
            self.heaterC.view.enable_pdca(False)
        return

    def load_stop_on_fail(self):
        if self.processes.check_stoponfail_status():
            self.scanC.view.stopOnFail.setText("StopOnFail")
            # self.heaterC.view.enable_pdca(False)
        else:
            self.scanC.view.stopOnFail.setText("ContinueOnFail")
            # self.heaterC.view.enable_pdca(True)
        return


    def loopAction(self):
        if self.scanC.looping:
            self.scanC.stopLoop()
        elif constant.SIMULATE:
            if not self.scanC.isReady():
                self._signalMessageBox.emit(f"Please scan SN first!", levels.WARNING)
                return
            self.scanC.startLoop()
            self.startTest(True)
        elif self.isLoading and not self.isTesting:
            self.scanC.startLoop()
            self.heaterC.startTest()
            if constant.SCANNER_FLAG:
                self.createTesterEvent("fixture_in")
            else:
                self.createTesterEvent("fixture_start")
            return
            self.scanC.startLoop()

    def scanAction(self):
        currSn = self.scanC.view.lineEditSn.text().strip().upper()
        if currSn:
            self.scanC.updateSn(currSn)

    def signatureEvent(self, sigFile, flag):
        if self.heaterC.signatureStatus and not flag:
            self.heaterC.updateSecurity(flag)
            self._signalMessageBox.emit(f"{sigFile} checksum fail!", levels.CRITICAL)


if __name__ == "__main__":
    freeze_support()
    app = QApplication(sys.argv)
    window = MainController()
    window.show()
    sys.exit(app.exec())
