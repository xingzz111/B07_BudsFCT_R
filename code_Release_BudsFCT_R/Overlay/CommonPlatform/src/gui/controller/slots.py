#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
======================
@author:Zcnwei
@time:2024/6/24 17:29
=====================
"""
from configure import constants
from configure.constants import State
from gui.resources.style import Font, Color
from PySide6.QtCore import Qt, QObject
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QFrame


class SlotsController(QObject):
    def __init__(self, slots=constants.SLOTS):
        super().__init__()
        self.view = SlotsView(slots)

    def setState(self, index:int, state:str):
        self.view[index].setState(state)

    def currState(self, index:int):
        return self.view[index].currState()

    def setText(self, index:int, txt:str):
        self.view[index].setText(txt)

    def currText(self, index:int):
        return self.view[index].currText()


class SlotsView(QFrame):
    def __init__(self, slots:int=0):
        super().__init__()
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(1, 1, 1, 1)
        mainLayout.setSpacing(1)
        self._slotsList = [SingleSlot(i) for i in range(slots)]
        [mainLayout.addWidget(w) for w in self._slotsList]
        self.setLayout(mainLayout)

    def __getitem__(self, item:int):
        return self._slotsList[item]


class SingleSlot(QFrame):
    def __init__(self, index:int=0):
        super().__init__()
        self._currentState = State.IDLE
        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(1, 1, 1, 1)
        mainLayout.setSpacing(0)
        leftLayout = QVBoxLayout()
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftLayout.setSpacing(5)
        rightLayout = QVBoxLayout()
        rightLayout.setContentsMargins(0, 0, 0, 0)
        rightLayout.setSpacing(0)
        self.labIndex = QLabel(str(index + 1))
        self.labContent = QLabel()
        self.chkBox = QCheckBox()
        self.chkBox.stateChanged.connect(self.chickEvent)
        self.chkBox.setChecked(True)
        leftLayout.addWidget(self.chkBox)
        leftLayout.addWidget(self.labIndex)
        rightLayout.addWidget(self.labContent)
        mainLayout.addLayout(leftLayout, 1)
        mainLayout.addLayout(rightLayout, 9)
        self.setupFormat()
        self.setLayout(mainLayout)
        self.setStyleSheet(Color.bg_orange)

    def setupFormat(self):
        # self.setFrameShape(QFrame.Shape.Box)
        # self.setFrameShadow(QFrame.Shadow.Raised)
        self.labContent.setText(State.IDLE)
        self.labContent.setFont(Font.FONT_16)
        self.labContent.setStyleSheet(Color.white)
        self.labContent.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.labIndex.setFont(Font.FONT_10)
        self.labIndex.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

    def chickEvent(self):
        currState = self.chkBox.isChecked()
        if currState:
            self.labContent.setText(State.IDLE)
            self.setStyleSheet(Color.bg_orange)
            self._currentState = State.IDLE
        else:
            self.labContent.setText(State.DISABLE)
            self.setStyleSheet(Color.bg_grey)
            self._currentState = State.DISABLE

    def setState(self, state):
        if state == State.IDLE:
            self.setStyleSheet(Color.bg_orange)
        elif state == State.READY:
            self.setStyleSheet(Color.bg_deep_orange)
        elif state == State.RUNNING:
            self.setStyleSheet(Color.bg_blue)
        elif state == State.PASS:
            self.setStyleSheet(Color.bg_green)
        elif state == State.FAIL:
            self.setStyleSheet(Color.bg_red)
        else:
            print(f"Unknown State:{state}")
        self._currentState = state

    def currState(self):
        return self._currentState

    def setText(self, txt:str):
        self.labContent.setText(str(txt).strip().upper())

    def currText(self):
        return self.labContent.text()



if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ui = SlotsView(4)
    ui.show()
    sys.exit(app.exec())

