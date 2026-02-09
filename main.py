"""
批量写稿软件 - 主程序入口
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui.main_window import MainWindow


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


##测试