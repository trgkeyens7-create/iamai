"""
主窗口模块 - 批量写稿软件 GUI 界面
"""

import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QTextEdit, QPushButton,
    QComboBox, QSpinBox, QSlider, QProgressBar, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

from core.api_client import APIClient
from core.excel_reader import ExcelReader
from core.task_executor import TaskExecutor, TaskStatus


class GenerateWorker(QThread):
    """后台生成工作线程"""
    task_started = pyqtSignal(int, str)  # index, title
    task_completed = pyqtSignal(int, str, bool, str)  # index, title, success, result
    progress_updated = pyqtSignal(int, int)  # completed, total
    all_completed = pyqtSignal()
    
    def __init__(self, api_client: APIClient, titles: list, prompt: str, output_dir: str, max_workers: int):
        super().__init__()
        self.api_client = api_client
        self.titles = titles
        self.prompt = prompt
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.executor = TaskExecutor(max_workers=max_workers)
        
    def run(self):
        self.executor.on_task_start = lambda idx, title: self.task_started.emit(idx, title)
        self.executor.on_task_complete = lambda idx, title, success, result: self.task_completed.emit(idx, title, success, result)
        self.executor.on_progress = lambda done, total: self.progress_updated.emit(done, total)
        self.executor.on_all_complete = lambda: self.all_completed.emit()
        
        self.executor.set_tasks(self.titles)
        
        def process_func(title: str) -> tuple:
            return self.api_client.generate_article(title, self.prompt)
        
        self.executor.start(process_func, self.output_dir)
        
        # 等待执行完成
        while self.executor.is_running:
            self.msleep(100)
    
    def pause(self):
        self.executor.pause()
    
    def resume(self):
        self.executor.resume()
    
    def cancel(self):
        self.executor.cancel()
    
    @property
    def is_paused(self):
        return self.executor.is_paused


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.excel_reader = ExcelReader()
        self.titles = []
        self.worker = None
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                        "config", "settings.json")
        
        self.init_ui()
        self.load_config()
        self.apply_styles()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("批量写稿软件")
        self.setMinimumSize(800, 700)
        self.resize(900, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # API 设置组
        api_group = self.create_api_group()
        main_layout.addWidget(api_group)
        
        # Excel 导入组
        excel_group = self.create_excel_group()
        main_layout.addWidget(excel_group)
        
        # 执行设置组
        exec_group = self.create_exec_group()
        main_layout.addWidget(exec_group)
        
        # 执行状态组
        status_group = self.create_status_group()
        main_layout.addWidget(status_group, 1)  # 拉伸
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def create_api_group(self) -> QGroupBox:
        """创建 API 设置组"""
        group = QGroupBox("API 设置")
        layout = QGridLayout(group)
        layout.setSpacing(10)
        
        # API 地址
        layout.addWidget(QLabel("API 地址:"), 0, 0)
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("例如: https://api.openai.com/v1")
        layout.addWidget(self.api_url_input, 0, 1)
        
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_btn, 0, 2)
        
        # API Key
        layout.addWidget(QLabel("API Key:"), 1, 0)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("输入您的 API Key")
        layout.addWidget(self.api_key_input, 1, 1, 1, 2)
        
        # 模型名称
        layout.addWidget(QLabel("模型名称:"), 2, 0)
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("例如: gpt-3.5-turbo, deepseek-chat")
        layout.addWidget(self.model_input, 2, 1, 1, 2)
        
        # Prompt 模板
        layout.addWidget(QLabel("Prompt:"), 3, 0, Qt.AlignmentFlag.AlignTop)
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("使用 {title} 作为标题占位符")
        self.prompt_input.setMaximumHeight(100)
        layout.addWidget(self.prompt_input, 3, 1, 1, 2)
        
        # 保存配置按钮
        save_btn = QPushButton("保存配置")
        save_btn.setProperty("secondary", True)
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn, 4, 2)
        
        return group
    
    def create_excel_group(self) -> QGroupBox:
        """创建 Excel 导入组"""
        group = QGroupBox("Excel 导入")
        layout = QHBoxLayout(group)
        layout.setSpacing(15)
        
        self.select_file_btn = QPushButton("选择文件")
        self.select_file_btn.clicked.connect(self.select_excel_file)
        layout.addWidget(self.select_file_btn)
        
        self.file_label = QLabel("未选择文件")
        layout.addWidget(self.file_label, 1)
        
        layout.addWidget(QLabel("标题列:"))
        self.column_combo = QComboBox()
        self.column_combo.setMinimumWidth(150)
        self.column_combo.currentTextChanged.connect(self.on_column_changed)
        layout.addWidget(self.column_combo)
        
        self.count_label = QLabel("共 0 条标题")
        layout.addWidget(self.count_label)
        
        return group
    
    def create_exec_group(self) -> QGroupBox:
        """创建执行设置组"""
        group = QGroupBox("执行设置")
        layout = QHBoxLayout(group)
        layout.setSpacing(15)
        
        # 线程数
        layout.addWidget(QLabel("线程数:"))
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 10)
        self.thread_spin.setValue(3)
        layout.addWidget(self.thread_spin)
        
        # 输出目录
        layout.addWidget(QLabel("输出目录:"))
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText("output")
        layout.addWidget(self.output_dir_input, 1)
        
        self.select_output_btn = QPushButton("选择")
        self.select_output_btn.setProperty("secondary", True)
        self.select_output_btn.clicked.connect(self.select_output_dir)
        layout.addWidget(self.select_output_btn)
        
        self.open_output_btn = QPushButton("打开")
        self.open_output_btn.setProperty("secondary", True)
        self.open_output_btn.clicked.connect(self.open_output_dir)
        layout.addWidget(self.open_output_btn)
        
        layout.addStretch()
        
        # 控制按钮
        self.start_btn = QPushButton("开始执行")
        self.start_btn.clicked.connect(self.start_execution)
        layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setProperty("secondary", True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        layout.addWidget(self.pause_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setProperty("secondary", True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_execution)
        layout.addWidget(self.cancel_btn)
        
        return group
    
    def create_status_group(self) -> QGroupBox:
        """创建执行状态组"""
        group = QGroupBox("执行状态")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar, 1)
        self.progress_label = QLabel("0/0")
        progress_layout.addWidget(self.progress_label)
        layout.addLayout(progress_layout)
        
        # 任务列表
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)
        
        return group
    
    def apply_styles(self):
        """应用样式表"""
        style_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_url_input.setText(config.get("api_url", ""))
                    self.api_key_input.setText(config.get("api_key", ""))
                    self.model_input.setText(config.get("model", "gpt-3.5-turbo"))
                    self.prompt_input.setPlainText(config.get("prompt_template", ""))
                    self.thread_spin.setValue(config.get("max_threads", 3))
                    self.output_dir_input.setText(config.get("output_dir", "output"))
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置"""
        try:
            config = {
                "api_url": self.api_url_input.text(),
                "api_key": self.api_key_input.text(),
                "model": self.model_input.text(),
                "prompt_template": self.prompt_input.toPlainText(),
                "max_threads": self.thread_spin.value(),
                "output_dir": self.output_dir_input.text()
            }
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            self.statusBar().showMessage("配置已保存", 3000)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存配置失败: {e}")
    
    def test_connection(self):
        """测试 API 连接"""
        api_url = self.api_url_input.text()
        api_key = self.api_key_input.text()
        model = self.model_input.text()
        
        if not api_url or not api_key:
            QMessageBox.warning(self, "提示", "请先输入 API 地址和 API Key")
            return
        
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        QApplication.processEvents()
        
        client = APIClient(api_url, api_key, model)
        success, message = client.test_connection()
        
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试连接")
        
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "失败", message)
    
    def select_excel_file(self):
        """选择 Excel 文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Excel 文件", "",
            "Excel 文件 (*.xlsx *.xls);;所有文件 (*)"
        )
        
        if file_path:
            success, message = self.excel_reader.load_file(file_path)
            
            if success:
                self.file_label.setText(os.path.basename(file_path))
                
                # 更新列选择
                columns = self.excel_reader.get_columns()
                self.column_combo.clear()
                self.column_combo.addItems(columns)
                
                self.statusBar().showMessage(message, 3000)
            else:
                QMessageBox.warning(self, "错误", message)
    
    def on_column_changed(self, column_name: str):
        """当选择的列改变时"""
        if column_name:
            self.titles = self.excel_reader.get_titles(column_name)
            self.count_label.setText(f"共 {len(self.titles)} 条标题")
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_input.setText(dir_path)
    
    def open_output_dir(self):
        """打开输出目录"""
        output_dir = self.output_dir_input.text()
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir)
        
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            QMessageBox.warning(self, "提示", "输出目录不存在")
    
    def start_execution(self):
        """开始执行"""
        # 验证
        if not self.api_url_input.text() or not self.api_key_input.text():
            QMessageBox.warning(self, "提示", "请先配置 API 参数")
            return
        
        if not self.titles:
            QMessageBox.warning(self, "提示", "请先导入 Excel 并选择标题列")
            return
        
        prompt = self.prompt_input.toPlainText()
        if not prompt:
            QMessageBox.warning(self, "提示", "请输入 Prompt 模板")
            return
        
        # 确定输出目录
        output_dir = self.output_dir_input.text()
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir)
        
        # 清空任务列表
        self.task_list.clear()
        for i, title in enumerate(self.titles):
            item = QListWidgetItem(f"[等待] {title}")
            self.task_list.addItem(item)
        
        # 创建 API 客户端
        api_client = APIClient(
            self.api_url_input.text(),
            self.api_key_input.text(),
            self.model_input.text()
        )
        
        # 创建工作线程
        self.worker = GenerateWorker(
            api_client, 
            self.titles, 
            prompt,
            output_dir,
            self.thread_spin.value()
        )
        
        # 连接信号
        self.worker.task_started.connect(self.on_task_started)
        self.worker.task_completed.connect(self.on_task_completed)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.all_completed.connect(self.on_all_completed)
        
        # 更新 UI 状态
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.titles))
        
        # 开始执行
        self.worker.start()
        self.statusBar().showMessage("正在执行...")
    
    def toggle_pause(self):
        """切换暂停/继续"""
        if self.worker:
            if self.worker.is_paused:
                self.worker.resume()
                self.pause_btn.setText("暂停")
                self.statusBar().showMessage("继续执行...")
            else:
                self.worker.pause()
                self.pause_btn.setText("继续")
                self.statusBar().showMessage("已暂停")
    
    def cancel_execution(self):
        """取消执行"""
        if self.worker:
            reply = QMessageBox.question(
                self, "确认", "确定要取消执行吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self.statusBar().showMessage("正在取消...")
    
    def on_task_started(self, index: int, title: str):
        """任务开始回调"""
        item = self.task_list.item(index)
        if item:
            item.setText(f"[处理中] {title}")
            self.task_list.scrollToItem(item)
    
    def on_task_completed(self, index: int, title: str, success: bool, result: str):
        """任务完成回调"""
        item = self.task_list.item(index)
        if item:
            if success:
                item.setText(f"[成功] {title}")
            else:
                item.setText(f"[失败] {title} - {result}")
    
    def on_progress_updated(self, completed: int, total: int):
        """进度更新回调"""
        self.progress_bar.setValue(completed)
        self.progress_label.setText(f"{completed}/{total}")
    
    def on_all_completed(self):
        """全部完成回调"""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("暂停")
        self.cancel_btn.setEnabled(False)
        
        self.statusBar().showMessage("执行完成！")
        QMessageBox.information(self, "完成", "所有任务已执行完成！")
    
    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认", "任务正在执行中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self.worker.wait(3000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
