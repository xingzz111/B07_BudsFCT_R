#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import OrderedDict
from configure import constants as constant
from PySide6.QtGui import QColor
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex


TPHEADER = ["INDEX", "GROUP", "SubTestName", "SubSubTestName", "LL", "UL", "UNIT"]
OFFSET = len(TPHEADER)
VIEWHEADER = TPHEADER[:]
for i in range(constant.SLOTS):
    VIEWHEADER.append("SLOT{}".format(i + 1))
RESULTS = [i + OFFSET for i in range(constant.SLOTS)]


class FailOnlyModel(QAbstractTableModel):
    def __init__(self, select_row_signal):
        super(FailOnlyModel, self).__init__()
        self._selected_row_signal = select_row_signal
        self._fail_items = []
        self._failBuff = {}
        self._fail_row = OrderedDict()

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._fail_items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._fail_items)):
            return
        row = index.row()
        item = self._fail_items[row]
        column = index.column()
        if role == Qt.DisplayRole:
            if column == 0:
                return item.get('index')
            elif column == 1:
                return item.get('group')
            elif column == 2:
                return item.get('tid')
            elif column == 3:
                return item.get('subsubtestname')
            elif column == 4:
                return item.get('low')
            elif column == 5:
                return item.get('high')
            elif column == 6:
                return item.get('unit')
            elif column in range(7, 100):
                return item.get(str(column - 7))
        elif role == Qt.ForegroundRole:
            if column > 6:
                if self._failBuff.get(row):
                    if self._failBuff.get(row).get(column - 7):
                        return QColor(Qt.red)
                    else:
                        return QColor(Qt.blue)
            else:
                return QColor(Qt.black)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(VIEWHEADER)

    def headerData(self, section, qt_orientation, role=None):
        """
        Returns the data for the given role and section in the header with the specified orientation.
        :param section:
        :param qt_orientation:
        :param role:
        :return:
        """
        if role == Qt.DisplayRole:
            if qt_orientation == Qt.Horizontal:
                return VIEWHEADER[section]
            else:
                return str(section)
        elif role == Qt.TextAlignmentRole:
            return int(Qt.AlignHCenter)

    def insert_fail_result(self, row, site, value, result, cur_row_dict):
        row_key = format(row, '05d')
        index = self._fail_row.get(row_key, None)
        if index is not None:
            self._fail_items[index][str(site)] = value
            self._failBuff[index][site] = True
        else:
            self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
            self._fail_items.append(cur_row_dict)
            self._failBuff[len(self._fail_items) - 1] = {site: True}
            self._fail_row.update({row_key: len(self._fail_items) - 1})
            self._fail_items[len(self._fail_items) - 1]['index'] = row
            self._fail_items[len(self._fail_items) - 1][str(site)] = value
            self.endInsertRows()
        self._selected_row_signal.emit(self.rowCount() - 1)
        return True

    def insert_fail_row(self, row, lValue):
        row_key = format(row, '05d')
        index = self._fail_row.get(row_key, None)
        if index is not None:
            self._fail_items[index]['low'] = lValue[3]
            self._fail_items[index]['high'] = lValue[4]
            self._fail_items[index]['unit'] = lValue[5]
            value = lValue[6:]
            for i, v in enumerate(value):
                self._fail_items[index][str(i)] = v

    def clean_column(self, site):
        self.beginResetModel()
        self._failBuff = {}
        self._fail_items = []
        self._fail_row.clear()
        self.endResetModel()
        self._selected_row_signal.emit(0)
