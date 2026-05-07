#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/3/22 16:56
=====================
"""
import re

from rtrpcLib import levels
from configure import constants
from configure.constants import State
from rtrpcLib.common import print_with_time
from configure.constants import ResetButtonQSS, UserPng, ResetPng
from gui.resources.style import Color
from gui.controller.login import LoginController
from gui.controller.slots import SlotsController
from PySide6.QtGui import QPixmap, QRegularExpressionValidator, QIcon, QKeySequence
from PySide6.QtCore import Qt, QObject, QSize, QRegularExpression, QTimer, Signal
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGroupBox, QPushButton,
    QGridLayout, QLineEdit, QSpacerItem, QSizePolicy, QComboBox
)


class ScanController(QObject):
    _signalLoop = Signal(bool)

    def __init__(self, signalBox=None):
        super().__init__()
        self._signalBox = signalBox
        self._looping = False
        self.reporter = None
        self._bufferETravelers = None
        self._timer = QTimer()
        self._timer.timeout.connect(self.nextCycle)
        self.slotsC = SlotsController(slots=constants.SLOTS)
        self.view = ScanView(self.slotsC.view)
        self.user = "NONE-Administrator"  ## just debug
        self.changeMode(self.user)

    def messageBox(self, msg, level=levels.INFO):
        if self._signalBox:
            self._signalBox.emit(msg, level)
        else:
            print_with_time(msg)
    @property
    def looping(self):
        return self._looping

    @property
    def loopAction(self):
        return self.view.selectLoopAction.currentText()

    def updateSn(self, mlbSn:str):
        if constants.CHECK_SN_LENGTH:
            if len(mlbSn) != constants.SN_LENGTH:
                self.clearScanText()
                self.setFocusScan()
                return self.messageBox(f"MLB: {mlbSn} Length is not {constants.SN_LENGTH}", level=levels.WARNING)
            if constants.CHECK_SN_PATTERN:
                if not re.match(constants.SN_PATTERN, mlbSn):
                    self.clearScanText()
                    self.setFocusScan()
                    return self.messageBox(f"MLB: {mlbSn} is not right,pls check", level=levels.WARNING)
        targetIndex = None
        for index in range(constants.SLOTS):
            currState = self.slotsC.currState(index)
            tmpSN = self.slotsC.currText(index)
            if currState == State.DISABLE:
                continue
            elif currState == State.READY and mlbSn.strip().upper() == tmpSN:
                self.clearScanText()
                self.setFocusScan()
                return self.messageBox(f"Repeated MLB: {mlbSn}", level=levels.WARNING)
            elif targetIndex is None and currState not in (State.READY, State.RUNNING):
                targetIndex = index
        if isinstance(targetIndex, int):
            self.slotsC.setText(targetIndex, mlbSn)
            self.slotsC.setState(targetIndex,State.READY)
        self.clearScanText()
        self.setFocusScan()

    def isReady(self):
        if self._looping and self._bufferETravelers:
            return self._bufferETravelers
        e_travelers = dict()
        for index in range(constants.SLOTS):
            currState = self.slotsC.currState(index)
            if currState not in (State.READY, State.DISABLE):
                return None
            elif currState == State.READY:
                currSn = self.slotsC.currText(index)
                e_travelers.setdefault(str(index), {"attributes": {"MLBSN": currSn, "cfg": ""}})
        return e_travelers

    def startTest(self, e_travelers=None):
        self._bufferETravelers = e_travelers or self._bufferETravelers
        self.view.buttonStart.setEnabled(False)
        self.view.lineEditSn.setEnabled(False)
        self.view.lineEditSn.setText("")
        self.view.buttonLoad.setEnabled(False)
        self.view.buttonReLoad.setEnabled(False)
        if not self._looping:
            self.view.buttonLoop.setEnabled(False)

    def endTest(self, result):
        self.changeMode(self.user)
        self.view.buttonStart.setEnabled(True)
        if not constants.SCANNER_FLAG:
            self.view.lineEditSn.setEnabled(True)
            self.view.lineEditSn.setFocus()
        self.checkLoop()

    def startLoop(self):
        self._looping = True
        self.view.buttonLoop.setEnabled(True)
        self.view.buttonLoop.setText("Loop Out")
        self.view.buttonStart.setEnabled(False)
        
    def stopLoop(self):
        self._looping = False
        self.view.buttonLoop.setText("Loop In")
    
    def checkLoop(self):
        if not self._looping:
            self._bufferETravelers = None
            return False
        loopCount = int(self.view.lineEditLoopCount.text()) - 1
        if loopCount <= 0:
            self.changeMode(self.user)
            self.view.lineEditLoopCount.setText("0")
            self.view.buttonLoop.setText("Loop In")
            self.view.buttonStart.setEnabled(True)
            self.view.lineEditSn.setEnabled(True)
            self.view.lineEditSn.setFocus()
            self._bufferETravelers = None
            self._looping = False
            return False
        else:
            self.view.lineEditLoopCount.setText(f"{loopCount}")
            duration = int(self.view.lineEditLoopDuration.text())
            self._timer.start(duration)
        return True

    def nextCycle(self):
        self._timer.stop()
        flag = self.loopAction != "Normal"
        self._signalLoop.emit(flag)

    def login(self):
        user = "Operator"
        if self.view.buttonLogin.text() == "Login":
            if LoginController.get_password():
                user = "Administrator"
        return self.changeMode(user)

    def changeMode(self, user):
        if user == "Administrator":
            self.view.buttonLogin.setText("Logout")
            self.view.labCurrUser.setText("Administrator")
            self.view.labCurrUser.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.view.buttonLoad.setEnabled(True)
            self.view.buttonReLoad.setEnabled(True)
            self.view.buttonLoop.setEnabled(True)
            self.view.stopOnFail.setEnabled(True)
        else:
            self.view.buttonLogin.setText("Login")
            self.view.labCurrUser.setText("Operator")
            self.view.labCurrUser.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.view.buttonLoad.setEnabled(False)
            self.view.buttonReLoad.setEnabled(False)
            self.view.buttonLoop.setEnabled(False)
            self.view.stopOnFail.setEnabled(False)
        self.user = user

    def updateYield(self, result):
        passCount = int(self.view.labPassCount.text())
        failCount = int(self.view.labFailCount.text())
        passCount = passCount + 1 if result else passCount
        failCount = failCount if result else failCount + 1
        totalCount = passCount + failCount
        passRate = round((passCount / totalCount) * 100, 2)
        failRate = round((failCount / totalCount) * 100, 2)
        self.view.labPassCount.setText(f"{passCount}")
        self.view.labFailCount.setText(f"{failCount}")
        self.view.labTotalCount.setText(f"{totalCount}")
        self.view.labPassRate.setText(f"{passRate}%")
        self.view.labFailRate.setText(f"{failRate}%")

    def clearScanText(self):
        self.view.lineEditSn.setText("")

    def setFocusScan(self):
        self.view.lineEditSn.setFocus()


class ScanView(QFrame):
    def __init__(self, slotsView):
        super(ScanView, self).__init__()
        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(5)
        self.mainLayout.addWidget(slotsView)
        ## lineEdit
        self.lineEditSn = None
        self.lineEditLoopCount = None
        self.lineEditLoopDuration = None
        self.selectLoopAction = None
        ## button
        self.buttonLogin = None
        self.buttonReset = None
        self.buttonLoad = None
        self.buttonReLoad = None
        self.buttonLoop = None
        self.buttonLogPath = None
        self.stopOnFail = None
        self.buttonStart = None
        self.buttonStop = None
        ## text label
        self.labPassCount = None
        self.labFailCount = None
        self.labTotalCount = None
        self.labPassRate = None
        self.labFailRate = None
        self.labCurrUser = None
        self.labFixtureText = None
        self.labUserText = None
        self.labOverlay = None
        ## widgets layout
        self.yieldLayout()
        self.controlLayout()
        # self.infoLayout()
        self.snScanLayout()
        self.setLayout(self.mainLayout)
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)

    def controlLayout(self):
        loginBox = QGroupBox()
        subLayout = QVBoxLayout(loginBox)
        subLayout.setContentsMargins(0, 0, 0, 0)
        subLayout.setSpacing(0)

        top1Layout = QHBoxLayout()
        top1Layout.setSpacing(2)
        top1Layout.setContentsMargins(0, 0, 0, 0)
        labUserPng = QLabel()
        # labUserPng.setFixedSize(40, 40)
        pixMap = QPixmap(UserPng)
        pixMap = pixMap.scaled(QSize(30, 30), Qt.KeepAspectRatio)
        labUserPng.setPixmap(pixMap)
        labUserPng.setAlignment(Qt.AlignCenter)
        labUserPng.setFixedSize(38, 30)
        self.labCurrUser = QLabel("Administrator")
        self.labCurrUser.setFixedSize(90, 30)
        self.labCurrUser.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.buttonLogin = QPushButton("Logout")
        top1Layout.addWidget(labUserPng)
        top1Layout.addWidget(self.labCurrUser)
        top1Layout.addWidget(self.buttonLogin)

        top2Layout = QHBoxLayout()
        top2Layout.setSpacing(2)
        top2Layout.setContentsMargins(0, 0, 0, 0)
        self.buttonLoad = QPushButton("Load")
        self.buttonLoad.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_L))
        self.buttonReLoad = QPushButton("MES")
        self.buttonReLoad.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_R))
        top2Layout.addWidget(self.buttonLoad)
        top2Layout.addWidget(self.buttonReLoad)

        top3Layout = QHBoxLayout()
        top3Layout.setSpacing(2)
        top3Layout.setContentsMargins(0, 0, 0, 0)
        self.buttonLoop = QPushButton("Loop In")
        self.buttonLogPath = QPushButton("TestLog")
        self.stopOnFail = QPushButton("StopOnFail")
        top3Layout.addWidget(self.buttonLoop)
        top3Layout.addWidget(self.buttonLogPath)
        top3Layout.addWidget(self.stopOnFail)

        top4Layout = QGridLayout()
        top4Layout.setSpacing(2)
        top4Layout.setContentsMargins(0, 0, 0, 0)
        labLoopCount = QLabel("LoopCount")
        self.lineEditLoopCount = QLineEdit("5")
        numValidator = QRegularExpressionValidator(QRegularExpression("[0-9]+"))
        self.lineEditLoopCount.setValidator(numValidator)
        labLoopDuration = QLabel("LoopDuration(ms)")
        self.lineEditLoopDuration = QLineEdit("5000")
        self.lineEditLoopDuration.setValidator(numValidator)
        labLoopAction = QLabel("LoopAction")
        self.selectLoopAction = QComboBox()
        self.selectLoopAction.addItems(["Normal", "NoAction"])
        self.selectLoopAction.setCurrentText("Normal")
        top4Layout.addWidget(labLoopAction, 0, 0)
        top4Layout.addWidget(self.selectLoopAction, 0, 1)
        top4Layout.addWidget(labLoopCount, 1, 0)
        top4Layout.addWidget(self.lineEditLoopCount, 1, 1)
        top4Layout.addWidget(labLoopDuration, 2, 0)
        top4Layout.addWidget(self.lineEditLoopDuration, 2, 1)

        subLayout.addLayout(top1Layout)
        subLayout.addLayout(top2Layout)
        subLayout.addLayout(top3Layout)
        subLayout.addLayout(top4Layout)
        self.mainLayout.addWidget(loginBox)

    def infoLayout(self):
        infoBox = QGroupBox()
        subLayout = QVBoxLayout(infoBox)
        subLayout.setContentsMargins(0, 0, 0, 0)
        fixtureID = QLabel("FixtureID:")
        self.labFixtureText = QLabel()
        userID = QLabel("OperatorID:")
        self.labUserText = QLabel()
        overlayID = QLabel("Overlay:")
        self.labOverlay = QLabel()
        subLayout.addWidget(fixtureID)
        subLayout.addWidget(self.labFixtureText)
        subLayout.addWidget(overlayID)
        subLayout.addWidget(self.labOverlay)
        subLayout.addWidget(userID)
        subLayout.addWidget(self.labUserText)
        self.mainLayout.addWidget(infoBox)

    def yieldLayout(self):
        subLayout = QHBoxLayout()
        yieldBox = QGroupBox()
        leftLayout = QVBoxLayout()
        self.buttonReset = QPushButton()
        if constants.PLATFORM == "Darwin":
            self.buttonReset.setStyleSheet(ResetButtonQSS)
        else:
            self.buttonReset.setIcon(QIcon(ResetPng))
            self.buttonReset.setIconSize(QSize(20, 20))
        self.buttonReset.setFixedSize(25, 25)
        self.buttonReset.clicked.connect(self.clean)
        labPass = QLabel("PASS:")
        labFail = QLabel("FAIL:")
        labTotal = QLabel("Total:")
        leftLayout.addWidget(self.buttonReset, 1)
        leftLayout.addWidget(labPass)
        leftLayout.addWidget(labFail)
        leftLayout.addWidget(labTotal)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftLayout.setSpacing(0)

        middleLayout = QVBoxLayout()
        lbl_fail_1 = QLabel("Tested:")
        self.labPassCount = QLabel("0")
        self.labFailCount = QLabel("0")
        self.labTotalCount = QLabel("0")
        middleLayout.addWidget(lbl_fail_1)
        middleLayout.addWidget(self.labPassCount)
        middleLayout.addWidget(self.labFailCount)
        middleLayout.addWidget(self.labTotalCount)
        middleLayout.setContentsMargins(0, 0, 0, 0)
        middleLayout.setSpacing(0)

        rightLayout = QVBoxLayout()
        labRate = QLabel("Rate:")
        self.labPassRate = QLabel("0%")
        self.labPassRate.setStyleSheet(Color.green)
        self.labFailRate = QLabel("0%")
        self.labFailRate.setStyleSheet(Color.red)
        labTotalRate = QLabel()
        rightLayout.addWidget(labRate)
        rightLayout.addWidget(self.labPassRate)
        rightLayout.addWidget(self.labFailRate)
        rightLayout.addWidget(labTotalRate)
        rightLayout.setSpacing(0)
        rightLayout.setContentsMargins(0, 0, 0, 0)

        subLayout.addLayout(leftLayout)
        subLayout.addLayout(middleLayout)
        subLayout.addLayout(rightLayout)
        subLayout.setSpacing(0)
        subLayout.setContentsMargins(0, 0, 0, 0)
        yieldBox.setFixedHeight(80)
        yieldBox.setFixedWidth(230)
        yieldBox.setLayout(subLayout)
        self.mainLayout.addWidget(yieldBox)

    def clean(self):
        self.labPassCount.setText('0')
        self.labFailCount.setText('0')
        self.labTotalCount.setText('0')
        self.labPassRate.setText('0%')
        self.labFailRate.setText('0%')

    def snScanLayout(self):
        space = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.mainLayout.addItem(space)
        scanLayout = QGridLayout()
        scanLayout.setContentsMargins(1, 1, 1, 1)
        self.lineEditSn = QLineEdit()
        snValidator = QRegularExpressionValidator(QRegularExpression("[a-zA-Z0-9]+"))
        self.lineEditSn.setValidator(snValidator)
        self.lineEditSn.setFocus()
        self.buttonStart = QPushButton("Start (F5)")
        self.buttonStart.setShortcut(QKeySequence(Qt.Key_F5))
        self.buttonStop = QPushButton("Stop")
        # self.buttonStop.setShortcut(QKeySequence(Qt.Key_F6))
        scanLayout.addWidget(self.lineEditSn, 0, 0, 1, 2)
        scanLayout.addWidget(self.buttonStart, 1, 0, 1, 1)
        scanLayout.addWidget(self.buttonStop, 1, 1, 1, 1)
        self.mainLayout.addLayout(scanLayout)


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ui = ScanController()
    # ui.startTest()
    ui.view.show()
    sys.exit(app.exec())