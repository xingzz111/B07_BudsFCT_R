#!/usr/bin/env python
# -*- coding: utf-8 -*-

from configure import constants as constant
from PySide6.QtGui import QColor
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex


class KTotalTableModel(QAbstractTableModel):
    def __init__(self, selected_row_signal, header):
        super(KTotalTableModel, self).__init__()

        # 2d array for store result
        self._result = []
        # 2d array for store test plan values
        self._items = []
        self._selected_row_signal = selected_row_signal
        self.init_header(header)

    def init_header(self, header):
        self.tpheader = header
        self.offset = len(self.tpheader)
        self.viewheader = self.tpheader[:]
        for f in range(constant.FIXTURE):
            for i in range(constant.SLOTS):
                if constant.FIXTURE > 1:
                    self.viewheader.append("SLOT-{}_{}".format(f + 1, i + 1))
                else:
                    self.viewheader.append("SLOT-{}".format(i + 1))
        self.results = [i + self.offset for i in range(constant.SLOTS * constant.FIXTURE)]

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._items)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.viewheader)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        column = index.column()
        cur_row_item = self._items[row]
        if role == Qt.DisplayRole:
            return cur_row_item[column]
        elif role == Qt.ForegroundRole:
            if column in self.results:
                result = self._result[column - self.offset][row]
                if result is not None:
                    if result:
                        return QColor(Qt.blue)
                    else:
                        return QColor(Qt.red)
                else:
                    return QColor(Qt.gray)
            return QColor(Qt.black)
        return None

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
                return self.viewheader[section]
            else:
                return str(section)
        elif role == Qt.TextAlignmentRole:
            return int(Qt.AlignHCenter)

    def insertColumns(self, position, columns, parent=None, *args, **kwargs):
        col_type = kwargs.get('col_type', None)
        data = kwargs.get('data', None)

        if col_type == 'test_plan' and data:
            self._result = []
            self.beginResetModel()
            self.beginRemoveColumns(QModelIndex(), 0, 4)
            self.endRemoveColumns()
            self.beginInsertColumns(QModelIndex(), position, position + columns - 1)
            rows = len(data[0])
            placeholder = [''] * rows
            for site in range(constant.SLOTS * constant.FIXTURE):
                self._result.append([False for row in range(rows)])

            for site in range(len(self.viewheader) - len(data)):
                data.append(placeholder)
            self._items = list(map(list, list(zip(*data))))
            self.endInsertColumns()
            self.endResetModel()
            return True
        else:
            return False

    def setData(self, index, value, role=Qt.EditRole):

        if index.isValid():
            row = index.row()
            column = index.column()
            if role == Qt.EditRole:
                self._items[row][column + self.offset] = value
                self._selected_row_signal.emit(row)
                return True
            if role == Qt.ForegroundRole:
                self._result[column][row] = value
                return True
        return False

    def clean_column(self, site):
        column = site + self.offset
        for row in range(self.rowCount()):
            self._items[row][column] = ''
            self._result[site][row] = False
        self._selected_row_signal.emit(0)

    def get_items(self):
        return self._items

    def get_values(self):
        return self._result
