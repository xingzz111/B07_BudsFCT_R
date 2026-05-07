#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import csv
from rtrpcLib import events
from configure import constants as constant
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout, QTabWidget
from gui.view.ktableview import KTableView
from gui.model.tablemodel import KTotalTableModel
from gui.model.failonlymodel import FailOnlyModel


class TestPlanController(QObject):
    signalTpAllSelectedRow = Signal(int)
    signalTpFailSelectedRow = Signal(int)
    signalTpStaticSelectedRow = Signal(int)

    def __init__(self, nDimensionId=0):
        super(TestPlanController, self).__init__()
        # dict for current dimension
        self.dictDimensionAttributes = {}
        self._nDimensionId = nDimensionId
        self._dimensionTag = 'SEQUENTIAL'

        # total rows count
        self._tpRowCount = 0
        self._currentRow = {}
        self.view = TestPlanView()

        self.tp_all_header = ["Group", "SubTestName", "SubSubTestName", "LowerLimit", "UpperLimit", "Units"]
        self.tpAllModel = KTotalTableModel(self.signalTpAllSelectedRow, self.tp_all_header)
        self.view.tp_all_view.setModel(self.tpAllModel)
        self.tp_static_header = ["Group", "SubTestName", "SubSubTestName", "Notes",
                                 "LowerLimit", "UpperLimit", "Units", "Function", "INPUT", "OUTPUT"]
        self.tpStaticModel = KTotalTableModel(self.signalTpStaticSelectedRow, self.tp_static_header)
        self.view.tp_static_view.setModel(self.tpStaticModel)

        self.tpFailModel = FailOnlyModel(self.signalTpFailSelectedRow)
        self.view.tp_fail_view.setModel(self.tpFailModel)

        # when data change, update table view
        self.signalTpAllSelectedRow.connect(self.view.tp_all_view.selectRow)
        self.signalTpFailSelectedRow.connect(self.view.tp_fail_view.selectRow)

    def reset_all_attributes(self):
        if self._dimensionTag in self.dictDimensionAttributes:
            self.dictDimensionAttributes[self._dimensionTag]["listGroupTid"] = []
            self.dictDimensionAttributes[self._dimensionTag]["sequenceEndFlag"] = []
            self.dictDimensionAttributes[self._dimensionTag]["columnValues"] = []
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotIdentify"] = []
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotItemFinish"] = []
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotDimensionFlag"] = []
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotRowData"] = []
            self.dictDimensionAttributes[self._dimensionTag]["failRow"] = set()

            for i in range(constant.SLOTS * constant.FIXTURE):
                self.dictDimensionAttributes[self._dimensionTag]["sequenceEndFlag"].append(False)
                self.dictDimensionAttributes[self._dimensionTag]["columnValues"].append(list())
                self.dictDimensionAttributes[self._dimensionTag]["currentSlotRowData"].append(dict())
                self.dictDimensionAttributes[self._dimensionTag]["currentSlotIdentify"].append('')
                self.dictDimensionAttributes[self._dimensionTag]["currentSlotDimensionFlag"].append(False)
                self.dictDimensionAttributes[self._dimensionTag]["currentSlotItemFinish"].append(True)

    def load_test_plan(self, tp_path, tp=None, tid_list=None, dimensionTag="SEQUENTIAL"):
        self._dimensionTag = dimensionTag
        # a dict to store current dimension attributes
        self.dictDimensionAttributes[dimensionTag] = {}
        self.reset_all_attributes()
        _limitUnit = {}
        if tp and tid_list:
            self.dictDimensionAttributes[dimensionTag]["listGroupTid"] = tid_list
        else:
            f = open(tp_path, 'r')
            reader = csv.DictReader(f)
            # GROUP,TID,UNIT,LOW,HIGH
            _tpAll = [[] for i in range(6)]
            _tpStatic = [[] for i in range(10)]
            self.dictDimensionAttributes[dimensionTag]["listGroupTid"] = []
            for row in reader:
                if row['Disable'].strip() == 'Y':
                    continue
                _tpAll[0].append(row['Group'])
                _tpAll[1].append(row['SubTestName'])
                _tpAll[2].append(row['SubSubTestName'])
                _tpAll[3].append(row['LowerLimit'])
                _tpAll[4].append(row['UpperLimit'])
                _tpAll[5].append(row['Units'])
                _tpStatic[0].append(row['Group'])
                _tpStatic[1].append(row['SubTestName'])
                _tpStatic[2].append(row['SubSubTestName'])
                _tpStatic[3].append(row['Notes'])
                _tpStatic[4].append(row['LowerLimit'])
                _tpStatic[5].append(row['UpperLimit'])
                _tpStatic[6].append(row['Units'])
                _tpStatic[7].append(row['Function'])
                _tpStatic[8].append(row['Input'])
                _tpStatic[9].append(row['Output'])
                _identify = re.sub('\W', '_',
                                   '{}_{}_{}'.format(row['Group'], row['SubTestName'], row['SubSubTestName']))
                self.dictDimensionAttributes[dimensionTag]["listGroupTid"].append(_identify)
                _limitUnit[_identify] = [row['LowerLimit'], row['UpperLimit'], row['Units']]
            f.close()

        self._tpRowCount = len(_tpAll[0])
        self.tpAllModel.insertColumns(0, 5, None, col_type='test_plan', data=_tpAll, rows=self._tpRowCount)
        self.tpStaticModel.insertColumns(0, 5, None, col_type='test_plan', data=_tpStatic, rows=self._tpRowCount)
        self.tpFailModel.clean_column(0)
        self.view.tp_all_view.set_columns_width()
        self.view.tp_static_view.set_columns_width([80, 150, 200, 150, 50, 50, 50])
        self.view.tp_fail_view.set_columns_width([30, 80, 150, 150, 50, 50])

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
        self.tpAllModel.clean_column(site)
        self.tpStaticModel.clean_column(site)
        self.tpFailModel.clean_column(site)
        self.dictDimensionAttributes[self._dimensionTag]['currentSlotIdentify'][site] = ''
        self.dictDimensionAttributes[self._dimensionTag]['sequenceEndFlag'][site] = False
        self.dictDimensionAttributes[self._dimensionTag]['currentSlotItemFinish'][site] = True
        self.dictDimensionAttributes[self._dimensionTag]["failRow"] = set()

    def sequence_end(self, site):
        pass
        # self.dictDimensionAttributes[self._dimensionTag]['sequenceEndFlag'][site] = True
        # self.dictDimensionAttributes[self._dimensionTag]['currentSlotIdentify'][site] = ''

    def item_start(self, site, message):
        # check if message for current dimension
        if self._dimensionTag == "SEQUENTIAL" or self._dimensionTag == message.data.get('dimension', ''):
            # if current item is not finish, it can't be in this function
            # if not self.dictDimensionAttributes[self._dimensionTag]['currentSlotItemFinish'][site]:
            #     return
            _identify = re.sub('\W', '_', '{}_{}_{}'.format(message.data.get('group', ''),
                                                            message.data.get('subtestname', ''),
                                                            message.data.get('subsubtestname', '')))
            # update current slot identify to buff
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotIdentify"][site] = _identify
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotRowData"][site].update(message.data)
            # set current slot testing item flag
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotItemFinish"][site] = False
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotDimensionFlag"][site] = True
        else:
            # currentSlotDimensionFlag if for item finish, only execute item start, this flag will set True
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotDimensionFlag"][site] = False

    def item_finish(self, site, message):
        _identify = re.sub('\W', '_', '{}_{}_{}'.format(message.data.get('group'), message.data.get('tid'),
                                                        message.data.get('subsubtestname')))
        if self.dictDimensionAttributes[self._dimensionTag]["currentSlotIdentify"][site] == _identify:
            self._currentRow.clear()
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotRowData"][site].update(message.data)
            value = message.data['value']
            # print("<<<<<<<<<<test value>>>>>>>>>>",value)
            result = message.data['result']
            # print("<<<<<<<<<<test result>>>>>>>>>>", result)
            if message.data.get('error'):
                result = False
                value = message.data['error']
            self._currentRow.update(message.data.copy())

            self.update_result(site, value, result)
            self.dictDimensionAttributes[self._dimensionTag]["currentSlotItemFinish"][site] = True

    def update_result(self, site, value, result):
        try:
            row = self.dictDimensionAttributes[self._dimensionTag]['listGroupTid'].index(
                self.dictDimensionAttributes[self._dimensionTag]['currentSlotIdentify'][site])
        except:
            return
        value_index = self.tpAllModel.createIndex(row, site, value)
        self.tpAllModel.setData(value_index, value, role=Qt.EditRole)
        self.tpStaticModel.setData(value_index, value, role=Qt.EditRole)

        if not result:
            self.dictDimensionAttributes[self._dimensionTag]["failRow"].add(row)
            self.tpFailModel.insert_fail_result(row, site, value, result, self._currentRow.copy())

        if 'SKIP' in str(value):
            result = None
        result_index = self.tpAllModel.createIndex(row, site, result)
        self.tpAllModel.setData(result_index, result, role=Qt.ForegroundRole)
        self.tpStaticModel.setData(result_index, result, role=Qt.ForegroundRole)

        if row in self.dictDimensionAttributes[self._dimensionTag]["failRow"]:
            _value = self.tpAllModel.get_items()[row]
            self.tpFailModel.insert_fail_row(row, _value,)

    def get_row_count(self):
        return self._tpRowCount

    def reset_result_column(self):
        for i in range(constant.SLOTS * constant.FIXTURE):
            self.tpAllModel.clean_column(i)
            self.tpStaticModel.clean_column(i)
        self.tpFailModel.clean_column(0)

    def flushTab(self):
        # ## flush table
        currIndex = self.view.tp_splitter.currentIndex()
        self.view.tp_splitter.setCurrentIndex(2)
        self.view.tp_splitter.setCurrentIndex(currIndex)
        self.signalTpFailSelectedRow.emit(0)
        self.signalTpStaticSelectedRow.emit(0)
        self.signalTpAllSelectedRow.emit(0)


