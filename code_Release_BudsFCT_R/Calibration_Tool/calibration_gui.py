#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
校准工具图形界面版本
基于PySide6实现，支持Windows系统
使用独立的校准功能模块，支持动态扩展
"""

import sys
import os
import time
import json
import serial
import serial.tools.list_ports
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QWidget, QLabel, QComboBox, QPushButton, QTextEdit,
                               QGroupBox, QSpinBox, QDoubleSpinBox, QProgressBar,
                               QTabWidget, QFrame, QSplitter, QMessageBox, QDialog,
                               QLineEdit, QDialogButtonBox, QFormLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap, QIcon

# 导入独立的校准功能模块
from calibration_functions import calibration_engine

class AddCalibrationDialog(QDialog):
    """添加校准类型对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加校准类型")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        """初始化对话框界面"""
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # 校准类型名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如: ADC校准")
        form_layout.addRow("校准类型名称:", self.name_edit)
        
        # 校准函数选择
        self.function_combo = QComboBox()
        self.function_combo.addItem("使用内置校准引擎", "builtin")
        self.function_combo.addItem("自定义校准函数", "custom")
        form_layout.addRow("校准函数:", self.function_combo)
        
        # 自定义函数名称（仅当选择自定义函数时显示）
        self.custom_function_edit = QLineEdit()
        self.custom_function_edit.setPlaceholderText("例如: my_custom_calibration")
        self.custom_function_edit.setVisible(False)
        form_layout.addRow("自定义函数名:", self.custom_function_edit)
        
        # 参数配置
        self.params_edit = QLineEdit()
        self.params_edit.setPlaceholderText("例如: target_voltage=3.3,tolerance=0.01")
        form_layout.addRow("参数配置:", self.params_edit)
        
        layout.addLayout(form_layout)
        
        # 连接函数选择变化信号
        self.function_combo.currentTextChanged.connect(self.on_function_changed)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_function_changed(self, text):
        """函数选择改变时的处理"""
        is_custom = self.function_combo.currentData() == "custom"
        self.custom_function_edit.setVisible(is_custom)
        
        # 更新表单标签
        form_layout = self.layout().itemAt(0)
        if isinstance(form_layout, QFormLayout):
            for i in range(form_layout.rowCount()):
                label = form_layout.itemAt(i, QFormLayout.LabelRole)
                field = form_layout.itemAt(i, QFormLayout.FieldRole)
                if field and field.widget() == self.custom_function_edit:
                    label_widget = label.widget()
                    if label_widget:
                        label_widget.setVisible(is_custom)
                    break
    
    def get_calibration_data(self):
        """获取校准数据"""
        name = self.name_edit.text().strip()
        function_type = self.function_combo.currentData()
        custom_function = self.custom_function_edit.text().strip() if function_type == "custom" else ""
        params_text = self.params_edit.text().strip()
        
        # 解析参数
        params = {}
        if params_text:
            for param in params_text.split(','):
                if '=' in param:
                    key, value = param.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 尝试转换为数字
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass  # 保持字符串格式
                    params[key] = value
        
        # 返回包含函数信息的数据
        calibration_data = {
            'name': name,
            'function_type': function_type,
            'custom_function': custom_function,
            'params': params
        }
        
        return calibration_data

class ManualIndexMapDialog(QDialog):
    """手动校准索引映射维护对话框"""
    def __init__(self, mappings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("手动校准索引映射维护")
        self.resize(700, 500)
        self.mappings = mappings or []
        self.selected_entry = None

        self.init_ui()
        self.load_table_from_mappings(self.mappings)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 说明
        info = QLabel("在此维护各工站的项目与对应的 index。双击单元格可编辑。")
        info.setStyleSheet("color: #666666;")
        layout.addWidget(info)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["工站", "项目", "index"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.table)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("新增行")
        self.del_btn = QPushButton("删除选中")
        self.save_btn = QPushButton("保存到JSON")
        self.apply_btn = QPushButton("应用选中到当前")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)

        # 连接信号
        self.add_btn.clicked.connect(self.on_add_row)
        self.del_btn.clicked.connect(self.on_delete_selected)
        self.save_btn.clicked.connect(self.on_save)
        self.apply_btn.clicked.connect(self.on_apply_selected)

        # 对话框按钮（关闭）
        dbb = QDialogButtonBox(QDialogButtonBox.Close)
        dbb.rejected.connect(self.reject)
        layout.addWidget(dbb)

    def load_table_from_mappings(self, mappings):
        self.table.setRowCount(0)
        for m in mappings:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(m.get("workstation", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(m.get("item", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(str(m.get("index", ""))))

    def get_mappings_from_table(self):
        rows = self.table.rowCount()
        result = []
        for r in range(rows):
            ws_item = self.table.item(r, 0)
            item_item = self.table.item(r, 1)
            index_item = self.table.item(r, 2)
            ws = ws_item.text().strip() if ws_item else ""
            it = item_item.text().strip() if item_item else ""
            idx_text = index_item.text().strip() if index_item else ""
            try:
                idx = int(idx_text)
            except Exception:
                idx = None
            result.append({"workstation": ws, "item": it, "index": idx})
        return result

    def on_add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(""))
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.setItem(row, 2, QTableWidgetItem(""))

    def on_delete_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def on_save(self):
        # 更新内存并让父窗口保存
        self.mappings = self.get_mappings_from_table()
        QMessageBox.information(self, "保存", "索引映射已更新，点击关闭返回主界面。")

    def on_apply_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先在表格中选择一行。")
            return
        ws = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
        it = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        idx_text = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
        try:
            idx = int(idx_text)
        except Exception:
            QMessageBox.warning(self, "错误", "index 必须为整数。")
            return
        self.selected_entry = {"workstation": ws.strip(), "item": it.strip(), "index": idx}
        self.accept()

class CalibrationWorker(QThread):
    """校准工作线程"""
    
    log_signal = Signal(str)
    progress_signal = Signal(int)
    finished_signal = Signal(bool, str)
    
    def __init__(self, port, calibration_type, params, parent=None):
        super().__init__(parent)
        self.port = port
        self.calibration_type = calibration_type
        self.params = params
        self.engine = calibration_engine
        self._is_running = True
    
    def run(self):
        """执行校准任务"""
        try:
            self.log_signal.emit(f"开始{self.calibration_type}校准...")
            
            # 处理校准类型名称
            actual_cal_type = self.calibration_type
            
            # 如果是自定义校准类型，移除[自定义]前缀
            if self.calibration_type.startswith("[自定义] "):
                actual_cal_type = self.calibration_type[5:]  # 移除"[自定义] "前缀
                
                # 为自定义校准类型添加必要的参数信息（仅当参数中不存在时）
                if 'function_type' not in self.params:
                    self.params['function_type'] = 'custom'
                # 注意：不要覆盖已经存在的custom_function参数
                # 因为start_calibration方法已经正确设置了custom_function
            
            # 添加调试日志，查看传递给校准引擎的参数
            self.log_signal.emit(f"DEBUG: 传递给校准引擎的参数 - actual_cal_type: {actual_cal_type}")
            self.log_signal.emit(f"DEBUG: 传递给校准引擎的参数 - params: {self.params}")
            
            # 使用校准引擎执行校准
            result, message = self.engine.execute_calibration(
                actual_cal_type, 
                self.port, 
                self.params,
                log_callback=self.log_signal.emit,
                progress_callback=self.progress_signal.emit
            )
            
            if result:
                self.finished_signal.emit(True, message)
            else:
                self.finished_signal.emit(False, message)
                
        except Exception as e:
            self.log_signal.emit(f"校准过程中发生错误: {str(e)}")
            self.finished_signal.emit(False, f"校准失败: {str(e)}")
    
    def stop(self):
        """停止校准"""
        self._is_running = False
        self.engine.stop_calibration()

class CalibrationTool(QMainWindow):
    """校准工具主窗口"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.custom_calibrations = {}  # 存储自定义校准类型
        # 手动索引映射与选择来源
        self.manual_index_map_path = "manual_index_map.json"
        self.manual_index_mappings = []
        self.selected_index_source = None
        self.init_ui()
        self.load_ports()
        self.load_custom_calibrations()
        self.load_manual_index_map()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("设备校准工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置窗口图标（Logo）
        self.set_window_icon()
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QPushButton.add-btn {
                background-color: #2196F3;
            }
            QPushButton.add-btn:hover {
                background-color: #1976D2;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 右侧日志面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 800])
        
        # 左侧：设备配置组
        device_group = QGroupBox("设备配置")
        device_layout = QVBoxLayout(device_group)
        
        # 端口选择
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("选择端口:"))
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        port_layout.addWidget(self.port_combo)
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_ports)
        port_layout.addWidget(refresh_btn)
        port_layout.addStretch()
        device_layout.addLayout(port_layout)
        
        # 校准类型选择
        cal_type_layout = QHBoxLayout()
        cal_type_layout.addWidget(QLabel("校准类型:"))
        self.cal_type_combo = QComboBox()
        self.cal_type_combo.currentTextChanged.connect(self.on_calibration_type_changed)
        cal_type_layout.addWidget(self.cal_type_combo)
        
        # 添加校准类型按钮
        self.add_cal_btn = QPushButton("添加")
        self.add_cal_btn.setObjectName("add-btn")
        self.add_cal_btn.clicked.connect(self.add_calibration_type)
        cal_type_layout.addWidget(self.add_cal_btn)
        
        # 删除校准类型按钮
        self.delete_cal_btn = QPushButton("删除")
        self.delete_cal_btn.setObjectName("delete-btn")
        self.delete_cal_btn.clicked.connect(self.delete_calibration_type)
        cal_type_layout.addWidget(self.delete_cal_btn)
        
        cal_type_layout.addStretch()
        device_layout.addLayout(cal_type_layout)
        
        # 参数配置组
        self.params_group = QGroupBox("参数配置")
        self.params_layout = QVBoxLayout(self.params_group)
        self.setup_parameter_controls()
        device_layout.addWidget(self.params_group)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始校准")
        self.start_btn.clicked.connect(self.start_calibration)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止校准")
        self.stop_btn.clicked.connect(self.stop_calibration)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        device_layout.addLayout(control_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        device_layout.addWidget(self.progress_bar)
        
        left_layout.addWidget(device_group)
        left_layout.addStretch()
        
        # 右侧：日志显示
        log_group = QGroupBox("校准日志")
        log_layout = QVBoxLayout(log_group)
        
        # 日志控制按钮布局
        log_control_layout = QHBoxLayout()
        
        # 清除日志按钮
        self.clear_log_btn = QPushButton("清除日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_control_layout.addWidget(self.clear_log_btn)
        
        log_control_layout.addStretch()
        log_layout.addLayout(log_control_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        
        # 设置日志颜色
        palette = self.log_text.palette()
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.Text, QColor(200, 200, 200))
        self.log_text.setPalette(palette)
        
        # 设置彩色日志格式
        self.log_text.setHtml("<body style='color: #c8c8c8; background-color: #1e1e1e;'>")
        
        # 创建彩色日志格式映射
        self.log_colors = {
            "INFO": "#87ceeb",      # 天蓝色 - 信息
            "PASS": "#90ee90",      # 浅绿色 - 成功
            "FAIL": "#ff6b6b",      # 浅红色 - 失败
            "CALIB": "#ffa500",     # 橙色 - 校准过程
            "MONITOR": "#ffd700",   # 金色 - 监控信息
            "RPC": "#98fb98",       # 淡绿色 - RPC调用
            "RPC_RESULT": "#add8e6", # 淡蓝色 - RPC结果
            "WARNING": "#ffa500",   # 橙色 - 警告
            "ERROR": "#ff6b6b"      # 红色 - 错误
        }
        
        log_layout.addWidget(self.log_text)
        right_layout.addWidget(log_group)
    
    def append_colored_log(self, message):
        """添加彩色日志消息"""
        # 获取当前时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 检测消息类型并设置颜色
        log_type = "INFO"  # 默认类型
        color = self.log_colors.get(log_type, "#c8c8c8")
        
        # 根据消息前缀确定类型和颜色
        for prefix, prefix_color in self.log_colors.items():
            if message.startswith(f"{prefix}:"):
                log_type = prefix
                color = prefix_color
                # 移除类型前缀，只显示消息内容
                message = message[len(prefix) + 1:].strip()
                break
        
        # 创建HTML格式的日志行
        html_message = f"<div style='color: {color}; margin: 2px 0;'>"
        html_message += f"<span style='color: #888;'>[{timestamp}]</span> "
        html_message += f"<span style='color: {color}; font-weight: bold;'>{log_type}:</span> "
        html_message += f"<span style='color: {color};'>{message}</span>"
        html_message += "</div>"
        
        # 添加到日志文本框
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertHtml(html_message)
        
        # 添加换行
        cursor.insertText("\n")
        
        # 滚动到底部
        self.log_text.ensureCursorVisible()
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        # 初始化校准类型列表（仅在GUI启动时调用一次）
        if not hasattr(self, '_calibration_types_initialized'):
            self.update_calibration_types()
            self._calibration_types_initialized = True
        
        # 在UI界面上显示Logo（仅在GUI启动时调用一次）
        if not hasattr(self, '_logo_added'):
            self.add_logo_to_ui()
    
    def set_window_icon(self):
        """设置窗口图标（Logo）"""
        try:
            # 检查Logo.png文件是否存在
            logo_path = "icon.png"
            if os.path.exists(logo_path):
                # 加载Logo图片并设置为窗口图标
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # 创建图标并设置
                    icon = QIcon(pixmap)
                    self.setWindowIcon(icon)
                    
                    # 设置应用程序图标（影响任务栏和系统托盘）
                    QApplication.setWindowIcon(icon)
                    
                    print(f"Logo已成功加载: {logo_path}")
                    return True
                else:
                    print("警告: Logo图片加载失败")
            else:
                print(f"警告: Logo文件不存在 - {logo_path}")
        except Exception as e:
            print(f"设置窗口图标时发生错误: {e}")
        
        return False
    
    def add_logo_to_ui(self):
        """在UI界面上添加Logo显示"""
        try:
            # 检查是否已经添加过Logo
            if hasattr(self, '_logo_added') and self._logo_added:
                return True
                
            # 检查Logo.png文件是否存在
            logo_path = "Logo.png"
            if os.path.exists(logo_path):
                # 加载Logo图片
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # 缩放图片到合适大小 - 加大Logo尺寸
                    scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    
                    # 创建Logo标签
                    logo_label = QLabel()
                    logo_label.setPixmap(scaled_pixmap)
                    logo_label.setAlignment(Qt.AlignCenter)
                    logo_label.setStyleSheet("QLabel { background-color: transparent; padding: 15px; }")
                    
                    # 创建版本信息和作者信息标签
                    version_label = QLabel("Version: 1.0.2")
                    version_label.setAlignment(Qt.AlignCenter)
                    version_label.setStyleSheet("QLabel { color: #666666; font-size: 10px; margin-top: 5px; }")
                    
                    author_label = QLabel("Author: XING")
                    author_label.setAlignment(Qt.AlignCenter)
                    author_label.setStyleSheet("QLabel { color: #666666; font-size: 10px; margin-bottom: 10px; }")
                    
                    # 创建Logo和信息容器
                    logo_container = QWidget()
                    logo_layout = QVBoxLayout(logo_container)
                    logo_layout.addWidget(logo_label)
                    logo_layout.addWidget(version_label)
                    logo_layout.addWidget(author_label)
                    logo_layout.setAlignment(Qt.AlignCenter)
                    logo_layout.setContentsMargins(0, 0, 0, 0)
                    
                    # 在设备配置组上方添加Logo容器
                    central_widget = self.centralWidget()
                    main_layout = central_widget.layout()
                    
                    # 获取分割器
                    splitter = main_layout.itemAt(0).widget()
                    
                    # 获取左侧面板
                    left_panel = splitter.widget(0)
                    left_layout = left_panel.layout()
                    
                    # 在设备配置组之前插入Logo容器
                    left_layout.insertWidget(0, logo_container)
                    
                    # 标记Logo已添加，避免重复添加
                    self._logo_added = True
                    
                    print(f"UI界面Logo已成功添加: {logo_path}")
                    return True
                else:
                    print("警告: Logo图片加载失败")
            else:
                print(f"警告: Logo文件不存在 - {logo_path}")
        except Exception as e:
            print(f"在UI界面上添加Logo时发生错误: {e}")
        
        return False
    
    def update_calibration_types(self):
        """更新校准类型列表"""
        self.cal_type_combo.clear()
        
        # 添加内置校准类型
        builtin_types = ["B08_B06_DAC_CAL", "B08_PWM_CAL", "B06_PWM_CAL_VERIFY", "B08 Ship Mode CAL", "COMMON_MANUAL_CAL", "B06_FWDL_设备Stlink_SN维护", "B08_FWDL_设备Stlink_SN维护"]
        for cal_type in builtin_types:
            self.cal_type_combo.addItem(cal_type)
        
        # 添加自定义校准类型
        for cal_name in self.custom_calibrations.keys():
            self.cal_type_combo.addItem(f"[自定义] {cal_name}")
    
    def add_calibration_type(self):
        """添加新的校准类型"""
        dialog = AddCalibrationDialog(self)
        if dialog.exec() == QDialog.Accepted:
            calibration_data = dialog.get_calibration_data()
            name = calibration_data['name']
            
            if not name:
                QMessageBox.warning(self, "错误", "请输入校准类型名称")
                return
            
            if name in self.custom_calibrations:
                QMessageBox.warning(self, "错误", f"校准类型 '{name}' 已存在")
                return
            
            # 添加到自定义校准列表
            self.custom_calibrations[name] = calibration_data
            
            # 更新校准类型列表
            self.update_calibration_types()
            
            # 保存到配置文件
            self.save_custom_calibrations()
            
            QMessageBox.information(self, "成功", f"校准类型 '{name}' 已添加")
    
    def delete_calibration_type(self):
        """删除自定义校准类型"""
        current_text = self.cal_type_combo.currentText()
        
        # 检查当前选择的是否为自定义校准类型
        if not current_text.startswith("[自定义] "):
            QMessageBox.warning(self, "错误", "请先选择要删除的自定义校准类型")
            return
        
        # 提取校准类型名称
        cal_name = current_text[5:].strip()
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除自定义校准类型 '{cal_name}' 吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 从自定义校准列表中删除
            if cal_name in self.custom_calibrations:
                del self.custom_calibrations[cal_name]
                
                # 更新校准类型列表
                self.update_calibration_types()
                
                # 保存到配置文件
                self.save_custom_calibrations()
                
                QMessageBox.information(self, "成功", f"自定义校准类型 '{cal_name}' 已删除")
            else:
                QMessageBox.warning(self, "错误", f"校准类型 '{cal_name}' 不存在")
    
    def load_custom_calibrations(self):
        """从配置文件加载自定义校准类型"""
        config_file = "calibration_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.custom_calibrations = data.get('custom_calibrations', {})
                
                # 添加调试日志，查看加载的自定义校准内容
                print(f"DEBUG: 加载的自定义校准配置: {self.custom_calibrations}")
                
                # 加载完成后更新校准类型列表
                self.update_calibration_types()
            except Exception as e:
                print(f"加载配置文件错误: {e}")
    
    def save_custom_calibrations(self):
        """保存自定义校准类型到配置文件"""
        config_file = "calibration_config.json"
        try:
            data = {
                'custom_calibrations': self.custom_calibrations
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件错误: {e}")
    
    def setup_parameter_controls(self):
        """设置参数控制组件"""
        # 清空现有控件和布局
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # 递归删除子布局中的控件
                self.clear_layout(item.layout())
        
        cal_type = self.cal_type_combo.currentText()
        
        # 检查是否为自定义校准类型
        if cal_type.startswith("[自定义] "):
            cal_name = cal_type[5:].strip()  # 移除"[自定义] "前缀，并使用strip()去除前后空格
            self.setup_custom_parameters(cal_name)
        elif cal_type == "B08_B06_DAC_CAL":
            self.setup_dac_parameters()
        elif cal_type == "B08_PWM_CAL":
            self.setup_pwm_parameters()
        elif cal_type == "B06_PWM_CAL_VERIFY":
            self.setup_pwm_verify_parameters()
        elif cal_type == "B08 Ship Mode CAL":
            self.setup_ship_mode_parameters()
        elif cal_type == "COMMON_MANUAL_CAL":
            self.setup_manual_cal_parameyers()
        elif cal_type == "B06_FWDL_设备Stlink_SN维护":
            # 该功能无需参数，提供说明标签
            info_label = QLabel("该功能将逐通道引导插入STLINK并记录SN（共4通道）。")
            info_label.setStyleSheet("color: #666666; font-style: italic;")
            self.params_layout.addWidget(info_label)
        elif cal_type == "B08_FWDL_设备Stlink_SN维护":
            # 该功能无需参数，提供说明标签
            info_label = QLabel("该功能将逐通道引导插入STLINK并记录SN（共4通道）。")
            info_label.setStyleSheet("color: #666666; font-style: italic;")
            self.params_layout.addWidget(info_label)
    
    def clear_layout(self, layout):
        """递归清空布局中的所有控件"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self.clear_layout(item.layout())
    
    def setup_custom_parameters(self, cal_name):
        """设置自定义校准参数"""
        calibration_data = self.custom_calibrations.get(cal_name, {})
        params = calibration_data.get('params', {})
        
        # 添加调试日志
        print(f"DEBUG: setup_custom_parameters called for {cal_name}")
        print(f"DEBUG: calibration_data: {calibration_data}")
        print(f"DEBUG: params: {params}")
        
        if not params:
            self.params_layout.addWidget(QLabel("无参数配置"))
            return
        
        self.custom_param_widgets = {}
        
        for param_name, default_value in params.items():
            param_layout = QHBoxLayout()
            param_layout.addWidget(QLabel(f"{param_name}:"))
            
            # 根据参数类型创建不同的控件
            if isinstance(default_value, (int, float)):
                if isinstance(default_value, int):
                    spin_box = QSpinBox()
                    spin_box.setRange(-10000, 10000)
                    spin_box.setValue(default_value)
                else:
                    spin_box = QDoubleSpinBox()
                    spin_box.setRange(-10000.0, 10000.0)
                    spin_box.setValue(default_value)
                    spin_box.setDecimals(3)
                
                self.custom_param_widgets[param_name] = spin_box
                param_layout.addWidget(spin_box)
            else:
                # 字符串参数
                line_edit = QLineEdit(str(default_value))
                self.custom_param_widgets[param_name] = line_edit
                param_layout.addWidget(line_edit)
            
            param_layout.addStretch()
            self.params_layout.addLayout(param_layout)
        
        # 添加调试日志，显示创建的控件
        print(f"DEBUG: custom_param_widgets created: {list(self.custom_param_widgets.keys())}")
    
    def setup_dac_parameters(self):
        """设置DAC校准参数 - 使用实际函数参数"""
        # EEPROM索引
        index_layout = QHBoxLayout()
        index_layout.addWidget(QLabel("EEPROM索引:"))
        self.dac_index_spin = QSpinBox()
        self.dac_index_spin.setRange(0, 255)
        self.dac_index_spin.setValue(22)
        self.dac_index_spin.setSingleStep(1)
        index_layout.addWidget(self.dac_index_spin)
        index_layout.addStretch()
        self.params_layout.addLayout(index_layout)
        
        # 设置电压
        voltage_layout = QHBoxLayout()
        voltage_layout.addWidget(QLabel("设置电压 (mV):"))
        self.set_voltage_spin = QSpinBox()
        self.set_voltage_spin.setRange(1000, 10000)
        self.set_voltage_spin.setValue(4100)
        self.set_voltage_spin.setSingleStep(100)
        voltage_layout.addWidget(self.set_voltage_spin)
        voltage_layout.addStretch()
        self.params_layout.addLayout(voltage_layout)
        
        # 添加说明标签
        info_label = QLabel("实际DAC校准函数参数 - 基于设备硬件要求")
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        self.params_layout.addWidget(info_label)
    
    def setup_pwm_parameters(self):
        """设置PWM校准参数 - 使用实际函数参数"""
        # 频率
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("频率 (Hz):"))
        self.frequency_spin = QSpinBox()
        self.frequency_spin.setRange(100000, 200000)
        self.frequency_spin.setValue(128000)
        self.frequency_spin.setSingleStep(1000)
        freq_layout.addWidget(self.frequency_spin)
        freq_layout.addStretch()
        self.params_layout.addLayout(freq_layout)
        
        # 占空比
        duty_layout = QHBoxLayout()
        duty_layout.addWidget(QLabel("占空比:"))
        self.duty_cycle_spin = QDoubleSpinBox()
        self.duty_cycle_spin.setRange(0.1, 0.9)
        self.duty_cycle_spin.setValue(0.4)
        self.duty_cycle_spin.setSingleStep(0.1)
        self.duty_cycle_spin.setDecimals(2)
        duty_layout.addWidget(self.duty_cycle_spin)
        duty_layout.addStretch()
        self.params_layout.addLayout(duty_layout)
        
        # EEPROM索引
        index_layout = QHBoxLayout()
        index_layout.addWidget(QLabel("EEPROM索引:"))
        self.pwm_index_spin = QSpinBox()
        self.pwm_index_spin.setRange(0, 255)
        self.pwm_index_spin.setValue(23)
        self.pwm_index_spin.setSingleStep(1)
        index_layout.addWidget(self.pwm_index_spin)
        index_layout.addStretch()
        self.params_layout.addLayout(index_layout)
        
        # 添加说明标签
        info_label = QLabel("实际PWM校准函数参数 - 基于设备硬件要求")
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        self.params_layout.addWidget(info_label)
    
    def setup_pwm_verify_parameters(self):
        """设置PWM校准验证参数 - 使用实际函数参数"""
        # 频率
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("频率 (Hz):"))
        self.verify_frequency_spin = QSpinBox()
        self.verify_frequency_spin.setRange(100000, 200000)
        self.verify_frequency_spin.setValue(128000)
        self.verify_frequency_spin.setSingleStep(1000)
        freq_layout.addWidget(self.verify_frequency_spin)
        freq_layout.addStretch()
        self.params_layout.addLayout(freq_layout)
        
        # 占空比
        duty_layout = QHBoxLayout()
        duty_layout.addWidget(QLabel("占空比:"))
        self.verify_duty_cycle_spin = QDoubleSpinBox()
        self.verify_duty_cycle_spin.setRange(0.1, 0.9)
        self.verify_duty_cycle_spin.setValue(0.4)
        self.verify_duty_cycle_spin.setSingleStep(0.1)
        self.verify_duty_cycle_spin.setDecimals(2)
        duty_layout.addWidget(self.verify_duty_cycle_spin)
        duty_layout.addStretch()
        self.params_layout.addLayout(duty_layout)
        
        # EEPROM索引
        index_layout = QHBoxLayout()
        index_layout.addWidget(QLabel("EEPROM索引:"))
        self.verify_pwm_index_spin = QSpinBox()
        self.verify_pwm_index_spin.setRange(0, 255)
        self.verify_pwm_index_spin.setValue(23)
        self.verify_pwm_index_spin.setSingleStep(1)
        index_layout.addWidget(self.verify_pwm_index_spin)
        index_layout.addStretch()
        self.params_layout.addLayout(index_layout)

        # 添加说明标签
        info_label = QLabel("实际PWM校准验证函数参数 - 基于设备硬件要求")
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        self.params_layout.addWidget(info_label)



    def setup_ship_mode_parameters(self):
        """设置Ship Mode校准参数 - 使用实际函数参数"""
        # 目标电流
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("目标电流 (mA):"))
        self.target_current_spin = QDoubleSpinBox()
        self.target_current_spin.setRange(0.0045, 1.0)
        self.target_current_spin.setValue(0.0045)
        self.target_current_spin.setSingleStep(0.0001)
        self.target_current_spin.setDecimals(5)
        current_layout.addWidget(self.target_current_spin)
        current_layout.addStretch()
        self.params_layout.addLayout(current_layout)
        
        # 添加说明标签
        info_label = QLabel("实际Ship Mode校准函数参数 - 基于设备硬件要求")
        info_label.setStyleSheet("color: #666666; font-style: italic;")
        self.params_layout.addWidget(info_label)
    
    def setup_manual_cal_parameyers(self):
        """设置手动校准参数 - 使用实际函数参数"""
        # index
        index_layout = QHBoxLayout()
        index_layout.addWidget(QLabel("index (int):"))
        self.index_spin = QSpinBox()
        self.index_spin.setRange(0, 255)
        self.index_spin.setValue(1)
        self.index_spin.setSingleStep(2)
        index_layout.addWidget(self.index_spin)
        index_layout.addStretch()
        self.params_layout.addLayout(index_layout)

        # 从映射选择index按钮与来源标签
        choose_layout = QHBoxLayout()
        self.open_index_map_btn = QPushButton("选择工站/项目索引")
        self.open_index_map_btn.clicked.connect(self.open_manual_index_map_dialog)
        choose_layout.addWidget(self.open_index_map_btn)
        self.index_source_label = QLabel("未选择工站/项目")
        self.index_source_label.setStyleSheet("color: #666666; font-style: italic;")
        choose_layout.addWidget(self.index_source_label)
        choose_layout.addStretch()
        self.params_layout.addLayout(choose_layout)

        # 当前测试值（支持浮点）
        currentValue_layout = QHBoxLayout()
        currentValue_layout.addWidget(QLabel("当前测试值:"))
        self.currentValue_spin = QDoubleSpinBox()
        self.currentValue_spin.setRange(-9999.0, 9999.0)
        self.currentValue_spin.setValue(1.0)
        self.currentValue_spin.setSingleStep(0.1)
        self.currentValue_spin.setDecimals(3)
        currentValue_layout.addWidget(self.currentValue_spin)
        currentValue_layout.addStretch()
        self.params_layout.addLayout(currentValue_layout)

        # 目标gain值（支持浮点）
        targetGain_layout = QHBoxLayout()
        targetGain_layout.addWidget(QLabel("目标gain值:"))
        self.targetGain_spin = QDoubleSpinBox()
        self.targetGain_spin.setRange(-9999.0, 9999.0)
        self.targetGain_spin.setValue(1.0)
        self.targetGain_spin.setSingleStep(0.1)
        self.targetGain_spin.setDecimals(3)
        targetGain_layout.addWidget(self.targetGain_spin)
        targetGain_layout.addStretch()
        self.params_layout.addLayout(targetGain_layout)
        # 目标offset值（支持浮点）
        targetOffset_layout = QHBoxLayout()
        targetOffset_layout.addWidget(QLabel("目标offset值:"))
        self.targetOffset_spin = QDoubleSpinBox()
        self.targetOffset_spin.setRange(-9999.0, 9999.0)
        self.targetOffset_spin.setValue(0.0)
        self.targetOffset_spin.setSingleStep(0.1)
        self.targetOffset_spin.setDecimals(3)
        targetOffset_layout.addWidget(self.targetOffset_spin)
        targetOffset_layout.addStretch()
        self.params_layout.addLayout(targetOffset_layout)

        # 监听 index 变化以重置参数
        try:
            self.index_spin.valueChanged.connect(self.reset_manual_cal_params)
        except Exception as e:
            print(f"绑定index变化信号失败: {e}")

    def open_manual_index_map_dialog(self):
        """打开索引映射维护与选择对话框"""
        dlg = ManualIndexMapDialog(mappings=self.manual_index_mappings, parent=self)
        result = dlg.exec()
        # 更新映射（如果在对话框中进行了保存操作，dlg.mappings会更新）
        self.manual_index_mappings = dlg.mappings
        self.save_manual_index_map(self.manual_index_mappings)

        if result == QDialog.Accepted and dlg.selected_entry:
            entry = dlg.selected_entry
            self.selected_index_source = {"workstation": entry["workstation"], "item": entry["item"]}
            self.index_spin.setValue(int(entry["index"]))
            self.index_source_label.setText(f"已选择: {entry['workstation']} / {entry['item']} -> index {entry['index']}")
            # 每次选择新的 index 时，将参数恢复为初始值
            self.reset_manual_cal_params()

    def load_manual_index_map(self):
        """加载手动索引映射"""
        try:
            if os.path.exists(self.manual_index_map_path):
                with open(self.manual_index_map_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.manual_index_mappings = data.get('mappings', [])
            else:
                self.manual_index_mappings = []
        except Exception as e:
            print(f"加载索引映射失败: {e}")
            self.manual_index_mappings = []

    def save_manual_index_map(self, mappings=None):
        """保存手动索引映射"""
        try:
            data = {"mappings": mappings if mappings is not None else self.manual_index_mappings}
            with open(self.manual_index_map_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存索引映射失败: {e}")

    def reset_manual_cal_params(self):
        """将手动校准参数恢复为初始值，避免误写系数"""
        try:
            if hasattr(self, 'currentValue_spin'):
                self.currentValue_spin.setValue(1.0)
            if hasattr(self, 'targetGain_spin'):
                self.targetGain_spin.setValue(1.0)
            if hasattr(self, 'targetOffset_spin'):
                self.targetOffset_spin.setValue(0.0)
        except Exception as e:
            print(f"重置手动校准参数失败: {e}")

    def on_calibration_type_changed(self, text):
        """校准类型改变时的处理"""
        self.setup_parameter_controls()
    
    def load_ports(self):
        """加载可用串口 - 兼容Windows COM口和macOS USB串口"""
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        available_ports = []
        
        # 在Windows上查找COM端口
        com_ports = [port.device for port in ports if port.device.startswith("COM")]
        
        # 在macOS上查找USB串口设备
        usb_ports = [port.device for port in ports if port.device.startswith("/dev/cu.usbmodem")]
        
        # 合并所有可用端口
        available_ports.extend(com_ports)
        available_ports.extend(usb_ports)
        
        if available_ports:
            self.port_combo.addItems(available_ports)
            self.append_colored_log(f"INFO: 找到 {len(available_ports)} 个可用端口:")
            for port in available_ports:
                if port.startswith("COM"):
                    self.append_colored_log(f"INFO:   - Windows COM口: {port}")
                elif port.startswith("/dev/cu.usbmodem"):
                    self.append_colored_log(f"INFO:   - macOS USB串口: {port}")
        else:
            self.append_colored_log("WARNING: 未找到可用的串口设备")
            self.append_colored_log("WARNING: 请检查设备连接或驱动程序安装")
    
    def start_calibration(self):
        """开始校准"""
        if not self.cal_type_combo.currentText():
            QMessageBox.warning(self, "警告", "请先选择校准类型")
            return
        
        # 获取参数
        cal_type = self.cal_type_combo.currentText()
        
        # 针对“设备Stlink_SN维护”，无需选择串口，直接执行维护流程
        if cal_type == "B06_FWDL_设备Stlink_SN维护":
            try:
                self.run_stlink_sn_maintenance()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"执行STLINK维护失败: {e}")
            return

        if cal_type == "B08_FWDL_设备Stlink_SN维护":
            try:
                self.run_stlink_sn_maintenance_edword()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"执行STLINK维护失败: {e}")
            return        


        # 其他类型仍需串口
        if not self.port_combo.currentText():
            QMessageBox.warning(self, "警告", "请先选择端口")
            return
        port = self.port_combo.currentText()
        
        # 处理自定义校准类型
        if cal_type.startswith("[自定义] "):
            cal_name = cal_type[5:].strip()  # 使用strip()去除前后空格
            
            calibration_data = self.custom_calibrations.get(cal_name, {})
            
            function_type = calibration_data.get('function_type', 'builtin')
            custom_function = calibration_data.get('custom_function', '')
            
            # 获取参数值 - 确保custom_param_widgets已初始化
            params = {}
            if hasattr(self, 'custom_param_widgets'):
                for param_name, widget in self.custom_param_widgets.items():
                    if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                        params[param_name] = widget.value()
                    else:
                        params[param_name] = widget.text()
            
            # 添加函数信息到参数中
            params['function_type'] = function_type
            params['custom_function'] = custom_function
            
        else:
            # 获取内置校准类型的参数 - 使用实际函数参数
            params = {}
            if cal_type == "B08_B06_DAC_CAL":
                params = {
                    'index': self.dac_index_spin.value(),
                    'setVoltage': self.set_voltage_spin.value()
                }
            elif cal_type == "B08_PWM_CAL":
                params = {
                    'frequency': self.frequency_spin.value(),
                    'duty': self.duty_cycle_spin.value(),
                    'index': self.pwm_index_spin.value()
                }
            elif cal_type == "B06_PWM_CAL_VERIFY":
                params = {
                    'frequency': self.verify_frequency_spin.value(),
                    'duty': self.verify_duty_cycle_spin.value(),
                    'index': self.verify_pwm_index_spin.value()
                }
            elif cal_type == "B08 Ship Mode CAL":
                params = {
                    'target_current': self.target_current_spin.value()
                }
            elif cal_type == "COMMON_MANUAL_CAL":
                params = {
                    'index' : self.index_spin.value(),
                    'currentValue' : self.currentValue_spin.value(),
                    'targetGain' : self.targetGain_spin.value(),
                    'targetOffset' : self.targetOffset_spin.value()
                }
                if self.selected_index_source:
                    params['index_source'] = self.selected_index_source
        
        # 禁用开始按钮，启用停止按钮
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 启动工作线程
        self.worker = CalibrationWorker(port, cal_type, params)
        self.worker.log_signal.connect(self.append_colored_log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.on_calibration_finished)
        self.worker.start()
        
        self.statusBar().showMessage(f"正在执行{cal_type}校准...")

    def run_stlink_sn_maintenance(self):
        """逐通道维护STLINK的SN，并保存到Windows路径JSON"""
        import subprocess
        import re
        import json
        import os

        # 默认STM32_Programmer_CLI路径（Windows）
        exe_path = r"C:\\Program Files\\STMicroelectronics\\STM32Cube\\STM32CubeProgrammer\\bin\\STM32_Programmer_CLI.exe"
        args = [exe_path, "-l", "stlink"]

        def list_stlink_output():
            try:
                completed = subprocess.run(args, capture_output=True, text=True, timeout=10)
                output = completed.stdout + "\n" + completed.stderr
                return output
            except Exception as e:
                raise RuntimeError(f"无法执行STM32_Programmer_CLI: {e}")

        def parse_probes(output: str):
            # 提取所有Probe块的SN
            sn_list = []
            # 查找所有包含“ST-Link Probe”到下一个空行的块，然后在块内找SN
            blocks = re.split(r"\n-{3,}|\n\s*-----------------------------------------------\s*\n", output)
            # 直接用正则查找所有SN行，较为稳健
            for m in re.finditer(r"ST-LINK SN\s*:\s*([0-9A-Za-z]+)", output):
                sn_list.append(m.group(1).strip())
            return sn_list

        channel_sn = {}

        for ch in range(1, 5):
            # 引导插入该通道的STLINK
            QMessageBox.information(self, "提示", f"请插入通道{ch}的STLINK（仅接一个），点击确定开始检测。")

            while True:
                output = list_stlink_output()
                sns = parse_probes(output)
                count = len(sns)

                # 记录日志，便于跟踪
                self.append_colored_log(f"INFO: 通道{ch}检测到STLINK数量: {count}")

                if count == 1:
                    sn = sns[0]
                    channel_sn[f"slot{ch}_stlink"] = sn
                    self.append_colored_log(f"PASS: 通道{ch}的STLINK SN: {sn}")
                    break
                elif count == 0:
                    reply = QMessageBox.question(
                        self, "未检测到STLINK", "未检测到STLINK，请确认已插入。是否重试？",
                        QMessageBox.Retry | QMessageBox.Cancel
                    )
                    if reply == QMessageBox.Cancel:
                        raise RuntimeError("用户取消STLINK维护流程（未检测到设备）")
                else:
                    reply = QMessageBox.warning(
                        self, "检测到多个STLINK",
                        f"检测到{count}个STLINK，请仅保留一个后重试。",
                        QMessageBox.Retry | QMessageBox.Cancel
                    )
                    if reply == QMessageBox.Cancel:
                        raise RuntimeError("用户取消STLINK维护流程（检测到多个设备）")

        # 保存到Windows路径
        target_dir = r"C:\\Users\\admin\\testerconfig"
        target_path = os.path.join(target_dir, "stlink_config.json")
        try:
            os.makedirs(target_dir, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(channel_sn, f, indent=2, ensure_ascii=False)
            self.append_colored_log(f"PASS: STLINK SN已保存到 {target_path}")
            QMessageBox.information(self, "成功", f"STLINK SN维护完成，并已保存到:\n{target_path}")
        except Exception as e:
            self.append_colored_log(f"ERROR: 保存STLINK配置失败: {e}")
            raise
    
    def run_stlink_sn_maintenance_edword(self):
        """逐通道维护STLINK的SN，并保存到Windows路径JSON"""
        import subprocess
        import re
        import json
        import os

        # 默认STM32_Programmer_CLI路径（Windows）
        exe_path = r"C:\\Program Files\\STMicroelectronics\\STM32Cube\\STM32CubeProgrammer\\bin\\STM32_Programmer_CLI.exe"
        args = [exe_path, "-l", "stlink"]

        def list_stlink_output():
            try:
                completed = subprocess.run(args, capture_output=True, text=True, timeout=10)
                output = completed.stdout + "\n" + completed.stderr
                return output
            except Exception as e:
                raise RuntimeError(f"无法执行STM32_Programmer_CLI: {e}")

        def parse_probes(output: str):
            # 提取所有Probe块的SN
            sn_list = []
            # 查找所有包含“ST-Link Probe”到下一个空行的块，然后在块内找SN
            blocks = re.split(r"\n-{3,}|\n\s*-----------------------------------------------\s*\n", output)
            # 直接用正则查找所有SN行，较为稳健
            for m in re.finditer(r"ST-LINK SN\s*:\s*([0-9A-Za-z]+)", output):
                sn_list.append(m.group(1).strip())
            return sn_list

        channel_sn = {}

        for ch in range(1, 5):
            # 引导插入该通道的STLINK
            QMessageBox.information(self, "提示", f"请插入通道{ch}的STLINK（仅接一个），点击确定开始检测。")

            while True:
                output = list_stlink_output()
                sns = parse_probes(output)
                count = len(sns)

                # 记录日志，便于跟踪
                self.append_colored_log(f"INFO: 通道{ch}检测到STLINK数量: {count}")

                if count == 1:
                    sn = sns[0]
                    channel_sn[f"slot{ch}_stlink"] = sn
                    self.append_colored_log(f"PASS: 通道{ch}的STLINK SN: {sn}")
                    break
                elif count == 0:
                    reply = QMessageBox.question(
                        self, "未检测到STLINK", "未检测到STLINK，请确认已插入。是否重试？",
                        QMessageBox.Retry | QMessageBox.Cancel
                    )
                    if reply == QMessageBox.Cancel:
                        raise RuntimeError("用户取消STLINK维护流程（未检测到设备）")
                else:
                    reply = QMessageBox.warning(
                        self, "检测到多个STLINK",
                        f"检测到{count}个STLINK，请仅保留一个后重试。",
                        QMessageBox.Retry | QMessageBox.Cancel
                    )
                    if reply == QMessageBox.Cancel:
                        raise RuntimeError("用户取消STLINK维护流程（检测到多个设备）")

        # 保存到Windows路径
        target_dir = r"C:\\Users\\Administrator\\testerconfig"
        target_path = os.path.join(target_dir, "stlink_config.json")
        try:
            os.makedirs(target_dir, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(channel_sn, f, indent=2, ensure_ascii=False)
            self.append_colored_log(f"PASS: STLINK SN已保存到 {target_path}")
            QMessageBox.information(self, "成功", f"STLINK SN维护完成，并已保存到:\n{target_path}")
        except Exception as e:
            self.append_colored_log(f"ERROR: 保存STLINK配置失败: {e}")
            raise


    def stop_calibration(self):
        """停止校准"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.terminate()
            self.worker.wait()
        
        self.on_calibration_finished(False, "校准已停止")
    
    def clear_log(self):
        """清除日志内容"""
        self.log_text.clear()
        self.log_text.setHtml("<body style='color: #c8c8c8; background-color: #1e1e1e;'>")
        self.append_colored_log("INFO: 日志已清除")
    
    def on_calibration_finished(self, success, message):
        """校准完成处理"""
        # 恢复按钮状态
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.statusBar().showMessage("校准完成")
            self.append_colored_log(f"PASS: {message}")
        else:
            self.statusBar().showMessage("校准失败")
            self.append_colored_log(f"FAIL: {message}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("设备校准工具")
    app.setApplicationVersion("1.0.1")
    
    # 创建主窗口
    window = CalibrationTool()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()