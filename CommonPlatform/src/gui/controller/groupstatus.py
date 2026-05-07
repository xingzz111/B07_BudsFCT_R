#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import csv
from rtLib import events
from configure.constants import State
from gui.resources.style import Font, Color
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget


class GroupController(QObject):
    signalGroupAllSelectedRow = Signal(int)

    def __init__(self):
        super().__init__()
        self.view = GroupView()
        self.groupAllResult = {}

    def load_test_plan(self, tp_path):
        self.view.cleanGroups()
        with open(tp_path, 'r') as f:
            reader = csv.DictReader(f)
            currGroup = ''
            for row in reader:
                if row['TESTNAME'].startswith('//'):
                    continue
                if currGroup != row['TESTNAME']:
                    self.groupAllResult[row['TESTNAME']] = {}
                    currGroup = row['TESTNAME']
                    self.view.addOneGroup(currGroup)
                _identify = f"{row['TESTNAME']}_{row['SUBTESTNAME']}_{row['SUBSUBTESTNAME']}"
                self.groupAllResult[row['TESTNAME']][_identify] = State.IDLE

    def clean(self):
        for group, items in self.groupAllResult.items():
            for item in items.keys():
                self.groupAllResult[group][item] = State.IDLE


    def parse_sequencer_message(self, site, message):
        if message:
            if message.event == events.SEQUENCE_START:
                self.sequence_start(site)
            elif message.event == events.SEQUENCE_END:
                self.sequence_end(site)
            elif message.event == events.ITEM_START:
                self.item_start(site, message)
            elif message.event == events.ITEM_FINISH:
                self.item_finish(site, message)

    def sequence_start(self, site):
        """for one slot"""
        for group in self.groupAllResult.keys():
            self.view.updateGroup(group, State.RUNNING)

    def sequence_end(self, site):
        pass

    def item_start(self, site, message):
        """for one slot"""
        group = message.data.get('group', '')
        tid = message.data.get('tid', '')
        subsubtestname = message.data.get('subsubtestname', '')
        _identify = f"{group}_{tid}_{subsubtestname}"
        self.groupAllResult[group][_identify] = State.RUNNING

    def item_finish(self, site, message):
        """for one slot"""
        group = message.data.get('group', '')
        tid = message.data.get('tid', '')
        subsubtestname = message.data.get('subsubtestname', '')
        _identify = f"{group}_{tid}_{subsubtestname}"
        result = State.PASS if message.data['result'] else State.FAIL
        self.groupAllResult[group][_identify] = result
        currState = list(self.groupAllResult[group].values())
        if State.IDLE not in currState and State.RUNNING not in currState:
            state = State.PASS if State.FAIL not in currState else State.FAIL
            self.view.updateGroup(group, state)


class GroupView(QWidget):
    def __init__(self):
        super().__init__()
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(2, 2, 2, 2)
        self.mainLayout.setSpacing(0)
        self.groupBox = {}
        self._groupWidgets = []
        self.borderQss = 'border: 2px solid black;'
        self._defaultGroups = ['Group1', 'Group2', 'Group3', 'Group4']
        [self.addOneGroup(group) for group in self._defaultGroups]

    def addOneGroup(self, group:str):
        subLayout = QVBoxLayout()
        subLayout.setContentsMargins(0, 0, 0, 0)
        subLayout.setSpacing(0)
        heater = QLabel(group)
        heater.setAlignment(Qt.AlignCenter)
        heater.setFont(Font.FONT_28)
        heater.setStyleSheet(Color.bg_white + Color.black + self.borderQss)
        status = QLabel()
        status.setText('IDLE')
        status.setAlignment(Qt.AlignCenter)
        status.setFont(Font.FONT_28)
        status.setStyleSheet(Color.bg_orange + Color.white + self.borderQss)
        subLayout.addWidget(heater)
        subLayout.addWidget(status)
        subwidget = QWidget()
        subwidget.setLayout(subLayout)
        self._groupWidgets.append(subwidget)
        self.groupBox[group] = status
        self.mainLayout.addWidget(subwidget)

    def cleanGroups(self):
        for subwidget in self._groupWidgets:
            subwidget.deleteLater()
            self.mainLayout.removeWidget(subwidget)
        del self.groupBox
        self.groupBox = {}
        self._groupWidgets.clear()

    def updateGroup(self, group, state):
        status = self.groupBox.get(group, None)
        if not status:
            return
        if state == State.IDLE:
            status.setText('IDLE')
            status.setStyleSheet(Color.bg_orange + Color.white + self.borderQss)
        elif state == State.RUNNING:
            status.setText('RUNNING')
            status.setStyleSheet(Color.bg_blue + Color.white + self.borderQss)
        elif state == State.PASS:
            status.setText('PASS')
            status.setStyleSheet(Color.bg_green + Color.white + self.borderQss)
        else:
            status.setText('FAIL')
            status.setStyleSheet(Color.bg_red + Color.white + self.borderQss)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = GroupController()
    ui.view.addOneGroup('Group1')
    ui.view.addOneGroup('Group2')
    ui.view.addOneGroup('Group3')
    ui.view.addOneGroup('Group4')
    ui.view.updateGroup('Group1', State.PASS)
    ui.view.updateGroup('Group2', State.RUNNING)
    ui.view.updateGroup('Group3', State.FAIL)
    ui.view.updateGroup('Group4', State.IDLE)
    ui.view.cleanGroups()
    ui.view.addOneGroup('Group1')
    ui.view.addOneGroup('Group2')
    ui.view.updateGroup('Group1', State.PASS)
    ui.view.updateGroup('Group2', State.RUNNING)
    ui.view.show()

    sys.exit(app.exec())
