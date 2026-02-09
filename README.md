# 批量写稿软件

一款基于 AI 的批量文章生成工具，支持导入 Excel 标题，多线程调用 AI API 批量生成文章。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能特点

- 🎨 **现代化界面** - 深色主题 GUI，美观易用
- 📊 **Excel 导入** - 支持 .xlsx/.xls 文件，自动识别列名
- 🤖 **多模型支持** - 兼容 OpenAI、Poe、DeepSeek 等 API
- ⚡ **多线程执行** - 1-10 线程并发，大幅提升效率
- 📁 **自动保存** - 生成内容自动保存为 txt 文件
- ⏸️ **任务控制** - 支持暂停/继续/取消操作

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动软件

```bash
python main.py
```

## 📖 使用说明

1. **配置 API**
   - 填入 API 地址（如 `https://api.poe.com/v1`）
   - 填入 API Key
   - 选择模型名称（如 `claude-sonnet-4`）
   - 编写 Prompt 模板，使用 `{title}` 作为标题占位符

2. **导入标题**
   - 点击「选择文件」导入 Excel
   - 从下拉框选择标题所在列

3. **执行生成**
   - 设置并发线程数
   - 点击「开始执行」
   - 生成的文章保存在 `output` 目录

## 📂 项目结构

```
写文软件/
├── main.py              # 程序入口
├── requirements.txt     # 依赖列表
├── config/
│   └── settings.json    # 配置文件
├── core/
│   ├── api_client.py    # API 调用模块
│   ├── excel_reader.py  # Excel 读取
│   └── task_executor.py # 多线程执行器
├── ui/
│   ├── main_window.py   # 主界面
│   └── styles.qss       # 样式表
└── output/              # 输出目录
```

## ⚙️ 配置说明

编辑 `config/settings.json`：

```json
{
    "api_url": "https://api.poe.com/v1",
    "api_key": "YOUR_API_KEY",
    "model": "claude-sonnet-4",
    "prompt_template": "请根据标题「{title}」写一篇800字文章",
    "max_threads": 3,
    "output_dir": "output"
}
```

## 🔧 支持的 API

| 平台 | API 地址 | 模型示例 |
|------|---------|---------|
| Poe | `https://api.poe.com/v1` | claude-sonnet-4 |
| OpenAI | `https://api.openai.com/v1` | gpt-4o |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat |

## 📝 Prompt 示例

```
请根据以下标题写一篇文章：

标题：{title}

要求：
1. 内容详实，逻辑清晰
2. 字数不少于800字
3. 语言流畅，结构完整
```

## 📄 License

MIT License
