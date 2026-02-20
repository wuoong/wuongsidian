# 🌳 梧桐知网 (Wutong Knet)

**基于 PyQt6 打造的极客知识库与 RAG 智能学习工作站**

---

## ✨ 核心功能

- **💻 Jupyter 内嵌代码沙盒**: 在 Markdown 中编写 Python 代码块，一键点击 `▶ 运行` 即可在底部控制台查看结果。
- **📋 YAML 自动化看板**: 笔记顶部写入 `status: todo`，即可在看板中通过拖拽自动改写本地源文件状态。
- **🤖 私人 RAG AI 引擎**: 接入 Qwen 2.5 7B 模型，支持读取本地笔记库进行精准问答。
- **🔗 动态知识图谱**: ECharts 驱动的全库笔记关联展示，知识脉络清晰可见。

## 🚀 快速开始

1. **安装依赖**: `pip install -r requirements.txt`
2. **启动程序**: `python main.py`
3. **初始设置**: 首次运行请选择一个本地文件夹作为您的知识库。

## 🛠️ 技术栈
`Python 3.12+` | `PyQt6` | `Markdown` | `ECharts` | `SiliconFlow API`