class TestPlanView(QFrame):
    def __init__(self):
        super(TestPlanView, self).__init__()
        self.tp_all_view = KTableView(self)
        self.tp_fail_view = KTableView(self)
        self.tp_static_view = KTableView(self)

        self.tp_splitter = QTabWidget()
        self.tp_all_view.setAutoScroll(True)
        self.tp_static_view.setAutoScroll(False)
        self.setFrameStyle(QFrame.NoFrame)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        _frame_tp_all = QFrame()
        _frame_tp_fail = QFrame()
        _frame_tp_static = QFrame()

        _tp_fail_layout = QVBoxLayout()
        _tp_fail_layout.setSpacing(0)
        _tp_fail_layout.setContentsMargins(1, 1, 1, 1)

        _tp_all_layout = QVBoxLayout()
        _tp_all_layout.setSpacing(1)
        _tp_all_layout.setContentsMargins(1, 1, 1, 1)

        _tp_static_layout = QVBoxLayout()
        _tp_static_layout.setSpacing(1)
        _tp_static_layout.setContentsMargins(1, 1, 1, 1)

        _tp_fail_layout.addWidget(self.tp_fail_view)
        _frame_tp_fail.setLayout(_tp_fail_layout)

        _tp_all_layout.addWidget(self.tp_all_view)
        _frame_tp_all.setLayout(_tp_all_layout)

        _tp_static_layout.addWidget(self.tp_static_view)
        _frame_tp_static.setLayout(_tp_static_layout)

        main_layout.addWidget(self.tp_splitter)
        self.setLayout(main_layout)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.tp_splitter.addTab(_frame_tp_all, "ALL_RECORDS")
        self.tp_splitter.addTab(_frame_tp_static, "STATIC_RECORDS")
        self.tp_splitter.addTab(_frame_tp_fail, "FAIL_RECORDS")



if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = TestPlanController()
    controller.view.setGeometry(100, 100, 850, 600)
    controller.view.tp_all_view.set_columns_width()
    controller.view.tp_fail_view.set_columns_width()
    controller.view.show()
    sys.exit(app.exec())
