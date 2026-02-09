"""
主窗口模块 - 批量写稿软件 GUI 界面
重新设计的现代化布局
"""

import os
import json
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QTextEdit, QPushButton,
    QComboBox, QSpinBox, QProgressBar, QListWidget,
    QListWidgetItem, QFileDialog, QMessageBox, QApplication,
    QFrame, QRadioButton, QButtonGroup, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from core.api_client import APIClient
from core.excel_reader import ExcelReader
from core.task_executor import TaskExecutor, TaskStatus


class GenerateWorker(QThread):
    """后台生成工作线程"""
    task_started = pyqtSignal(int, str)
    task_completed = pyqtSignal(int, str, bool, str)
    progress_updated = pyqtSignal(int, int)
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


class StatusCard(QFrame):
    """状态卡片组件"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", bg_style: str = ""):
        super().__init__()
        self.setFixedHeight(110)
        self.setMinimumWidth(200)
        
        # 设置背景样式
        self.setStyleSheet(f"""
            StatusCard {{
                {bg_style}
                border-radius: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        
        # 标题
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.9); font-weight: normal; background: transparent;")
        layout.addWidget(self.title_label)
        
        # 数值
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 36px; font-weight: bold; color: white; background: transparent;")
        layout.addWidget(self.value_label)
        
        # 副标题
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.7); background: transparent;")
        layout.addWidget(self.subtitle_label)
        
        layout.addStretch()
    
    def set_value(self, value: str):
        self.value_label.setText(value)
    
    def set_subtitle(self, subtitle: str):
        self.subtitle_label.setText(subtitle)
    
    def set_bg_style(self, bg_style: str):
        self.setStyleSheet(f"""
            StatusCard {{
                {bg_style}
                border-radius: 10px;
            }}
        """)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.excel_reader = ExcelReader()
        self.titles = []
        self.worker = None
        self.today_count = 0
        self.total_count = 0
        self.current_page = "workbench"  # 当前页面
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                        "config", "settings.json")
        
        self.init_ui()
        self.load_config()
        self.apply_styles()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("批量写稿软件")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主水平布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧边栏
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # 右侧堆叠页面
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #f5f5f5;")
        
        # 添加各个页面
        self.stacked_widget.addWidget(self.create_workbench_page())  # 0: 工作台
        self.stacked_widget.addWidget(self.create_config_page())     # 1: 任务配置
        self.stacked_widget.addWidget(self.create_api_page())        # 2: API设置
        self.stacked_widget.addWidget(self.create_about_page())      # 3: 关于我们
        
        main_layout.addWidget(self.stacked_widget, 1)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def create_sidebar(self) -> QWidget:
        """创建左侧边栏"""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(140)
        sidebar.setStyleSheet("""
            #sidebar {
                background-color: #ffffff;
                border-right: 1px solid #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 菜单项配置: (名称, 页面索引)
        menu_items = [
            ("工作台", 0),
            ("任务配置", 1),
            ("API设置", 2),
            ("排版设置", -1),
            ("密钥管理", -1),
            ("使用说明", -1),
            ("关于我们", 3),
        ]
        
        self.menu_buttons = []
        for i, (name, page_index) in enumerate(menu_items):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(i == 0)  # 默认选中第一个
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-left: 3px solid transparent;
                    text-align: left;
                    padding: 15px 20px;
                    color: #666666;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #f8f8f8;
                    color: #333333;
                }
                QPushButton:checked {
                    background-color: #fff5f5;
                    border-left: 3px solid #e74c3c;
                    color: #e74c3c;
                    font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, idx=page_index, b=btn: self.switch_page(idx, b))
            self.menu_buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        return sidebar
    
    def switch_page(self, page_index: int, clicked_btn: QPushButton):
        """切换页面"""
        if page_index >= 0:
            self.stacked_widget.setCurrentIndex(page_index)
        
        # 更新按钮状态
        for btn in self.menu_buttons:
            btn.setChecked(btn == clicked_btn)
    
    def create_workbench_page(self) -> QWidget:
        """创建工作台页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # 顶部状态卡片
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.card_api = StatusCard(
            "API检测", "环境检测", "快速检测API密钥状态",
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);"
        )
        cards_layout.addWidget(self.card_api)
        
        self.card_today = StatusCard(
            "今日创作文章", "0", "",
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #11998e, stop:1 #38ef7d);"
        )
        cards_layout.addWidget(self.card_today)
        
        self.card_total = StatusCard(
            "累计创作文章", "0", "",
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eb3349, stop:1 #f45c43);"
        )
        cards_layout.addWidget(self.card_total)
        
        layout.addLayout(cards_layout)
        
        # 工作模式选择
        mode_layout = QHBoxLayout()
        mode_label = QLabel("工作模式：")
        mode_label.setStyleSheet("font-size: 14px; color: #333;")
        mode_layout.addWidget(mode_label)
        
        self.mode_group = QButtonGroup(self)
        self.mode_excel = QRadioButton("Excel批量生文")
        self.mode_excel.setChecked(True)
        self.mode_excel.setStyleSheet("color: #333; font-size: 14px;")
        self.mode_group.addButton(self.mode_excel)
        mode_layout.addWidget(self.mode_excel)
        
        self.mode_image = QRadioButton("以图生文")
        self.mode_image.setStyleSheet("color: #333; font-size: 14px;")
        self.mode_group.addButton(self.mode_image)
        mode_layout.addWidget(self.mode_image)
        
        mode_layout.addStretch()
        
        # 线程数量
        thread_label = QLabel("线程数量：")
        thread_label.setStyleSheet("font-size: 14px; color: #333;")
        mode_layout.addWidget(thread_label)
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 20)
        self.thread_spin.setValue(3)
        self.thread_spin.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px 10px;
                min-width: 60px;
            }
        """)
        mode_layout.addWidget(self.thread_spin)
        
        layout.addLayout(mode_layout)
        
        # Excel 导入区域
        excel_frame = QFrame()
        excel_frame.setStyleSheet("background: white; border-radius: 8px; padding: 10px;")
        excel_layout = QHBoxLayout(excel_frame)
        
        self.select_file_btn = QPushButton("选择Excel文件")
        self.select_file_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px 20px;
                color: #666;
            }
            QPushButton:hover {
                background: #eee;
            }
        """)
        self.select_file_btn.clicked.connect(self.select_excel_file)
        excel_layout.addWidget(self.select_file_btn)
        
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("color: #999; font-size: 13px;")
        excel_layout.addWidget(self.file_label, 1)
        
        col_label = QLabel("标题列：")
        col_label.setStyleSheet("color: #333;")
        excel_layout.addWidget(col_label)
        self.column_combo = QComboBox()
        self.column_combo.setMinimumWidth(120)
        self.column_combo.setStyleSheet("""
            QComboBox {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self.column_combo.currentTextChanged.connect(self.on_column_changed)
        excel_layout.addWidget(self.column_combo)
        
        self.count_label = QLabel("共 0 条")
        self.count_label.setStyleSheet("color: #666;")
        excel_layout.addWidget(self.count_label)
        
        layout.addWidget(excel_frame)
        
        # 日志显示区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("等待开始...")
        self.log_area.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
                color: #333;
            }
        """)
        layout.addWidget(self.log_area, 1)
        
        # 进度条
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #e0e0e0;
                border: none;
                border-radius: 8px;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #f45c43);
                border-radius: 8px;
            }
        """)
        progress_layout.addWidget(self.progress_bar, 1)
        self.progress_label = QLabel("0/0")
        self.progress_label.setStyleSheet("color: #666; font-weight: bold;")
        progress_layout.addWidget(self.progress_label)
        layout.addLayout(progress_layout)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.start_btn = QPushButton("开始工作")
        self.start_btn.setFixedSize(160, 45)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e74c3c, stop:1 #f45c43);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c0392b, stop:1 #e74c3c);
            }
            QPushButton:disabled {
                background: #ccc;
            }
        """)
        self.start_btn.clicked.connect(self.start_execution)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止工作")
        self.stop_btn.setFixedSize(160, 45)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 8px;
                color: #666;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #eee;
            }
            QPushButton:disabled {
                color: #bbb;
            }
        """)
        self.stop_btn.clicked.connect(self.cancel_execution)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 底部 API Key 快速输入
        key_frame = QFrame()
        key_frame.setStyleSheet("background: white; border-radius: 8px; padding: 5px;")
        key_layout = QHBoxLayout(key_frame)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入您的 API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                background: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #9b59b6;
            }
        """)
        key_layout.addWidget(self.api_key_input, 1)
        
        self.verify_btn = QPushButton("验证卡密")
        self.verify_btn.setFixedSize(100, 42)
        self.verify_btn.setStyleSheet("""
            QPushButton {
                background: #9b59b6;
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #8e44ad;
            }
        """)
        self.verify_btn.clicked.connect(self.test_connection)
        key_layout.addWidget(self.verify_btn)
        
        layout.addWidget(key_frame)
        
        return page
    
    def create_config_page(self) -> QWidget:
        """创建任务配置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("任务配置")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        # Prompt 模板配置
        prompt_group = QGroupBox("Prompt 模板")
        prompt_group.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 15px;
                padding: 20px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #333;
            }
        """)
        prompt_layout = QVBoxLayout(prompt_group)
        
        prompt_hint = QLabel("使用 {title} 作为文章标题占位符")
        prompt_hint.setStyleSheet("color: #999; font-size: 12px; font-weight: normal;")
        prompt_layout.addWidget(prompt_hint)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("请输入 Prompt 模板...")
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                background: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self.prompt_input.setMinimumHeight(150)
        prompt_layout.addWidget(self.prompt_input)
        
        layout.addWidget(prompt_group)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_group.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 15px;
                padding: 20px;
                font-weight: bold;
            }
        """)
        output_layout = QHBoxLayout(output_group)
        
        output_layout.addWidget(QLabel("输出目录："))
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText("output")
        self.output_dir_input.setStyleSheet("""
            QLineEdit {
                background: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        output_layout.addWidget(self.output_dir_input, 1)
        
        select_dir_btn = QPushButton("选择目录")
        select_dir_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #eee;
            }
        """)
        select_dir_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(select_dir_btn)
        
        open_dir_btn = QPushButton("打开目录")
        open_dir_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        open_dir_btn.clicked.connect(self.open_output_dir)
        output_layout.addWidget(open_dir_btn)
        
        layout.addWidget(output_group)
        
        # 保存按钮
        save_btn = QPushButton("保存配置")
        save_btn.setFixedSize(150, 45)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2ecc71;
            }
        """)
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addStretch()
        
        return page
    
    def create_api_page(self) -> QWidget:
        """创建API设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("API 设置")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        # API 配置
        api_group = QGroupBox("API 配置")
        api_group.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 15px;
                padding: 20px;
                font-weight: bold;
            }
        """)
        api_layout = QGridLayout(api_group)
        api_layout.setSpacing(15)
        
        api_layout.addWidget(QLabel("API 地址："), 0, 0)
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("例如: https://api.poe.com/v1")
        self.api_url_input.setStyleSheet("""
            QLineEdit {
                background: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        api_layout.addWidget(self.api_url_input, 0, 1)
        
        api_layout.addWidget(QLabel("模型名称："), 1, 0)
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("例如: claude-sonnet-4")
        self.model_input.setStyleSheet("""
            QLineEdit {
                background: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        api_layout.addWidget(self.model_input, 1, 1)
        
        layout.addWidget(api_group)
        
        # 保存按钮
        save_api_btn = QPushButton("保存API配置")
        save_api_btn.setFixedSize(150, 45)
        save_api_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2ecc71;
            }
        """)
        save_api_btn.clicked.connect(self.save_config)
        layout.addWidget(save_api_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addStretch()
        
        return page
    
    def create_about_page(self) -> QWidget:
        """创建关于页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("关于我们")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        # 关于内容
        about_frame = QFrame()
        about_frame.setStyleSheet("background: white; border-radius: 8px; padding: 30px;")
        about_layout = QVBoxLayout(about_frame)
        
        app_name = QLabel("批量写稿软件")
        app_name.setStyleSheet("font-size: 24px; font-weight: bold; color: #e74c3c;")
        about_layout.addWidget(app_name, alignment=Qt.AlignmentFlag.AlignCenter)
        
        version = QLabel("版本 1.0.0")
        version.setStyleSheet("font-size: 14px; color: #666;")
        about_layout.addWidget(version, alignment=Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel("基于 AI 的批量文章生成工具\n支持 Excel 导入标题，多线程并发调用 API")
        desc.setStyleSheet("font-size: 14px; color: #666; margin-top: 20px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(desc)
        
        layout.addWidget(about_frame)
        layout.addStretch()
        
        return page
    
    def apply_styles(self):
        """应用样式表"""
        style_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                base_style = f.read()
                # 合并基础样式
                self.setStyleSheet(self.styleSheet() + base_style)
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_key_input.setText(config.get("api_key", ""))
                    self.api_url_input.setText(config.get("api_url", "https://api.poe.com/v1"))
                    self.model_input.setText(config.get("model", "claude-sonnet-4"))
                    self.prompt_input.setPlainText(config.get("prompt_template", ""))
                    self.output_dir_input.setText(config.get("output_dir", "output"))
                    self.thread_spin.setValue(config.get("max_threads", 3))
                    self.total_count = config.get("total_count", 0)
                    self.card_total.set_value(str(self.total_count))
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
                "output_dir": self.output_dir_input.text(),
                "total_count": self.total_count
            }
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            self.statusBar().showMessage("配置已保存", 3000)
            QMessageBox.information(self, "成功", "配置已保存！")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存配置失败: {e}")
    
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
            os.makedirs(output_dir, exist_ok=True)
            os.startfile(output_dir)
    
    def log(self, message: str):
        """添加日志"""
        self.log_area.append(message)
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def test_connection(self):
        """测试 API 连接"""
        api_key = self.api_key_input.text()
        
        if not api_key:
            QMessageBox.warning(self, "提示", "请先输入 API Key")
            return
        
        self.verify_btn.setEnabled(False)
        self.verify_btn.setText("验证中...")
        self.log("正在验证 API 密钥...")
        QApplication.processEvents()
        
        api_url = self.api_url_input.text() or "https://api.poe.com/v1"
        model = self.model_input.text() or "claude-sonnet-4"
        
        client = APIClient(api_url, api_key, model)
        success, message = client.test_connection()
        
        self.verify_btn.setEnabled(True)
        self.verify_btn.setText("验证卡密")
        
        if success:
            self.card_api.set_value("已连接")
            self.card_api.set_bg_style("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #11998e, stop:1 #38ef7d);")
            self.log("✓ API 密钥验证成功！")
            self.save_config()
            QMessageBox.information(self, "成功", message)
        else:
            self.card_api.set_value("连接失败")
            self.log(f"✗ API 验证失败: {message}")
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
                self.file_label.setStyleSheet("color: #27ae60; font-size: 13px;")
                columns = self.excel_reader.get_columns()
                self.column_combo.clear()
                self.column_combo.addItems(columns)
                self.log(f"✓ 已加载文件: {os.path.basename(file_path)}")
                self.statusBar().showMessage(message, 3000)
            else:
                self.log(f"✗ 加载失败: {message}")
                QMessageBox.warning(self, "错误", message)
    
    def on_column_changed(self, column_name: str):
        """当选择的列改变时"""
        if column_name:
            self.titles = self.excel_reader.get_titles(column_name)
            self.count_label.setText(f"共 {len(self.titles)} 条")
            self.log(f"已选择列「{column_name}」，共 {len(self.titles)} 条标题")
    
    def start_execution(self):
        """开始执行"""
        api_key = self.api_key_input.text()
        if not api_key:
            QMessageBox.warning(self, "提示", "请先输入并验证 API Key")
            return
        
        if not self.titles:
            QMessageBox.warning(self, "提示", "请先导入 Excel 并选择标题列")
            return
        
        api_url = self.api_url_input.text() or "https://api.poe.com/v1"
        model = self.model_input.text() or "claude-sonnet-4"
        prompt = self.prompt_input.toPlainText() or "请根据标题「{title}」写一篇文章"
        output_dir = self.output_dir_input.text() or "output"
        
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir)
        
        self.log_area.clear()
        self.log(f"开始批量生成，共 {len(self.titles)} 条任务")
        self.log(f"使用模型: {model}")
        self.log(f"线程数: {self.thread_spin.value()}")
        self.log("-" * 40)
        
        api_client = APIClient(api_url, api_key, model)
        
        self.worker = GenerateWorker(
            api_client, 
            self.titles, 
            prompt,
            output_dir,
            self.thread_spin.value()
        )
        
        self.worker.task_started.connect(self.on_task_started)
        self.worker.task_completed.connect(self.on_task_completed)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.all_completed.connect(self.on_all_completed)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.titles))
        
        self.worker.start()
        self.statusBar().showMessage("正在执行...")
    
    def cancel_execution(self):
        """取消执行"""
        if self.worker:
            reply = QMessageBox.question(
                self, "确认", "确定要停止工作吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.cancel()
                self.log("正在停止...")
                self.statusBar().showMessage("正在取消...")
    
    def on_task_started(self, index: int, title: str):
        """任务开始回调"""
        short_title = title[:30] + "..." if len(title) > 30 else title
        self.log(f"[{index + 1}] 正在生成: {short_title}")
    
    def on_task_completed(self, index: int, title: str, success: bool, result: str):
        """任务完成回调"""
        short_title = title[:30] + "..." if len(title) > 30 else title
        if success:
            self.log(f"[{index + 1}] ✓ 完成: {short_title}")
            self.today_count += 1
            self.total_count += 1
            self.card_today.set_value(str(self.today_count))
            self.card_total.set_value(str(self.total_count))
        else:
            self.log(f"[{index + 1}] ✗ 失败: {short_title} - {result}")
    
    def on_progress_updated(self, completed: int, total: int):
        """进度更新回调"""
        self.progress_bar.setValue(completed)
        self.progress_label.setText(f"{completed}/{total}")
    
    def on_all_completed(self):
        """全部完成回调"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_config()
        
        self.log("-" * 40)
        self.log(f"全部完成！成功: {self.today_count} 篇")
        self.statusBar().showMessage("执行完成！")
        QMessageBox.information(self, "完成", f"所有任务已执行完成！\n本次生成: {self.today_count} 篇")
    
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
                self.save_config()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_config()
            event.accept()
